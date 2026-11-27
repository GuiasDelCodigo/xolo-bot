variable "region" {
  description = "AWS region; us-east-1 is allowed by AWS Academy Learner Lab"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "xolo-bot"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  type    = string
  default = "10.0.1.0/24"
}

variable "ssh_ingress_cidr" {
  description = "Allowed CIDR for SSH ingress; set your own IP before apply"
  type        = string
  default     = "0.0.0.0/0"
}

variable "instance_name" {
  type    = string
  default = "xolo-bot"
}

variable "instance_type" {
  type    = string
  default = "m6g.medium"
}

variable "root_volume_size" {
  type    = number
  default = 30
}

variable "data_volume_size" {
  type    = number
  default = 30
}

variable "ssh_users" {
  description = "Map of Linux usernames to SSH public keys"
  type        = map(string)
  default     = {}
}
