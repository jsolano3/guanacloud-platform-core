terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# ==============================================================================
# 1. HABILITACIÓN DE APIS
# ==============================================================================
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com", "sqladmin.googleapis.com", "firestore.googleapis.com",
    "storage-component.googleapis.com", "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com", "aiplatform.googleapis.com", "iam.googleapis.com",
    "vpcaccess.googleapis.com", "chat.googleapis.com", "bigquery.googleapis.com",
    "compute.googleapis.com", "artifactregistry.googleapis.com", "servicenetworking.googleapis.com",
    "containerregistry.googleapis.com", "logging.googleapis.com", "monitoring.googleapis.com",
    "cloudtrace.googleapis.com", "serviceusage.googleapis.com", "bigquerymigration.googleapis.com",
    "bigqueryconnection.googleapis.com", "bigquerystorage.googleapis.com", "cloudapis.googleapis.com",
    "analyticshub.googleapis.com", "bigquerydatapolicy.googleapis.com", "bigqueryreservation.googleapis.com",
    "dataform.googleapis.com", "dataplex.googleapis.com", "oslogin.googleapis.com",
    "pubsub.googleapis.com", "datastore.googleapis.com", "firebaserules.googleapis.com",
    "sql-component.googleapis.com", "servicemanagement.googleapis.com", "storage-api.googleapis.com",
    "cloudbuild.googleapis.com", "cloudfunctions.googleapis.com","storage.googleapis.com"
  ])
  project            = "537990588927"
  service            = each.key
  disable_on_destroy = false
}

# ==============================================================================
# 2. PROYECTO
# ==============================================================================
resource "google_project" "connectdatakai" {
  project_id      = "connectdatakai"
  name            = "ConnectDataKai"
  billing_account = "01F0AE-0878CD-37CFCC"
  org_id          = "897375052532"
}

# ==============================================================================
# 3. CLOUD RUN SERVICES
# ==============================================================================
resource "google_cloud_run_v2_service" "kai_api_dev" {
  project  = var.gcp_project_id
  location = var.gcp_region
  name     = "kai-api-dev"
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account                  = "537990588927-compute@developer.gserviceaccount.com"
    execution_environment            = "EXECUTION_ENVIRONMENT_GEN1"
    max_instance_request_concurrency = 80
    timeout                          = "300s"

    scaling {
      min_instance_count = 0
      max_instance_count = 100
    }

    vpc_access {
      egress = "ALL_TRAFFIC"
    }

    containers {
      image = "us-central1-docker.pkg.dev/connectdatakai/kai-core-api/kai-api-dev:e840d7f5583e585bf6dcf21c19ad127f874373e0"
      ports { container_port = 8080 }
    }
  }
}

resource "google_cloud_run_v2_service" "kai_api_prod" {
  project  = var.gcp_project_id
  location = var.gcp_region
  name     = "kai-api-prod"
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account                  = "537990588927-compute@developer.gserviceaccount.com"
    max_instance_request_concurrency = 80
    timeout                          = "300s"

    scaling {
      min_instance_count = 1
      max_instance_count = 100
    }

    vpc_access {
      egress = "ALL_TRAFFIC"
    }

    containers {
      image = "us-central1-docker.pkg.dev/connectdatakai/kai-core-api/kai-api-prod:ec58c9abd15b4c49fd141bfa680a26c140748279"
      ports { container_port = 8080 }
    }
  }
}

# ==============================================================================
# 4. CLOUD SQL INSTANCES
# ==============================================================================
resource "google_sql_database_instance" "kai_postgres_prod" {
  project             = var.gcp_project_id
  name                = "kai-postgres-prod"
  database_version    = "POSTGRES_17"
  region              = var.gcp_region
  deletion_protection = true

  settings {
    tier              = "db-custom-1-3840"
    availability_type = "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 10
    disk_autoresize   = true
    ip_configuration {
      ipv4_enabled    = false
      private_network = "projects/${var.gcp_project_id}/global/networks/default"
    }
  }
}

