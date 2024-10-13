resource "aws_glue_security_configuration" "glue_encryption" {
    name="predict-elt-${terraform.workspace}-security-configurations"

  encryption_configuration {
    cloudwatch_encryption {
      cloudwatch_encryption_mode = "DISABLED"
    }

    job_bookmarks_encryption {
      job_bookmarks_encryption_mode = "DISABLED"
    }

    s3_encryption {
      kms_key_arn        = data.aws_kms_key.ecr_kms_key.arn
      s3_encryption_mode = "SSE-KMS"
    }
  }
}