
# OCI auth
variable "api_fingerprint" {
  description = "Fingerprint of the OCI API key"
  type        = string
}

variable "api_private_key_path" {
  description = "Path to the OCI API private key"
  type        = string
}

variable "tenancy_id" {
  description = "OCID of the OCI tenancy"
  type        = string
}

variable "user_id" {
  description = "OCID of the OCI user used by Terraform"
  type        = string
}

variable "region" {
  description = "OCI region for all resources"
  type        = string
  default     = "mx-queretaro-1"
}

# Compartment / project
variable "parent_compartment_ocid" {
  description = "OCID of the parent compartment (usually tenancy root)"
  type        = string
}

variable "compartment_name" {
  description = "Name of the dedicated compartment"
  type        = string
  default     = "xolo-bot"
}

variable "compartment_description" {
  description = "Description of the dedicated compartment"
  type        = string
  default     = "Dedicated compartment for xolo-bot infrastructure"
}

variable "project_name" {
  description = "Base project name used for tags and naming"
  type        = string
  default     = "xolo-bot"
}

# Network
variable "vcn_cidr" {
  description = "CIDR block for the VCN"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "ssh_ingress_cidr" {
  description = "Allowed CIDR for SSH ingress; host hardening enforces key-only access"
  type        = string
  default     = "0.0.0.0/0"
}

# Compute
variable "instance_name" {
  description = "Compute instance display name and hostname base"
  type        = string
  default     = "xolo-bot"
}

variable "shape" {
  description = "OCI compute shape"
  type        = string
  default     = "VM.Standard.A1.Flex"
}

variable "instance_ocpus" {
  description = "Number of OCPUs for the A1.Flex instance"
  type        = number
  default     = 1
}

variable "instance_memory_in_gbs" {
  description = "Memory in GB for the A1.Flex instance"
  type        = number
  default     = 6
}

variable "boot_volume_size_in_gbs" {
  description = "Boot volume size in GB"
  type        = number
  default     = 50
}

variable "ubuntu_os_version" {
  description = "Ubuntu OS version for the ARM image"
  type        = string
  default     = "24.04"
}

# SSH
variable "ssh_users" {
  description = "Map of Linux usernames to SSH public keys"
  type        = map(string)
  default     = {}
}

# Storage
variable "data_volume_size_in_gbs" {
  description = "Data block volume size in GB"
  type        = number
  default     = 130
}

# Budget
variable "budget_amount" {
  description = "Monthly budget amount in USD"
  type        = number
  default     = 1
}

variable "budget_alert_email" {
  description = "Email recipient for budget alerts; set in terraform.tfvars"
  type        = string
  default     = ""
  sensitive   = true

  validation {
    condition     = length(trimspace(var.budget_alert_email)) > 0
    error_message = "Set budget_alert_email in terraform.tfvars before apply."
  }
}