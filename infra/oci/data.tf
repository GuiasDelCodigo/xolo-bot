data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_id
}

data "oci_core_images" "ubuntu_arm" {
  compartment_id           = var.tenancy_id
  operating_system         = "Canonical Ubuntu"
  operating_system_version = var.ubuntu_os_version
  shape                    = var.shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
  state                    = "AVAILABLE"
}

# Lookups used to attach a reserved public IP to the instance VNIC.
data "oci_core_vnic_attachments" "xolo_bot" {
  compartment_id = oci_identity_compartment.xolo_bot.id
  instance_id    = oci_core_instance.xolo_bot.id

  depends_on = [oci_core_instance.xolo_bot]
}

data "oci_core_vnic" "xolo_bot" {
  vnic_id = data.oci_core_vnic_attachments.xolo_bot.vnic_attachments[0].vnic_id
}

data "oci_core_private_ips" "xolo_bot" {
  vnic_id = data.oci_core_vnic.xolo_bot.id
}
