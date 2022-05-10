/**
 * A No-Op Example VPC component for testing purposes only
 */
provider "aws" {
  region = var.aws_region
}

terraform {
  required_version = ">= 1.0, < 2.0"

  required_providers {
    # aws = {
    #   source  = "hashicorp/aws"
    #   version = ">= 4.0.0, < 5.0.0"
    # }
    null = {
      source  = "hashicorp/null"
      version = ">= 3.1.0, < 4.0.0"
    }
  }
  # provided by backend.tfvars
  backend "s3" {}
}

output "foo" {
  value = "bar"
}
