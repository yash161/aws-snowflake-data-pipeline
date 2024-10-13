resource "aws_iam_policy" "glue_s3" {
  name        = "glue_s3_policy_${terraform.workspace}"
  description = "glue_s3 policy"

  # Insert your policy document here, either directly or through a data block.
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "VisualEditor0",
        Effect = "Allow",
        Action = [
          "s3:ListStorageLensConfigurations",
          "s3:ListAccessPointsForObjectLambda",
          "s3:GetAccessPoint",
          "s3:PutAccountPublicAccessBlock",
          "s3:GetAccountPublicAccessBlock",
          "s3:ListAllMyBuckets",
          "s3:ListAccessPoints",
          "s3:PutAccessPointPublicAccessBlock",
          "s3:ListJobs",
          "s3:PutStorageLensConfiguration",
          "s3:ListMultiRegionAccessPoints",
          "s3:CreateJob",
        ],
        Resource = "*"
      },
      {
        Sid    = "VisualEditor1",
        Effect = "Allow",
        Action = "s3:*",
        Resource = [
          "arn:aws:s3:::*/*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "sns_full_access_policy_glue" {
  name        = "sns-full-access-policy_glue-${terraform.workspace}"
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

resource "aws_iam_policy" "AWSGlueConsoleFullAccess_policy" {
  name        = "AWSGlueConsoleFullAccess-policy-${terraform.workspace}"
  description = "Policy providing full access to AWS Glue via the AWS Management Console"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = "glue:*",
        Resource = "*",
      },
    ],
  })
}

resource "aws_iam_policy" "AWSGlueServiceRole_policy" {
  name        = "AWSGlueServiceRole-policy-${terraform.workspace}"
  description = "Policy for AWS Glue service role which allows access to related services"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ec2:CreateTags",
          "ec2:DescribeNetworkInterfaces",
          "ec2:CreateNetworkInterface",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeInstances",
          "ec2:AttachNetworkInterface",
          "ec2:Describe*",
          "s3:Get*",
          "s3:List*",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ],
        Resource = "*",
      },
    ],
  })
}

resource "aws_iam_policy" "secret_manager_policy" {
  name        = "SecretsManagerReadWrite-policy-${terraform.workspace}"
  description = "Policy for Secrets Manager Read and Write"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "secretsmanager:Get*",
          "secretsmanager:List*",
          "secretsmanager:Put*",
          "secretsmanager:Update*",
          "secretsmanager:Delete*",
        ],
        Resource = "*",
      },
    ],
  })
}
