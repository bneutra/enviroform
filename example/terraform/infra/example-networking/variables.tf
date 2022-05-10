# default input variables
variable "aws_region" {}
variable "env_name" {}
variable "tf_state_bucket" {}

# config specific variables
variable "cidr_range" {
  description = "IPV4 cidir range"
  type = string
}
