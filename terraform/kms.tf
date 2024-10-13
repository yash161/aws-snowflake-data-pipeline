data "aws_kms_key" "ecr_kms_key" {
  key_id = var.kms_key_id
}

data "aws_kms_key" "sns_kms_key" {
  key_id = var.sns_kms_key_id
}