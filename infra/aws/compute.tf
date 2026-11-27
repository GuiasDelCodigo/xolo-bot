resource "aws_key_pair" "xolo_bot" {
  key_name   = "${local.name}-key"
  public_key = var.ssh_public_key
}
