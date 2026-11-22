
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