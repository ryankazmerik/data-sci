model_subtypes = {
  # "AHL-Admirals" = {
  #   lkupclientid = "16"
  #   training = {
  #     timer_expression               = "cron(0 5 ? * 1 *)",
  #     preprocess_instance_count      = 1,
  #     preprocess_instance_type       = "ml.m5.2xlarge",
  #     preprocess_max_runtime_seconds = 150 * 60,
  #     training_instance_count        = 1,
  #     training_instance_type         = "ml.m5.4xlarge",
  #     training_max_runtime_seconds   = 360 * 60,
  #     evaluate_instance_count        = 1,
  #     evaluate_instance_type         = "ml.m5.2xlarge",
  #     evaluate_max_runtime_seconds   = 150 * 60
  #     create_model_instance_type     = "ml.m4.xlarge",
  #     inference_instances            = ["ml.m5.4xlarge"],
  #     transform_instances            = ["ml.m5.4xlarge"]
  #   }
  #   inference = {
  #     timer_expression               = "cron(0 16 ? * * *)",
  #     preprocess_instance_type       = "ml.m5.2xlarge",
  #     preprocess_instance_count      = 1,
  #     preprocess_max_runtime_seconds = 360 * 60,
  #     transform_instance_type        = "ml.m5.4xlarge",
  #     transform_instance_count       = 1
  #   }
  # },
}
