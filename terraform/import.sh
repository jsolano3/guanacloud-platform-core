#!/bin/bash
# =================================================================================
# SCRIPT DE IMPORTACIÓN CORREGIDO
# =================================================================================

echo "--- INICIALIZANDO TERRAFORM ---"
terraform init

echo "--- IMPORTANDO RECURSOS EXISTENTES ---"

# IAM
terraform import google_service_account.compute_default_sa projects/connectdatakai/serviceAccounts/537990588927-compute@developer.gserviceaccount.com
terraform import google_service_account.github_actions_deployer projects/connectdatakai/serviceAccounts/github-actions-deployer@connectdatakai.iam.gserviceaccount.com
terraform import google_service_account.sql_scheduler_invoker projects/connectdatakai/serviceAccounts/sql-scheduler-invoker@connectdatakai.iam.gserviceaccount.com
terraform import 'google_project_iam_member.sql_admin_binding' "connectdatakai roles/cloudsql.admin serviceAccount:sql-scheduler-invoker@connectdatakai.iam.gserviceaccount.com"

# Automation
echo "--- Importando Cloud Functions, Permisos y Schedulers ---"
terraform import google_cloudfunctions2_function.stop_sql_dev projects/connectdatakai/locations/us-central1/functions/stop-sql-instance-dev
terraform import google_cloudfunctions2_function.start_sql_dev projects/connectdatakai/locations/us-central1/functions/start-sql-instance-dev
terraform import 'google_cloud_run_v2_service_iam_member.stop_sql_invoker' "projects/connectdatakai/locations/us-central1/services/stop-sql-instance-dev roles/run.invoker serviceAccount:sql-scheduler-invoker@connectdatakai.iam.gserviceaccount.com"
terraform import 'google_cloud_run_v2_service_iam_member.start_sql_invoker' "projects/connectdatakai/locations/us-central1/services/start-sql-instance-dev roles/run.invoker serviceAccount:sql-scheduler-invoker@connectdatakai.iam.gserviceaccount.com"
terraform import google_cloud_scheduler_job.stop_sql_dev_nightly projects/connectdatakai/locations/us-central1/jobs/stop-sql-dev-nightly
terraform import google_cloud_scheduler_job.start_sql_dev_morning projects/connectdatakai/locations/us-central1/jobs/start-sql-dev-morning

# Vertex AI
echo "--- Importando recursos de Vertex AI ---"
terraform import google_vertex_ai_index.agent_kai_kb_index projects/537990588927/locations/us-central1/indexes/6357448799568265216
terraform import google_vertex_ai_index_endpoint.endpoint_agent_kai projects/537990588927/locations/us-central1/indexEndpoints/712995907217391616

# BigQuery
echo "--- Importando Datasets y Tablas de BigQuery ---"
terraform import google_bigquery_dataset.connect_helpdesk_kai_prod projects/connectdatakai/datasets/connect_helpdesk_kai_prod
terraform import google_bigquery_dataset.connect_helpdesk_kai_dev projects/connectdatakai/datasets/connect_helpdesk_kai_dev
terraform import google_bigquery_table.nps_feedback_dev projects/connectdatakai/datasets/connect_helpdesk_kai_dev/tables/nps_feedback
terraform import google_bigquery_table.sla_configuracion_dev projects/connectdatakai/datasets/connect_helpdesk_kai_dev/tables/sla_configuracion
terraform import google_bigquery_table.tickets_dev projects/connectdatakai/datasets/connect_helpdesk_kai_dev/tables/tickets
terraform import google_bigquery_table.roles_usuarios_dev projects/connectdatakai/datasets/connect_helpdesk_kai_dev/tables/roles_usuarios
terraform import google_bigquery_table.eventos_tiquetes_dev projects/connectdatakai/datasets/connect_helpdesk_kai_dev/tables/eventos_tiquetes
terraform import google_bigquery_table.eventos_tiquetes_prod projects/connectdatakai/datasets/connect_helpdesk_kai_prod/tables/eventos_tiquetes
terraform import google_bigquery_table.nps_feedback_prod projects/connectdatakai/datasets/connect_helpdesk_kai_prod/tables/nps_feedback
terraform import google_bigquery_table.roles_usuarios_prod projects/connectdatakai/datasets/connect_helpdesk_kai_prod/tables/roles_usuarios
terraform import google_bigquery_table.sla_configuracion_prod projects/connectdatakai/datasets/connect_helpdesk_kai_prod/tables/sla_configuracion
terraform import google_bigquery_table.tickets_prod projects/connectdatakai/datasets/connect_helpdesk_kai_prod/tables/tickets

