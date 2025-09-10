import asana
from src.utils.database_client import get_asana_gid_for_user
from src.config import settings 

def get_asana_client():
    """Configura y devuelve el cliente de la API de Asana."""
    if not settings.ASANA_PERSONAL_ACCESS_TOKEN:
        print("🔴 Error: La variable ASANA_PERSONAL_ACCESS_TOKEN no está configurada.")
        return None
    
    client = asana.Client.access_token(settings.ASANA_PERSONAL_ACCESS_TOKEN) 
    # CAMBIO: Se actualiza el nombre del cliente que interactúa con la API de Asana.
    client.options['client_name'] = "GuanaCloudPlatformBot"
    return client

def crear_tarea_asana(nombre_tarea: str, notas: str, responsable_email: str, fecha_entrega: str) -> dict:
    client = get_asana_client()
    if not client or not settings.ASANA_PROJECT_GID: 
        return {"error": "El cliente de Asana o el GID del proyecto no están configurados."}

    print(f"▶️  Buscando Asana GID para el responsable: {responsable_email}...")
    assignee_gid = get_asana_gid_for_user(responsable_email)
    
    if not assignee_gid:
        error_message = f"No se pudo encontrar un GID de Asana para '{responsable_email}'."
        print(f"🔴 {error_message}")
        return {"error": error_message}

    try:
        task_data = {
            "name": nombre_tarea,
            "notes": notas,
            "projects": [settings.ASANA_PROJECT_GID], 
            "assignee": assignee_gid,
            "due_on": fecha_entrega
        }
        
        print(f"▶️  Creando tarea en Asana para {responsable_email} (GID: {assignee_gid})...")
        result = client.tasks.create_task(task_data, opt_pretty=True)
        
        task_url = f"https://app.asana.com/0/{settings.ASANA_PROJECT_GID}/{result['gid']}" 
        print(f"✅ Tarea creada en Asana: {result['gid']} | URL: {task_url}")
        
        return {"asana_task_gid": result['gid'], "asana_task_url": task_url}

    except asana.error.InvalidRequestError as e:
        print(f"🔴 Error de API de Asana: {e.response['body']['errors']}")
        return {"error": f"Error de API de Asana: {e.response['body']['errors'][0]['message']}"}
    except Exception as e:
        print(f"🔴 Error inesperado al crear la tarea en Asana: {e}")
        return {"error": str(e)}