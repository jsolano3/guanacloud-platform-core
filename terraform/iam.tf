resource "google_service_account" "compute_default_sa" {
  project      = var.gcp_project_id
  account_id   = "default-compute-sa-kai"
  display_name = "Default compute service account"
}

resource "google_service_account" "github_actions_deployer" {
  project      = var.gcp_project_id
  account_id   = "github-actions-deployer"
  display_name = "github-actions-deployer"
  description  = "SA para deploy de github a la cloud run"
}

resource "google_service_account" "sql_scheduler_invoker" {
  project      = var.gcp_project_id
  account_id   = "sql-scheduler-invoker"
  display_name = "Cloud SQL Scheduler Invoker"
  description  = "SA para encender y apagar la instancia de Cloud SQL de desarrollo."
}

resource "google_project_iam_member" "sql_admin_binding" {
  project = var.gcp_project_id
  role    = "roles/cloudsql.admin"
  member  = "serviceAccount:${google_service_account.sql_scheduler_invoker.email}"
}