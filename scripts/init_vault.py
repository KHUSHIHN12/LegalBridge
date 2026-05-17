import json
import os
import time
import urllib.error
import urllib.request


VAULT_ADDR = os.getenv("VAULT_ADDR", "http://localhost:8200").rstrip("/")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "legalbridge-root-token")
SECRET_PATH = "secret/data/legalbridge/config"

DEMO_SECRETS = {
    "SECRET_KEY": "legalbridge-vault-secret",
    "JWT_SECRET": "legalbridge-vault-jwt-secret",
    "FLASK_ENV": "development",
    "DEBUG": "false",
}


def vault_request(method, path, payload=None):
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        f"{VAULT_ADDR}/v1/{path}",
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-Vault-Token": VAULT_TOKEN,
        },
    )

    with urllib.request.urlopen(request, timeout=5) as response:
        if response.status not in (200, 204):
            raise RuntimeError(f"Vault returned HTTP {response.status}")
        return response.read()


def wait_for_vault():
    for attempt in range(1, 11):
        try:
            vault_request("GET", "sys/health")
            return
        except (urllib.error.URLError, TimeoutError, RuntimeError):
            if attempt == 10:
                raise RuntimeError(
                    "Vault is not reachable. Start it first with: docker compose up -d vault"
                )
            time.sleep(2)


def main():
    wait_for_vault()
    vault_request("POST", SECRET_PATH, {"data": DEMO_SECRETS})
    print("Demo Vault secrets written successfully")
    print(f"Vault address: {VAULT_ADDR}")
    print("Secret path: secret/data/legalbridge/config")
    print("Secret values were not printed for safety")


if __name__ == "__main__":
    main()
