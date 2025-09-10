import os
import json
import vertexai
import numpy as np
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel
from google.cloud import storage
from src.config import settings
from src.utils.prompt_loader import load_prompt_from_file

kb_index_cache = None
storage_client = storage.Client()

def _get_kb_index():
    global kb_index_cache
    if kb_index_cache is not None: return kb_index_cache
    try:
        bucket = storage_client.bucket(settings.KNOWLEDGE_BASE_BUCKET)
        blob = bucket.blob("kb_index.json")
        if blob.exists():
            kb_index_cache = json.loads(blob.download_as_text())
            for item in kb_index_cache:
                item['embedding'] = np.array(item['embedding'])
            return kb_index_cache
        else:
            kb_index_cache = []
            return kb_index_cache
    except Exception as e:
        print(f"🔴 Error crítico al cargar el índice del KB: {e}")
        kb_index_cache = []
        return kb_index_cache

def search_knowledge_base(user_query: str, similarity_threshold=0.65) -> dict | None:
    """
    Busca en el KB usando similitud de coseno y un umbral para filtrar.
    """
    model = GenerativeModel(settings.GEMINI_TASK_MODEL)
    embedding_model = TextEmbeddingModel.from_pretrained(settings.EMBEDDING_MODEL_NAME)
    
    kb_index = _get_kb_index()
    if not kb_index:
        return None

    print(f"▶️  Buscando en KB por similitud para: '{user_query}'")
    query_embedding = np.array(embedding_model.get_embeddings([user_query])[0].values)

    candidates = []
    for doc in kb_index:
        doc_embedding = doc['embedding']
        similarity = np.dot(query_embedding, doc_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding))
        
        if similarity >= similarity_threshold:
            candidates.append({
                "file_name": doc["file_name"],
                "summary": doc["summary"],
                "similarity": round(similarity, 4)
            })

    if not candidates:
        print(f"ℹ️  No se encontraron documentos con una similitud >= {similarity_threshold}")
        return None

    candidates.sort(key=lambda x: x["similarity"], reverse=True)
    print(f"   ✅ Se encontraron {len(candidates)} candidatos relevantes. El más alto: {candidates[0]['similarity']:.4f}")
    
    prompt_template_classify = load_prompt_from_file("rag_classify_document.md")
    prompt_clasificacion = prompt_template_classify.format(
        user_query=user_query,
        candidate_documents=json.dumps(candidates, indent=2)
    )

    try:
        response = model.generate_content(prompt_clasificacion)
        best_doc_name = response.text.strip()
        
        bucket = storage_client.bucket(settings.KNOWLEDGE_BASE_BUCKET)
        content_blob = bucket.blob(f"fuentes/{best_doc_name}")
        document_content = content_blob.download_as_text()
        
        prompt_template_final = load_prompt_from_file("rag_final_answer.md")
        prompt_respuesta_final = prompt_template_final.format(
            document_content=document_content,
            user_query=user_query
        )
        final_response = model.generate_content(prompt_respuesta_final)

        return {
            "answer": final_response.text.strip(),
            "source": "Knowledge Base - IT"
        }

    except Exception as e:
        print(f"🔴 Error durante el proceso de RAG con embeddings: {e}")
        return None