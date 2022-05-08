/**
 * A No-Op Example VPC component for testing purposes only
 */
provider "aws" {
  region = var.aws_region
}

terraform {
  required_version = "1.1.9"

  required_providers {
    # aws = {
    #   source  = "hashicorp/aws"
    #   version = "4.12.1"
    # }
    null = {
      source  = "hashicorp/null"
      version = "3.1.1"
    }
  }
  # provided by backend.tfvars
  backend "s3" {}
}