resource "google_sql_database_instance" "kai_postgres_dev" {
  project             = var.gcp_project_id
  name                = "kai-postgres-dev"
  database_version    = "POSTGRES_17"
  region              = var.gcp_region
  deletion_protection = true

  settings {
    tier              = "db-g1-small"
    availability_type = "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 10
    disk_autoresize   = true
    ip_configuration {
      ipv4_enabled    = false
      private_network = "projects/${var.gcp_project_id}/global/networks/default"
    }
  }
}

# ==============================================================================
# 5. BIGQUERY
# ==============================================================================
resource "google_bigquery_dataset" "connect_helpdesk_kai_prod" {
  project    = var.gcp_project_id
  dataset_id = "connect_helpdesk_kai_prod"
  location   = "US"
}

resource "google_bigquery_table" "eventos_tiquetes_prod" {
  project    = var.gcp_project_id
  dataset_id = "connect_helpdesk_kai_prod"
  table_id   = "eventos_tiquetes"
  schema     = "[{\"mode\":\"REQUIRED\",\"name\":\"EventoID\",\"type\":\"STRING\"},{\"mode\":\"REQUIRED\",\"name\":\"TicketID\",\"type\":\"STRING\"},{\"mode\":\"NULLABLE\",\"name\":\"FechaEvento\",\"type\":\"TIMESTAMP\"},{\"mode\":\"NULLABLE\",\"name\":\"Autor\",\"type\":\"STRING\"},{\"mode\":\"NULLABLE\",\"name\":\"TipoEvento\",\"type\":\"STRING\"},{\"mode\":\"NULLABLE\",\"name\":\"Detalles\",\"type\":\"STRING\"}]"
}

resource "google_bigquery_table" "nps_feedback_prod" {
  project    = var.gcp_project_id
  dataset_id = "connect_helpdesk_kai_prod"
  table_id   = "nps_feedback"
  schema     = "[{\"mode\":\"REQUIRED\",\"name\":\"feedback_id\",\"type\":\"STRING\"},{\"name\":\"session_id\",\"type\":\"STRING\"},{\"name\":\"user_email\",\"type\":\"STRING\"},{\"name\":\"rating\",\"type\":\"INTEGER\"},{\"name\":\"comment\",\"type\":\"STRING\"},{\"mode\":\"REQUIRED\",\"name\":\"timestamp\",\"type\":\"TIMESTAMP\"}]"
}

resource "google_bigquery_table" "roles_usuarios_prod" {
  project    = var.gcp_project_id
  dataset_id = "connect_helpdesk_kai_prod"
  table_id   = "roles_usuarios"
  schema     = "[{\"description\":\"Correo electrónico del usuario, es la clave principal.\",\"name\":\"user_email\",\"type\":\"STRING\"},{\"description\":\"Nombre del usuario para referencia.\",\"name\":\"user_name\",\"type\":\"STRING\"},{\"description\":\"Rol del usuario: admin, lead, o agent.\",\"name\":\"role\",\"type\":\"STRING\"},{\"description\":\"Departamento al que pertenece el usuario, ej: 'Data Engineering', 'Data Analyst / BI'.\",\"name\":\"department\",\"type\":\"STRING\"}]"
}

resource "google_bigquery_table" "sla_configuracion_prod" {
  project    = var.gcp_project_id
  dataset_id = "connect_helpdesk_kai_prod"
  table_id   = "sla_configuracion"
  schema     = "[{\"description\":\"ID único para la regla de SLA.\",\"name\":\"config_id\",\"type\":\"STRING\"},{\"description\":\"Departamento al que aplica la regla, ej: 'Data Engineering'.\",\"name\":\"department\",\"type\":\"STRING\"},{\"description\":\"Nivel de prioridad: 'alta', 'media', 'baja'.\",\"name\":\"priority\",\"type\":\"STRING\"},{\"description\":\"Número de horas asignadas para el SLA.\",\"name\":\"sla_hours\",\"type\":\"INTEGER\"}]"
}

