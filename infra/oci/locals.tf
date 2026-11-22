locals {
  name = var.project_name

  common_tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}
