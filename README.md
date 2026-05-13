# LegalBridge

LegalBridge is a Legal-Tech DevOps project with a Flask backend, frontend UI, SQLite database, Docker Compose, Prometheus monitoring, GitHub Actions CI/CD, local Terraform Docker Provider IaC, and HashiCorp Vault for local secrets management.

## Project Structure

```text
LegalBridge/
|-- backend/
|   |-- app.py
|   |-- requirements.txt
|   `-- search_engine.py
|-- data/
|   `-- sections.json
|-- frontend/
|-- monitoring/
|   `-- prometheus.yml
|-- nginx/
|-- scripts/
|   `-- init_vault.py
|-- terraform/
|-- docker-compose.yml
|-- Dockerfile
|-- .env.example
|-- SECURITY_MANAGEMENT.md
`-- README.md
```

## Secrets Management with HashiCorp Vault

LegalBridge uses HashiCorp Vault as the local secrets management tool for the final-year DevOps security requirement. Vault stores sensitive values outside the source code so secrets are not hardcoded in Flask files, Docker files, or GitHub Actions workflows.

Secrets managed for this demo:

- `SECRET_KEY`
- `JWT_SECRET`
- `FLASK_ENV`
- `DEBUG`

Vault runs locally through Docker Compose using the official `hashicorp/vault` image. It is configured in dev mode for student/demo use only and is exposed at:

```text
http://localhost:8200
```

Demo token:

```text
legalbridge-root-token
```

The Flask backend reads Vault settings from:

```text
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=legalbridge-root-token
```

Inside Docker, Flask connects to the `vault` service name. From your host machine, helper scripts connect through `http://localhost:8200`.

If Vault is unavailable, the Flask app does not crash. It prints a safe message and falls back to `.env` or normal environment variables. Actual secret values are never printed.

## Run with Docker Compose

Create your local environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Recommended first run:

```bash
docker compose up -d vault
python scripts/init_vault.py
docker compose up --build
```

This starts Vault first, writes the demo secrets, and then starts the full stack so Flask can load secrets from Vault during startup.

For later runs, start the full stack directly:

```bash
docker compose up --build
```

If you initialize Vault after the backend is already running, restart the backend so Flask reloads the Vault-backed configuration:

```bash
docker compose restart backend
```

Services:

- Flask backend: `http://localhost:5000`
- Frontend UI: `http://localhost:8080`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
- Vault UI: `http://localhost:8200`

Log in to Vault UI with:

```text
Token: legalbridge-root-token
```

## Local Flask Run

Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Run the backend:

```bash
python app.py
```

If Vault is not running locally, Flask uses the values from `.env`.

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/analyze` | Analyze complaint text |
| POST | `/api/mapping/ipc-to-bns` | Map IPC section to BNS |
| POST | `/api/mapping/bns-to-ipc` | Map BNS section to IPC |
| GET | `/api/sections/search` | Intelligent legal search |

Example:

```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"The accused committed murder","date":"2024-06-20"}'
```

## Terraform Docker Provider

The `terraform/` folder uses the Docker Provider for local IaC. It does not use AWS IAM or paid cloud services.

The local Terraform setup can create Docker resources such as:

- Vault container
- LegalBridge backend container
- Nginx container
- Shared Docker network

Typical commands:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Security Notes

- `.env` is ignored by Git.
- `.env.example` is safe to commit.
- Vault dev mode is for demonstration only.
- The demo root token must not be used in production.
- Production Vault should use real storage, unseal keys, policies, and non-root tokens.

For the full security explanation and viva notes, see [SECURITY_MANAGEMENT.md](SECURITY_MANAGEMENT.md).
