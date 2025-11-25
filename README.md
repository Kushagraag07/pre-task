# cme-task — Phase 1 & Phase 2

Overview
--------
This repository contains a Flask-based Product Management REST API (Phase 1).

Files included (high level)
- `app.py` — Flask application and REST endpoints.
- `app_logging.py` — Logging configuration used by the application.
- `models.sql` — Postgres initialization SQL (creates `product` table and `uuid-ossp` extension).
- `Dockerfile` — Image for running the app with `gunicorn`.
- `docker-compose.yml` — Local development stack: `backend` + `db`.
- `requirements.txt` — Python dependencies.
- `phase2-iac/` — Terraform + Kubernetes manifests for GCP (see list below).

Phase 1 — Local development
---------------------------
Quick start (Python virtualenv)

1. Create and activate a virtual environment (PowerShell):

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Set environment variables (example):

   ```powershell
   $env:DB_HOST = "localhost"
   $env:DB_PORT = "5432"
   $env:DB_USER = "postgres"
   $env:DB_PASS = "yourpassword"
   $env:DB_NAME = "cmeproducts_db"
   $env:API_KEY = "my-secret-key"
   ```

4. Run locally:

   ```powershell
   python app.py
   ```

Docker Compose (recommended for parity with local DB behavior)

1. Provide `DB_PASS` in your environment and start:

   ```powershell
   $env:DB_PASS = "your_db_password"
   docker-compose up --build
   ```

2. The API will be at `http://localhost:5000`. PostgreSQL is exposed on host port `5433` (container `5432`).

Database initialization

- Local Postgres (used by Docker Compose) runs `models.sql` on first initialization (`/docker-entrypoint-initdb.d/init.sql`).
- For production Cloud SQL, run migrations (e.g., Alembic) or apply schema via CI/CD rather than mounting init SQL.

Phase 1 — API summary

- `GET /` — Index message
- `GET /health` — Health check
- `GET /db-check` — Simple DB query to validate connectivity
- `GET /products` — List products
- `GET /products/<uuid>` — Get product by UUID
- `POST /products` — Create product (requires `X-API-Key` header)
- `PUT /products/<uuid>` — Update product (requires `X-API-Key` header)
- `DELETE /products/<uuid>` — Delete product (requires `X-API-Key` header)

Authentication

Write endpoints require an API key in the header `X-API-Key`. Set `API_KEY` to a secret value in your environment or secret store.
 OR 
Can use JWT token for More Stronger authentication.

Metrics & Logging

- Prometheus metrics: `GET /metrics` (Prometheus client used in `app.py`).
- Structured logging configured in `app_logging.py`.

Phase 2 — Infrastructure as Code (IaC)
Understood --- here is your **complete, fully rewritten Phase-2 README**, including the new **podmonitoring.yaml** section **with NO omissions, NO gaps, NO skipped parts**.\
Everything is included top to bottom, fully detailed, clean, professional, and ready to use.


Phase 2 --- Infrastructure as Code (IaC) & Google Cloud SQL Setup



Phase 2 focuses on deploying the application built in **Phase 1** onto **Google Cloud Platform (GCP)** using a fully automated and secure **Infrastructure as Code (IaC)** approach. All infrastructure --- VPC networks, GKE Autopilot cluster, Cloud SQL PostgreSQL instance, IAM permissions, container registry, and Kubernetes manifests --- is created and managed using **Terraform** and **Kubernetes YAML files**.

The goal of this phase is to transition the backend application into a **cloud-native, secure, scalable, and observable** environment.



🧠 Learning Objectives
----------------------

| Objective | Description |
| --- | --- |
| **IaC Implementation** | Provision and manage infrastructure using declarative configuration (Terraform). |
| **Automation** | Fully automate creation of cloud resources to avoid manual errors and ensure reproducibility. |
| **Security** | Use private IPs, IAM roles, Workload Identity, and Kubernetes Secrets for secure deployment. |
| **Container Orchestration** | Deploy and manage containers using Kubernetes & GKE Autopilot. |
| **Scalability** | Implement Horizontal Pod Autoscaling for on-demand scaling. |
| **Monitoring** | Collect application metrics using PodMonitoring and Cloud Monitoring. |


