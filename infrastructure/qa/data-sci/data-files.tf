data "archive_file" "data_sci_slack_lambda" {
  count = var.enable_slack_integration ? 1 : 0
  
  type             = "zip"
  source_dir       = "${path.module}/../../src/lambda/data_sci_slack_sns"
  output_path      = "${path.module}/zips/data_sci_slack_sns.zip"
  output_file_mode = "0666"
}
