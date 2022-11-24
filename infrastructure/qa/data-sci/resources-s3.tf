module "data_sci_experiments_s3" {
  count = var.enable_sagemaker_notebooks ? 1 : 0

  source                = "../../../../infrastructure-common/modules/s3_bucket_v2"
  s3_bucket_name        = local.experiments_bucket_name
  versioning            = false
  sse_algorithm         = "aws:kms"
  sse_kms_key_id        = data.terraform_remote_state.account.outputs.account_kms_key.id
  logging_target_bucket = data.terraform_remote_state.account.outputs.s3_bucket_access_logs != null ? data.terraform_remote_state.account.outputs.s3_bucket_access_logs.s3_bucket_name : null
  logging_target_prefix = local.experiments_bucket_name
  object_lock_enabled   = false

  tags = merge({
    "stellar:data-sensitivity" = "stellaralgo-confidential",
    "stellar:lifecycle"        = "data-sci"
  }, local.tags)
}