🧰 Technologies & Tools Used
----------------------------

| Category | Tools / Services | Purpose |
| --- | --- | --- |
| IaC | Terraform | Automate creation of VPC, GKE, Cloud SQL, IAM, Artifact Registry |
| Cloud Provider | Google Cloud Platform | Hosting for all infrastructure |
| Container Runtime | Docker | Build backend container image |
| Container Registry | Google Artifact Registry | Store and serve Docker images |
| Database | Google Cloud SQL (PostgreSQL 15) | Managed relational database |
| Orchestration | GKE Autopilot | Run and scale application containers |
| Secret Management | Kubernetes Secrets | Secure storage of DB credentials |
| Autoscaling | Horizontal Pod Autoscaler (HPA) | CPU-based scaling |
| Monitoring | PodMonitoring + Cloud Monitoring | Observability and metrics scraping |


Architecture Overview


This phase creates the following cloud architecture:

```
                     ┌────────────────────────────┐
                     │ Google Cloud SQL (Postgres)│
                     │     Private IP Only        │
                     └────────────▲───────────────┘
                                  │
                   Private VPC Peering (Service Networking)
                                  │
┌─────────────────────────────────────────────────────────────────────┐
│                          GKE Autopilot Cluster                      │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                     Backend Deployment                      │   │
│   │  - Runs Flask REST API                                      │   │
│   │  - Secrets injected as ENV vars                             │   │
│   │  - Metrics exposed at /metrics                              │   │
│   │  - PodMonitoring scrapes metrics via Cloud Monitoring       │   │
│   │  - Autoscaling via HPA                                      │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   LoadBalancer Service → Provides public access to the REST API     │
└─────────────────────────────────────────────────────────────────────┘

               ▲
               │ Cloud Monitoring scrapes metrics from backend pods
               │
      Google Cloud Managed Prometheus / Monitoring

```


Infrastructure as Code (Terraform)


Your Terraform directory contains:

```
terraform/
├── main.tf
├── gke.tf
├── sql.tf
├── iam.tf
├── variables.tf
├── output.tf
└── terraform.tfvars

```

# Terraform Responsibilities

Terraform provisions:

-   A **custom VPC** and **subnetwork** with secondary IP ranges for pods/services.

-   A **Google Cloud SQL PostgreSQL** instance using **private IP only**.

-   A **GKE Autopilot Cluster** with:

    -   Workload Identity

    -   Private nodes

    -   Regular release channel updates

    -   Pod/service secondary ranges

-   IAM roles for secure access between GKE and Cloud SQL.

-   An Artifact Registry repository for storing Docker images.


File-by-File Explanation


# **1\. `main.tf` -- Network + Artifact Registry Setup**

-   Creates a **VPC** with manual subnets (auto-mode disabled).

-   Creates a **subnetwork** that includes **secondary IP ranges**:

    -   `10.20.0.0/16` → pod IPs

    -   `10.30.0.0/16` → service cluster IPs

-   Enables **private Google access** for internal communication.

-   Creates an **Artifact Registry** repository (`DOCKER` format).


# **2\. `gke.tf` -- GKE Autopilot Cluster**

-   `enable_autopilot = true` → fully managed Kubernetes cluster.

-   Private nodes (no public IPs).

-   Workload Identity configuration:

    ```
    workload_pool = "<PROJECT_ID>.svc.id.goog"

    ```

-   IP allocation policy using the secondary ranges from `main.tf`.

-   Release channel: `"REGULAR"` for stable updates.

-   Maintenance policy for planned cluster updates.

-   Master authorized networks configured (can be restricted further for security).


# **3\. `sql.tf` -- Cloud SQL PostgreSQL**

Creates:

-   A **PostgreSQL 15** database instance.

-   Enables **private IP** access only (no public connectivity):

    ```
    ipv4_enabled = false
    private_network = google_compute_network.vpc.id

    ```

-   A root DB user.

-   A named database (e.g., `cmeproducts_db`).

-   Automatic backups enabled.



# **4\. `iam.tf` -- IAM Roles + Workload Identity**

Creates a **Google Service Account** for the application and grants it:

