import json
import traceback
import hmac
import hashlib
import google.auth
import vertexai
from datetime import datetime
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Response
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build

from src.logic import handle_guanacloud_logic
from src.tasks.summary_task import send_daily_summaries
from src.utils.database_client import registrar_feedback, upsert_user
from src.services.memory_service import get_or_create_active_session, set_session_state
from src.services.ticket_manager import _create_ticket_with_assigned_lead, agendar_reunion_gcalendar
from src.tools.create_kb_index import create_knowledge_base_index
from src.services.github_service import ejecutar_revision_de_codigo
from src.config import settings

print("🚀 Inicializando la aplicación y Vertex AI...")
vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.LOCATION)
print("✅ Vertex AI inicializado.")

# CAMBIO: Se actualiza el título y la descripción de la API.
app = FastAPI(
    title="GuanaCloud Platform API",
    description="API para el asistente de la plataforma GuanaCloud.",
    version="1.0.0"
)

def create_chat_message_sync(space_name: str, thread_name: str, message_body: dict | str):
    """
    Función síncrona para crear mensajes en Google Chat.
    Se ejecuta en un hilo separado por la tarea de fondo.
    """
    try:
        creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/chat.bot'])
        creds.refresh(GoogleAuthRequest())
        chat_service = build('chat', 'v1', credentials=creds)

        payload = {"thread": {"name": thread_name}}
        if isinstance(message_body, str):
            payload["text"] = message_body
        elif isinstance(message_body, dict):
            payload.update(message_body)

        print(f"🚀 Creando mensaje en el space (asíncrono): {space_name}")
        chat_service.spaces().messages().create(parent=space_name, body=payload).execute()
        print("✅ Mensaje asíncrono creado exitosamente.")
    except Exception as e:
        print(f"🔴 Error fatal al crear mensaje asíncrono: {e}")


def background_logic_runner(space_name: str, thread_name: str, user_message: str, user_info: dict, attachment_url: str | None, attachment_name: str | None):
    """
    Wrapper para la tarea de fondo que ejecuta la lógica principal y envía la respuesta.
    """
    # CAMBIO: Se llama a la función de lógica con el nuevo nombre.
    response_data = handle_guanacloud_logic(
        user_message=user_message,
        user_email=user_info.get("email"),
        user_display_name=user_info.get("displayName"),
        user_id=user_info.get("name"),
        attachment_url=attachment_url,
        attachment_name=attachment_name
    )
    create_chat_message_sync(space_name, thread_name, response_data)

