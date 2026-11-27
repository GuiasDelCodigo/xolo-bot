resource "aws_vpc" "xolo_bot" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${local.name}-vcn"
  }
}

resource "aws_internet_gateway" "xolo_bot" {
  vpc_id = aws_vpc.xolo_bot.id

  tags = {
    Name = "${local.name}-igw"
  }
}

resource "aws_route_table" "xolo_bot_public" {
  vpc_id = aws_vpc.xolo_bot.id

  tags = {
    Name = "${local.name}-public-rt"
  }
}

resource "aws_route" "xolo_bot_default" {
  route_table_id         = aws_route_table.xolo_bot_public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.xolo_bot.id
}

resource "aws_subnet" "xolo_bot_public" {
  vpc_id            = aws_vpc.xolo_bot.id
  cidr_block        = var.public_subnet_cidr
  availability_zone = var.availability_zone != "" ? var.availability_zone : data.aws_availability_zones.available.names[0]
  # The stable public IP comes from the EIP added in a later commit.
  map_public_ip_on_launch = false

  tags = {
    Name = "${local.name}-public-subnet"
  }
}

resource "aws_route_table_association" "xolo_bot_public" {
  subnet_id      = aws_subnet.xolo_bot_public.id
  route_table_id = aws_route_table.xolo_bot_public.id
}
