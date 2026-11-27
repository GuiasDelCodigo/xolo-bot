# AWS Infrastructure (`infra/aws`)

Terraform configuration for the base AWS resources used by `xolo-bot`. It mirrors `infra/oci` with the economic profile and no budget resource.

## What this creates

- **Network**: VPC `10.0.0.0/16`, Internet Gateway, route table with `0.0.0.0/0`, public subnet `10.0.1.0/24`.
- **Security**: security group allowing inbound SSH (`TCP/22`) from `ssh_ingress_cidr` (default `0.0.0.0/0`) and all outbound traffic.
- **SSH key**: `aws_key_pair` named `xolo-bot-key`, created from `ssh_public_key`.
- **Compute**: `m6g.medium` EC2 instance (1 vCPU / 4 GiB, ARM Graviton) with Ubuntu 24.04 ARM64.
- **Storage**: 30 GB gp3 root volume and 30 GB gp3 encrypted data volume attached at `/dev/sdh`.
- **Public IP**: Elastic IP associated with the instance for stable SSH access.
- **Host bootstrap**: cloud-init creates users from `ssh_users`, disables password/root SSH, enables fail2ban, and mounts the data volume at `/opt/xolo-bot/data`.
- **Outputs**: VPC/subnet/instance/volume IDs, private/public IPs, and an SSH command example.

This stack does **not** create a budget, RDS, Redis, S3 bucket, Docker, a deploy script, or backups.

## File layout

| File | Purpose |
|---|---|
| `versions.tf` | Terraform/provider version constraints. |
| `providers.tf` | AWS provider configuration and default tags. |
| `variables.tf` | Input variable contract. |
| `terraform.tfvars.example` | Committable placeholder values. |
| `locals.tf` | Common name and tags. |
| `data.tf` | Availability zones and Ubuntu ARM AMI lookups. |
| `network.tf` | VPC, Internet Gateway, route table, subnet. |
| `security.tf` | Security group rules. |
| `compute.tf` | Key pair, EC2 instance, Elastic IP, association. |
| `outputs.tf` | Useful Terraform outputs. |
| `templates/cloud-init.yaml.tftpl` | Cloud-init bootstrap template. |
| `.terraform.lock.hcl` | Provider version lock file; keep this committed. |

## Prerequisites

- Terraform installed (compatible with `versions.tf`).
- AWS credentials from **AWS Academy Learner Lab**: choose **Start Lab**, then **AWS Details → Show**.
- In the same PowerShell session where Terraform runs, set all three values:

```powershell
$env:AWS_ACCESS_KEY_ID="..."
$env:AWS_SECRET_ACCESS_KEY="..."
$env:AWS_SESSION_TOKEN="..."
$env:AWS_DEFAULT_REGION="us-east-1"
```

The lab session lasts about 4 hours. When it expires, choose **Start Lab** again and paste the new credentials. Do not write them to `terraform.tfvars` or any repo file.

The default region is `us-east-1`, which is allowed by AWS Academy. Do not use `mx-central-1` here.

## How to use

### 1. Create local tfvars

```powershell
cd infra/aws
Copy-Item terraform.tfvars.example terraform.tfvars
```

Fill in at least:

- `ssh_public_key` with your SSH public key (`ssh-ed25519 AAAA...`).
- `ssh_ingress_cidr` with your public IP plus `/32` if you want to restrict SSH.
- `ssh_users` with the Linux users cloud-init should create.

Optional:

- `availability_zone` (empty means AWS picks the first available zone).
- `instance_type` (default `m6g.medium`).

`terraform.tfvars` is gitignored. **Never commit it.**

### 2. Initialize

```powershell
terraform init
```

### 3. Format and validate

```powershell
terraform fmt -recursive
terraform validate
```

`validate` works before `tfvars` is filled. `plan` does not: `ssh_public_key` has a validation rule.

### 4. Review plan

```powershell
terraform plan
```

Check:

- Only SSH ingress on TCP 22 from `ssh_ingress_cidr`; all egress allowed.
- Instance `m6g.medium`, Ubuntu 24.04 ARM, 30 GB root + 30 GB encrypted data disk.
- One Elastic IP and one association.
- No budget or database resources.

### 5. Apply

```powershell
terraform apply
```

### 6. Read outputs

```powershell
terraform output
terraform output -raw ssh_command_example
```

### 7. Connect and verify

```powershell
ssh ubuntu@<elastic_public_ip>
```

On the instance:

```bash
cloud-init status --wait
lsblk
df -h /opt/xolo-bot/data
sudo fail2ban-client status sshd
sudo sshd -T | grep -i passwordauthentication
```

The first SSH user is `ubuntu`, authenticated by the key pair. Users in `ssh_users` are created inside the VM by cloud-init.

### 8. Destroy when finished

```powershell
terraform destroy
```

This releases the Elastic IP and stops all charges from this stack.

## Operational notes

- **State is local** (`terraform.tfstate*` is gitignored). Losing it means Terraform loses track of the resources.
- **Elastic IP is billed even when the instance is stopped** (~USD 3.65/month). **End Lab** stops the VM but does not release the EIP. **Reset** deletes everything, including the EIP; the next `apply` allocates a different IP.
- **Three credentials are required** in the lab. With only the access key and secret key, Terraform fails.
- **ARM may be restricted** in the lab. If `apply` rejects `m6g.medium`, set `instance_type = "t3.medium"` and change the AMI filter in `data.tf` from `arm64` to `amd64`.
- **`ssh_ingress_cidr` defaults to `0.0.0.0/0`**. Security relies on SSH keys, password auth disabled, and fail2ban. Restrict it to your own IP when possible.
- **Cloud-init is first-boot oriented**. Changing `user_data` may not reconfigure an existing instance and can trigger replacement. `lifecycle { ignore_changes = [ami] }` avoids replacement when a newer AMI appears.
- **Spending control is manual**: there is no Terraform budget. Use the AWS Academy spending panel and `terraform destroy`.
- **No application deploy yet**: Docker, compose, `deploy.sh`, backups, and bot environment variables are separate work.

## Security and git hygiene

Never commit:

- `terraform.tfvars`
- `.terraform/`
- `*.tfstate`, `*.tfstate.*`
- crash logs or plan files
- private keys (`id_ed25519`, `*.pem`, `*.key`)

The repository `.gitignore` already covers Terraform state, tfvars, and `.terraform`. Keep `.terraform.lock.hcl` committed.

## Useful commands

```powershell
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
terraform output
terraform destroy
```