@app.post("/")
async def handle_chat_event(request: Request, background_tasks: BackgroundTasks):
    """Punto de entrada principal para todos los eventos de Google Chat."""
    event_data = await request.json()
    try:
        event_type = event_data.get('type')

        if event_type == 'MESSAGE':
            space_info = event_data.get('space', {})
            space_type = space_info.get('type')

            if space_type == 'ROOM':
                print("▶️  Detectada interacción en una Sala (ROOM). Usando modo ASÍNCRONO.")
                background_tasks.add_task(
                    background_logic_runner,
                    space_name=space_info.get('name'),
                    thread_name=event_data.get('message', {}).get('thread', {}).get('name'),
                    user_message=event_data.get('message', {}).get('text', '').strip(),
                    user_info=event_data.get('user', {}),
                    attachment_url=event_data.get('message', {}).get('attachment', [{}])[0].get('downloadUri'),
                    attachment_name=event_data.get('message', {}).get('attachment', [{}])[0].get('name')
                )
                return {"text": "Procesando tu consulta... ⏳"}
            else: 
                print("▶️  Detectada interacción en un DM. Usando modo SÍNCRONO.")
                user_info = event_data.get('user', {})
                attachment = event_data.get('message', {}).get('attachment', [{}])[0]
                # CAMBIO: Se llama a la función de lógica con el nuevo nombre.
                return handle_guanacloud_logic(
                    user_message=event_data.get('message', {}).get('text', '').strip(),
                    user_email=user_info.get("email"),
                    user_display_name=user_info.get("displayName"),
                    user_id=user_info.get("name"),
                    attachment_url=attachment.get('downloadUri'),
                    attachment_name=attachment.get('name')
                )

        elif event_type == 'CARD_CLICKED':
            # ... (El resto de la lógica de esta sección no necesita cambios)
            action = event_data.get('common', {}).get('invokedFunction')
            user_info = event_data.get('user', {})
            user_email = user_info.get("email")
            user_id = user_info.get("name")
            session_id, session_state_str = get_or_create_active_session(user_id)

            if action == 'submit_agendar_reunion_form':
                form_inputs = event_data.get('common', {}).get('formInputs', {})
                titulo = form_inputs.get('titulo_reunion', {}).get('stringInputs', {}).get('value', [''])[0]

                timestamp_ms = form_inputs.get('fecha_hora_reunion', {}).get('dateTimeInput', {}).get('msSinceEpoch')
                dt_object = datetime.fromtimestamp(int(timestamp_ms) / 1000)
                fecha = dt_object.strftime('%Y-%m-%d')
                hora = dt_object.strftime('%H:%M')

                duracion_str = form_inputs.get('duracion', {}).get('stringInputs', {}).get('value', ['30'])[0]
                duracion = int(duracion_str) if duracion_str.isdigit() else 30

                invitados_str = form_inputs.get('invitados', {}).get('stringInputs', {}).get('value', [''])[0]
                invitados_adicionales = [email.strip() for email in invitados_str.split(',') if email.strip()]

                if not titulo:
                    return {"actionResponse": {"type": "UPDATE_MESSAGE"}, "text": "🔴 Error: El título de la reunión es obligatorio."}

                response_json_str = agendar_reunion_gcalendar(
                    titulo_reunion=titulo,
                    fecha_reunion=fecha,
                    hora_reunion=hora,
                    solicitante_email=user_email,
                    duracion_minutos=duracion,
                    email_invitados_adicionales=invitados_adicionales
                )

                response_data = json.loads(response_json_str)
                card_final = {
                    "header": {"title": "Invitación Lista para Enviar"},
                    "sections": [{"widgets": [{"textParagraph": {"text": response_data["message"]}},{"buttonList": {"buttons": [{"text": "Abrir y Guardar en Google Calendar","onClick": {"openLink": {"url": response_data["url"]}}}]}}]}]
                }
                return {"actionResponse": {"type": "UPDATE_MESSAGE"}, "cardsV2": [{"cardId": "calendar_final_card", "card": card_final}]}

            if action == 'assign_to_lead':
                session_data = json.loads(session_state_str)
                if session_data.get("state") == "AWAITING_LEAD_ASSIGNMENT":
                    ticket_details = session_data.get("ticket_details")
                    selected_lead = event_data.get('common', {}).get('parameters', {}).get('lead_email')

                    final_response = _create_ticket_with_assigned_lead(
                        ticket_details=ticket_details,
                        responsable=selected_lead,
                        solicitante_email=user_email,
                        solicitante_nombre=user_info.get("displayName"),
                        attachment_url=ticket_details.get("attachment_url"),
                        attachment_name=ticket_details.get("attachment_name")
                    )
                    set_session_state(user_id, None)
                    return {"actionResponse": {"type": "UPDATE_MESSAGE"}, "text": final_response}

            if action == 'submit_user_management_form':
                form_inputs = event_data.get('common', {}).get('formInputs', {})
                email_to_manage = form_inputs.get('user_email', {}).get('stringInputs', {}).get('value', [''])[0]
                new_role = form_inputs.get('role', {}).get('stringInputs', {}).get('value', [''])[0]
                department_selection = form_inputs.get('department', {}).get('stringInputs', {}).get('value', [''])[0]

                if department_selection == '__create_new__':
                    final_department = form_inputs.get('new_department_name', {}).get('stringInputs', {}).get('value', [''])[0]
                else:
                    final_department = department_selection

                if not all([email_to_manage, new_role, final_department]):
                    return {"actionResponse": {"type": "UPDATE_MESSAGE"}, "text": "🔴 Error: Todos los campos son obligatorios."}

                result_message = upsert_user(email_to_manage, new_role, final_department)
                return {"actionResponse": {"type": "UPDATE_MESSAGE"}, "text": f"✅ Operación completada: {result_message}"}

            response_card = { "actionResponse": { "type": "UPDATE_MESSAGE" } }
            if action == 'register_feedback_positive':
                registrar_feedback(session_id, user_email, 1)
                response_card["text"] = "¡Gracias por tu feedback positivo!"
                return response_card

            elif action == 'register_feedback_negative':
                registrar_feedback(session_id, user_email, 0)
                set_session_state(user_id, json.dumps({'state': 'AWAITING_FEEDBACK_COMMENT'}))
                response_card["text"] = "Lamento tu experiencia. ¿Podrías darme más detalles para mejorar?"
                return response_card

            return {}

        elif event_type == 'ADDED_TO_SPACE':
            # CAMBIO: Se actualiza el mensaje de bienvenida.
            return {"text": "¡Gracias por añadirme! Soy el asistente de GuanaCloud Platform, listo para ayudarte."}

        return {}
    except Exception as e:
        print(json.dumps({"log_name": "HandleChatEvent_Error", "error": str(e), "traceback": traceback.format_exc()}))
        raise HTTPException(status_code=500, detail="Error interno del servidor.")

# ... (El resto de los endpoints /run-summary, /run-kb-index, /github-webhook no necesitan cambios)
@app.post("/run-summary")
async def handle_summary_trigger():
    print("🚀 Tarea de resumen diario iniciada.")
    try:
        send_daily_summaries()
        return Response(content="Tarea de resumen completada.", status_code=200)
    except Exception as e:
        print(f"🔴 Error ejecutando la tarea de resumen: {e}")
        raise HTTPException(status_code=500, detail="Error en la tarea.")

@app.post("/run-kb-index")
async def handle_kb_index_trigger():
    print("🚀 Tarea de re-indexación de KB iniciada.")
    try:
        create_knowledge_base_index()
        return Response(content="Tarea de indexación completada.", status_code=200)
    except Exception as e:
        print(f"🔴 Error ejecutando la tarea de indexación: {e}")
        raise HTTPException(status_code=500, detail="Error en la tarea.")

@app.post("/github-webhook")
async def handle_github_webhook(request: Request, background_tasks: BackgroundTasks):
    signature = request.headers.get("X-Hub-Signature-265")
    if not signature:
        raise HTTPException(status_code=403, detail="Signature header missing")

    sha_name, signature_hash = signature.split("=", 1)
    if sha_name != "sha256":
        raise HTTPException(status_code=403, detail="Invalid signature format")

    mac = hmac.new(settings.GITHUB_WEBHOOK_SECRET.encode(), msg=await request.body(), digestmod=hashlib.sha256)
    if not hmac.compare_digest(mac.hexdigest(), signature_hash):
        raise HTTPException(status_code=403, detail="Invalid signature")

    event_data = await request.json()
    if event_data.get("action") in ["opened", "reopened", "synchronize"]:
        pr_number = event_data.get("number")
        print(f"🚀  Revisión de código iniciada para el PR #{pr_number}")
        background_tasks.add_task(ejecutar_revision_de_codigo, event_data)

    return {"status": "received"}