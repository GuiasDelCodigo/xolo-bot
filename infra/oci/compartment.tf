# Dedicated compartment for all xolo-bot resources.
resource "oci_identity_compartment" "xolo_bot" {
  compartment_id = var.parent_compartment_ocid
  name           = var.compartment_name
  description    = var.compartment_description
  enable_delete  = true

  freeform_tags = local.common_tags
}
