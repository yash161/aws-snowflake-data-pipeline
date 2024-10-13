resource "aws_iam_policy" "step_function_policy" {
  name = "snowflake_replication_sf_policy_${terraform.workspace}"
#  role = aws_iam_role.step_function_role.id

  policy = <<-EOF
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Action": [
            "lambda:InvokeFunction"
          ],
          "Effect": "Allow",
          "Resource": "*"
        }
      ]
    }
  EOF
}
resource "aws_iam_policy" "step_function_log_policy" {
   name = "snowflake_replication_step_funtion_log_policy_${terraform.workspace}"
  policy = <<-EOF
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Action": [
            "logs:CreateLogDelivery",
            "logs:CreateLogStream",
            "logs:GetLogDelivery",
            "logs:UpdateLogDelivery",
            "logs:DeleteLogDelivery",
            "logs:ListLogDeliveries",
            "logs:PutLogEvents",
            "logs:PutResourcePolicy",
            "logs:DescribeResourcePolicies",
            "logs:DescribeLogGroups"
          ],
          "Effect": "Allow",
          "Resource": "*"
        }
      ]
    }
  EOF
}
resource "aws_iam_policy" "LambdaInvokeScopedAccessPolicy" {
  name        = "LambdaInvokeScopedAccessPolicy_${terraform.workspace}"
  description = "Allow AWS Step Functions to invoke Lambda functions on your behalf"
  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                aws_lambda_function.fetch_replication_list.arn,
              aws_lambda_function.lambda_postgres_to_snowflake_sync.arn
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
               aws_lambda_function.fetch_replication_list.arn,
              aws_lambda_function.lambda_postgres_to_snowflake_sync.arn
            ]
        }
    ]

  })

}

resource "aws_iam_policy" "step_functions_full_access_policy" {
  name        = "step-functions-policy_${terraform.workspace}"
  description = "Policy providing full access to AWS Step Functions"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = "states:*",
        Resource = "*",
      },
    ],
  })

}
resource "aws_iam_policy" "sns_full_access_policy" {
  name        = "sns-access-policy_${terraform.workspace}"
  description = "Policy providing full access to Amazon SNS"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = "sns:*",
        Resource = "*",
      },
    ],
  })
}

resource "aws_iam_policy" "EcsTaskManagementScopedAccessPolicy" {
  name        = "EcsTaskManagementScopedAccessPolicy_${terraform.workspace}"
  description = "Allows AWS Step Functions to run ECS tasks on your behalf."
  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "ecs:StopTask",
                "ecs:DescribeTasks"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "events:PutTargets",
                "iam:PassRole",
                "events:DescribeRule",
                "ecs:RunTask",
                "events:PutRule"
            ],
           "Resource": "*"
        }
    ]
  })
}

resource "aws_iam_policy" "glue_service_role_policy" {
  name        = "glue-service-role-policy-${terraform.workspace}"
  description = "Policy for AWS Glue service role"
  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "glue:*",
                "s3:GetBucketLocation",
                "s3:ListBucket",
                "s3:ListAllMyBuckets",
                "s3:GetBucketAcl",
                "ec2:DescribeVpcEndpoints",
                "ec2:DescribeRouteTables",
                "ec2:CreateNetworkInterface",
                "ec2:DeleteNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeSubnets",
                "ec2:DescribeVpcAttribute",
                "iam:ListRolePolicies",
                "iam:GetRole",
                "iam:GetRolePolicy",
                "cloudwatch:PutMetricData"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:CreateBucket"
            ],
            "Resource": [
                "arn:aws:s3:::aws-glue-*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::aws-glue-*/*",
                "arn:aws:s3:::*/*aws-glue-*/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::crawler-public*",
                "arn:aws:s3:::aws-glue-*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:*:*:*:/aws-glue/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateTags",
                "ec2:DeleteTags"
            ],
            "Condition": {
                "ForAllValues:StringEquals": {
                    "aws:TagKeys": [
                        "aws-glue-service-resource"
                    ]
                }
            },
            "Resource": [
                "arn:aws:ec2:*:*:network-interface/*",
                "arn:aws:ec2:*:*:security-group/*",
                "arn:aws:ec2:*:*:instance/*"
            ]
        }
    ]

  })
}
resource "aws_iam_policy" "GlueJobRunManagementFullAccessPolicy" {
  name        = "GlueJobRunManagementFullAccessPolicy_${terraform.workspace}"
  description = "Allows AWS Step Functions to run Glue jobs on your behalf."
  policy = jsonencode({
    "Statement": [
        {
            "Action": [
                "glue:StartJobRun",
                "glue:GetJobRun",
                "glue:GetJobRuns",
                "glue:BatchStopJobRun"
            ],
            "Effect": "Allow",
            "Resource": [
                "*"
            ]
        }
    ],
    "Version": "2012-10-17"
  })

}
resource "aws_iam_policy" "cloudwatch_full" {
  name        = "cloudwatch_full_${terraform.workspace}"
  description = "IAM policy for EventBridge"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "EventBridgeActions",
        Effect = "Allow",
        Action = [
          "events:*",
          "schemas:*",
          "scheduler:*",
          "pipes:*",
        ],
        Resource = "*",
      },
      {
        Sid    = "IAMCreateServiceLinkedRoleForApiDestinations",
        Effect = "Allow",
        Action = "iam:CreateServiceLinkedRole",
        Resource = "arn:aws:iam::*:role/aws-service-role/AmazonEventBridgeApiDestinationsServiceRolePolicy",
        Condition = {
          StringEquals = {
            "iam:AWSServiceName" = "apidestinations.events.amazonaws.com",
          },
        },
      },
      {
        Sid    = "IAMCreateServiceLinkedRoleForAmazonEventBridgeSchemas",
        Effect = "Allow",
        Action = "iam:CreateServiceLinkedRole",
        Resource = "arn:aws:iam::*:role/aws-service-role/schemas.amazonaws.com/AWSServiceRoleForSchemas",
        Condition = {
          StringEquals = {
            "iam:AWSServiceName" = "schemas.amazonaws.com",
          },
        },
      },
      {
        Sid    = "SecretsManagerAccessForApiDestinations",
        Effect = "Allow",
        Action = [
          "secretsmanager:CreateSecret",
          "secretsmanager:UpdateSecret",
          "secretsmanager:DeleteSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
        ],
        Resource = "arn:aws:secretsmanager:*:*:secret:events!*",
      },
      {
        Sid    = "IAMPassRoleForCloudWatchEvents",
        Effect = "Allow",
        Action = "iam:PassRole",
        Resource = "arn:aws:iam::*:role/AWS_Events_Invoke_Targets",
      },
      {
        Sid    = "IAMPassRoleAccessForScheduler",
        Effect = "Allow",
        Action = "iam:PassRole",
        Resource = "arn:aws:iam::*:role/*",
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "scheduler.amazonaws.com",
          },
        },
      },
      {
        Sid    = "IAMPassRoleAccessForPipes",
        Effect = "Allow",
        Action = "iam:PassRole",
        Resource = "arn:aws:iam::*:role/*",
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "pipes.amazonaws.com",
          },
        },
      },
    ],
  })
}
