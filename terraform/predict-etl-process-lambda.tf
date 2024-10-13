
data "aws_s3_bucket_object" "lambda_zip" {
 bucket = var.artifact_bucket_name
  key    = "${terraform.workspace}/lambda_fetch_replication_list.zip"
}


resource "aws_lambda_function" "fetch_replication_list" {
  function_name = "predict_etl_${terraform.workspace}_fetch_replication_list"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"
  memory_size   = 128
  timeout       = 180
  environment {
    variables = {

      snowflake_secret_name = var.snowflake_secret_name,
      connect_postgres_secret_name =var.connect_postgres_secret_name
      aidbox_postgres_secret_name=var.aidbox_postgres_secret_name
      SNOWFLAKE_METADATA_DATABASE_NAME=var.SNOWFLAKE_METADATA_DATABASE_NAME
      SNOWFLAKE_METADATA_SCHEMA_NAME=var.SNOWFLAKE_METADATA_SCHEMA_NAME
      SNOWFLAKE_METADATA_TABLE_NAME=var.SNOWFLAKE_METADATA_TABLE_NAME
      sns_secret_name=var.sns_secret_name
    }
  }
  # Attach an existing Lambda layer
  layers = [
    var.postgres_layer_arn,
    aws_lambda_layer_version.main.arn,
    aws_lambda_layer_version.tenacity_layer.arn
  ]
  s3_bucket         = data.aws_s3_bucket_object.lambda_zip.bucket
  s3_key            = data.aws_s3_bucket_object.lambda_zip.key
  s3_object_version = data.aws_s3_bucket_object.lambda_zip.version_id
 vpc_config {
    subnet_ids         = [data.aws_subnet.predict-subnet-private1-us-east-1a.id, data.aws_subnet.predict-subnet-private2-us-east-1b.id]  # Replace with your subnet IDs
    security_group_ids = [data.aws_security_group.predict-lmb-sg.id]  # Replace with your security group ID
  }
}
