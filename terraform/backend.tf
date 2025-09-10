terraform {
  backend "gcs" {
    bucket  = "terraform-connect"
    prefix  = "terraform/state"
  }
}