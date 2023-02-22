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

variable "deploy_retention" {
  description = "Deploys the retention fallback."
  type        = bool
  default     = false
}

variable "deploy_product_propensity" {
  description = "Deploys the product_prodeploy_product_propensity fallback."
  type        = bool
  default     = false
}

variable "deploy_sagemaker_image" {
  description = "Deploys the sagemaker custom image."
  type        = bool
  default     = false
}

variable "retention_trigger" {
  description = "Enables the trigger for retention lambda."
  type        = bool
  default     = false
}

variable "product_propensity_trigger" {
  description = "Enables the trigger for product propensity lambda."
  type        = bool
  default     = false
}


### Variables for run pipeline
variable "deploy_training" {
  description = "Deploys the training pipeline."
  type        = bool
  default     = false
}

variable "enable_training_trigger" {
  description = "Enables trigger on training pipeline."
  type        = bool
  default     = false
}

variable "default_training_timer_expression" {
  description = "Default training cron expression if none is supplied."
  type        = string
  default     = "cron(0 5 ? * 1 *)"
}

variable "deploy_inference" {
  description = "Deploys the inference pipeline."
  type        = bool
  default     = false
}

variable "enable_inference_trigger" {
  description = "Enables trigger on inference pipeline."
  type        = bool
  default     = false
}

variable "default_inference_timer_expression" {
  description = "Default inference cron expression if none is supplied."
  type        = string
  default     = "cron(0 16 ? * * *)"
}

variable "run_pipeline_handler" {
  description = "The initial handler to run pipeline."
  type        = string
  default     = "lambda.run"
}

variable "run_pipeline_runtime" {
  description = "The run pipeline runtime to use."
  type        = string
  default     = "python3.9"
}

variable "table_load_event_source" {
  description = "Listen for specific env events from legacy."
  type        = string
}

variable "model_subtypes" {
  description = "Map of all the model sub types and associated settings."

  type    = map(any)
  default = {}
}

variable "model_subtype_config" {
  description = "Map of the model sub type pipeline settings."

  type = object({
    training = object({
      timer_expression               = string
      preprocess_instance_count      = number
      preprocess_instance_type       = string
      preprocess_max_runtime_seconds = number
      training_instance_count        = number
      training_instance_type         = string
      training_max_runtime_seconds   = number
      evaluate_instance_count        = number
      evaluate_instance_type         = string
      evaluate_max_runtime_seconds   = number
      create_model_instance_type     = string
      inference_instances            = list(string)
      transform_instances            = list(string)
    })
    inference = object({
      timer_expression               = string
      preprocess_instance_type       = string
      preprocess_instance_count      = number
      preprocess_max_runtime_seconds = number
      transform_instance_type        = string
      transform_instance_count       = number
    })
  })

  default = {
    training = {
      timer_expression               = "cron(0 5 ? * 1 *)"
      preprocess_instance_count      = 2
      preprocess_instance_type       = "ml.m5.2xlarge"
      preprocess_max_runtime_seconds = 150 * 60
      training_instance_count        = 1
      training_instance_type         = "ml.p2.xlarge"
      training_max_runtime_seconds   = 360 * 60
      evaluate_instance_count        = 2
      evaluate_instance_type         = "ml.m5.2xlarge"
      evaluate_max_runtime_seconds   = 150 * 60
      create_model_instance_type     = "ml.m4.xlarge"
      inference_instances            = ["ml.m5.2xlarge"]
      transform_instances            = ["ml.c5.4xlarge"]
    }
    inference = {
      timer_expression               = "cron(0 16 ? * * *)"
      preprocess_instance_type       = "ml.m5.2xlarge"
      preprocess_instance_count      = 2
      preprocess_max_runtime_seconds = 360 * 60
      transform_instance_type        = "ml.c5.4xlarge"
      transform_instance_count       = 2
    }
  }
}
