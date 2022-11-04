resource "random_string" "random_role_id" {
  length  = 6
  special = false
  upper   = false
  lower   = true
}

# resource "random_string" "random_bucket_id" {
#   length  = 6
#   special = false
#   upper   = false
#   lower   = true
# }

resource "random_string" "random_sg_id" {
  length  = 6
  special = false
  upper   = false
  lower   = true
}

# resource "random_string" "training_pipeline_id" {
#   count   = var.deploy_training ? 1 : 0
#   length  = 12
#   special = false
#   upper   = false
#   lower   = true

#   keepers = {
#     deploy_hash = data.archive_file.run_training_pipeline.output_base64sha256
#   }
# }

# resource "random_string" "inference_pipeline_id" {
#   count   = var.deploy_inference ? 1 : 0
#   length  = 12
#   special = false
#   upper   = false
#   lower   = true

#   keepers = {
#     deploy_hash = data.archive_file.run_inference_pipeline.output_base64sha256
#   }
# }
