resource "aws_cloudwatch_log_group" "step_function_log_group" {
  name = "step-function-${terraform.workspace}-log-group"
}