

resource "google_storage_bucket" "functions_source" {
  project                     = var.gcp_project_id
  name                        = "${var.gcp_project_id}-functions-source"
  location                    = var.gcp_region
  uniform_bucket_level_access = true
}

resource "google_cloudfunctions2_function" "stop_sql_dev" {
  project  = var.gcp_project_id
  name     = "stop-sql-instance-dev"
  location = var.gcp_region
  build_config {
    runtime     = "python312"
    entry_point = "stop_instance_handler"
    source {
      storage_source {
        bucket = google_storage_bucket.functions_source.name
        object = "source.zip" # Placeholder
      }
    }
  }
  service_config {
    max_instance_count    = 1
    service_account_email = google_service_account.sql_scheduler_invoker.email
    environment_variables = {
      DB_INSTANCE_NAME = "kai-postgres-dev"
    }
  }
}

resource "google_cloudfunctions2_function" "start_sql_dev" {
  project  = var.gcp_project_id
  name     = "start-sql-instance-dev"
  location = var.gcp_region
  build_config {
    runtime     = "python312"
    entry_point = "start_instance_handler"
    source {
      storage_source {
        bucket = google_storage_bucket.functions_source.name
        object = "source.zip" # Placeholder
      }
    }
  }
  service_config {
    max_instance_count    = 1
    service_account_email = google_service_account.sql_scheduler_invoker.email
    environment_variables = {
      DB_INSTANCE_NAME = "kai-postgres-dev"
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "stop_sql_invoker" {
  project  = var.gcp_project_id
  location = google_cloudfunctions2_function.stop_sql_dev.location
  name     = google_cloudfunctions2_function.stop_sql_dev.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.sql_scheduler_invoker.email}"
}

resource "google_cloud_run_v2_service_iam_member" "start_sql_invoker" {
  project  = var.gcp_project_id
  location = google_cloudfunctions2_function.start_sql_dev.location
  name     = google_cloudfunctions2_function.start_sql_dev.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.sql_scheduler_invoker.email}"
}

resource "google_cloud_scheduler_job" "stop_sql_dev_nightly" {
  project   = var.gcp_project_id
  name      = "stop-sql-dev-nightly"
  region    = var.gcp_region
  schedule  = "0 20 * * 1-5"
  time_zone = "America/Costa_Rica"
  http_target {
    uri         = google_cloudfunctions2_function.stop_sql_dev.service_config[0].uri
    http_method = "POST"
    oidc_token {
      service_account_email = google_service_account.sql_scheduler_invoker.email
    }
  }
}

resource "google_cloud_scheduler_job" "start_sql_dev_morning" {
  project   = var.gcp_project_id
  name      = "start-sql-dev-morning"
  region    = var.gcp_region
  schedule  = "0 6 * * 1-5"
  time_zone = "America/Costa_Rica"
  http_target {
    uri         = google_cloudfunctions2_function.start_sql_dev.service_config[0].uri
    http_method = "POST"
    oidc_token {
      service_account_email = google_service_account.sql_scheduler_invoker.email
    }
  }
}