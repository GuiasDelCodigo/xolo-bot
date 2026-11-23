
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