variable "project_id" {
  type = string
}
variable "region" {
  type    = string
  default = "us-central1"
}
variable "zone" {
  type    = string
  default = "us-central1-c"
}

variable "subnet_cidr" {
  type    = string
  default = "10.10.0.0/20"
}

variable "artifact_repo_id" {
  type    = string
  default = "my-docker-repo"
}

# Database configuration
variable "db_name" {
  type    = string
  default = "cmeproducts_db"
}
variable "db_user" {
  type    = string
  default = "postgres"
}
variable "db_password" {
  type = string
}
variable "db_tier" {
  type    = string
  default = "db-f1-micro"
}
variable "db_port" {
  type    = string
  default = "5433"
}

variable "k8s_namespace" {
  type    = string
  default = "app"
}
variable "k8s_service_account" {
  type    = string
  default = "app-sa"
}
