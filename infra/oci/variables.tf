
variable "api_fingerprint" {
  description = "Fingerprint of OCI API private"
  type        = string
}

variable "api_private_key_path" {
  description = "Path to OCI API private key"
  type        = string
}

variable "tenancy_id" {
  description = "Tenancy ID where to create resources for Tenancy"
  type        = string
}

variable "user_id" {
  description = "User ID that Terraform will use to create resources"
  type        = string
}

variable "region" {
  description = "OCI region where resources will be created"
  type        = string
}