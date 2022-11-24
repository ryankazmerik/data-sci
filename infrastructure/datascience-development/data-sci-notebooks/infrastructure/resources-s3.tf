### random_string.bucket_randomize
# Generate a random string for S3 bucket names to avoid collisions globally
###
resource "random_string" "bucket_randomize" {
  count = var.enable_notebook ? 1 : 0

  length  = 6
  special = false
  upper   = false
  lower   = true
}

module "s3_ai_experimentation" {
  count = var.enable_notebook ? 1 : 0

  source                = "../../../../../infrastructure-common/modules/s3_bucket"
  s3_bucket_name        = format("%s-experimentation-%s", local.product_name, random_string.bucket_randomize[0].result)
  versioning            = false
  sse_algorithm         = "aws:kms"
  sse_kms_key_id        = data.terraform_remote_state.account.outputs.account_kms_key.id
  logging_target_bucket = data.terraform_remote_state.account.outputs.s3_bucket_access_logs != null ? data.terraform_remote_state.account.outputs.s3_bucket_access_logs.s3_bucket_name : null
  logging_target_prefix = format("%s-experimentation-%s", local.product_name, random_string.bucket_randomize[0].result)
  object_lock_enabled   = false

  tags = merge({
    "stellar:data-sensitivity" = "stellaralgo-confidential",
    "stellar:lifecycle"        = local.product_name
  }, local.tags)
}