resource "google_bigquery_table" "tickets_prod" {
  project    = var.gcp_project_id
  dataset_id = "connect_helpdesk_kai_prod"
  table_id   = "tickets"
  schema     = "[{\"mode\":\"REQUIRED\",\"name\":\"TicketID\",\"type\":\"STRING\"},{\"mode\":\"NULLABLE\",\"name\":\"Solicitante\",\"type\":\"STRING\"},{\"mode\":\"NULLABLE\",\"name\":\"FechaCreacion\",\"type\":\"TIMESTAMP\"},{\"mode\":\"NULLABLE\",\"name\":\"SLA_horas\",\"type\":\"INTEGER\"},{\"mode\":\"NULLABLE\",\"name\":\"FechaVencimiento\",\"type\":\"TIMESTAMP\"}]"
}

resource "google_bigquery_dataset" "connect_helpdesk_kai_dev" {
  project    = var.gcp_project_id
  dataset_id = "connect_helpdesk_kai_dev"
  location   = "US"
}

resource "google_bigquery_table" "eventos_tiquetes_dev" {
  project    = var.gcp_project_id
  dataset_id = "connect_helpdesk_kai_dev"
  table_id   = "eventos_tiquetes"
  schema     = "[{\"mode\":\"REQUIRED\",\"name\":\"EventoID\",\"type\":\"STRING\"},{\"mode\":\"REQUIRED\",\"name\":\"TicketID\",\"type\":\"STRING\"},{\"mode\":\"NULLABLE\",\"name\":\"FechaEvento\",\"type\":\"TIMESTAMP\"},{\"mode\":\"NULLABLE\",\"name\":\"Autor\",\"type\":\"STRING\"},{\"mode\":\"NULLABLE\",\"name\":\"TipoEvento\",\"type\":\"STRING\"},{\"mode\":\"NULLABLE\",\"name\":\"Detalles\",\"type\":\"STRING\"}]"
}

resource "google_bigquery_table" "nps_feedback_dev" {
  project    = var.gcp_project_id
  dataset_id = "connect_helpdesk_kai_dev"
  table_id   = "nps_feedback"
  schema     = "[{\"mode\":\"REQUIRED\",\"name\":\"feedback_id\",\"type\":\"STRING\"},{\"name\":\"session_id\",\"type\":\"STRING\"},{\"name\":\"user_email\",\"type\":\"STRING\"},{\"name\":\"rating\",\"type\":\"INTEGER\"},{\"name\":\"comment\",\"type\":\"STRING\"},{\"mode\":\"REQUIRED\",\"name\":\"timestamp\",\"type\":\"TIMESTAMP\"}]"
}

resource "google_bigquery_table" "roles_usuarios_dev" {
  project    = var.gcp_project_id
  dataset_id = "connect_helpdesk_kai_dev"
  table_id   = "roles_usuarios"
  schema     = "[{\"description\":\"Correo electrónico del usuario, es la clave principal.\",\"name\":\"user_email\",\"type\":\"STRING\"},{\"description\":\"Nombre del usuario para referencia.\",\"name\":\"user_name\",\"type\":\"STRING\"},{\"description\":\"Rol del usuario: admin, lead, o agent.\",\"name\":\"role\",\"type\":\"STRING\"},{\"description\":\"Departamento al que pertenece el usuario, ej: 'Data Engineering', 'Data Analyst / BI'.\",\"name\":\"department\",\"type\":\"STRING\"}]"
}