-   `roles/cloudsql.client` --- required to connect to Cloud SQL.

-   `roles/artifactregistry.reader` --- needed to pull images from Artifact Registry.

Binds the GSA to a Kubernetes ServiceAccount (KSA) via:

```
roles/iam.workloadIdentityUser

```
verify :
```
kubectl -n default get sa backend-sa -o yaml

```

This allows pods to authenticate to Google Cloud *without storing service account keys*.


# **5\. `variables.tf` -- Configurable Variables**

Defines all inputs:

-   Project ID

-   Region & zone

-   CIDR ranges

-   DB name, tier, port

-   Kubernetes namespace/service account

This makes Terraform reusable and parameterized.



# **6\. `output.tf` -- Useful Outputs**

After provisioning, Terraform prints:

-   GKE cluster name

-   Cloud SQL instance name

-   Artifact Registry repo name

-   DB connection information


Google Cloud SQL Setup

  The Cloud SQL instance:

-   Uses the **db-f1-micro** tier (GCP free-trial friendly).

-   Uses **private IP** only for secure, internal access (no public exposure).

-   Automatically backs up data.

-   Has a dedicated database and a DB user created via Terraform.

  Because GKE runs in the same VPC via VPC peering, the backend app can connect to Cloud SQL privately.


GKE Autopilot Cluster Details


# Why Autopilot mode?

-   You don't manage nodes (GCP handles scale, upgrades, optimizations).

-   You pay **only for CPU/Memory your pods request**.

-   Ideal for free trial accounts and lightweight apps.

 Kubernetes Deployment

Your Kubernetes manifests contain these files:

```
kubernetes/
├── deployment.yaml
├── service.yaml
├── hpa.yaml
├── secret.yaml
└── podmonitoring.yaml  

```



 `deployment.yaml`


Defines:

-   A Deployment named `cme-task`.

-   2 replicas of your backend Flask container.

-   Resource requests & limits → important for GKE Autopilot billing.

-   Liveness probe → ensures the application is running.

-   Readiness probe → ensures the app is ready before receiving traffic.

-   Loads DB credentials from Kubernetes `Secret`.

* * * * *

 `service.yaml`


Defines:

-   A `LoadBalancer` type Service.

-   Exposes backend over the internet.

-   GCP automatically provisions a Cloud Load Balancer.

-   Maps external port → pod port (5000).

* * * * *

 `hpa.yaml`


Configures horizontal pod autoscaling:

-   Minimum replicas: 2

-   Maximum replicas: 4

-   CPU target: 70% utilization

-   GKE Autopilot + Cloud Monitoring provide CPU metrics automatically.

* * * * *

 `secret.yaml`


Stores:

-   `DB_USER`

-   `DB_PASS`

-   `DB_NAME`

-   `DB_HOST`

-   `DB_PORT`

(Loaded into the backend container as environment variables.)

* * * * *


 `podmonitoring.yaml` 


# Purpose

This manifest integrates **Google Cloud Managed Prometheus / Cloud Monitoring** with your application by exposing metrics from your pods.


# What it does:

-   Targets pods with label `app: cme-task`.

-   Scrapes metrics from `/metrics` every 30 seconds.

-   Sends metrics to **Cloud Monitoring dashboards**.

-   Enables:

    -   Request rate tracking

    -   Error metrics

    -   Custom dashboards

    -   Alerting & SLOs

    -   Better autoscaling decisions

# Requirement:

Your backend must expose `/metrics`.\
(e.g., using  Prometheus client library.)


# Security Considerations


# Non-root containers

Using `USER app` inside Dockerfile improves security.

# Private networking

Cloud SQL uses **private IP only**, inaccessible from the internet.

# Workload Identity

Pods authenticate to GCP **without service account keys**.

# Kubernetes Secrets

DB credentials are stored as Secrets, not hardcoded.

# IAM Least Privilege

Only essential roles are granted (`cloudsql.client`, `artifactregistry.reader`).


Deployment Steps


# Authenticate to GCP

```
gcloud auth login
gcloud config set project <PROJECT_ID>

```

# Enable required APIs

