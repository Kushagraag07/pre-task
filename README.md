# PRE-TASK

Overview
--------
This repository contains a Flask-based Product Management REST API (Phase 1).


Files included (high level)
- `app.py` — Flask application and REST endpoints.
- `app_logging.py` — Logging configuration used by the application.
- `models.sql` — Postgres initialization SQL (creates `product` table and `uuid-ossp` extension).
- `Dockerfile` — Production container for the backend (see below).
- `docker-compose.yml` — Local development stack: `backend` + `db` (see below).
- `requirements.txt` — Python dependencies.
- `phase2-iac/` — Terraform + Kubernetes manifests for GCP (see list below).
- `.github\workflows` — CI-CD pipeline 

# run locally 
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

---
Dockerfile (Production Container)
---------------------------------
* Uses `python:3.11-slim` for a secure, minimal Python environment.
* Creates a non-root user (`app`) for security; avoids running as root.
* Installs system dependencies (`libpq-dev`, `build-essential`) for database connectivity.
* Installs Python dependencies from `requirements.txt`.
* Copies all application code into `/app` and sets correct ownership.
* Runs the app with Gunicorn (`CMD ["gunicorn", ...]`) for production-grade serving, binding to port 5000.
* Exposes logs to stdout/stderr for integration with container logging systems.
* Environment variables like `LOG_LEVEL`, `PORT`, and Python settings are set for best practices.

How to build and run the Docker image manually:
```powershell
# Build the image
docker build -t cme-task-backend:latest .

# Run the container (example, with environment variables)
docker run -e DB_HOST=localhost -e DB_PORT=5432 -e DB_USER=postgres -e DB_PASS=yourpassword -e DB_NAME=cmeproducts_db -p 5000:5000 cme-task-backend:latest
```

docker-compose.yml (Local Development)
--------------------------------------
* Defines two services: `backend` (Flask app) and `db` (Postgres 15).
* The `backend` service builds from the local `Dockerfile` and sets up all required environment variables for DB connectivity.
* The `db` service uses the official Postgres image, mounts `models.sql` for automatic DB/table creation, and exposes port 5433 on the host for local access.
* Healthchecks are defined for both services to ensure readiness.
* Uses a custom Docker network for secure inter-container communication.
* Environment variables are passed securely; you should set `DB_PASS` in your shell before running Compose.

How to use docker-compose for local development:
```powershell
# Set your DB password in the environment
$env:DB_PASS = "your_db_password"

# Start both services (builds images if needed)
docker-compose up --build

# Stop and clean up
docker-compose down
```

* The backend will be available at `http://localhost:5000`.
* The Postgres database will be available on your host at port 5433 (useful for connecting with tools like DBeaver, pgAdmin, etc.).
* Logs and healthchecks are visible in the Compose output.


# Google Cloud SQL – PostgreSQL Setup Guide

This section explains how to create and access a **PostgreSQL instance on Google Cloud Platform (GCP)** for your project. Example instance name: `my-postfres-instance`.

 Prerequisites
* Google Cloud Platform (GCP) account
* GCP project created
* Billing enabled

Step 1: Create or Select a GCP Project
1. Go to the Google Cloud Console.
2. Click the **Project Dropdown** (top navigation bar).
3. Select an existing project or create a new one.
4. Note your **Project ID**.

Step 2: Enable Cloud SQL Admin API
1. Go to **Navigation Menu → APIs & Services → Library**.
2. Search for **Cloud SQL Admin API**.
3. Click **Enable**.

Step 3: Create the PostgreSQL Instance
1. Go to **Navigation Menu → SQL → Create Instance**.
2. Select **PostgreSQL**.
3. Fill in:
    * **Instance ID**: `my-postfres-instance`
    * **Password** for the default `postgres` user
    * Region (e.g., `us-central1`)
4. Click **Create Instance**.
 
Step 4: View Your Created Instance
 Web Console:
* Navigate to → **SQL Dashboard**: https://console.cloud.google.com/sql
* Ensure the correct **Project** is selected.
* Your PostgreSQL instance will appear on the list.

 Cloud Shell / gcloud CLI:
```powershell
gcloud sql instances list
gcloud sql instances describe my-postfres-instance
```

 Step 5: Configure Connections (Public Access for Testing)
1. Open your instance → **Connections** tab.
2. Under **Authorized Networks**, click **Add Network**.
3. Add:
    * Name: `dev-access`
    * Network: `0.0.0.0/0` *(for testing only — not secure for production)*

 Step 6: Get Connection Information
In the instance overview, note:
* **Public IP** (e.g., `35.200.xxx.xxx`)
* **Instance Connection Name** (e.g., `your-project:us-central1:my-postfres-instance`)

 Step 7: Connect to PostgreSQL
 Option A — Using Google Cloud Shell
