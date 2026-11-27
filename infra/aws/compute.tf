resource "aws_key_pair" "xolo_bot" {
  key_name   = "${local.name}-key"
  public_key = var.ssh_public_key
}

resource "aws_instance" "xolo_bot" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  availability_zone           = aws_subnet.xolo_bot_public.availability_zone
  subnet_id                   = aws_subnet.xolo_bot_public.id
  vpc_security_group_ids      = [aws_security_group.xolo_bot.id]
  key_name                    = aws_key_pair.xolo_bot.key_name
  associate_public_ip_address = false
  monitoring                  = false

  root_block_device {
    volume_size           = var.root_volume_size
    volume_type           = "gp3"
    delete_on_termination = true
  }

  ebs_block_device {
    device_name           = "/dev/sdh"
    volume_size           = var.data_volume_size
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  user_data = templatefile("${path.module}/templates/cloud-init.yaml.tftpl", {
    ssh_users = var.ssh_users
  })

  tags = {
    Name = var.instance_name
  }

  lifecycle {
    ignore_changes = [ami]
  }
}

resource "aws_eip" "xolo_bot" {
  domain = "vpc"

  tags = {
    Name = "${local.name}-eip"
  }
}

resource "aws_eip_association" "xolo_bot" {
  instance_id   = aws_instance.xolo_bot.id
  allocation_id = aws_eip.xolo_bot.id
}
