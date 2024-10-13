data "aws_s3_bucket_object" "lambda_layer_zip" {
 bucket = var.artifact_bucket_name
  key    = "${terraform.workspace}/src/layers/snowflake_connector_layer.zip"
}
data "aws_s3_bucket_object" "lambda_layer_zip_tenacity" {
 bucket = var.artifact_bucket_name
  key    = "${terraform.workspace}/src/layers/tenacity_layer.zip"
}
data "aws_s3_bucket_object" "lambda_postgres_to_snowflake_sync_layer" {
 bucket = var.artifact_bucket_name
  key    = "${terraform.workspace}/src/layers/postgres_to_snowflake_sync_layer.zip"
}
resource "aws_lambda_layer_version" "main" {
	  layer_name       = "predict-etl-${terraform.workspace}-snowflake-connector-layer"
	  description      = var.layer_description
	  s3_bucket         = data.aws_s3_bucket_object.lambda_layer_zip.bucket
      s3_key            = data.aws_s3_bucket_object.lambda_layer_zip.key
      s3_object_version = data.aws_s3_bucket_object.lambda_layer_zip.version_id
	  compatible_runtimes = [var.lambda_runtime]
	  depends_on = [
	    data.aws_s3_bucket_object.lambda_layer_zip,
	  ]
}
resource "aws_lambda_layer_version" "tenacity_layer" {
	  layer_name       = "predict-etl-${terraform.workspace}-tenacity-connector-layer"
	  description      = "Tenacity for Retry Lambda layer"
	  s3_bucket         = data.aws_s3_bucket_object.lambda_layer_zip_tenacity.bucket
      s3_key            = data.aws_s3_bucket_object.lambda_layer_zip_tenacity.key
      s3_object_version = data.aws_s3_bucket_object.lambda_layer_zip_tenacity.version_id
	  compatible_runtimes = [var.lambda_runtime]
	  depends_on = [
	    data.aws_s3_bucket_object.lambda_layer_zip_tenacity,
	  ]
}
resource "aws_lambda_layer_version" "postgres_to_snowflake_sync_layer" {
	  layer_name       = "predict-etl-${terraform.workspace}-postgres-to-snowflake-sync-layer"
	  description      = "Pandas,Snowflake layer for lambda"
	  s3_bucket         = data.aws_s3_bucket_object.lambda_postgres_to_snowflake_sync_layer.bucket
      s3_key            = data.aws_s3_bucket_object.lambda_postgres_to_snowflake_sync_layer.key
      s3_object_version = data.aws_s3_bucket_object.lambda_postgres_to_snowflake_sync_layer.version_id
	  compatible_runtimes = [var.lambda_runtime]
	  depends_on = [
	    data.aws_s3_bucket_object.lambda_postgres_to_snowflake_sync_layer,
	  ]
}