```
gcloud services enable\
  compute.googleapis.com\
  container.googleapis.com\
  artifactregistry.googleapis.com\
  sqladmin.googleapis.com\
  servicenetworking.googleapis.com\
  iam.googleapis.com

```

* * * * *

# Deploy Terraform

```
cd terraform/
terraform init
terraform plan -var="project_id=<PROJECT_ID>" -var="db_password=<YOUR_DB_PASS>"
terraform apply

```

* * * * *

# Connect to GKE cluster

```
gcloud container clusters get-credentials <CLUSTER_NAME> --region <REGION>

```

* * * * *

# Build and push the Docker image

```
docker build -t us-central1-docker.pkg.dev/<PROJECT_ID>/my-docker-repo/backend:latest .
docker push us-central1-docker.pkg.dev/<PROJECT_ID>/my-docker-repo/backend:latest

```

* * * * *

# Apply Kubernetes manifests

```
kubectl apply -f kubernetes/secret.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/hpa.yaml
kubectl apply -f kubernetes/podmonitoring.yaml    # NEW

```

* * * * *

# Verify everything

```
kubectl get pods
kubectl get svc
kubectl get hpa
kubectl get podmonitoring

```

Cleanup (to avoid charges)
```
terraform destroy

```


Phase 3 — CI/CD Pipeline (GitHub Actions)
----------------------------------------
This project includes a GitHub Actions workflow at `.github/workflows/ci-cd.yml` that implements a secure, keyless CI/CD pipeline: build → push → deploy → smoke-test. The workflow uses OIDC Workload Identity to authenticate to GCP, pushes images to Artifact Registry, and deploys to GKE.

Quick summary (what the workflow does)
- Trigger: `push` to `main` branch.
- Authenticate: `google-github-actions/auth@v1` uses Workload Identity (OIDC) to impersonate the GCP service account specified in the workflow.
- Build & Push: `docker/build-push-action@v4` builds the container and pushes two tags to Artifact Registry: `:<SHA>` and `:latest` (configured via the `IMAGE_REPO` env).
- Deploy: obtains GKE credentials and applies Kubernetes manifests from `phase2-iac/k8s-manifests/`, ensures an `api-key` secret exists, patches the Deployment to reference the `API_KEY` if missing, and performs a rolling update with `kubectl set image`.
- Verify: waits for rollout (timeout extended to 600s) and runs post-deploy smoke tests against `/health` and `/db-check`. If LoadBalancer IP is not ready, the workflow falls back to port-forward for verification.

Key workflow notes (from `ci-cd.yml`)
- Environment values used in the workflow: `PROJECT_ID`, `LOCATION`, `CLUSTER_NAME`, `IMAGE_REPO`, `NAMESPACE`, `DEPLOYMENT`, `CONTAINER_NAME`, `SERVICE_NAME`, `PORT`.
- The workflow creates/updates a Kubernetes secret `api-key` from the `secrets.API_KEY` GitHub secret (idempotent).
- The workflow patches the Deployment to ensure the container has an `API_KEY` env var sourced from the `api-key` secret if it was not included in the manifest.
- After pushing the new image (tagged with the commit SHA), the workflow updates the Deployment's container image and waits for a successful rollout, printing diagnostics and logs on failure.

Important security detail
- The workflow uses Workload Identity Federation (OIDC) for keyless authentication. This is configured outside the repo (Workload Identity Pool & Provider + IAM binding) and avoids storing long-lived service account keys in GitHub.

How to run locally / verify manually (PowerShell)
1) Get GKE credentials:

```powershell
gcloud container clusters get-credentials "<Cluster_name>" --region "<Region of work>" --project "<Project_name>"
```

2) Check current deployment and image:

```powershell
kubectl -n default get deployment cme-task -o wide
kubectl -n default get pods -l app=cme-task -o wide
```

3) Manually update image (if needed):

```powershell
kubectl -n default set image deployment/cme-task backend=us-central1-docker.pkg.dev/cme-task-476714/my-docker-repo/test_project-2-backend:<SHA>
kubectl -n default rollout status deployment/cme-task --timeout=600s
```

4) Run the smoke checks locally (when LoadBalancer IP is available):

