resource "google_container_cluster" "autopilot_cluster" {
  name     = "${var.project_id}-autopilot"
  location = var.region

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.subnet.id

  # Enable Autopilot mode
  enable_autopilot = true


  # Workload Identity Configuration
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }


  # Release Channel Configuration
  release_channel {
    channel = "REGULAR"
  }

  # IP allocation policy for services
  ip_allocation_policy {
    cluster_secondary_range_name  = "pod-ranges"
    services_secondary_range_name = "svc-ranges"
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  # Master authorized networks
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "all"
    }
  }

  # Maintenance policy
  maintenance_policy {
    recurring_window {
      start_time = "2023-01-01T09:00:00Z"
      end_time   = "2023-01-01T17:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=SA,SU"
    }
  }
}
