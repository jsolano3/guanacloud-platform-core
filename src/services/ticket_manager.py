import json
import uuid
import requests
import google.auth
import pytz
from datetime import datetime, timedelta
from google.cloud import storage
from google.auth.transport.requests import AuthorizedSession
from urllib.parse import urlencode
from sqlalchemy.sql import text
from src.utils.database_client import get_db_connection
from src.services.notification_service import enviar_notificacion_email, enviar_notificacion_chat
from src.services.asana_service import crear_tarea_asana
from src.config import settings

def _get_leads_for_department(department_name: str, conn):
    """Busca en la base de datos todos los usuarios con rol 'lead' para un departamento."""
    query = text("SELECT user_email FROM roles_usuarios WHERE department = :dept AND role = 'lead'")
    return conn.execute(query, {"dept": department_name}).fetchall()

def _handle_attachment(attachment_url: str, attachment_name: str, ticket_id: str) -> str | None:
    """Descarga un adjunto de Google Chat y lo sube a GCS."""
    if not all([attachment_url, attachment_name, settings.GCS_ATTACHMENT_BUCKET]):
        return None
    try:
        print(f"▶️  Manejando adjunto: {attachment_name}")
        creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/chat.bot'])
        authed_session = AuthorizedSession(creds)
        response = authed_session.get(attachment_url)
        response.raise_for_status()
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.GCS_ATTACHMENT_BUCKET)
        
        file_extension = '.' + attachment_name.split('.')[-1] if '.' in attachment_name else ''
        blob_name = f"attachments/{ticket_id}/{uuid.uuid4()}{file_extension}"
        blob = bucket.blob(blob_name)

        blob.upload_from_string(response.content, content_type=response.headers.get('Content-Type'))
        blob.make_public()
        
        print(f"✅ Adjunto subido a GCS en: {blob.public_url}")
        return blob.public_url
    except Exception as e:
        print(f"🔴 Error al manejar el adjunto: {e}")
        return None

def _obtener_sla_por_configuracion(equipo: str, prio: str) -> int:
    """Consulta la tabla de configuración para obtener las horas de SLA."""
    db = get_db_connection() 
    with db.connect() as conn:
        query = text("SELECT sla_hours FROM sla_configuracion WHERE department = :depto AND priority = :prio LIMIT 1")
        result = conn.execute(query, {"depto": equipo, "prio": prio}).scalar_one_or_none()
        return result or 24

def _create_ticket_with_assigned_lead(ticket_details: dict, responsable: str, solicitante_email: str, solicitante_nombre: str, attachment_url: str = None, attachment_name: str = None) -> str:
    """Función interna para crear el tiquete una vez que el responsable ha sido definido."""
    db = get_db_connection()
    try:
        descripcion = ticket_details['descripcion']
        equipo_asignado = ticket_details['equipo_asignado']
        prioridad = ticket_details['prioridad']
        
        # CAMBIO: Se actualiza el prefijo del ID del tiquete.
        ticket_id = f"GNP-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4().hex)[:4].upper()}"
        attachment_gcs_url = _handle_attachment(attachment_url, attachment_name, ticket_id)
        
        sla_horas = _obtener_sla_por_configuracion(equipo_asignado, prioridad)
        fecha_creacion = datetime.utcnow()
        fecha_vencimiento = fecha_creacion + timedelta(hours=sla_horas)

        with db.connect() as conn:
            with conn.begin():
                conn.execute(text("INSERT INTO tickets (TicketID, Solicitante, FechaCreacion, SLA_horas, FechaVencimiento) VALUES (:id, :email, :creacion, :sla, :vencimiento)"), {"id": ticket_id, "email": solicitante_email, "creacion": fecha_creacion, "sla": sla_horas, "vencimiento": fecha_vencimiento})
                detalles = {"descripcion": descripcion, "prioridad_asignada": prioridad}
                conn.execute(text("INSERT INTO eventos_tiquetes (TicketID, Autor, TipoEvento, equipo_asignado, responsable, attachment_url, otros_detalles) VALUES (:id, :autor, 'CREADO', :equipo, :resp, :attach, :detalles)"), {"id": ticket_id, "autor": solicitante_email, "equipo": equipo_asignado, "resp": responsable, "attach": attachment_gcs_url, "detalles": json.dumps(detalles)})
        
        primer_nombre = solicitante_nombre.split(" ")[0]
        asunto_solicitante = f"✅ Tiquete Creado: {ticket_id}"
        cuerpo_solicitante = f"<html><body><h2>Hola, {primer_nombre},</h2><p>Hemos creado el tiquete <b>{ticket_id}</b>.</p><p><b>Descripción:</b> {descripcion}</p><p>Asignado a: <b>{responsable}</b>.</p>"
        asunto_responsable = f"⚠️ Nuevo Tiquete: {ticket_id}"
        cuerpo_responsable = f"<html><body><p>Se te ha asignado el tiquete: <b>{ticket_id}</b>.</p><p><b>Solicitante:</b> {solicitante_nombre} ({solicitante_email})</p><p><b>Descripción:</b> {descripcion}</p>"
        mensaje_chat = f"✅ Tiquete Creado: *{ticket_id}*\n*Solicitante:* {solicitante_nombre}\n*Asignado a:* {responsable}\n*Descripción:* {descripcion}"

        if attachment_gcs_url:
            cuerpo_solicitante += f"<p><b>Adjunto:</b> <a href='{attachment_gcs_url}'>Ver Archivo</a></p>"
            cuerpo_responsable += f"<p><b>Adjunto:</b> <a href='{attachment_gcs_url}'>Ver Archivo</a></p>"
            mensaje_chat += f"\n*Adjunto:* {attachment_gcs_url}"

        # CAMBIO: Se actualiza la firma en la notificación por correo.
        cuerpo_solicitante += "<p>Gracias,<br>El equipo de GuanaCloud Platform</p></body></html>"
        cuerpo_responsable += "</body></html>"
        enviar_notificacion_email(solicitante_email, asunto_solicitante, cuerpo_solicitante)
        enviar_notificacion_email(responsable, asunto_responsable, cuerpo_responsable)
        enviar_notificacion_email("Helpdesk@guanacloud.com", asunto_responsable, cuerpo_responsable)
        enviar_notificacion_chat(mensaje_chat)
        
        return f"Tiquete {ticket_id} creado con prioridad '{prioridad}' y SLA de {sla_horas} horas. Asignado a {responsable}."
    except Exception as e:
        print(f"🔴 Error al crear tiquete final: {e}")
        return "Ocurrió un error crítico al finalizar la creación del tiquete."

