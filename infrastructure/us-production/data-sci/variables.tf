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
  description = "Email contact for the management/organization AWS acount."
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

variable "tf_state" {
  description = "The idenitifer of the current state used."
  type        = string
  default     = ""
}

variable "environment" {
  description = "Environment naming prefix."
  type        = string
}

variable "region" {
  description = "AWS region identifier."
  type        = string
}

variable "owner" {
  description = "Name of the person or team responsible for these resources."
  type        = string
}

variable "tags" {
  description = "Global list of tags associated to all resources."
  type        = map(any)

  default = {
    maintained_by = "terraform"
  }
}

################################################################
# Sagemaker
################################################################
variable "enable_sagemaker_studio" {
  description = "Feature flag to enable sagemaker studio for account."
  type        = bool
}

variable "enable_sagemaker_notebooks" {
  description = "Feature flag to enable sagemaker notebooks for account."
  type        = bool
}

variable "sagemaker_user_profiles" {
  description = "Map of all the user profiles."

  type = map(object({
    email = string
  }))

  default = {}
}

################################################################
# Slack
################################################################
variable "enable_slack_integration" {
  description = "Feature flag to enable slack integration for data sci."
  type        = bool
}
