resource "aws_iam_policy" "lambda_basic_execution" {
  name        = "MyLambdaBasicExecutionPolicy-${terraform.workspace}"
  description = "My Lambda Basic Execution Policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_vpc_access_execution" {
  name        = "MyLambdaVPCAccessExecutionPolicy-${terraform.workspace}"
  description = "My Lambda VPC Access Execution Policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:AssignPrivateIpAddresses",
          "ec2:UnassignPrivateIpAddresses"
        ],
        Resource = "*"
      }
    ]
  })
}
resource "aws_iam_policy" "sns_policy_lambda" {
  name        = "sns-${terraform.workspace}-access-policy-lambda"
  description = "Policy providing full access to Amazon SNS for aws lambda"
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
resource "aws_iam_policy" "step_functions_full_access" {
  name        = "MyStepFunctionsFullAccessPolicy-${terraform.workspace}"
  description = "My Step Functions Full Access Policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid      = "VisualEditor0",
        Effect   = "Allow",
        Action   = "states:*",
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "secrets_manager_read_write" {
  name        = "MySecretsManagerReadWritePolicy-${terraform.workspace}"
  description = "My Secrets Manager Read/Write Policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:DeleteSecret",
          "secretsmanager:CreateSecret",
          "secretsmanager:UpdateSecret",
          "secretsmanager:ListSecrets",
          "secretsmanager:ListSecretVersionIds",
          "secretsmanager:TagResource",
          "secretsmanager:UntagResource"
        ],
        Resource = "*"
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "lambda:AddPermission",
          "lambda:CreateFunction",
          "lambda:GetFunction",
          "lambda:InvokeFunction",
          "lambda:UpdateFunctionConfiguration"
        ],
        "Resource" : "arn:aws:lambda:*:*:function:SecretsManager*"
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "serverlessrepo:CreateCloudFormationChangeSet",
          "serverlessrepo:GetApplication"
        ],
        "Resource" : "arn:aws:serverlessrepo:*:*:applications/SecretsManager*"
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "s3:GetObject"
        ],
        "Resource" : [
          "arn:aws:s3:::awsserverlessrepo-changesets*",
          "arn:aws:s3:::secrets-manager-rotation-apps-*/*"
        ]
      }
    ]
  })
}
