variable "aws_account_id" {
  description = "AWS account ID where resources will be deployed."
  type        = string
}

variable "aws_account_alias" {
  description = "Alias for the management/organization AWS acount."
  type        = string
  default     = null
}

variable "aws_account_email" {
  description = "Email for the management/organization AWS acount."
  type        = string
  default     = null
}

variable "account_name" {
  description = "The name of the account."
  type        = string
  default     = null
}

variable "deployment_role" {
  description = "An IAM role that will be assumed in order to perform the deployment."
  type        = string
}

variable "workspace" {
  description = "Terraform workspace. Must specify a tfvars file by adding --var-file=\"<workspace name>.tfvars\" to every terraform command."
  type        = string
}

variable "environment" {
  description = "Environment naming prefix."
  type        = string
}

variable "region" {
  description = "AWS region identifier."
  type        = string
}

variable "tags" {
  description = "The tags"
  type        = any
  default     = {}
}

### Variables for AI Notebooks
variable "sagemaker_github_secret" {
  default = {
    username = "changeme"
    password = "changeme"
  }

  type = map(string)
}

### Variables for AI Pipeline
variable "enable_notebook" {
  description = "The tags"
  type        = bool
  default     = false
}

variable "sagemaker_git_repos" {
  description = "Map of all the repos imported to Sagemaker repositories."
  type        = map(any)
  default     = {}
}

variable "sagemaker_notebooks" {
  description = "Map of all the notebooks to be created."
  type        = map(any)
  default     = {}
}
