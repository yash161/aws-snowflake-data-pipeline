variable "worker_type" {
  type = string
}
variable "eventbrigde_schedule_expression" {
  type = string
}
variable "eventbrigde_description" {
  type = string
}
variable "glue_job_name" {
  type = string
}
variable "glue_version" {
  type = string
}
variable "artifact_bucket_name" {
  type = string
}
variable "glue_number_of_workers" {
  type = string
}
variable "sns_secret_name" {
  type = string
}
variable "glue_max_concurrent_runs" {
  type = string
}
variable "kms_key_id" {
  type = string
}
variable "sns_kms_key_id" {
  type = string
}
variable "account_id" {
  type = string
}
variable "vpc_subnet1" {
  type = string
}
variable "vpc_subnet2" {
  type = string
}
variable "vpc_id" {
  type = string
}
variable "vpc_sg" {
  type = string
}
variable "aidbox_postgres_secret_name" {
  type = string
}
variable "connect_postgres_secret_name" {
  type = string
}
variable "lambda_bucket" {
  type = string
}

variable "postgres_layer_arn" {
  type = string
}
variable "snowflake_connector_layer_arn" {
  type = string
}

variable "glue_script_bucket" {
  type = string
}

variable "aws_ecr_repository" {
    type= string
}

variable "lambda_role" {
    type= string
}
variable "tag" {
  type = string
}

variable "region" {
  type = string
}
variable "eks_cluster_name" {
  type = string
}
variable "eks_cluster_namespace" {
  type = string
}
variable "lambda_runtime" {
  type = string
}
variable "layer_description" {
  type = string
}

variable "certificate_authority" {
  type = string
}
variable "aws_ecs_service" {
  type = string
}

#variable "subnet_ids" {
#  type = list(string)
#}
variable "glue_worker_type" {
  type = string
}
#variable "security_group_ids" {
#  type = list(string)
#}
variable "SNOWFLAKE_METADATA_DATABASE_NAME"{
    type = string
}
variable "SNOWFLAKE_METADATA_SCHEMA_NAME"{
    type = string
}
variable "SNOWFLAKE_METADATA_TABLE_NAME"{
    type = string
}

variable "postgres_secret_name"{
    type = string
}
variable "snowflake_secret_name"{
    type = string
}
variable "glue_connection_username"{
    type = string
}
variable "glue_connection_subnet"{
    type = string
}
variable "glue_connection_availability_zone"{
    type = string
}
variable "glue_connection_sg"{
    type = string
}
variable "glue_connection_JDBC_CONNECTION_URL"{
    type = string
}