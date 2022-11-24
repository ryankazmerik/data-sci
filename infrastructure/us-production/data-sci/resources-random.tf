resource "random_string" "random_role_id" {
  length  = 6
  special = false
  upper   = false
  lower   = true
}

resource "random_string" "random_bucket_id" {
  length  = 6
  special = false
  upper   = false
  lower   = true
}

resource "random_string" "random_sg_id" {
  length  = 6
  special = false
  upper   = false
  lower   = true
}