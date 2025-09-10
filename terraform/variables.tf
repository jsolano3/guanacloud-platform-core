variable "gcp_project_id" {
  description = "El ID de tu proyecto de Google Cloud."
  type        = string
}

variable "gcp_region" {
  description = "La región donde se desplegarán los recursos."
  type        = string
  default     = "us-central1"
}

variable "db_password_prod" {
  description = "La contraseña para la base de datos de producción de Cloud SQL."
  type        = string
  sensitive   = true
}

variable "db_password_dev" {
  description = "La contraseña para la base de datos de desarrollo de Cloud SQL."
  type        = string
  sensitive   = true
}