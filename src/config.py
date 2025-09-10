import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Clase de configuración centralizada que carga y valida las variables de entorno usando Pydantic.
    
    Prioridad de Carga:
    1. Variables de Entorno del Sistema (Usado en Cloud Run a través de deploy.yml).
    2. Variables definidas en el archivo .env (Usado para desarrollo local).
    
    Esto asegura que el mismo código funcione sin cambios en ambos entornos.
    """
    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # --- Configuración del Proyecto GCP ---
    GCP_PROJECT_ID: str
    LOCATION: str = "us-central1"
    APP_BASE_URL: str
    
    # --- Configuración de Modelos de IA (Vertex AI) ---
    GEMINI_CHAT_MODEL: str = "gemini-2.5-flash"
    GEMINI_TASK_MODEL: str = "gemini-2.5-pro"
    IMAGEN_MODEL: str = "imagen-4.0-generate-001"
    EMBEDDING_MODEL_NAME: str = "text-embedding-005"
    VECTOR_SEARCH_INDEX_ID: str
    VECTOR_SEARCH_ENDPOINT_ID: str
    DEPLOYED_INDEX_ID: str

    # --- Configuración de Base de Datos (inyectada por Cloud Run o .env) ---
    DB_USER: str = "postgres"
    DB_NAME: str = "postgres"
    DB_CONNECTION_NAME: str
    DB_PASS: str # Esta vendrá de Secret Manager

    # --- Configuración de BigQuery ---
    BIGQUERY_DATASET_ID: str

    # --- Configuración de Cloud Storage ---
    GCS_BUCKET_NAME: str
    # CAMBIO: Se renombra el bucket de adjuntos.
    GCS_ATTACHMENT_BUCKET: str = "guanacloud-ticket-attachments" 
    # CAMBIO: Se renombra el bucket de la base de conocimiento.
    KNOWLEDGE_BASE_BUCKET: str = "guanacloud-knowledge-base" 
    LOOKER_GCS_BUCKET: str 
    
    # --- APIs y Webhooks (inyectadas desde Secret Manager o .env) ---
    GOOGLE_CHAT_WEBHOOK_URL: str
    BREVO_API_KEY: str
    ASANA_PERSONAL_ACCESS_TOKEN: str
    GITHUB_PAT: str
    GITHUB_WEBHOOK_SECRET: str
    LOOKERSDK_CLIENT_ID: str
    LOOKERSDK_CLIENT_SECRET: str

    # --- Configuración de Asana ---
    ASANA_PROJECT_GID: str
    ASANA_LEAD_DATA_ENGINEERING_GID: str
    ASANA_LEAD_BI_ANALYST_GID: str
    
    # --- Configuración de Looker ---
    LOOKERSDK_BASE_URL: str = ""
    LOOKER_DASHBOARD_ID: str

    # --- Configuración de Notificaciones ---
    SENDER_EMAIL: str = "jose.solano@guanacloud.com"
    # CAMBIO: Se actualiza el nombre del remitente para reflejar la nueva marca.
    SENDER_NAME: str = "Soporte GuanaCloud" 
    
    # --- Configuración de Firestore ---
    # CAMBIO: Se actualiza el ID de la base de datos para alinearlo con el proyecto.
    FIRESTORE_DATABASE_ID: str = "guanacloud-platform"

    # --- Deprecado, pero mantenido por si algún script antiguo lo usa ---
    TICKETS_TABLE_NAME: str = "tickets"
    EVENTOS_TABLE_NAME: str = "eventos_tiquetes"


# Instancia única y validada de la configuración para ser importada en otros módulos
settings = Settings()