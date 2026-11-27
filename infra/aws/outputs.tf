output "vpc_id" {
  value = aws_vpc.xolo_bot.id
}

output "subnet_id" {
  value = aws_subnet.xolo_bot_public.id
}

output "instance_id" {
  value = aws_instance.xolo_bot.id
}

output "instance_private_ip" {
  value = aws_instance.xolo_bot.private_ip
}

output "elastic_public_ip" {
  value = aws_eip.xolo_bot.public_ip
}

output "root_volume_id" {
  value = aws_instance.xolo_bot.root_block_device[0].volume_id
}

output "data_volume_id" {
  value = tolist(aws_instance.xolo_bot.ebs_block_device)[0].volume_id
}

output "ssh_command_example" {
  value = "ssh -i ~/.ssh/id_ed25519 ubuntu@${aws_eip.xolo_bot.public_ip}"
}
