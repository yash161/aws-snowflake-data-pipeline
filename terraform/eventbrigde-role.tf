resource "aws_iam_role" "eventbridge_to_stepfunctions_role" {
  name = "predict-etl-${terraform.workspace}-EventBridgeToStepFunctionsRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })
    managed_policy_arns = [
    aws_iam_policy.eventbridge_to_stepfunctions_policy.arn,

  ]
}