resource "google_bigquery_table" "sla_configuracion_dev" {
  project    = var.gcp_project_id
  dataset_id = "connect_helpdesk_kai_dev"
  table_id   = "sla_configuracion"
  schema     = "[{\"description\":\"ID único para la regla de SLA.\",\"name\":\"config_id\",\"type\":\"STRING\"},{\"description\":\"Departamento al que aplica la regla, ej: 'Data Engineering'.\",\"name\":\"department\",\"type\":\"STRING\"},{\"description\":\"Nivel de prioridad: 'alta', 'media', 'baja'.\",\"name\":\"priority\",\"type\":\"STRING\"},{\"description\":\"Número de horas asignadas para el SLA.\",\"name\":\"sla_hours\",\"type\":\"INTEGER\"}]"
}

resource "google_bigquery_table" "tickets_dev" {
  project    = var.gcp_project_id
  dataset_id = "connect_helpdesk_kai_dev"
  table_id   = "tickets"
  schema     = "[{\"mode\":\"REQUIRED\",\"name\":\"TicketID\",\"type\":\"STRING\"},{\"mode\":\"NULLABLE\",\"name\":\"Solicitante\",\"type\":\"STRING\"},{\"mode\":\"NULLABLE\",\"name\":\"FechaCreacion\",\"type\":\"TIMESTAMP\"},{\"mode\":\"NULLABLE\",\"name\":\"SLA_horas\",\"type\":\"INTEGER\"},{\"mode\":\"NULLABLE\",\"name\":\"FechaVencimiento\",\"type\":\"TIMESTAMP\"}]"
}

# ==============================================================================
# 6. CLOUD STORAGE
# ==============================================================================
resource "google_storage_bucket" "kai_knowledge_base" {
  project                     = var.gcp_project_id
  name                        = "kai-knowledge-base"
  location                    = "US-CENTRAL1"
  uniform_bucket_level_access = true
  storage_class               = "STANDARD"
}

resource "google_storage_bucket" "kai_tiquete_attachments" {
  project                     = var.gcp_project_id
  name                        = "kai-tiquete-attachments"
  location                    = "US-CENTRAL1"
  uniform_bucket_level_access = true
  storage_class               = "STANDARD"
}

resource "google_storage_bucket" "kai_looker_looks" {
  project                     = var.gcp_project_id
  name                        = "kai-looker-looks"
  location                    = "US-CENTRAL1"
  uniform_bucket_level_access = true
  storage_class               = "STANDARD"
}

# ==============================================================================
# 7. ARTIFACT REGISTRY
# ==============================================================================
resource "google_artifact_registry_repository" "kai_core_api" {
  project       = var.gcp_project_id
  location      = var.gcp_region
  repository_id = "kai-core-api"
  description   = "Docker images for the Kai Core API service"
  format        = "DOCKER"
  mode          = "STANDARD_REPOSITORY"
}

# ==============================================================================
# 8. VERTEX AI
# ==============================================================================
resource "google_vertex_ai_index" "agent_kai_kb_index" {
  project             = "537990588927"
  region              = var.gcp_region
  display_name        = "agent-kai-kb"
  description         = "index para vector de KB en agent Kai"
  index_update_method = "BATCH_UPDATE"

  metadata {
    contents_delta_uri = ""
    config {
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 1000
          leaf_nodes_to_search_percent = 0
        }
      }
      approximate_neighbors_count = 150
      dimensions                  = 768
      distance_measure_type       = "COSINE_DISTANCE"
    }
  }
}

resource "google_vertex_ai_index_endpoint" "endpoint_agent_kai" {
  project      = "537990588927"
  region       = var.gcp_region
  display_name = "endpoint-agent-kai"
}

# ==============================================================================
# 9. NETWORKING
# ==============================================================================
resource "google_compute_global_address" "default_ip_range" {
  project       = var.gcp_project_id
  name          = "default-ip-range"
  address_type  = "INTERNAL"
  purpose       = "VPC_PEERING"
  prefix_length = 20
  network       = "https://www.googleapis.com/compute/v1/projects/${var.gcp_project_id}/global/networks/default"
}

