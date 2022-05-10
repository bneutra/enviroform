# default input variables
variable "aws_region" {}
variable "env_name" {}
variable "tf_state_bucket" {}

# config specific input variables
variable "app_name" {
  description = "A label for this app with which to name resources"
  type = string
}

variable "task_count" {
  description = "Number of tasks to deploy"
  type = number
}
