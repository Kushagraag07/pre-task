resource "google_service_account" "gke_app_sa" {
  account_id   = "gke-app-sa"
  display_name = "GKE app service account"
}

resource "google_project_iam_member" "sa_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.gke_app_sa.email}"
}

resource "google_project_iam_member" "sa_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.gke_app_sa.email}"
}

# Bind KSA -> GSA for Workload Identity (replace namespace/ksa name when creating KSA)
resource "google_service_account_iam_binding" "workload_identity_binding" {
  service_account_id = google_service_account.gke_app_sa.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[${var.k8s_namespace}/${var.k8s_service_account}]"
  ]
}