```powershell
curl --fail http://<EXTERNAL-IP>:5000/health
curl --fail http://<EXTERNAL-IP>:5000/db-check
```

If LoadBalancer IP is not ready, use port-forward as the workflow does:

```powershell
kubectl -n default port-forward svc/cme-task-service 8080:5000
# then in another shell
curl --fail http://127.0.0.1:8080/health
curl --fail http://127.0.0.1:8080/db-check
```

Notes for maintainers
- Confirm the GitHub repository `secrets.API_KEY` is set; the workflow will create the `api-key` Kubernetes secret from it.
- Ensure the OIDC provider and service account bindings exist and match the `audience` and `workload_identity_pool` values used when configuring the `google-github-actions/auth` step.
- The workflow applies all manifests under `phase2-iac/k8s-manifests/`. Keep those manifests source-controlled and parameterized where possible (image, secrets, resource requests).

Phase 4 — Monitoring, Logging & Optimization
-------------------------------------------
This section documents the monitoring and observability work (Prometheus metrics, Cloud Monitoring, Cloud Logging) and provides actionable steps to enable alerting, autoscaling, and cost optimizations.

Prometheus metrics (what's implemented)
- `http_requests_total` (Counter): labeled by method, path, status — tracks total requests and error rates.
- `request_latency_seconds` (Histogram): buckets [0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2] — measures request latency distribution.
- Automatic instrumentation via Flask middleware (`before_request` / `after_request`) so all routes are measured without per-route changes.
- Metrics endpoint exposed at `/metrics` using `generate_latest()` and `CONTENT_TYPE_LATEST` (compatible with Prometheus and Google Managed Prometheus).

Cloud Monitoring & Logging (GKE integration)
- Enable required APIs:

   ```powershell
   gcloud services enable monitoring.googleapis.com logging.googleapis.com
   ```

- Verify GKE Autopilot cluster integration (logging/monitoring services):

   ```powershell
   gcloud container clusters describe <Cluster_name> --region <region> --format="value(loggingService, monitoringService)"
   ```

- Expected output:
   - `logging.googleapis.com/kubernetes`
   - `monitoring.googleapis.com/kubernetes`

- If not enabled, update the cluster:

   ```powershell
   gcloud container clusters update <Cluster_name> --region <Region> --logging=SYSTEM,WORKLOAD --monitoring=SYSTEM,WORKLOAD
   ```

Application logging
- The Flask app runs under Gunicorn; logs to stdout/stderr are collected by GKE and forwarded to Cloud Logging.
- Make logs structured for better searching; example in `app_logging.py` and use `app.logger.info()`.
- View recent logs:

   ```powershell
   gcloud logging read "resource.type=k8s_container AND resource.labels.cluster_name=<Cluster_name>" --limit 10
   ```

Custom metrics & alerting
- Create alerting policies in Cloud Monitoring for latency, error rates, and high CPU. Example (High CPU):

   ```powershell
   gcloud monitoring policies create --notification-channels="email:youremail@example.com" --condition-display-name="High CPU Usage on GKE Pods" --condition-filter='metric.type="kubernetes.io/container/cpu/core_usage_time" AND resource.type="k8s_container"' --condition-threshold-value=0.7
   ```

- Suggested alert rules:
   - Latency > 1s for 5 minutes
   - 5xx error rate > 5% over 5 minutes
   - Pod restart count > 3 in 10 minutes

Horizontal Pod Autoscaler (HPA)
- The deployment can autoscale based on CPU or custom metrics (Prometheus). Example HPA settings used:
   - `minReplicas: 2`
   - `maxReplicas: 5`
   - `targetCPUUtilizationPercentage: 70`

- View HPA:

   ```powershell
   kubectl get hpa
   kubectl describe hpa cme-task-hpa
   ```

Cost optimization & operational tips
- Pause Cloud SQL when idle to save credits:

   ```powershell
   gcloud sql instances stop <Instance_name>
   ```

- Scale deployments to zero when not in use:

   ```powershell
   kubectl scale deployment cme-task --replicas=0
   ```

- Consider smaller DB tiers or preemptible nodes for non-production environments to reduce costs.
   ```