def crear_tiquete(descripcion: str, equipo_asignado: str, prioridad: str, **kwargs) -> str:
    """Punto de entrada para la creación de tiquetes. Determina el responsable o pide desambiguación."""
    db = get_db_connection()
    with db.connect() as conn:
        leads_result = _get_leads_for_department(equipo_asignado, conn)
        leads = [row[0] for row in leads_result]

    if not leads:
        return json.dumps({"type": "error", "message": f"No se encontró un lead para el departamento '{equipo_asignado}'. No se puede crear el tiquete."})

    attachment_url = kwargs.get("attachment_url")
    attachment_name = kwargs.get("attachment_name")

    ticket_details = {
        "descripcion": descripcion,
        "equipo_asignado": equipo_asignado,
        "prioridad": prioridad,
        "attachment_url": attachment_url,
        "attachment_name": attachment_name
    }

    if len(leads) == 1:
        responsable = leads[0]
        return _create_ticket_with_assigned_lead(
            ticket_details=ticket_details,
            responsable=responsable,
            solicitante_email=kwargs.get("solicitante_email"),
            solicitante_nombre=kwargs.get("solicitante_nombre"),
            attachment_url=attachment_url,
            attachment_name=attachment_name
        )
    else:
        return json.dumps({
            "type": "disambiguate_lead",
            "message": f"He detectado que hay varios líderes para el equipo de {equipo_asignado}. ¿A cuál de ellos te gustaría asignarle el tiquete?",
            "leads": leads,
            "ticket_details": ticket_details
        })

# El resto del archivo no contenía referencias a "Kai" y no requiere cambios.
# ... (funciones cerrar_tiquete, reasignar_tiquete, etc.)
def cerrar_tiquete(ticket_id: str, resolucion: str, **kwargs) -> str:
    """Cierra un tiquete y devuelve una respuesta especial para solicitar feedback sobre la resolución."""
    db = get_db_connection()
    solicitante_email = kwargs.get("solicitante_email")
    try:
        with db.connect() as conn:
            with conn.begin():
                detalles_json = {"resolucion": resolucion, "cerrado_por": solicitante_email}
                conn.execute(
                    text("INSERT INTO eventos_tiquetes (TicketID, Autor, TipoEvento, otros_detalles) VALUES (:ticket_id, :autor, 'CERRADO', :detalles)"),
                    {"ticket_id": ticket_id, "autor": solicitante_email, "detalles": json.dumps(detalles_json)}
                )
        
        enviar_notificacion_chat(f"✔️ Tiquete Cerrado: *{ticket_id}*\n*Resolución:* {resolucion}")
        
        return json.dumps({
            "type": "resolution_feedback",
            "message": f"El tiquete {ticket_id} ha sido cerrado exitosamente.",
            "question": f"La resolución fue: '{resolucion}'. ¿Cómo calificarías esta solución?"
        })
    except Exception as e:
        print(f"🔴 Error al cerrar tiquete: {e}")
        return json.dumps({"type": "error", "message": "Ocurrió un error al cerrar el tiquete."})

