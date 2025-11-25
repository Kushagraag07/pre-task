# cme-task — Phase 1 & Phase 2

Overview
--------
This repository contains a Flask-based Product Management REST API (Phase 1) and Terraform-based Infrastructure as Code (Phase 2) to deploy the application on Google Cloud Platform (GCP).

Files included (high level)
- `app.py` — Flask application and REST endpoints.
- `app_logging.py` — Logging configuration used by the application.
- `models.py` — SQLAlchemy model definitions (if present).
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

Metrics & Logging

- Prometheus metrics: `GET /metrics` (Prometheus client used in `app.py`).
- Structured logging configured in `app_logging.py`.

Phase 2 — Infrastructure as Code (IaC)
-------------------------------------
All IaC lives in `phase2-iac/`. The Terraform and Kubernetes manifests provision and deploy the app to GCP (GKE Autopilot + Cloud SQL + Artifact Registry + VPC).

Included Phase 2 files
- `phase2-iac/main.tf` — provider, VPC, subnet, Artifact Registry resource
- `phase2-iac/gke.tf` — GKE Autopilot cluster configuration
- `phase2-iac/iam.tf` — service accounts and IAM bindings (Workload Identity)
- `phase2-iac/sql.tf` — Cloud SQL instance, database, and user
- `phase2-iac/variables.tf` — Terraform variable definitions
- `phase2-iac/outputs.tf` — outputs such as cluster/instance names
- `phase2-iac/k8s-manifests/` — Kubernetes manifests (`deployment.yaml`, `service.yaml`, `cme-task-secret.yaml`, `hap.yaml`, `podmonitoring.yaml`)

Phase 2 — What was provisioned (summary)

- Secure VPC with private subnet and secondary IP ranges for GKE pods/services
- Artifact Registry (Docker repository) in `us-central1`
- GKE Autopilot cluster with Workload Identity enabled
- Cloud SQL (Postgres 15) instance with private IP
- Kubernetes Deployment & Service with health/readiness probes
- Monitoring/logging integration with Cloud Monitoring (recommended)

Phase 2 — Recommended quick workflow (PowerShell)

1. Set Terraform variables (example):

   ```powershell
   setx TF_VAR_project_id "your-gcp-project-id"
   setx TF_VAR_region "us-central1"
   # set other TF_VAR_ values or create phase2-iac/terraform.tfvars
   ```

2. Initialize/apply Terraform (from `phase2-iac/`):

   ```powershell
   cd phase2-iac
   terraform init
   terraform apply -var="project_id=your-gcp-project-id"
   ```

3. Build and push the backend image to Artifact Registry:

   ```powershell
   gcloud auth configure-docker us-central1-docker.pkg.dev
   docker build -t us-central1-docker.pkg.dev/<PROJECT>/<REPO>/backend:latest .
   docker push us-central1-docker.pkg.dev/<PROJECT>/<REPO>/backend:latest
   ```

4. Deploy Kubernetes manifests (after configuring kubeconfig):

   ```powershell
   gcloud container clusters get-credentials <cluster-name> --region <region> --project <project-id>
   kubectl apply -f phase2-iac/k8s-manifests/
   ```

Notes: Use a Terraform GCS backend for remote state and enable state locking when working in a team.

Troubleshooting checklist
-------------------------
- ImagePull errors: run `gcloud auth configure-docker` and verify Artifact Registry IAM roles for the service account.
- DB connection problems: ensure Cloud SQL private IP is reachable from GKE and Workload Identity has `roles/cloudsql.client`.
- Pending pods: `kubectl describe pod <pod>` and `kubectl logs <pod>` to inspect init/errors.

Next steps I can do for you
--------------------------
- Commit the improved `README.md` to git.
- Create `README-phase2.md` with expanded Terraform snippets and the exact resource names from your `phase2-iac/*` files.
- Add a `phase2-iac/backend.tf` sample that configures a GCS Terraform backend for remote state.

Contact / Notes
---------------


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
gcloud container clusters get-credentials "cme-task-476714-autopilot" --region "us-central1" --project "cme-task-476714"
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
   gcloud container clusters describe cme-task-476714-autopilot --region us-central1 --format="value(loggingService, monitoringService)"
   ```

- Expected output:
   - `logging.googleapis.com/kubernetes`
   - `monitoring.googleapis.com/kubernetes`

- If not enabled, update the cluster:

   ```powershell
   gcloud container clusters update cme-task-476714-autopilot --region us-central1 --logging=SYSTEM,WORKLOAD --monitoring=SYSTEM,WORKLOAD
   ```

Application logging
- The Flask app runs under Gunicorn; logs to stdout/stderr are collected by GKE and forwarded to Cloud Logging.
- Make logs structured for better searching; example in `app_logging.py` and use `app.logger.info()`.
- View recent logs:

   ```powershell
   gcloud logging read "resource.type=k8s_container AND resource.labels.cluster_name=cme-task-476714-autopilot" --limit 10
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
   gcloud sql instances stop cme-task-476714-pg
   ```

- Scale deployments to zero when not in use:

   ```powershell
   kubectl scale deployment cme-task --replicas=0
   ```

- Consider smaller DB tiers or preemptible nodes for non-production environments to reduce costs.
   ```

Summary & next steps
- Phase 4 completes the observability stack: Prometheus metrics exposed by the app, Cloud Monitoring/Logging integration on GKE, alerting policies, HPA tuning, and cost-saving recommendations.
- Next I can:
   - Add example alert policy configurations to `phase2-iac/` or documentation,
   - Add a sample HPA manifest tied to Prometheus custom metrics,
   - Commit the README changes.




