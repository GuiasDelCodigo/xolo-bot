# Data block volume attached to the instance.
resource "oci_core_volume" "xolo_bot_data" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = oci_identity_compartment.xolo_bot.id
  display_name        = "${local.name}-data-volume"
  size_in_gbs         = var.data_volume_size_in_gbs

  freeform_tags = local.common_tags
}

resource "oci_core_volume_attachment" "xolo_bot_data" {
  attachment_type = "paravirtualized"
  instance_id     = oci_core_instance.xolo_bot.id
  volume_id       = oci_core_volume.xolo_bot_data.id
  display_name    = "${local.name}-data-attachment"
}
