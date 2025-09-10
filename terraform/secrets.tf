
resource "google_secret_manager_secret" "kai_postgres_password_prod" {
  project   = "537990588927"
  secret_id = "kai-postgres-password-prod"
  
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret_version" "version_kai_postgres_password_prod" {
  secret      = google_secret_manager_secret.kai_postgres_password_prod.id
  secret_data = var.db_password_prod
}

resource "google_secret_manager_secret" "kai_postgres_password_dev" {
  project   = "537990588927"
  secret_id = "kai-postgres-password-dev"

  replication {
    auto {}
  }
}
resource "google_secret_manager_secret_version" "version_kai_postgres_password_dev" {
  secret      = google_secret_manager_secret.kai_postgres_password_dev.id
  secret_data = var.db_password_dev
}

resource "google_secret_manager_secret" "asana_pat" {
  project   = "537990588927"
  secret_id = "asana-pat"

  replication {
    auto {}
  }
}
resource "google_secret_manager_secret_version" "version_asana_pat" {
  secret      = google_secret_manager_secret.asana_pat.id
  secret_data = "placeholder_for_asana_pat"
}

resource "google_secret_manager_secret" "google_chat_webhook_url" {
  project   = "537990588927"
  secret_id = "GOOGLE_CHAT_WEBHOOK_URL"

  replication {
    auto {}
  }
}
resource "google_secret_manager_secret_version" "version_google_chat_webhook_url" {
  secret      = google_secret_manager_secret.google_chat_webhook_url.id
  secret_data = "placeholder_for_webhook_url"
}

resource "google_secret_manager_secret" "brevo_api_key" {
  project   = "537990588927"
  secret_id = "BREVO_API_KEY"
  
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret_version" "version_brevo_api_key" {
  secret      = google_secret_manager_secret.brevo_api_key.id
  secret_data = "placeholder_for_brevo_key"
}

resource "google_secret_manager_secret" "firebase_service_account" {
  project   = "537990588927"
  secret_id = "firebase-service-account"
  
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret_version" "version_firebase_service_account" {
  secret      = google_secret_manager_secret.firebase_service_account.id
  secret_data = "placeholder"
}