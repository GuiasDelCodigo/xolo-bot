output "compartment_id" {
  description = "OCID of the xolo-bot compartment"
  value       = oci_identity_compartment.xolo_bot.id
}

output "vcn_id" {
  description = "OCID of the VCN"
  value       = oci_core_vcn.xolo_bot.id
}

output "subnet_id" {
  description = "OCID of the public subnet"
  value       = oci_core_subnet.xolo_bot_public.id
}

output "instance_id" {
  description = "OCID of the compute instance"
  value       = oci_core_instance.xolo_bot.id
}

output "instance_private_ip" {
  description = "Private IP of the compute instance"
  value       = oci_core_instance.xolo_bot.private_ip
}

output "reserved_public_ip" {
  description = "Reserved public IP of the compute instance"
  value       = oci_core_public_ip.xolo_bot_reserved.ip_address
}

output "data_volume_id" {
  description = "OCID of the data block volume"
  value       = oci_core_volume.xolo_bot_data.id
}

output "ssh_command_example" {
  description = "Example SSH command; replace <user> with a Linux user from ssh_users"
  value       = "ssh <user>@${oci_core_public_ip.xolo_bot_reserved.ip_address}"
}
