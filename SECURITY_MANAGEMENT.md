# LegalBridge Secrets and Security Management

This guide explains how LegalBridge handles secrets in a beginner-friendly DevOps architecture using Flask, SQLite, Docker Compose, Prometheus, GitHub Actions, and Terraform.

LegalBridge uses SQLite only. There is no MongoDB configuration in this project.

## What Secrets Management Means

Secrets management means storing sensitive values outside source code and passing them securely to the application at runtime.

Examples of secrets:

- `SECRET_KEY`: Flask session signing key.
- `JWT_SECRET`: signing key for JWT tokens if JWT authentication is added.
- Cloud credentials, API keys, SSH keys, and deployment tokens.

Non-secret configuration can also live beside secrets:

- `FLASK_ENV`: application environment such as `development`, `testing`, or `production`.
- `DEBUG`: whether Flask debug mode is enabled.

## Why Hardcoding Secrets Is Dangerous

Hardcoding means writing secrets directly in files like `app.py`, `docker-compose.yml`, or GitHub Actions YAML.

This is dangerous because:

- Anyone with repository access can see the secret.
- Git history keeps old secrets even after a file is edited.
- Attackers can steal session cookies or forge tokens if Flask/JWT secrets leak.
- Public GitHub repositories are scanned by bots for exposed keys.
- A leaked CI/CD secret can allow unauthorized deployments.

## How .env Files Improve Security

A `.env` file stores local environment variables outside the code. Flask loads it with `python-dotenv`, and Docker Compose can read it automatically.

The important rule is:

- Commit `.env.example`.
- Never commit `.env`.

The `.env.example` file documents the required variables without exposing real values.

## Required Local .env Variables

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Generate secure values:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Use one generated value for `SECRET_KEY` and a different generated value for `JWT_SECRET`.

Example `.env` format:

```env
SECRET_KEY=replace-with-a-generated-token-urlsafe-value
JWT_SECRET=replace-with-a-different-generated-token-urlsafe-value
FLASK_ENV=development
DEBUG=false
```

For production:

```env
FLASK_ENV=production
DEBUG=false
```

## Flask Configuration Code

LegalBridge loads secrets in [backend/app.py](backend/app.py):

```python
from dotenv import load_dotenv

load_dotenv()

secret_key = os.getenv("SECRET_KEY")
jwt_secret = os.getenv("JWT_SECRET")
```

The app stores them in Flask configuration:

```python
app.config.update(
    SECRET_KEY=secret_key,
    JWT_SECRET=jwt_secret,
    FLASK_ENV=flask_env,
    DEBUG=debug_enabled,
)
```

In production, `SECRET_KEY` and `JWT_SECRET` are required. If either is missing, the app stops instead of starting insecurely.

## Docker Compose Environment Integration

[docker-compose.yml](docker-compose.yml) reads `.env` and passes values into the backend container:

```yaml
backend:
  env_file:
    - .env
  environment:
    SECRET_KEY: ${SECRET_KEY}
    JWT_SECRET: ${JWT_SECRET}
    FLASK_ENV: ${FLASK_ENV:-development}
    DEBUG: ${DEBUG:-false}
```

How Docker reads `.env` variables:

1. Docker Compose looks for `.env` in the same folder as `docker-compose.yml`.
2. Compose substitutes values like `${SECRET_KEY}`.
3. The backend container receives those values as environment variables.
4. Flask reads those variables using `os.getenv()` and `python-dotenv`.

## GitHub Secrets for CI/CD

GitHub Secrets protect CI/CD values so they are not written directly in workflow files.

Add these repository secrets in GitHub:

- `LEGALBRIDGE_SECRET_KEY`
- `LEGALBRIDGE_JWT_SECRET`

Path in GitHub:

```text
Repository > Settings > Secrets and variables > Actions > New repository secret
```

The workflow [legalbridge-ci.yml](.github/workflows/legalbridge-ci.yml) uses them like this:

```yaml
env:
  SECRET_KEY: ${{ secrets.LEGALBRIDGE_SECRET_KEY }}
  JWT_SECRET: ${{ secrets.LEGALBRIDGE_JWT_SECRET }}
  FLASK_ENV: testing
  DEBUG: "false"
```

GitHub masks secret values in logs, so accidental `echo "$SECRET_KEY"` output is hidden. Still, never print secrets intentionally.

## .gitignore Protection

[.gitignore](.gitignore) protects local secrets and generated files:

```gitignore
.env
.env.*
!.env.example
*.db
terraform/*.tfvars
!terraform/*.tfvars.example
```

This means:

- Real `.env` files stay local.
- `.env.example` can be safely uploaded.
- SQLite database files are not committed.
- Real Terraform variable files are not committed.

## Basic IAM Concept

IAM means Identity and Access Management. It controls who or what can access cloud resources.

Beginner-friendly IAM rule:

> Give each user, service, or pipeline only the permissions it needs, and nothing extra.

Examples:

- A GitHub Actions deployment role should deploy LegalBridge, but should not manage billing.
- A student developer may read logs, but should not delete production infrastructure.
- Terraform should use a limited AWS IAM user or role instead of the AWS root account.

This is called the principle of least privilege.

## Folder Structure

```text
LegalBridge/
|-- .env.example
|-- .gitignore
|-- SECURITY_MANAGEMENT.md
|-- docker-compose.yml
|-- Dockerfile
|-- README.md
|-- .github/
|   `-- workflows/
|       `-- legalbridge-ci.yml
|-- backend/
|   |-- app.py
|   |-- requirements.txt
|   `-- search_engine.py
|-- data/
|   `-- sections.json
|-- frontend/
|   |-- Dockerfile
|   |-- index.html
|   |-- signin.html
|   `-- signup.html
|-- monitoring/
|   `-- prometheus.yml
`-- terraform/
    |-- main.tf
    |-- variables.tf
    |-- terraform.tfvars.example
    `-- outputs.tf
```

## Local Setup Steps

Install Python dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Create a local `.env` file:

```bash
cd ..
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Run Flask locally:

```bash
cd backend
python app.py
```

Test the backend:

```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/metrics
```

Run with Docker Compose:

```bash
docker compose up --build
```

Access services:

- Flask backend: `http://localhost:5000`
- Frontend: `http://localhost:8080`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

Stop containers:

```bash
docker compose down
```

## Beginner-Friendly Security Practices Used

- Secrets are loaded from environment variables.
- `.env` is ignored by Git.
- `.env.example` documents required variables safely.
- GitHub Actions uses GitHub Secrets for CI/CD values.
- Flask debug mode is disabled by default.
- Production mode refuses to start without required secrets.
- SQLite database files are ignored.
- Terraform state and real variable files are ignored.
- No MongoDB credentials are included because LegalBridge uses SQLite.

## How Secrets and Security Are Implemented in the LegalBridge DevOps Architecture

LegalBridge separates code from configuration. Flask reads `SECRET_KEY`, `JWT_SECRET`, `FLASK_ENV`, and `DEBUG` from environment variables instead of hardcoded source code. During local development, these values come from a private `.env` file loaded by `python-dotenv`. During containerized execution, Docker Compose reads the same `.env` file and injects the variables into the backend container. During CI/CD, GitHub Actions receives equivalent values from encrypted GitHub Secrets.

The repository protects secret files through `.gitignore`, while still providing `.env.example` and `terraform.tfvars.example` so students can understand exactly what to configure. Terraform variable and state files are ignored because infrastructure metadata can become sensitive. This creates a clean DevOps security flow: developers use local `.env`, Docker uses environment injection, GitHub Actions uses encrypted secrets, and production uses required runtime secrets with debug mode disabled.
