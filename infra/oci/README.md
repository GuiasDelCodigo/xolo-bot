# OCI Infrastructure (`infra/oci`)

Terraform configuration for provisioning the base Oracle Cloud Infrastructure (OCI) resources for `xolo-bot`.

## What this creates

This stack creates a small, single-VM OCI setup:

- **Compartment**: dedicated `xolo-bot` compartment.
- **Network**: VCN, Internet Gateway, public route table, and public subnet.
- **Security**: security list allowing inbound SSH (`TCP/22`) from `ssh_ingress_cidr` (default `0.0.0.0/0`) and all outbound traffic.
- **Compute**: `VM.Standard.A1.Flex` instance (default 1 OCPU / 6 GB), Ubuntu 24.04 ARM, 50 GB boot volume, in the public subnet.
- **Public IP**: reserved public IP attached to the instance VNIC for stable SSH access.
- **Storage**: 130 GB block volume attached to the instance (paravirtualized).
- **Host bootstrap**: cloud-init template that creates Linux users from `ssh_users`, configures SSH key-only access, installs/enables fail2ban, and formats/mounts the data volume at `/opt/xolo-bot/data`.
- **Outputs**: compartment/network/instance/volume IDs, private/reserved public IP, and an SSH command example.

## File layout

| File | Purpose |
|---|---|
| `versions.tf` | Terraform/provider version constraints. |
| `providers.tf` | OCI provider configuration using variables. |
| `variables.tf` | Input variable contract. |
| `terraform.tfvars.example` | Committable placeholder values. |
| `locals.tf` | Common name/tags. |
| `compartment.tf` | Dedicated compartment. |
| `network.tf` | VCN, IGW, route table, public subnet. |
| `security.tf` | Security list rules. |
| `data.tf` | Availability domains, Ubuntu ARM image, VNIC/private IP lookups. |
| `compute.tf` | Compute instance and reserved public IP. |
| `storage.tf` | Data block volume and attachment. |
| `templates/cloud-init.yaml.tftpl` | Cloud-init bootstrap template. |
| `outputs.tf` | Useful Terraform outputs. |

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) installed (compatible with `versions.tf`).
- An OCI tenancy with permissions to manage compartment/network/compute/storage resources.
- An OCI API key configured for the Terraform user.
- The private key file path accessible from your machine (example: `C:/Users/<you>/.oci/oci_api_key.pem`).
- An SSH public key for each Linux user you want cloud-init to create.

## How to use

### 1. Create local tfvars

Copy the example and fill real values locally:

```powershell
cd infra/oci
Copy-Item terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set real values for OCI auth and project settings. **Do not commit `terraform.tfvars`.**

Important values to review:

- `tenancy_id`, `user_id`, `api_fingerprint`, `api_private_key_path`, `parent_compartment_ocid`
- `region` (default `mx-queretaro-1`)
- `ssh_users` with at least your user and SSH public key before apply
- `ssh_ingress_cidr` (default `0.0.0.0/0`; host hardening is expected)

### 2. Initialize

```powershell
terraform init
```

This creates `.terraform/` locally and uses `.terraform.lock.hcl` (lock file should be committed when provider versions change).

### 3. Format and validate

```powershell
terraform fmt -recursive
terraform validate
```

### 4. Review plan

```powershell
terraform plan
```

Check carefully:

- Shape/config: `VM.Standard.A1.Flex`, OCPUs, memory, boot volume size.
- Network: VCN/subnet CIDRs, only SSH ingress expected, public subnet association.
- IP: reserved public IP (`RESERVED`), no ephemeral public IP on the instance.
- Storage: 130 GB data volume, same AD as instance, paravirtualized attachment.
- Cloud-init: `user_data` changes can cause instance replacement; review plan before apply.

### 5. Apply

```powershell
terraform apply
```

After apply, Terraform outputs useful values:

```powershell
terraform output
terraform output reserved_public_ip
terraform output -raw ssh_command_example
```

### 6. Connect and verify (after apply)

```powershell
ssh <user>@<reserved_public_ip>
```

On the VM, verify bootstrap:

```bash
lsblk
df -h /opt/xolo-bot/data
sudo fail2ban-client status sshd
sudo sshd -T | grep -i passwordauthentication
```

## Operational notes

- **State is local** in this directory for now (`terraform.tfstate*` are gitignored). Losing state means Terraform loses track of existing resources.
- **A1 capacity is not guaranteed**. `plan` may succeed while `apply` fails due to `VM.Standard.A1.Flex` capacity in the selected AD/region. Retry later or evaluate AD/shape adjustments.
- **Always Free block storage limit**: tenancy total is 200 GB. This setup uses 50 GB boot + 130 GB data = 180 GB, leaving 20 GB margin.
- **SSH ingress is broad by design** (`0.0.0.0/0` default) because users may have dynamic IPs. Security relies on SSH keys, password auth disabled, and fail2ban configured by cloud-init.
- **Cloud-init is first-boot oriented**. Changing `user_data` may not reapply all changes to an existing instance and can trigger replacement depending on Terraform/provider behavior. Always inspect `terraform plan`.
- **No backups/bucket/cron configured yet**. Data volume deletion or destructive operations can cause data loss.
- **Budget alert is intentionally pending**. Add budget resources in a later step.

## Security and git hygiene

Never commit:

- `terraform.tfvars`
- `.terraform/`
- `*.tfstate`, `*.tfstate.*`
- crash logs / plan files with sensitive data
- private keys (`*.pem`, `*.key`)

The repository `.gitignore` already covers Terraform state/tfvars/`.terraform` patterns. Keep `.terraform.lock.hcl` committed.

## Useful commands

```powershell
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
terraform output
terraform destroy  # destructive; review carefully
```