```powershell
gcloud sql connect my-postfres-instance --user=postgres
```
You will be prompted for your password.

 Option B — Using psql from Local Machine
```powershell
psql "host=<PUBLIC_IP> user=postgres password=<YOUR_PASSWORD> dbname=postgres sslmode=require"
```

 Step 8: Create Database and User (Optional)
Once connected:
```sql
CREATE DATABASE cmeproducts_db;
CREATE USER cmeuser WITH PASSWORD 'strongpassword';
GRANT ALL PRIVILEGES ON DATABASE cmeproducts_db TO cmeuser;
```

 Step 9: Connect from Your Application
Use the following connection string:
```
postgresql://cmeuser:strongpassword@<PUBLIC_IP>:5432/cmeproducts_db
```
Example environment variables:
```
DB_HOST=35.200.xxx.xxx
DB_NAME=cmeproducts_db
DB_USER=cmeuser
DB_PASSWORD=strongpassword
DB_PORT=5432
```

 Step 10: Production Recommendations
* Disable public IP access
* Use **Private IP** when connecting from GKE, Cloud Run, or VM
* Enable automated backups
* Configure IAM database authentication if needed

Completed
You have successfully:
* Enabled Cloud SQL API
* Created a PostgreSQL instance (`my-postfres-instance`)
* Viewed and accessed your instance
* Connected using Cloud Shell / psql
* Created databases and users



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


# Phase 2 --- Infrastructure as Code (IaC) & Google Cloud SQL Setup



Phase 2 focuses on deploying the application built in **Phase 1** onto **Google Cloud Platform (GCP)** using a fully automated and secure **Infrastructure as Code (IaC)** approach. All infrastructure --- VPC networks, GKE Autopilot cluster, Cloud SQL PostgreSQL instance, IAM permissions, container registry, and Kubernetes manifests --- is created and managed using **Terraform** and **Kubernetes YAML files**.

The goal of this phase is to transition the backend application into a **cloud-native, secure, scalable, and observable** environment.
Architecture Overview


This phase creates the following cloud architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Google Cloud Platform (GCP)                        │
│                                                                             │
│   ┌─────────────────────────────┐      ┌─────────────────────────────┐       │
│   │  Google Cloud SQL (Postgres)│◄────►│  GKE Autopilot Cluster      │       │
│   │    Private IP Only          │      │  (Kubernetes)               │       │
│   └─────────────────────────────┘      │                                 │   │
│           ▲   │                        │   ┌─────────────────────────┐   │   │
│           │   │ VPC Peering            │   │ Backend Deployment      │   │   │
│           │   └────────────────────────┘   │ - Flask REST API        │   │   │
│           │                                │ - Secrets as ENV vars   │   │   │
│           │                                │ - /metrics endpoint     │   │   │
│           │                                │ - PodMonitoring         │   │   │
│           │                                │ - Autoscaling (HPA)     │   │   │
│           │                                └─────────────────────────┘   │   │
│           │                                │   ▲                         │   │
│           │                                │   │                         │   │
│           │                                │   │ Cloud Monitoring        │   │
│           │                                │   │ scrapes metrics         │   │
│           │                                │   ▼                         │   │
│           │                                └─────────────────────────────┘   │
│           │                                │                                 │
│           │                                │ LoadBalancer Service            │
│           │                                │ (Public REST API access)        │
│           │                                └─────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
* Private VPC Peering connects Cloud SQL and GKE securely (no public IP exposure).
* Backend pods expose Prometheus metrics, scraped by Cloud Monitoring.
* LoadBalancer Service provides public API access.
* All secrets and DB credentials are injected securely via Kubernetes Secrets.



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


**1\. `main.tf` -- Network + Artifact Registry Setup**

-   Creates a **VPC** with manual subnets (auto-mode disabled).

-   Creates a **subnetwork** that includes **secondary IP ranges**:

    -   `10.20.0.0/16` → pod IPs

    -   `10.30.0.0/16` → service cluster IPs

-   Enables **private Google access** for internal communication.

-   Creates an **Artifact Registry** repository (`DOCKER` format).

 **2\. `gke.tf` -- GKE Autopilot Cluster**

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

 **3\. `sql.tf` -- Cloud SQL PostgreSQL**

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


 **4\. `iam.tf` -- IAM Roles + Workload Identity**

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

 **5\. `variables.tf` -- Configurable Variables**

Defines all inputs:

-   Project ID

-   Region & zone

-   CIDR ranges

-   DB name, tier, port

-   Kubernetes namespace/service account

This makes Terraform reusable and parameterized.


 **6\. `output.tf` -- Useful Outputs**

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


