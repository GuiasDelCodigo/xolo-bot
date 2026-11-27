resource "aws_security_group" "xolo_bot" {
  name        = "${local.name}-ssh"
  description = "SSH access and unrestricted egress for xolo-bot"
  vpc_id      = aws_vpc.xolo_bot.id

  tags = {
    Name = "${local.name}-security-group"
  }
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  security_group_id = aws_security_group.xolo_bot.id
  description       = "SSH from trusted CIDR"
  cidr_ipv4         = var.ssh_ingress_cidr
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.xolo_bot.id
  description       = "All outbound traffic"
  cidr_ipv4         = "0.0.0.0/0"
  # -1 means all protocols.
  ip_protocol = "-1"
}
