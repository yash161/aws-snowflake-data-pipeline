resource "aws_sns_topic" "glue_sns" {
  name = "predict_etl_${terraform.workspace}_glue_job_alerts"
  kms_master_key_id = var.sns_kms_key_id
}

resource "aws_sns_topic" "step_function_sns" {
  name = "predict_etl_${terraform.workspace}_step_function_alerts"
   kms_master_key_id = var.sns_kms_key_id
}