resource "aws_ssm_parameter" "experimentation_s3_bucket" {
  count = var.enable_notebook ? 1 : 0

  depends_on = [
    module.s3_ai_experimentation
  ]

  name        = "/product/${local.product_name}/resources/s3/experimentation_s3_bucket"
  description = "The ${local.product_name} experimentation s3 bucket."
  type        = "String"

  value = module.s3_ai_experimentation[0].s3_bucket_name

  tags = merge({
    "stellar:lifecycle" = local.product_name
  }, local.tags)

  lifecycle {
    ignore_changes = [
      tags
    ]
  }
}
