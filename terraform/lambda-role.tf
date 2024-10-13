resource "aws_iam_role" "lambda_role" {
  name = "predict_etl_${terraform.workspace}_fetch_replication_list-${terraform.workspace}-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  managed_policy_arns = [
    aws_iam_policy.lambda_basic_execution.arn,
    aws_iam_policy.step_functions_full_access.arn,
    aws_iam_policy.lambda_vpc_access_execution.arn,
    aws_iam_policy.sns_policy_lambda.arn,
    aws_iam_policy.secrets_manager_read_write.arn
  ]
}