output "sagemaker_training_sg_id" {
  description = "Special sagemaker security group for training instances."
  value       = module.sagemaker_training_sg.security_group_id
}
