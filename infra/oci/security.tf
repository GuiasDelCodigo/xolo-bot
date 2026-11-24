# Security list for public subnet access.
resource "oci_core_security_list" "xolo_bot" {
  compartment_id = oci_identity_compartment.xolo_bot.id
  vcn_id         = oci_core_vcn.xolo_bot.id
  display_name   = "${local.name}-security-list"

  ingress_security_rules {
    protocol    = "6" # TCP
    source      = var.ssh_ingress_cidr
    source_type = "CIDR_BLOCK"
    description = "SSH ingress"

    tcp_options {
      min = 22
      max = 22
    }
  }

  egress_security_rules {
    protocol         = "all"
    destination      = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    description      = "Allow outbound traffic"
  }

  freeform_tags = local.common_tags
}
