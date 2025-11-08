# Products API with GCP Infrastructure

A Flask REST API for Product Management with Google Cloud Platform infrastructure.

## Phase 1: Application Design & Development

### Flask 3 Compatibility
The app is compatible with Flask 3+, using modern initialization patterns for database setup and configuration.

### Local Development Setup
Create a `.env` file in the project root with your database credentials. A
sample `.env` has been added with placeholder values. Do NOT commit real
secrets to source control — add `.env` to your `.gitignore` in real projects.

Quick start (local)
--------------------
1. Create and activate a Python virtualenv (optional but recommended).
2. Install dependencies:

	pip install -r requirements.txt

3. Create a `.env` in the project root (see sample) and start the app:

	python app.py

The API will be available at http://127.0.0.1:5000

Docker
------
Build the image (from project root):

	docker build -t products-api:latest .

Run the container (pass DB credentials via environment variables or a
managed secret store):

	docker run -e DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/dbname" -p 5000:5000 products-api:latest

Google Cloud SQL
----------------
You can connect to a Cloud SQL Postgres instance in a few ways:

- Use the Cloud SQL Auth Proxy locally and set `DATABASE_URL` to the
  proxied TCP address (e.g. `postgresql+psycopg2://user:pass@127.0.0.1:5432/db`).
- When deploying to Cloud Run, set the `DB` connection via the Cloud SQL
  connection string and attach the Cloud SQL instance to the service.

Security Notes
-------------
- Don't store credentials in source control. Use environment variables or
  a secrets manager.
- Run containers as a non-root user (Dockerfile already switches to `app` user).

## Phase 2: Infrastructure as Code (IaC)

The `phase2-iac` directory contains Terraform configurations for deploying the application to Google Cloud Platform.

### Prerequisites

1. Install required tools:
   - [Terraform](https://www.terraform.io/downloads.html)
   - [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
   - [kubectl](https://kubernetes.io/docs/tasks/tools/)

2. Configure GCP authentication:
   ```bash
   gcloud auth application-default login
   ```

### Infrastructure Components

- **Google Kubernetes Engine (GKE)**
  - Autopilot cluster for managed Kubernetes
  - Workload identity enabled for secure service account access
  - Private cluster configuration with authorized networks

- **Cloud SQL**
  - PostgreSQL 15 database instance
  - Private IP configuration
  - Automated backups enabled
  - Secure user management

- **Artifact Registry**
  - Docker repository for container images
  - IAM configuration for secure access

- **Networking**
  - VPC with custom subnets
  - Private service access
  - Proper IP range management

### Deployment Steps

1. Initialize Terraform:
   ```bash
   cd phase2-iac
   terraform init
   ```

2. Configure variables:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. Review and apply the infrastructure:
   ```bash
   terraform plan
   terraform apply
   ```

4. Configure kubectl for GKE:
   ```bash
   gcloud container clusters get-credentials $(terraform output -raw gke_cluster_name) --region $(terraform output -raw region)
   ```

5. Deploy the application:
   ```bash
   kubectl apply -f k8s-manifests/
   ```

### Infrastructure Updates

To update the infrastructure:
```bash
cd phase2-iac
terraform plan    # Review changes
terraform apply   # Apply changes
```

### Cleanup

To destroy the infrastructure:
```bash
cd phase2-iac
terraform destroy
```

### Important Notes

- Keep `terraform.tfstate` secure and consider using remote state storage
- Review and update `variables.tf` for customization
- Check `terraform.tfvars.example` for required variables
- Use workload identity for secure service account access
- Monitor Cloud SQL usage and adjust instance size as needed

## CI/CD Pipeline (.github/workflows)

The project includes a GitHub Actions workflow for continuous integration and deployment.

### Workflow Features

- **Automated Testing**: Runs Python tests for each push and pull request
- **Security Scanning**: 
  - Container image vulnerability scanning
  - Infrastructure-as-Code security checks
  - Dependencies security audit
- **Deployment Stages**:
  1. Build and test application
  2. Build and push Docker image to Artifact Registry
  3. Apply Terraform infrastructure changes
  4. Deploy to GKE cluster

### Workflow Configuration

File: `.github/workflows/ci-cd.yml`

```yaml
# Main branches trigger full pipeline
on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

# Environment requirements
permissions:
  contents: read
  id-token: write  # Needed for GCP authentication

jobs:
  - Test & Build
  - Infrastructure
  - Deploy
```

### Required Secrets

Configure these GitHub repository secrets:
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: Workload Identity provider
- `GCP_SERVICE_ACCOUNT`: Service account email
- `DB_PASSWORD`: Database password (for tests)

### Security Features

- Uses Workload Identity Federation for GCP authentication
- No static credentials stored in GitHub
- Infrastructure changes require approval
- Automated security scanning in pipeline

### Manual Deployment

To manually trigger a deployment:
1. Go to GitHub Actions tab
2. Select "CI/CD Pipeline"
3. Click "Run workflow"
4. Choose branch and trigger manually

### Monitoring Deployments

- Check GitHub Actions tab for pipeline status
- Review workflow logs for detailed information
- Monitor GCP Console for resource status
- Check deployment status in GKE


