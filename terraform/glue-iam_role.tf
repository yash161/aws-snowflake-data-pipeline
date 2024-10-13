resource "aws_iam_role" "glue_job_role" {
  name = "predict-etl-${terraform.workspace}-source-to-snowflake-sync-${terraform.workspace}-role"

  assume_role_policy = <<-EOF
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Action": "sts:AssumeRole",
          "Principal": {
            "Service": "glue.amazonaws.com"
          },
          "Effect": "Allow",
          "Sid": "GlueJobAssumeRole"
        }
      ]
    }
  EOF

  managed_policy_arns = [
    aws_iam_policy.glue_s3.arn,
    aws_iam_policy.sns_full_access_policy_glue.arn,
    aws_iam_policy.AWSGlueConsoleFullAccess_policy.arn,
    aws_iam_policy.AWSGlueServiceRole_policy.arn,
    aws_iam_policy.secret_manager_policy.arn,
  ]
}
