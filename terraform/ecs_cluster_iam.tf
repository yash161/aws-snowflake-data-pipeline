#resource "aws_iam_role" "ecs_task_execution_role" {
#  name = "ecs_task_execution_role-${terraform.workspace}"
#
#  assume_role_policy = jsonencode({
#    Version = "2012-10-17",
#    Statement = [
#      {
#        Action = "sts:AssumeRole",
#        Effect = "Allow",
#        Principal = {
#          Service = "ecs-tasks.amazonaws.com"
#        }
#      }
#    ]
#  })
#    managed_policy_arns = [
#    aws_iam_policy.ecs_execution_role_policy.arn
#  ]
#}