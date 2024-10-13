#resource "aws_iam_policy" "ecs_execution_role_policy" {
#  name        = "ecs_execution_role_policy_${terraform.workspace}"
#  description = "Policy for ECS task execution role"
#
#  policy = jsonencode({
#    "Version": "2012-10-17",
#    "Statement": [
#        {
#            "Effect": "Allow",
#            "Action": [
#                "ecr:GetAuthorizationToken",
#                "ecr:BatchCheckLayerAvailability",
#                "ecr:GetDownloadUrlForLayer",
#                "ecr:BatchGetImage",
#                "logs:CreateLogStream",
#                "logs:PutLogEvents"
#            ],
#            "Resource": "*"
#        }
#    ],
#  })
#}