# Core Infra
echo "--- Importando Artifact Registry, Proyecto, Cloud SQL y Networking ---"
terraform import google_artifact_registry_repository.kai_core_api projects/connectdatakai/locations/us-central1/repositories/kai-core-api
terraform import google_project.connectdatakai projects/connectdatakai
terraform import google_sql_database_instance.kai_postgres_prod projects/connectdatakai/instances/kai-postgres-prod
terraform import google_sql_database_instance.kai_postgres_dev projects/connectdatakai/instances/kai-postgres-dev
terraform import google_compute_global_address.default_ip_range projects/connectdatakai/global/addresses/default-ip-range
terraform import google_compute_firewall.default_allow_internal projects/connectdatakai/global/firewalls/default-allow-internal
terraform import google_compute_firewall.default_allow_ssh projects/connectdatakai/global/firewalls/default-allow-ssh
terraform import google_compute_firewall.default_allow_icmp projects/connectdatakai/global/firewalls/default-allow-icmp
terraform import google_compute_address.serverless_ipv4 projects/connectdatakai/regions/us-central1/addresses/serverless-ipv4-1756740508488398707
terraform import google_compute_firewall.default_allow_rdp projects/connectdatakai/global/firewalls/default-allow-rdp
terraform import google_compute_address.nat_auto_ip projects/connectdatakai/regions/us-central1/addresses/nat-auto-ip-10978999-11-1756744069660644
terraform import google_compute_router.at_router_default_us_central1 projects/connectdatakai/regions/us-central1/routers/at-router-default-us-central1

# Logging
echo "--- Importando Sinks de Logging ---"
terraform import 'google_logging_project_sink.required_sink' 'projects/537990588927/sinks/_Required'
terraform import 'google_logging_project_sink.default_sink' 'projects/537990588927/sinks/_Default'

# Secrets
echo "--- Importando Secretos y Versiones de Secret Manager ---"
terraform import google_secret_manager_secret.asana_pat projects/537990588927/secrets/asana-pat
terraform import google_secret_manager_secret.google_chat_webhook_url projects/537990588927/secrets/GOOGLE_CHAT_WEBHOOK_URL
terraform import google_secret_manager_secret.brevo_api_key projects/537990588927/secrets/BREVO_API_KEY
terraform import google_secret_manager_secret.firebase_service_account projects/537990588927/secrets/firebase-service-account
terraform import google_secret_manager_secret.kai_postgres_password_dev projects/537990588927/secrets/kai-postgres-password-dev
terraform import google_secret_manager_secret.kai_postgres_password_prod projects/537990588927/secrets/kai-postgres-password-prod
terraform import google_secret_manager_secret_version.version_firebase_service_account projects/537990588927/secrets/firebase-service-account/versions/1
terraform import google_secret_manager_secret_version.version_asana_pat projects/537990588927/secrets/asana-pat/versions/1
terraform import google_secret_manager_secret_version.version_brevo_api_key projects/537990588927/secrets/BREVO_API_KEY/versions/1
terraform import google_secret_manager_secret_version.version_kai_postgres_password_prod projects/537990588927/secrets/kai-postgres-password-prod/versions/1
terraform import google_secret_manager_secret_version.version_google_chat_webhook_url projects/537990588927/secrets/GOOGLE_CHAT_WEBHOOK_URL/versions/1
terraform import google_secret_manager_secret_version.version_kai_postgres_password_dev projects/537990588927/secrets/kai-postgres-password-dev/versions/1

# APIs
echo "--- Importando APIs Habilitadas (Project Services) ---"
APIS=(
  "bigquerymigration.googleapis.com" "artifactregistry.googleapis.com" "bigqueryconnection.googleapis.com"
  "bigquerystorage.googleapis.com" "cloudapis.googleapis.com" "bigquery.googleapis.com"
  "aiplatform.googleapis.com" "chat.googleapis.com" "analyticshub.googleapis.com"
  "compute.googleapis.com" "cloudscheduler.googleapis.com" "bigquerydatapolicy.googleapis.com"
  "cloudtrace.googleapis.com" "bigqueryreservation.googleapis.com" "containerregistry.googleapis.com"
  "dataform.googleapis.com" "dataplex.googleapis.com" "run.googleapis.com"
  "oslogin.googleapis.com" "pubsub.googleapis.com" "datastore.googleapis.com"
  "firestore.googleapis.com" "firebaserules.googleapis.com" "secretmanager.googleapis.com"
  "servicenetworking.googleapis.com" "serviceusage.googleapis.com" "sqladmin.googleapis.com"
  "logging.googleapis.com" "monitoring.googleapis.com" "storage-component.googleapis.com"
  "storage.googleapis.com" "sql-component.googleapis.com" "servicemanagement.googleapis.com"
  "storage-api.googleapis.com" "cloudbuild.googleapis.com" "cloudfunctions.googleapis.com"
)
for API in "${APIS[@]}"; do
  terraform import "google_project_service.apis[\"$API\"]" "537990588927/$API"
done

# Cloud Run
echo "--- Importando Cloud Run Services ---"
terraform import google_cloud_run_v2_service.kai_api_dev projects/connectdatakai/locations/us-central1/services/kai-api-dev
terraform import google_cloud_run_v2_service.kai_api_prod projects/connectdatakai/locations/us-central1/services/kai-api-prod

# Storage
echo "--- Importando Cloud Storage Buckets ---"
terraform import google_storage_bucket.kai_knowledge_base kai-knowledge-base
terraform import google_storage_bucket.kai_tiquete_attachments kai-tiquete-attachments

echo "--- ¡PROCESO DE IMPORTACIÓN FINALIZADO! ---"
echo "Ahora ejecuta 'terraform plan' para verificar que no haya cambios pendientes."