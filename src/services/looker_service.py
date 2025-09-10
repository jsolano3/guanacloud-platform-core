
import json
import time
import uuid
import looker_sdk
from datetime import timedelta
from google.cloud import storage
import google.auth
from google.auth.transport.requests import Request
from src.config import settings

def _render_and_upload_looker_element(sdk, element_title: str, look_id: str = None, query_id: str = None) -> str:
    """Función auxiliar para renderizar un elemento (Look o Query) y subirlo a GCS."""
    render_task = None
    render_id = None

    if look_id:
        print(f"▶️  Renderizando Look ID: {look_id}...")
        render_id = look_id
        render_task = sdk.create_look_render_task(look_id=look_id, result_format="png", width=960, height=540)
    elif query_id:
        print(f"▶️  Renderizando Query ID: {query_id}...")
        render_id = query_id
        render_task = sdk.create_query_render_task(query_id=query_id, result_format="png", width=960, height=540)
    else:
        raise ValueError("Se debe proporcionar un look_id o un query_id para renderizar.")

    if not (render_task and render_task.id):
        raise Exception("No se pudo crear la tarea de renderizado en Looker.")

    elapsed = 0.0
    while True:
        poll = sdk.render_task(render_task.id)
        if poll.status == "success": break
        if poll.status == "failure": raise Exception(f"La tarea de renderizado falló: {poll.status_detail}")
        time.sleep(0.5)
        elapsed += 0.5
        if elapsed > 30: raise Exception("Timeout esperando el renderizado.")

    image_bytes = sdk.render_task_results(render_task.id)
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(settings.LOOKER_GCS_BUCKET) 
    blob_name = f"looks/{render_id}-{uuid.uuid4()}.png"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(image_bytes, content_type="image/png")
    
    credentials, _ = google.auth.default()
    credentials.refresh(Request())
    
    return blob.generate_signed_url(
        version="v4", expiration=timedelta(minutes=15), method="GET",
        service_account_email=credentials.service_account_email, access_token=credentials.token
    )

def get_look_image_by_title(nombre_metrica: str, solicitante_email: str, **kwargs) -> str:
    """Busca un 'Look' individual, lo renderiza y devuelve la imagen."""
    sdk = looker_sdk.init40()
    try:
        sdk.login_user(sdk.search_users(email=solicitante_email)[0].id)
        looks = sdk.search_looks(title=nombre_metrica)
        if not looks:
            return json.dumps({"text": f"Lo siento, no pude encontrar el gráfico '{nombre_metrica}' o no tienes permisos."})
        target_look = looks[0]
        image_url = _render_and_upload_looker_element(sdk, target_look.title, look_id=target_look.id)
        card = {"cardsV2": [{"cardId": "looker_visual_card", "card": {"header": {"title": "Visualización de Datos de Looker", "subtitle": target_look.title}, "sections": [{"widgets": [{"image": {"imageUrl": image_url}}]}]}}]}
        return json.dumps(card)
    except Exception as e:
        return json.dumps({"text": f"Ocurrió un error al generar la visualización desde Looker: {e}"})
    finally:
        sdk.logout()

def get_dashboard_preview_image(nombre_dashboard: str, solicitante_email: str, **kwargs) -> str:
    """Busca un Dashboard, renderiza su PRIMER elemento y devuelve la tarjeta."""
    sdk = looker_sdk.init40()
    try:
        sdk.login_user(sdk.search_users(email=solicitante_email)[0].id)
        dashboards = sdk.search_dashboards(title=nombre_dashboard)
        if not dashboards:
            return json.dumps({"text": f"Lo siento, no pude encontrar el dashboard '{nombre_dashboard}' o no tienes permisos."})

        target_dashboard = dashboards[0]
        dashboard_url = f"{settings.LOOKERSDK_BASE_URL}{target_dashboard.url}"
        print(f"✅ Dashboard encontrado: '{target_dashboard.title}' (URL: {dashboard_url})")
        
        dashboard_elements = sdk.dashboard_dashboard_elements(dashboard_id=target_dashboard.id)
        if not dashboard_elements:
            return json.dumps({"text": f"El dashboard '{target_dashboard.title}' no contiene elementos visuales."})

        first_element = dashboard_elements[0]
        image_url = None
        if first_element.look_id:
            image_url = _render_and_upload_looker_element(sdk, first_element.title, look_id=first_element.look_id)
        elif first_element.query_id:
            image_url = _render_and_upload_looker_element(sdk, first_element.title, query_id=first_element.query_id)
        
        if not image_url:
            return json.dumps({"text": f"No se pudo renderizar un preview del dashboard '{target_dashboard.title}'."})

        widgets = [
            {"image": {"imageUrl": image_url}},
            {"buttonList": {"buttons": [{"text": "Abrir Dashboard Interactivo", "onClick": {"openLink": {"url": dashboard_url}}}]}}
        ]

        card = {"cardsV2": [{"cardId": "looker_dashboard_preview_card", "card": {"header": {"title": "Previsualización de Dashboard", "subtitle": target_dashboard.title}, "sections": [{"widgets": widgets}]}}]}
        return json.dumps(card)
    except Exception as e:
        error_message = f"Ocurrió un error al generar la previsualización del dashboard: {e}"
        print(f"🔴 {error_message}")
        return json.dumps({"text": error_message})
    finally:
        sdk.logout()