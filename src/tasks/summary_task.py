from datetime import datetime, timezone, timedelta
from collections import defaultdict
from sqlalchemy.sql import text
from src.utils.database_client import get_db_connection
from src.services.notification_service import enviar_notificacion_email, enviar_notificacion_chat

def get_open_tickets_summary():
    db = get_db_connection()
    query = text("""
        WITH UltimosEventos AS (
            SELECT
                TicketID,
                responsable,
                equipo_asignado,
                TipoEvento,
                ROW_NUMBER() OVER(PARTITION BY TicketID ORDER BY FechaEvento DESC) as rn
            FROM eventos_tiquetes
        )
        SELECT
            t.TicketID,
            t.Solicitante,
            t.FechaVencimiento,
            ue.responsable AS Responsable,
            ue.equipo_asignado AS Departamento
        FROM tickets t
        JOIN UltimosEventos ue ON t.TicketID = ue.TicketID
        WHERE
            ue.rn = 1
            AND ue.TipoEvento != 'CERRADO'
            AND t.FechaVencimiento IS NOT NULL
    """)
    try:
        with db.connect() as conn:
            results = conn.execute(query).fetchall()
        all_tickets = []
        user_tickets = defaultdict(list)
        for row in results:
            due_date_aware = row.FechaVencimiento.replace(tzinfo=timezone.utc) if row.FechaVencimiento.tzinfo is None else row.FechaVencimiento
            ticket_data = {
                "ticket_id": row.TicketID,
                "solicitante": row.Solicitante,
                "due_date": due_date_aware,
                "assignee": row.Responsable or "No asignado",
                "departamento": row.Departamento or "Sin Departamento"
            }
            all_tickets.append(ticket_data)
            user_tickets[row.Solicitante].append(ticket_data)
        return all_tickets, user_tickets
    except Exception as e:
        print(f"🔴 Error al obtener tiquetes abiertos: {e}")
        return None, None

def format_time_remaining(due_date, is_email=False):
    if not due_date:
        return "Fecha no definida"
    now = datetime.now(timezone.utc)
    remaining = due_date - now
    if remaining.total_seconds() <= 0:
        if is_email:
            days_overdue = -remaining.days
            if days_overdue == 0:
                return "<span style='color:red;'>Vencido (Hoy)</span>"
            else:
                return f"<span style='color:red;'>Vencido por {days_overdue} día(s)</span>"
        else:
            return "Vencido"
    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if days > 0:
        return f"{days}d {hours}h"
    else:
        return f"{hours}h {minutes}m"


def send_daily_summaries():
    """
    Genera un resumen en formato de Tarjeta para administradores (Chat)
    y notificaciones detalladas a usuarios (Email).
    """
    print("🚀 Iniciando el envío de resúmenes diarios de tiquetes abiertos...")
    all_tickets, user_tickets = get_open_tickets_summary()
    
    if all_tickets is None:
        print("🔴 Finalizando la tarea debido a un error al consultar la base de datos.")
        return

    if not all_tickets:
        admin_summary = "✅ ¡Buen día! No hay tiquetes abiertos pendientes hoy."
        print(admin_summary)
        enviar_notificacion_chat(admin_summary)
        return

    stats = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'due_soon': 0, 'overdue': 0}))
    now = datetime.now(timezone.utc)
    four_hours_from_now = now + timedelta(hours=4)

    for ticket in all_tickets:
        dept = ticket['departamento']
        assignee = ticket['assignee']
        due_date = ticket['due_date']
        
        stats[dept][assignee]['total'] += 1
        if due_date < now:
            stats[dept][assignee]['overdue'] += 1
        elif due_date < four_hours_from_now:
            stats[dept][assignee]['due_soon'] += 1

    card_header = {
        "title": "Resumen Diario de Tiquetes Abiertos",
        "subtitle": f"{len(all_tickets)} tiquetes en total",
        "imageUrl": "https://i.imgur.com/K81mJCV.png", 
        "imageType": "CIRCLE"
    }

    card_sections = []
    for dept, assignees in sorted(stats.items()):
        card_sections.append({"widgets": [{"divider": {}}]})
        card_sections.append({
            "header": f"Departamento: {dept}",
            "collapsible": True,
            "widgets": []
        })
        
        for assignee, data in sorted(assignees.items()):
            
            summary_text = (
                f"<b>Total: {data['total']}</b> "
                f"(<font color='#10B981'>Sin Vencer: {data['total'] - data['overdue']}</font> | "
                f"<font color='#EF4444'>Vencidos: {data['overdue']}</font>)"
            )
            if data['due_soon'] > 0:
                summary_text += f" | 🔥 <font color='#F59E0B'>Por Vencer: {data['due_soon']}</font>"

            widget = {
                "decoratedText": {
                    "topLabel": assignee,
                    "text": summary_text,
                    "startIcon": {
                        "knownIcon": "PERSON"
                    }
                }
            }
            card_sections[-1]["widgets"].append(widget)

    admin_card_summary = {
        "cardsV2": [{
            "cardId": "daily_summary_card",
            "card": {
                "header": card_header,
                "sections": card_sections
            }
        }]
    }
    
    print("📢 Enviando resumen de administrador en formato de tarjeta...")
    enviar_notificacion_chat(admin_card_summary)

    for user_email, tickets in user_tickets.items():
        asunto = "📄 Tu Resumen Diario de Tiquetes Abiertos"
        html_body = "<html><body><h2>Hola,</h2><p>Este es tu resumen diario de tiquetes de soporte abiertos:</p>"
        html_body += "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse:collapse;'>"
        html_body += "<tr style='background-color:#f2f2f2;'><th>ID del Tiquete</th><th>Asignado a</th><th>Estado del SLA</th></tr>"
        for ticket in tickets:
            time_left = format_time_remaining(ticket['due_date'], is_email=True)
            html_body += f"<tr><td>{ticket['ticket_id']}</td><td>{ticket['assignee']}</td><td style='text-align:center;'>{time_left}</td></tr>"
        
        # CAMBIO: Se actualiza la firma del correo con el nuevo nombre de la plataforma.
        html_body += "</table><p>Gracias,<br>El equipo de GuanaCloud Platform</p></body></html>"
        
        print(f"✉️  Enviando resumen por email a {user_email}...")
        enviar_notificacion_email(user_email, asunto, html_body)

    print("✅ Proceso de resúmenes diarios finalizado.")