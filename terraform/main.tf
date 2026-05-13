
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.6.2"
    }
  }
}

provider "docker" {}

# -----------------------------
# Shared Docker Network
# -----------------------------
resource "docker_network" "legalbridge_network" {
  name = "terraform-legalbridge-network"
}

# -----------------------------
# Vault Image
# -----------------------------
resource "docker_image" "vault" {
  name = "hashicorp/vault:latest"
}

# -----------------------------
# Vault Container
# -----------------------------
resource "docker_container" "vault" {
  name  = "terraform-legalbridge-vault"
  image = docker_image.vault.image_id

  command = ["server", "-dev"]

  env = [
    "VAULT_DEV_ROOT_TOKEN_ID=legalbridge-root-token",
    "VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200",
  ]

  ports {
    internal = 8200
    external = 8200
  }

  networks_advanced {
    name = docker_network.legalbridge_network.name
  }
}

# -----------------------------
# Backend Image
# -----------------------------
resource "docker_image" "legalbridge_backend" {
  name = "legalbridge-backend:terraform"

  build {
    context    = ".."
    dockerfile = "Dockerfile"
  }
}

# -----------------------------
# Backend Container
# -----------------------------
resource "docker_container" "legalbridge_backend_container" {
  name  = "terraform-legalbridge-backend"
  image = docker_image.legalbridge_backend.image_id

  env = [
    "VAULT_ADDR=http://terraform-legalbridge-vault:8200",
    "VAULT_TOKEN=legalbridge-root-token",
    "FLASK_ENV=development",
    "DEBUG=false",
  ]

  ports {
    internal = 5000
    external = 5001
  }

  networks_advanced {
    name = docker_network.legalbridge_network.name
  }

  depends_on = [
    docker_container.vault,
  ]
}

# -----------------------------
# Nginx Image
# -----------------------------
resource "docker_image" "nginx" {
  name = "nginx:latest"
}

# -----------------------------
# Nginx Container
# -----------------------------
resource "docker_container" "nginx_container" {
  name  = "terraform-nginx"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = 80
  }

  volumes {
    host_path      = "${path.cwd}/../nginx/nginx.conf"
    container_path = "/etc/nginx/nginx.conf"
  }

  networks_advanced {
    name = docker_network.legalbridge_network.name
  }
}

