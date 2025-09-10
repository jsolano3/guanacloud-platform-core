import json
import traceback
from vertexai.generative_models import GenerativeModel, Part
from src.config import settings
from src.services import ticket_manager, ticket_visualizer, query_service, admin_service, looker_service, drafting_service, dwh_query_service
from src.tools.tool_definitions import all_tools_config
from src.services.memory_service import get_chat_history, save_chat_history, get_or_create_active_session, set_session_state
from src.utils.database_client import obtener_rol_usuario, actualizar_feedback_comentario
from src.services.knowledge_service import search_knowledge_base
from src.utils.prompt_loader import load_prompt_from_file

system_prompt = load_prompt_from_file("system_prompt.md")

available_tools = {
    "crear_tiquete_helpdesk": ticket_manager.crear_tiquete,
    "consultar_estado_tiquete": query_service.consultar_estado_tiquete,
    "cerrar_tiquete": ticket_manager.cerrar_tiquete,
    "reasignar_tiquete": ticket_manager.reasignar_tiquete,
    "modificar_sla_manual": ticket_manager.modificar_sla_manual,
    "visualizar_flujo_tiquete": ticket_visualizer.visualizar_flujo_tiquete,
    "consultar_metricas": query_service.consultar_metricas,
    "consultar_dwh": dwh_query_service.query_dwh, 
    "convertir_incidencia_a_tarea": ticket_manager.convertir_incidencia_a_tarea,
    "start_agendar_reunion_form": ticket_manager.start_agendar_reunion_form,
    "start_user_management_form": admin_service.start_user_management_form,
    "update_user_in_system": admin_service.update_user_in_system,
    "delete_user_from_system": admin_service.delete_user_from_system,
    "redactar_borrador": drafting_service.redactar_borrador,
    "visualizar_metrica_looker": looker_service.get_look_image_by_title,
    "visualizar_dashboard_looker": looker_service.get_dashboard_preview_image
}

def tiene_permiso(rol: str, herramienta: str) -> bool:
    permisos = {
        "admin": list(available_tools.keys()),
        "lead": [k for k in available_tools.keys() if 'user_management' not in k and 'delete_user' not in k],
        "agent": ["crear_tiquete_helpdesk", "consultar_estado_tiquete", "cerrar_tiquete", "visualizar_flujo_tiquete", "consultar_metricas", "visualizar_metrica_looker", "visualizar_dashboard_looker","consultar_dwh"],
        "user": ["crear_tiquete_helpdesk", "consultar_estado_tiquete", "visualizar_flujo_tiquete", "consultar_metricas", "visualizar_metrica_looker", "visualizar_dashboard_looker","consultar_dwh"]
    }
    return herramienta in permisos.get(rol, [])

# CAMBIO: Se renombra la función principal para reflejar el nuevo nombre del proyecto.
def handle_guanacloud_logic(user_message: str, user_email: str, user_display_name: str, user_id: str, attachment_url: str = None, attachment_name: str = None):
    try:
        session_id, session_state_str = get_or_create_active_session(user_id)
        if not session_id:
            return "Lo siento, no pude iniciar una sesión de chat para ti en este momento."

        if session_state_str and json.loads(session_state_str).get("state") == 'AWAITING_FEEDBACK_COMMENT':
            actualizar_feedback_comentario(session_id, user_message)
            set_session_state(user_id, None)
            return "Muchas gracias por tus comentarios, los tomaré en cuenta para mejorar."

        user_role, user_department = obtener_rol_usuario(user_email)
        history = get_chat_history(session_id)
        num_initial_messages = len(history)
        
        model = GenerativeModel(settings.GEMINI_CHAT_MODEL, system_instruction=system_prompt, tools=[all_tools_config])
        chat = model.start_chat(history=history)

        user_message_lower = user_message.lower()
        TICKET_KEYWORDS = ['tiquete', 'ticket', 'problema', 'error', 'incidencia', 'ayuda', 'soporte', 'fallo', 'no funciona']
        LOOKER_KEYWORDS = ['dashboard', 'panel', 'reporte', 'look', 'metrica', 'gráfico', 'ver', 'mostrar', 'muéstrame']
        DRAFT_KEYWORDS = ['redactar', 'escribir', 'borrador', 'correo', 'mensaje', 'chat']
        
        ACTION_KEYWORDS = TICKET_KEYWORDS + LOOKER_KEYWORDS + DRAFT_KEYWORDS
        
        should_search_kb = not any(keyword in user_message_lower for keyword in ACTION_KEYWORDS)

        if should_search_kb:
            print(f"▶️  Ejecutando búsqueda proactiva en KB para: '{user_message}'")
            kb_result = search_knowledge_base(user_message)
            if kb_result and kb_result.get("answer"):
                print("✅ Respuesta encontrada en KB. Devolviendo directamente.")
                final_text = f"{kb_result['answer']}\n\n(Fuente: {kb_result['source']})"
                
                temp_history = list(chat.history)
                temp_history.append(Part.from_text(user_message))
                temp_history.append(Part.from_text(final_text))
                save_chat_history(session_id, user_id, temp_history, num_initial_messages)
                
                return {"text": f"{final_text}\n\n¿Hay algo más en lo que pueda ayudarte?"}

        mensaje_con_contexto = f"[Mi nombre es {user_display_name}, mi rol es '{user_role}'] {user_message}"
        response = chat.send_message(mensaje_con_contexto)
        
        function_call = None
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    break
        
        if function_call:
            tool_name = function_call.name
            
            if not tiene_permiso(user_role, tool_name):
                return f"Lo siento, tu rol de '{user_role}' no te permite realizar la acción de '{tool_name}'."

            tool_to_call = available_tools.get(tool_name)
            if not tool_to_call:
                raise ValueError(f"Herramienta desconocida solicitada: {tool_name}")

            tool_args = {key: value for key, value in function_call.args.items()}
            tool_args.update({
                "solicitante_email": user_email, "solicitante_nombre": user_display_name, 
                "solicitante_rol": user_role, "solicitante_departamento": user_department,
                "attachment_url": attachment_url, "attachment_name": attachment_name,
                "user_id": user_id
            })
            
            tool_response_text = tool_to_call(**tool_args)
            
            try:
                response_json = json.loads(tool_response_text)
                if response_json.get("type") == "disambiguate_lead":
                    set_session_state(user_id, json.dumps({"state": "AWAITING_LEAD_ASSIGNMENT", "ticket_details": response_json["ticket_details"]}))
                return response_json
            except (json.JSONDecodeError, TypeError):
                pass 

            final_response = chat.send_message(Part.from_function_response(name=tool_name, response={"content": tool_response_text}))
            final_text = final_response.text
        else:
            final_text = response.text
        
        save_chat_history(session_id, user_id, chat.history, num_initial_messages)
        return {"text": final_text}

    except Exception as e:
        print(json.dumps({"log_name": "HandleGuanaCloudLogic_Error", "error": str(e), "traceback": traceback.format_exc()}))
        return {"text": "Lo siento, ocurrió un error interno al procesar tu solicitud. El equipo técnico ha sido notificado."}