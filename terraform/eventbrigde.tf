resource "aws_cloudwatch_event_rule" "step_function_event_rule" {
  name        = "predict-etl-${terraform.workspace}step-function-trigger-rule"
  description = var.eventbrigde_description
  schedule_expression = var.eventbrigde_schedule_expression
}

resource "aws_cloudwatch_event_target" "step_function_target" {
  arn = aws_sfn_state_machine.sfn_state_machine.arn
  rule = aws_cloudwatch_event_rule.step_function_event_rule.name
  target_id = "step-function-${terraform.workspace}-target"
  role_arn =aws_iam_role.eventbridge_to_stepfunctions_role.arn
}
