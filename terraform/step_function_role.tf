resource "aws_iam_role" "step_function_role" {
  name = "snowflake_replication_${terraform.workspace}_sf_policy_role"

  assume_role_policy = <<-EOF
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Action": "sts:AssumeRole",
          "Principal": {
            "Service": "states.amazonaws.com"
          },
          "Effect": "Allow",
          "Sid": "StepFunctionAssumeRole"
        }
      ]
    }
  EOF

  managed_policy_arns = [
    aws_iam_policy.sns_full_access_policy.arn,
    aws_iam_policy.glue_service_role_policy.arn,
    aws_iam_policy.step_functions_full_access_policy.arn,
    aws_iam_policy.step_function_policy.arn,
    aws_iam_policy.cloudwatch_full.arn,
    aws_iam_policy.GlueJobRunManagementFullAccessPolicy.arn,
    aws_iam_policy.lambda_basic_execution.arn,
    aws_iam_policy.EcsTaskManagementScopedAccessPolicy.arn,
    aws_iam_policy.LambdaInvokeScopedAccessPolicy.arn,
    aws_iam_policy.step_function_log_policy.arn
  ]
}
