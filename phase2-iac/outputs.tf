output "gke_cluster_name" {
  value = google_container_cluster.autopilot_cluster.name
}
output "cloudsql_instance_name" {
  value = google_sql_database_instance.postgres.name
}
output "artifact_registry_repo" {
  value = google_artifact_registry_repository.docker_repo.name
}
