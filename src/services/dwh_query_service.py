import json
from google.cloud import bigquery
from vertexai.generative_models import GenerativeModel
from src.config import settings
from src.utils.prompt_loader import load_prompt_from_file
import google.auth
from src.utils.database_client import check_dwh_permission 

def query_dwh(pregunta_del_usuario: str, solicitante_email: str, **kwargs) -> str:
    """
    Verifica los permisos del usuario en PostgreSQL y, si son válidos,
    ejecuta una consulta en BigQuery usando las credenciales de la Cloud Run.
    """
    print(f"▶️  Verificando permisos de DWH para el usuario: {solicitante_email}")
    if not check_dwh_permission(solicitante_email):
        print(f"🔴 Acceso denegado. El usuario {solicitante_email} no tiene el permiso 'can_query_dwh'.")
        return "Lo siento, parece que no tienes los permisos necesarios para realizar consultas al Data Warehouse. Por favor, contacta a un administrador."

    print(f"✅ Permiso concedido para {solicitante_email}. Procediendo con la consulta.")
    try:
        creds, project_id = google.auth.default()
        bq_client = bigquery.Client(credentials=creds, project=settings.GCP_PROJECT_ID)

        prompt_template_sql = load_prompt_from_file("generate_dwh_sql_from_nl.md")
        prompt_para_sql = prompt_template_sql.format(pregunta_del_usuario=pregunta_del_usuario)

        model = GenerativeModel(settings.GEMINI_TASK_MODEL)
        response = model.generate_content(prompt_para_sql)
        sql_query = response.text.strip().replace("`", "").replace("sql", "", 1)
        
        forbidden_keywords = ['DELETE', 'UPDATE', 'INSERT', 'DROP', 'TRUNCATE', 'GRANT', 'REVOKE']
        if any(keyword in sql_query.upper() for keyword in forbidden_keywords):
            return "Lo siento, no puedo procesar esa solicitud por motivos de seguridad."

        print(f"▶️  SQL Generado: {sql_query}")
        print("▶️  Ejecutando consulta en BigQuery con la identidad del servicio...")
        query_job = bq_client.query(sql_query)
        results = query_job.result()

        if results.total_rows == 0:
            return "La consulta no arrojó resultados."

        results_dict = [dict(row) for row in results]

        prompt_final = f"""
        Dado el siguiente resultado de base de datos en JSON, que responde a la pregunta original del usuario: '{pregunta_del_usuario}',
        resume el resultado en una frase clara y concisa en español. No menciones que es un JSON ni la estructura. Sé directo y amigable.

        Resultado: {json.dumps(results_dict, default=str)}
        Respuesta amigable:
        """
        final_response = model.generate_content(prompt_final)
        return final_response.text.strip()

    except Exception as e:
        print(f"🔴 Error al consultar el DWH con IA: {e}")
        return f"Ocurrió un error al procesar tu pregunta sobre el DWH: {e}"