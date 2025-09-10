import os
import json
import vertexai
from sqlalchemy.sql import text
from vertexai.generative_models import GenerativeModel
from src.utils.database_client import get_db_connection
from src.config import settings
from src.utils.prompt_loader import load_prompt_from_file

def consultar_estado_tiquete(ticket_id: str, **kwargs) -> str:
    """Consulta el último evento de un tiquete en PostgreSQL para determinar su estado."""
    db = get_db_connection() 
    ticket_id = ticket_id.upper()
    try:
        with db.connect() as conn:
            query = text("""
                SELECT TipoEvento, responsable, otros_detalles
                FROM eventos_tiquetes
                WHERE TicketID = :ticket_id
                ORDER BY FechaEvento DESC
                LIMIT 1
            """)
            ultimo_evento = conn.execute(query, {"ticket_id": ticket_id}).fetchone()

        if not ultimo_evento:
            return f"No se encontró ningún tiquete o evento con el ID '{ticket_id}'."

        detalles = json.loads(ultimo_evento.otros_detalles) if ultimo_evento.otros_detalles else {}

        if ultimo_evento.TipoEvento == "CREADO":
            return f"El tiquete {ticket_id} está 'Abierto' y asignado a {ultimo_evento.responsable}."
        elif ultimo_evento.TipoEvento == "CERRADO":
            resolucion = detalles.get('resolucion', 'No especificada.')
            return f"El tiquete {ticket_id} está 'Cerrado'. Resolución: {resolucion}."
        elif ultimo_evento.TipoEvento == "REASIGNADO":
            return f"El tiquete {ticket_id} está 'Abierto' y ha sido reasignado a {ultimo_evento.responsable}."
        else:
            return f"El último evento para el tiquete {ticket_id} fue '{ultimo_evento.TipoEvento}'."

    except Exception as e:
        print(f"🔴 Error al consultar estado en PostgreSQL: {e}")
        return f"Ocurrió un error al consultar el estado del tiquete."


def consultar_metricas(pregunta_del_usuario: str, solicitante_email: str, solicitante_rol: str, solicitante_departamento: str, **kwargs) -> str:
    """
    Convierte una pregunta en lenguaje natural en una consulta SQL segura para PostgreSQL,
    la ejecuta y devuelve una respuesta en lenguaje natural.
    """
    db = get_db_connection()
    model = GenerativeModel(settings.GEMINI_TASK_MODEL)
    
    prompt_template_sql = load_prompt_from_file("generate_sql_from_nl.md")
    prompt_para_sql = prompt_template_sql.format(
        solicitante_email=solicitante_email,
        solicitante_rol=solicitante_rol,
        solicitante_departamento=solicitante_departamento,
        pregunta_del_usuario=pregunta_del_usuario
    )

    try:
        print("▶️  Generando consulta SQL segura con IA...")
        response = model.generate_content(prompt_para_sql)
        sql_query = response.text.strip().replace("`", "").replace("sql", "", 1)
        
        forbidden_keywords = ['DELETE', 'UPDATE', 'INSERT', 'DROP', 'TRUNCATE', 'GRANT', 'REVOKE']
        if any(keyword in sql_query.upper() for keyword in forbidden_keywords):
            return "Lo siento, no puedo procesar esa solicitud por motivos de seguridad."

        print(f"▶️  SQL Generado: {sql_query}")
        with db.connect() as conn:
            results = conn.execute(text(sql_query)).fetchall()

        if not results: return "La consulta no arrojó resultados."
        results_dict = [row._asdict() for row in results]
        
        prompt_final = f"""
        Dado el siguiente resultado de base de datos en JSON, que responde a la pregunta original del usuario: '{pregunta_del_usuario}',
        resume el resultado en una frase clara y concisa en español. No menciones que es un JSON ni la estructura. Sé directo.
        
        Resultado: {json.dumps(results_dict, default=str)}
        Respuesta amigable:
        """
        final_response = model.generate_content(prompt_final)
        return final_response.text.strip()

    except Exception as e:
        print(f"🔴 Error al consultar métricas con IA: {e}")
        return "Ocurrió un error al procesar tu pregunta sobre métricas."