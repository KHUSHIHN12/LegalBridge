# LegalBridge Secrets and Security Management

This document explains how LegalBridge handles secrets using HashiCorp Vault locally with Docker. It is written for a beginner-friendly final-year DevOps project and avoids AWS IAM or paid cloud services.

## Security Goal

LegalBridge needs sensitive values for Flask sessions, future JWT signing, and runtime configuration. These values should not be hardcoded in source code because Git history, public repositories, CI logs, and shared systems can expose them.

Secrets used by LegalBridge:

- `SECRET_KEY`: Flask session signing key.
- `JWT_SECRET`: signing key for future JWT-based authentication.
- `FLASK_ENV`: runtime environment.
- `DEBUG`: debug mode flag.

## Why Secrets Should Not Be Hardcoded

Hardcoded secrets are dangerous because:

- Anyone with repository access can read them.
- Old secrets remain visible in Git history.
- Public GitHub repositories are scanned for leaked credentials.
- Leaked Flask secrets can allow forged sessions.
- CI/CD logs can expose values if secrets are printed accidentally.

LegalBridge keeps secrets outside code and loads them at runtime.

## Vault Architecture

LegalBridge uses HashiCorp Vault in local Docker dev mode.

Architecture:

```text
Developer Machine
|
|-- Docker Compose
|   |-- legalbridge-vault     port 8200
|   |-- legalbridge-backend   port 5000
|   |-- legalbridge-frontend  port 8080
|   |-- prometheus            port 9090
|   `-- grafana               port 3000
|
`-- .env fallback
```

Vault service settings:

```text
Image: hashicorp/vault
Mode: dev
Port: 8200
Demo root token: legalbridge-root-token
Listen address: 0.0.0.0:8200
```

The backend receives:

```text
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=legalbridge-root-token
```

## Secret Flow

Secret flow in LegalBridge:

1. Docker Compose starts Vault.
2. Docker Compose starts the Flask backend.
3. Flask loads `.env` first using `python-dotenv`.
4. Flask tries to connect to Vault using `VAULT_ADDR` and `VAULT_TOKEN`.
5. Flask reads secrets from `secret/data/legalbridge/config`.
6. If Vault is available, Vault values are used.
7. If Vault is unavailable, Flask safely falls back to `.env` or environment variables.
8. Flask never prints actual secret values.

The backend prints only safe status messages:

```text
Vault secrets loaded successfully
```

or:

```text
Vault unavailable, using environment fallback
```

## Vault Secret Path

LegalBridge reads this KV v2 path:

```text
secret/data/legalbridge/config
```

Stored demo keys:

```text
SECRET_KEY
JWT_SECRET
FLASK_ENV
DEBUG
```

## Initializing Demo Secrets

Recommended first run:

```bash
docker compose up -d vault
python scripts/init_vault.py
docker compose up --build
```

This starts Vault first, writes the demo secrets, and then starts the full stack so Flask can load secrets from Vault during startup.

If the backend is already running before Vault secrets are initialized, restart it:

```bash
docker compose restart backend
```

The script writes:

```text
SECRET_KEY=legalbridge-vault-secret
JWT_SECRET=legalbridge-vault-jwt-secret
FLASK_ENV=development
DEBUG=false
```

The script does not print the secret values after writing them.

## Vault UI

Open:

```text
http://localhost:8200
```

Login method:

```text
Token
```

Demo token:

```text
legalbridge-root-token
```

## .env Fallback

`.env` is still useful for local development and CI fallback. It lets the app run even when Vault is not started.

Create it from the example:

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

Example values are documented in `.env.example`, while the real `.env` file is ignored by Git.

## Difference Between .env and Vault

`.env`:

- Simple local file.
- Good for beginner development.
- Easy to accidentally copy or leak.
- No access control.
- No audit trail.

Vault:

- Central secrets manager.
- Stores secrets outside the codebase.
- Supports policies, tokens, leases, audit logs, and secret rotation in real deployments.
- Better for DevOps and security demonstrations.
- Dev mode is only for learning and demos.

## Local Demo Limitations

This project uses Vault dev mode only for student demonstration.

Limitations:

- The root token is fixed and visible for demo convenience.
- Secrets are stored in memory inside the dev Vault container.
- Secrets are lost when the dev Vault container is recreated.
- There are no production policies or real authentication methods.
- The root token has full admin access.

This is acceptable for a final-year local demo, but not for production.

## Production Vault Expectations

A production Vault setup should use:

- Persistent storage.
- Initialization and unseal process.
- Separate admin and application tokens.
- Least-privilege policies.
- TLS.
- Audit logging.
- Secret rotation.
- No hardcoded root token.

LegalBridge intentionally does not use production Vault here because the project requirement is a safe local DevOps demonstration without cloud billing.

## GitHub Actions CI/CD

GitHub Actions still works without Vault. CI provides secrets through environment variables:

```text
SECRET_KEY
JWT_SECRET
FLASK_ENV
DEBUG
```

When Vault is not available in CI, Flask uses the environment fallback and continues safely.

## Docker Compose Integration

`docker-compose.yml` includes:

- `vault`: local HashiCorp Vault dev server.
- `backend`: Flask app that receives Vault connection variables.
- `prometheus`: monitoring.
- `grafana`: dashboards.
- `frontend`: UI.

The backend depends on Vault so Docker starts Vault before Flask.

## Terraform Docker Provider Integration

LegalBridge uses Terraform Docker Provider for local IaC. It does not use AWS IAM or paid cloud services.

The Terraform setup can manage local Docker resources, including:

- Vault container.
- Backend container.
- Nginx container.
- Shared Docker network.

This keeps the DevOps demo cloud-free and reproducible on Docker Desktop.

## .gitignore Protection

`.gitignore` protects local secrets and generated files:

```gitignore
.env
.env.*
!.env.example
*.db
terraform/.terraform/
terraform/*.tfstate
terraform/*.tfstate.*
terraform/*.tfvars
```

This means:

- Real `.env` files stay local.
- `.env.example` remains safe to commit.
- SQLite databases are not committed.
- Terraform state and real variable files are not committed.

## Viva Explanation

For viva, explain it like this:

LegalBridge implements HashiCorp Vault as the secrets management layer. Vault runs locally in Docker dev mode, so the project avoids AWS IAM and paid cloud dependencies. The Flask backend receives Vault address and token through Docker Compose, connects with the Python `hvac` client, and reads secrets from `secret/data/legalbridge/config`. If Vault is unavailable, Flask falls back to `.env` values so the app and CI do not break. This demonstrates a real DevOps security practice: secrets are separated from source code, injected at runtime, and never printed in logs.

## Beginner-Friendly Security Practices Used

- Secrets are not hardcoded in Python code.
- `.env` is ignored by Git.
- `.env.example` documents required variables safely.
- Vault stores demo secrets locally.
- Flask has safe fallback behavior.
- Secret values are never printed.
- GitHub Actions can run without local Vault.
- No AWS IAM or paid cloud services are used.