def reasignar_tiquete(ticket_id: str, nuevo_responsable_email: str, solicitante_email: str, **kwargs) -> str:
    """Reasigna un tiquete en PostgreSQL."""
    db = get_db_connection()
    try:
        with db.connect() as conn:
            with conn.begin():
                conn.execute(
                    text("INSERT INTO eventos_tiquetes (TicketID, Autor, TipoEvento, responsable) VALUES (:ticket_id, :autor, 'REASIGNADO', :nuevo_responsable)"),
                    {"ticket_id": ticket_id, "autor": solicitante_email, "nuevo_responsable": nuevo_responsable_email}
                )
        enviar_notificacion_chat(f"👤 Tiquete Reasignado: *{ticket_id}*\n*Nuevo Responsable:* {nuevo_responsable_email}")
        return f"El tiquete {ticket_id} ha sido reasignado a {nuevo_responsable_email}."
    except Exception as e:
        print(f"🔴 Error al reasignar tiquete: {e}")
        return f"Ocurrió un error al reasignar el tiquete."

def modificar_sla_manual(ticket_id: str, nuevas_horas_sla: int, solicitante_email: str, solicitante_rol: str, solicitante_departamento: str, **kwargs) -> str:
    """Modifica el SLA de un tiquete en PostgreSQL."""
    db = get_db_connection()
    try:
        with db.connect() as conn:
            with conn.begin():
                query_fecha = text("SELECT FechaCreacion FROM tickets WHERE TicketID = :ticket_id")
                fecha_creacion_result = conn.execute(query_fecha, {"ticket_id": ticket_id}).scalar_one_or_none()

                if not fecha_creacion_result:
                    return f"Error: El tiquete '{ticket_id}' no fue encontrado."

                nueva_fecha_vencimiento = fecha_creacion_result + timedelta(hours=nuevas_horas_sla)

                update_query = text("""
                    UPDATE tickets
                    SET SLA_horas = :nuevas_horas, FechaVencimiento = :nueva_fecha
                    WHERE TicketID = :ticket_id
                """)
                conn.execute(update_query, {
                    "nuevas_horas": nuevas_horas_sla,
                    "nueva_fecha": nueva_fecha_vencimiento,
                    "ticket_id": ticket_id
                })

                detalles_json = {"nuevo_sla_horas": nuevas_horas_sla, "modificado_por": solicitante_email}
                conn.execute(
                    text("""
                        INSERT INTO eventos_tiquetes (TicketID, Autor, TipoEvento, otros_detalles)
                        VALUES (:ticket_id, :autor, 'SLA_MODIFICADO', :detalles)
                    """),
                    {"ticket_id": ticket_id, "autor": solicitante_email, "detalles": json.dumps(detalles_json)}
                )
        
        return f"El SLA del tiquete {ticket_id} ha sido modificado a {nuevas_horas_sla} horas."
    except Exception as e:
        print(f"🔴 Error al modificar el SLA: {e}")
        return "Ocurrió un error al intentar modificar el SLA del tiquete."


def convertir_incidencia_a_tarea(ticket_id: str, motivo: str, fecha_entrega: str, solicitante_email: str, **kwargs) -> str:
    """Convierte una incidencia en una tarea de Asana y lo registra en PostgreSQL."""
    db = get_db_connection() 
    try:
        responsable_actual = None
        with db.connect() as conn:
            query = text("""
                SELECT responsable FROM eventos_tiquetes
                WHERE TicketID = :ticket_id AND responsable IS NOT NULL
                ORDER BY FechaEvento DESC
                LIMIT 1
            """)
            responsable_actual = conn.execute(query, {"ticket_id": ticket_id}).scalar_one_or_none()

        if not responsable_actual:
            return "Error: No se pudo determinar el responsable actual del tiquete para asignarlo en Asana."

        nombre_tarea = f"Tarea [Desde Tiquete {ticket_id}]"
        notas_tarea = f"Esta tarea fue convertida desde una incidencia.\n\nMotivo: {motivo}\nSolicitante: {solicitante_email}"
        
        resultado_asana = crear_tarea_asana(
            nombre_tarea=nombre_tarea,
            notas=notas_tarea,
            responsable_email=responsable_actual,
            fecha_entrega=fecha_entrega
        )

        if "error" in resultado_asana:
            return f"No se pudo crear la tarea en Asana: {resultado_asana['error']}"

        with db.connect() as conn:
            with conn.begin():
                detalles_conversion = {
                    "motivo": motivo,
                    "convertido_por": solicitante_email,
                    "asana_task_info": resultado_asana
                }
                conn.execute(
                    text("""
                        INSERT INTO eventos_tiquetes (TicketID, Autor, TipoEvento, otros_detalles)
                        VALUES (:ticket_id, :autor, 'CONVERTIDO_A_TAREA', :detalles)
                    """),
                    {"ticket_id": ticket_id, "autor": solicitante_email, "detalles": json.dumps(detalles_conversion)}
                )
        
        mensaje_chat = f"🔄 Tiquete *{ticket_id}* convertido a Tarea en Asana.\nAsignado a: *{responsable_actual}*\nURL: {resultado_asana['asana_task_url']}"
        enviar_notificacion_chat(mensaje_chat)
        
        return f"Tiquete {ticket_id} convertido exitosamente a una tarea en Asana."

    except Exception as e:
        print(f"🔴 Error al convertir tiquete a tarea: {e}")
        return f"Ocurrió un error inesperado durante la conversión: {e}"


