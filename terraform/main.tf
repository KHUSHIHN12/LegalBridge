
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

  ports {
    internal = 5000
    external = 5001
  }
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
}

