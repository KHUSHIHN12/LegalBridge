# LegalBridge Terraform Cleanup

This folder has been cleaned to remove the previous AWS-based Terraform implementation. LegalBridge no longer contains Terraform code that creates cloud resources, depends on the AWS provider, or can create AWS billing charges.

## Folder Structure

```text
LegalBridge/
+-- backend/
+-- frontend/
+-- monitoring/
+-- docker-compose.yml
+-- Dockerfile
+-- terraform/
    +-- main.tf
    +-- variables.tf
    +-- outputs.tf
    +-- .gitignore
    +-- README.md
```

## Files Deleted

The following AWS-specific Terraform files were removed:

- `provider.tf`: removed AWS provider configuration.
- `terraform.tfvars`: removed AWS region, EC2 key pair, repository, CIDR, and port settings.
- `terraform.tfvars.example`: removed AWS example values.

## Files Modified

The following files were kept as safe placeholders:

- `main.tf`: AWS resources, data sources, EC2 bootstrap, and `user_data` scripts removed.
- `variables.tf`: AWS variables removed.
- `outputs.tf`: AWS outputs removed.
- `README.md`: replaced AWS deployment documentation with cleanup guidance.
- `.gitignore`: kept Terraform state and cache exclusions.

## AWS Terraform Removed

The cleanup removed references to:

- `aws_instance`
- `aws_security_group`
- `aws_vpc`
- `aws_subnets`
- `aws_ami`
- AWS provider blocks
- AWS variables such as `aws_region`, `instance_type`, `key_name`, and CIDR allowlists
- AWS outputs such as public IP, public DNS, SSH command, Flask URL, and Prometheus URL
- EC2 `user_data` bootstrap scripts
- Docker installation scripts intended for EC2
- GitHub clone scripts intended for EC2

## Why This Cleanup Was Done

The old Terraform setup deployed LegalBridge to AWS. That is useful for a cloud DevOps demo, but it can create real AWS resources and possible billing. This project is now being prepared for a simpler local Docker-based Terraform setup, so the cloud deployment code has been removed.

## Cloud Terraform vs Local Docker Terraform

Cloud Terraform usually manages infrastructure such as EC2 instances, VPCs, subnets, security groups, IAM roles, load balancers, and cloud databases. It needs cloud credentials and may create paid resources.

Local Docker Terraform manages resources on your own machine, such as Docker containers, Docker networks, Docker volumes, and local service ports. It is better for beginner-friendly demos because it does not require AWS billing or cloud accounts.

## Cleanup Steps

If the old AWS Terraform was already applied, destroy the AWS resources before deleting local state:

```bash
cd LegalBridge/terraform
terraform destroy
```

Only run `terraform destroy` while the old AWS Terraform configuration and state are still available. If the AWS files were already removed but resources still exist in AWS, restore the old Terraform files from Git history or delete the resources carefully from the AWS console.

After confirming that no AWS resources remain, remove local Terraform state and cache files:

PowerShell:

```powershell
Remove-Item -Recurse -Force .terraform
Remove-Item -Force terraform.tfstate
Remove-Item -Force terraform.tfstate.backup
```

Git Bash or Linux/macOS shell:

```bash
rm -rf .terraform
rm -f terraform.tfstate terraform.tfstate.backup
```

If state files have different names, delete any matching files:

```text
*.tfstate
*.tfstate.*
```

## Reinitializing Terraform Later

When the local Docker-based Terraform implementation is added, reinitialize Terraform:

```bash
cd LegalBridge/terraform
terraform init
terraform fmt
terraform validate
terraform plan
```

At the moment, this folder intentionally has no provider, resources, variables, or outputs.

## How This Prepares LegalBridge

This reset gives LegalBridge a clean Terraform base without cloud dependencies. The next Terraform version can focus on local Docker resources, such as:

- Docker network for LegalBridge services
- Flask backend container
- Frontend container
- Prometheus container
- Grafana container
- Local volumes for monitoring data

That makes the project safer for a student DevOps portfolio because the app can be demonstrated locally without AWS billing risk.

## Safety Checklist

- Confirm old AWS resources are destroyed before deleting state.
- Confirm no AWS provider block remains.
- Confirm no `aws_*` resources or data sources remain.
- Confirm no AWS variables or outputs remain.
- Keep Terraform state files out of Git.
- Re-run `terraform init` only after adding the next local Docker Terraform provider.

## Current Terraform Status

The Terraform folder is now a placeholder. It is safe to commit as a clean starting point for the future local Docker Terraform implementation.
