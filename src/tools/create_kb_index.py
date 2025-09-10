import os
import json
import vertexai
from google.cloud import storage
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel
from src.config import settings
from src.utils.prompt_loader import load_prompt_from_file

def create_knowledge_base_index():
    """
    Lee archivos de GCS, genera resúmenes y embeddings, y guarda un índice JSON.
    """
    vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.LOCATION)
    model = GenerativeModel(settings.GEMINI_TASK_MODEL)
    embedding_model = TextEmbeddingModel.from_pretrained(settings.EMBEDDING_MODEL_NAME)
    storage_client = storage.Client()
    bucket = storage_client.bucket(settings.KNOWLEDGE_BASE_BUCKET)
    blobs = storage_client.list_blobs(settings.KNOWLEDGE_BASE_BUCKET, prefix="fuentes/")

    kb_index = []
    prompt_template = load_prompt_from_file("summarize_document.md")
    print("🚀 Iniciando la creación del índice de la base de conocimiento (con embeddings)...")

    for blob in blobs:
        if not blob.name.endswith('/'): 
            print(f"📄 Procesando: {blob.name}...")
            content = blob.download_as_text()
            prompt = prompt_template.format(document_content=content)
            
            try:
                response = model.generate_content(prompt)
                summary = response.text.strip()
                
                print("   ▶️ Generando embedding para el resumen...")
                embeddings = embedding_model.get_embeddings([summary])
                vector = embeddings[0].values

                kb_index.append({
                    "file_name": os.path.basename(blob.name),
                    "summary": summary,
                    "embedding": vector 
                })
            except Exception as e:
                print(f"🔴 Error procesando el archivo {blob.name}: {e}")

    index_blob = bucket.blob("kb_index.json")
    index_blob.upload_from_string(json.dumps(kb_index, indent=2), content_type="application/json")
    print(f"\n✅ Índice con embeddings creado exitosamente y guardado en gs://{settings.KNOWLEDGE_BASE_BUCKET}/kb_index.json")

if __name__ == "__main__":
    create_knowledge_base_index()