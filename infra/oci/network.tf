resource "oci_core_vcn" "xolo_bot" {
  compartment_id = oci_identity_compartment.xolo_bot.id
  cidr_blocks    = [var.vcn_cidr]
  display_name   = "${local.name}-vcn"
  dns_label      = "xolobot"

  freeform_tags = local.common_tags
}

resource "oci_core_internet_gateway" "xolo_bot" {
  compartment_id = oci_identity_compartment.xolo_bot.id
  vcn_id         = oci_core_vcn.xolo_bot.id
  display_name   = "${local.name}-igw"
  enabled        = true

  freeform_tags = local.common_tags
}

resource "oci_core_route_table" "xolo_bot_public" {
  compartment_id = oci_identity_compartment.xolo_bot.id
  vcn_id         = oci_core_vcn.xolo_bot.id
  display_name   = "${local.name}-public-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.xolo_bot.id
    description       = "Default route to internet"
  }

  freeform_tags = local.common_tags
}

resource "oci_core_subnet" "xolo_bot_public" {
  compartment_id             = oci_identity_compartment.xolo_bot.id
  vcn_id                     = oci_core_vcn.xolo_bot.id
  cidr_block                 = var.public_subnet_cidr
  display_name               = "${local.name}-public-subnet"
  dns_label                  = "public"
  route_table_id             = oci_core_route_table.xolo_bot_public.id
  security_list_ids          = [oci_core_security_list.xolo_bot.id]
  prohibit_public_ip_on_vnic = false

  freeform_tags = local.common_tags
}
