
import os
import json
import io
from google.cloud import storage
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from sqlalchemy.sql import text
from src.utils.database_client import get_db_connection
from src.config import settings
from src.utils.prompt_loader import load_prompt_from_file

db = get_db_connection()

def visualizar_flujo_tiquete(ticket_id: str, **kwargs) -> str:
    """
    Genera una infografía del historial del tiquete desde PostgreSQL,
    la sube a GCS y devuelve un objeto JSON con la URL pública.
    """
    if not settings.GCS_BUCKET_NAME:
        return json.dumps({"error": "Error de configuración: La variable GCS_BUCKET_NAME no está definida."})

    ticket_id = ticket_id.upper()
    
    try:
        with db.connect() as conn:
            query = text("""
                SELECT TipoEvento, FechaEvento, otros_detalles, responsable, equipo_asignado
                FROM eventos_tiquetes WHERE TicketID = :ticket_id ORDER BY FechaEvento ASC
            """)
            eventos = conn.execute(query, {"ticket_id": ticket_id}).fetchall()

        if not eventos:
            return json.dumps({"error": f"No se encontró historial para el tiquete con ID '{ticket_id}'."})
        
        event_prompts = []
        total_eventos = len(eventos)
        for i, evento in enumerate(eventos):
            tipo_evento = evento.TipoEvento.replace("_", " ").title()
            fecha_local = evento.FechaEvento.astimezone().strftime('%d %b, %H:%M')
            detalles = json.loads(evento.otros_detalles) if evento.otros_detalles else {}
            es_el_ultimo_evento = (i == total_eventos - 1)
            
            prompt_line = "- "
            if es_el_ultimo_evento and tipo_evento.lower() != "cerrado":
                prompt_line += f"Un círculo grande y brillante (estado actual) con el texto '{tipo_evento}'. Debajo, la fecha '{fecha_local}'. "
            else:
                prompt_line += f"Un círculo pequeño (evento completado) con el título '{tipo_evento}'. Debajo, la fecha '{fecha_local}'. "
            
            if tipo_evento.lower() == "creado":
                prompt_line += f"Añade un texto pequeño: 'Prioridad {detalles.get('prioridad_asignada', 'N/A')}'. "
            elif tipo_evento.lower() == "reasignado" and evento.responsable:
                prompt_line += f"Añade un texto pequeño: 'Asignado a {evento.responsable}'. "
            event_prompts.append(prompt_line)
        
        prompt_template = load_prompt_from_file("generate_timeline_infographic.md")
        prompt_para_imagen = prompt_template.format(ticket_id=ticket_id, event_prompts="\n".join(event_prompts))

        generation_model = ImageGenerationModel.from_pretrained(settings.IMAGEN_MODEL)
        
        print("▶️  Generando imagen con IA...")
        images = generation_model.generate_images(prompt=prompt_para_imagen, number_of_images=1, aspect_ratio="16:9")
        
        buffer = io.BytesIO()
        images[0]._pil_image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()

        print(f"▶️  Subiendo imagen al bucket '{settings.GCS_BUCKET_NAME}'...")
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
        
        nombre_archivo_en_bucket = f"flujos/{ticket_id}_timeline.png"
        blob = bucket.blob(nombre_archivo_en_bucket)
        
        blob.upload_from_string(image_bytes, content_type="image/png")
        blob.make_public()
        
        print(f"✅ Imagen disponible en: {blob.public_url}")
        
        response_data = {
            "type": "image_flow",
            "imageUrl": blob.public_url,
            "ticketId": ticket_id
        }
        return json.dumps(response_data)

    except Exception as e:
        print(f"🔴 Error al visualizar el flujo: {e}")
        return json.dumps({"error": f"Ocurrió un error al intentar generar el diagrama del tiquete: {e}"})