resource "google_compute_firewall" "default_allow_internal" {
  project       = var.gcp_project_id
  name          = "default-allow-internal"
  network       = "https://www.googleapis.com/compute/v1/projects/${var.gcp_project_id}/global/networks/default"
  direction     = "INGRESS"
  priority      = 65534
  source_ranges = ["10.128.0.0/9"]
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "icmp"
  }
}

resource "google_compute_firewall" "default_allow_ssh" {
  project       = var.gcp_project_id
  name          = "default-allow-ssh"
  network       = "https://www.googleapis.com/compute/v1/projects/${var.gcp_project_id}/global/networks/default"
  direction     = "INGRESS"
  priority      = 65534
  source_ranges = ["0.0.0.0/0"]
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

resource "google_compute_firewall" "default_allow_icmp" {
  project       = var.gcp_project_id
  name          = "default-allow-icmp"
  network       = "https://www.googleapis.com/compute/v1/projects/${var.gcp_project_id}/global/networks/default"
  direction     = "INGRESS"
  priority      = 65534
  source_ranges = ["0.0.0.0/0"]
  allow {
    protocol = "icmp"
  }
}

resource "google_compute_address" "serverless_ipv4" {
  project      = var.gcp_project_id
  name         = "serverless-ipv4-1756740508488398707"
  region       = var.gcp_region
  address_type = "INTERNAL"
  purpose      = "SERVERLESS"
  prefix_length = 28
  subnetwork   = "https://www.googleapis.com/compute/v1/projects/${var.gcp_project_id}/regions/${var.gcp_region}/subnetworks/default"
}

resource "google_compute_firewall" "default_allow_rdp" {
  project       = var.gcp_project_id
  name          = "default-allow-rdp"
  network       = "https://www.googleapis.com/compute/v1/projects/${var.gcp_project_id}/global/networks/default"
  direction     = "INGRESS"
  priority      = 65534
  source_ranges = ["0.0.0.0/0"]
  allow {
    protocol = "tcp"
    ports    = ["3389"]
  }
}

resource "google_compute_address" "nat_auto_ip" {
  project      = var.gcp_project_id
  name         = "nat-auto-ip-10978999-11-1756744069660644"
  region       = var.gcp_region
  address_type = "EXTERNAL"
  purpose      = "NAT_AUTO"
}

resource "google_compute_router" "at_router_default_us_central1" {
  project = var.gcp_project_id
  name    = "at-router-default-us-central1"
  network = "https://www.googleapis.com/compute/v1/projects/${var.gcp_project_id}/global/networks/default"
  region  = var.gcp_region
}

# ==============================================================================
# 10. LOGGING
# ==============================================================================
resource "google_logging_project_sink" "required_sink" {
  project     = "537990588927"
  name        = "_Required"
  destination = "logging.googleapis.com/projects/connectdatakai/locations/global/buckets/_Required"
  filter      = "LOG_ID(\"cloudaudit.googleapis.com/activity\") OR LOG_ID(\"externalaudit.googleapis.com/activity\") OR LOG_ID(\"cloudaudit.googleapis.com/system_event\") OR LOG_ID(\"externalaudit.googleapis.com/system_event\") OR LOG_ID(\"cloudaudit.googleapis.com/access_transparency\") OR LOG_ID(\"externalaudit.googleapis.com/access_transparency\")"
}

resource "google_logging_project_sink" "default_sink" {
  project     = "537990588927"
  name        = "_Default"
  destination = "logging.googleapis.com/projects/connectdatakai/locations/global/buckets/_Default"
  filter      = "NOT LOG_ID(\"cloudaudit.googleapis.com/activity\") AND NOT LOG_ID(\"externalaudit.googleapis.com/activity\") AND NOT LOG_ID(\"cloudaudit.googleapis.com/system_event\") AND NOT LOG_ID(\"externalaudit.googleapis.com/system_event\") AND NOT LOG_ID(\"cloudaudit.googleapis.com/access_transparency\") AND NOT LOG_ID(\"externalaudit.googleapis.com/access_transparency\")"
}