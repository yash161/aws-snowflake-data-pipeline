resource "aws_iam_policy" "eventbridge_to_stepfunctions_policy" {
  name        = "predict-etl-${terraform.workspace}-EventBridgeToStepFunctionsPolicy"
  description = "IAM policy to allow CloudWatch Events to trigger Step Functions"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "states:StartExecution",
        Effect = "Allow",
        Resource = aws_sfn_state_machine.sfn_state_machine.arn
      }
    ]
  })
}
