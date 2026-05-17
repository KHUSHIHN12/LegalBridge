output "vault_url" {
  description = "Local HashiCorp Vault URL."
  value       = "http://localhost:8200"
}

output "backend_url" {
  description = "Local LegalBridge backend URL created by Terraform Docker Provider."
  value       = "http://localhost:5001"
}