def agendar_reunion_gcalendar(titulo_reunion: str, fecha_reunion: str, hora_reunion: str, solicitante_email: str, duracion_minutos: int = 30, ticket_id: str = None, email_invitados_adicionales: list = None, **kwargs) -> str:
    """
    Construye un enlace de Google Calendar con todos los detalles pre-llenados
    (incluyendo fecha y hora) para que el usuario finalice el agendamiento.
    """
    try:
        invitados = {solicitante_email}
        if email_invitados_adicionales:
            for email in email_invitados_adicionales:
                invitados.add(email)
        invitados.discard(None)

        tz = pytz.timezone('America/Costa_Rica')
        start_time_str = f"{fecha_reunion} {hora_reunion}"
        start_datetime_local = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
        start_datetime_aware = tz.localize(start_datetime_local)
        end_datetime_aware = start_datetime_aware + timedelta(minutes=duracion_minutos)

        start_utc = start_datetime_aware.astimezone(pytz.utc).strftime('%Y%m%dT%H%M%SZ')
        end_utc = end_datetime_aware.astimezone(pytz.utc).strftime('%Y%m%dT%H%M%SZ')

        detalles = f"Reunión para discutir el tema: {titulo_reunion}."
        if ticket_id:
            detalles += f"\nContexto del tiquete: {ticket_id}"

        params = {
            "action": "TEMPLATE",
            "text": titulo_reunion,
            "dates": f"{start_utc}/{end_utc}",
            "details": detalles,
            "add": ",".join(invitados),
            "crm": "true"
        }
        base_url = "https://calendar.google.com/calendar/render?"
        url_final = base_url + urlencode(params)

        card_data = {
            "type": "calendar_link",
            "message": f"He preparado un borrador de la invitación para '{titulo_reunion}'.",
            "url": url_final
        }
        return json.dumps(card_data)

    except Exception as e:
        print(f"🔴 Error al construir el enlace de calendario: {e}")
        return json.dumps({"type": "error", "message": f"Ocurrió un error al preparar el enlace para la reunión: {e}"})

def start_agendar_reunion_form(solicitante_email: str, email_invitados_adicionales: list = None, **kwargs) -> str:
    """Construye y devuelve el JSON de una tarjeta con un formulario para agendar una reunión."""
    
    invitados_str = ""
    if email_invitados_adicionales:
        invitados_str = ", ".join(email_invitados_adicionales)

    card = {
        "cardsV2": [{
            "cardId": "agendar_reunion_card",
            "card": {
                "header": {"title": "Agendar Nueva Reunión"},
                "sections": [{
                    "widgets": [
                        {"textInput": {"label": "Título de la Reunión", "name": "titulo_reunion"}},
                        {"textInput": {"label": "Invitar a (emails separados por coma)", "name": "invitados", "value": invitados_str}},
                        {
                            "dateTimePicker": {
                                "name": "fecha_hora_reunion",
                                "label": "Selecciona Fecha y Hora",
                                "valueMsEpoch": str(int(datetime.now().timestamp() * 1000))
                            }
                        },
                        {"textInput": {"label": "Duración (minutos)", "name": "duracion", "value": "30"}},
                        {
                            "buttonList": {
                                "buttons": [{
                                    "text": "Preparar Invitación",
                                    "onClick": {"action": {"function": "submit_agendar_reunion_form"}}
                                }]
                            }
                        }
                    ]
                }]
            }
        }]
    }
    return json.dumps(card)