# GKE Autopilot Cluster Details


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


`Purpose`

This manifest integrates **Google Cloud Managed Prometheus / Cloud Monitoring** with your application by exposing metrics from your pods.


` What it does:`

-   Targets pods with label `app: cme-task`.

-   Scrapes metrics from `/metrics` every 30 seconds.

-   Sends metrics to **Cloud Monitoring dashboards**.

-   Enables:

    -   Request rate tracking

    -   Error metrics

    -   Custom dashboards

    -   Alerting & SLOs

    -   Better autoscaling decisions

`Requirement:`

Your backend must expose `/metrics`.\
(e.g., using  Prometheus client library.)


# Security Considerations


 `Non-root containers`

Using `USER app` inside Dockerfile improves security.

`Private networking`

Cloud SQL uses **private IP only**, inaccessible from the internet.

`Workload Identity`

Pods authenticate to GCP **without service account keys**.

`Kubernetes Secrets`

DB credentials are stored as Secrets, not hardcoded.

`IAM Least Privilege`

Only essential roles are granted (`cloudsql.client`, `artifactregistry.reader`).


# Deployment Steps


`Authenticate to GCP`

```
gcloud auth login
gcloud config set project <PROJECT_ID>

```

`Enable required APIs`

```
gcloud services enable\
  compute.googleapis.com\
  container.googleapis.com\
  artifactregistry.googleapis.com\
  sqladmin.googleapis.com\
  servicenetworking.googleapis.com\
  iam.googleapis.com

```


`Deploy Terraform`

```
cd terraform/
terraform init
terraform plan -var="project_id=<PROJECT_ID>" -var="db_password=<YOUR_DB_PASS>"
terraform apply

```



`Connect to GKE cluster`

```
gcloud container clusters get-credentials <CLUSTER_NAME> --region <REGION>

```


`Build and push the Docker image`

```
docker build -t us-central1-docker.pkg.dev/<PROJECT_ID>/my-docker-repo/backend:latest .
docker push us-central1-docker.pkg.dev/<PROJECT_ID>/my-docker-repo/backend:latest

```

* * * * *

`Apply Kubernetes manifests`

```
kubectl apply -f kubernetes/secret.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/hpa.yaml
kubectl apply -f kubernetes/podmonitoring.yaml    # NEW

```

`Verify everything`

```
kubectl get pods
kubectl get svc
kubectl get hpa
kubectl get podmonitoring

```

`Cleanup (to avoid charges)`
```
terraform destroy

```


# Phase 3 — CI/CD Pipeline (GitHub Actions)
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

# Phase 4 — Monitoring, Logging & Optimization
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

 Alerting Policies

- Google Cloud Monitoring Alerting Policies continuously watch your cluster and automatically trigger notifications if issues arise.

Your alert policies include:

* * * * *

1\. Backend 5xx Error Alert (previously named "backup alert")

Type: Google Cloud Metrics  
Purpose: Detects when the backend API begins returning **HTTP 5xx server errors**, indicating failures inside the application or infrastructure.  
Triggers When:  
- A sudden spike in 500/502/503/504 errors  
- Application crash  
- Database connectivity failure  
- Misconfigured deployment  

This alert helps ensure the API remains reliable and any backend failures are caught immediately.

* * * * *

2\. Pod Restart Spike (>3 restarts in 10 min)


Type: PromQL Query\
Purpose: Detects Kubernetes pod crash loops or unstable deployments.\
Logic:\
Alerts if pod restarts exceed 3 within 10 minutes.\
This helps detect:

-   CrashLoopBackOff

-   ImagePull errors

-   Misconfigured environment variables

* * * * *

3\. p95 Latency > 800ms


Type: PromQL Query\
Purpose: Tracks backend request performance using 95th percentile latency.\
Triggers When:\
95% of requests take longer than **800ms**, indicating:

-   Heavy load

-   DB delays

-   Slow API responses

* * * * *

4\. Backend -- High Error Rate

Type: PromQL Query\
Purpose: Tracks HTTP error responses (5xx / 4xx).\
Triggers When:\
Error rate exceeds threshold (e.g., >10% of total requests).

This prevents silent failures.

* * * * *

 Viewing Alerts


Cloud Console → Monitoring → Alerting

There you see:

-   Active / closed incidents

-   List of alert policies

-   Snoozed alerts

-   Severity levels

-   Last modified date

Cost optimization & operational tips
- Pause Cloud SQL when idle to save credits:

   ```powershell
   gcloud sql instances stop <Instance_name>
   ```

- Scale deployments to zero when not in use:

   ```powershell
   kubectl scale deployment <deployment_name> --replicas=0
   ```

- Consider smaller DB tiers or preemptible nodes for non-production environments to reduce costs.

