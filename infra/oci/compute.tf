resource "oci_core_instance" "xolo_bot" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = oci_identity_compartment.xolo_bot.id
  display_name        = var.instance_name
  shape               = var.shape

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_in_gbs
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.xolo_bot_public.id
    display_name     = "${local.name}-vnic"
    assign_public_ip = false
    hostname_label   = replace(var.instance_name, "-", "")
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.ubuntu_arm.images[0].id
    boot_volume_size_in_gbs = var.boot_volume_size_in_gbs
  }

  metadata = {
    user_data = base64encode(templatefile("${path.module}/templates/cloud-init.yaml.tftpl", {
      ssh_users = var.ssh_users
    }))
  }

  preserve_boot_volume = false

  freeform_tags = local.common_tags

  lifecycle {
    ignore_changes = [
      source_details[0].source_id,
    ]
  }
}

# Reserved public IP for stable SSH access.
resource "oci_core_public_ip" "xolo_bot_reserved" {
  compartment_id = oci_identity_compartment.xolo_bot.id
  lifetime       = "RESERVED"
  display_name   = "${local.name}-reserved-ip"
  private_ip_id  = data.oci_core_private_ips.xolo_bot.private_ips[0].id

  freeform_tags = local.common_tags

  depends_on = [oci_core_instance.xolo_bot]
}
