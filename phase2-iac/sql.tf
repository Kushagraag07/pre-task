resource "google_sql_database_instance" "postgres" {
  name             = "${var.project_id}-pg"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = var.db_tier
    backup_configuration { enabled = true }


    # Private IP (for GKE internal access)
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }
}
resource "google_sql_database" "app_db" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app_user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

output "db_connection_info" {
  value = {
    name     = var.db_name
    user     = var.db_user
    port     = var.db_port
    instance = google_sql_database_instance.postgres.name
  }
}
