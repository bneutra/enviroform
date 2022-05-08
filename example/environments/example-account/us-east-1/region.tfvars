# region specific variables
aws_region = "us-east-1"
# backend.tfvars should reference the same bucket
# this makes the bucket location available e.g. for terraform remote tstate
tf_state_bucket = "myservice-us-east-1-prod-tf-state-bucket"
