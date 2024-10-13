resource "aws_glue_job" "glue_job" {
  name = "predict-elt-${terraform.workspace}-postgres-to-snowflake-sync"
  role_arn     = aws_iam_role.glue_job_role.arn
  glue_version =var.glue_version
   worker_type = var.glue_worker_type
  number_of_workers=var.glue_number_of_workers
   connections = [aws_glue_connection.glue_connection.name]
  security_configuration   =aws_glue_security_configuration.glue_encryption.id

  command {
    name = "gluestreaming"
    script_location = "s3://${var.artifact_bucket_name}/${terraform.workspace}/src/glue/source_to_snowflake_sync/main.py"
    python_version  = 3
  }
  execution_property {
    max_concurrent_runs = var.glue_max_concurrent_runs
}
  default_arguments = {
    "--additional-python-modules" = "botocore,psycopg2-binary,boto3,snowflake-connector-python,fastparquet"
    "--snowflake_secret_name"= var.snowflake_secret_name
    "--extra-py-files" = "s3://${var.artifact_bucket_name}/${terraform.workspace}/postgres_to_snowflake_sync.zip"
     "--aidbox_postgres_secret_name"= var.aidbox_postgres_secret_name
     "--connect_postgres_secret_name"=var.connect_postgres_secret_name
     "--sns_secret_name"=var.sns_secret_name
     "--glue_job_name"=var.glue_job_name
  }
}