# "Resource": "${aws_lambda_function.snowflake_lambda.arn}",
resource "aws_sfn_state_machine" "sfn_state_machine" {
  name     = "predict-etl-${terraform.workspace}-step-function"
  role_arn = aws_iam_role.step_function_role.arn
  logging_configuration {
    log_destination        ="${aws_cloudwatch_log_group.step_function_log_group.arn}:*"
    include_execution_data = true
    level                  = "ERROR"
  }
  definition = jsonencode({
    "StartAt" : "Lambda Invoke",
    "States" : {
      "Lambda Invoke" : {
        "Type" : "Task",
        "Resource" : "arn:aws:states:::lambda:invoke",
        "OutputPath" : "$.Payload",
        "Parameters" : {
          "Payload.$" : "$",
          "FunctionName" : aws_lambda_function.fetch_replication_list.arn
        },
        "Retry" : [
          {
            "ErrorEquals" : ["Glue.AWSGlueException"],
            "BackoffRate" : 2,
            "IntervalSeconds" : 2,
            "MaxAttempts" : 3
          }
        ],
        "Catch" : [
          {
            "ErrorEquals" : ["States.ALL"],
            "Next" : "SNS Publish"
          }
        ],
        "Next" : "Map"
      },
      "Map" : {
        "Type" : "Map",
        "Catch": [
        {
          "ErrorEquals": [
            "States.ALL"
          ],
          "Next": "SNS Publish"
        }
      ],
        "ItemProcessor" : {
          "ProcessorConfig" : {
            "Mode" : "INLINE"
          },
          "StartAt" : "Choice",
          "States" : {
            "Choice": {
            "Type": "Choice",
            "Choices": [
              {
                "Variable": "$.src_type",
                "StringEquals": "s3",
                "Next": "Glue StartJobRun"
              }
            ],
            "Default": "Snowflake data replication"
          },
          "Glue StartJobRun": {
            "Type": "Task",
             "Catch": [
              {
                "ErrorEquals": [
                  "States.TaskFailed"
                ],
                "Next": "Pass"
              }
            ],
             "Retry" : [
                {
                  "ErrorEquals" : ["Glue.AWSGlueException"],
                  "BackoffRate" : 2,
                  "IntervalSeconds" : 10,
                  "MaxAttempts" : 3
                }
              ],
            "Resource": "arn:aws:states:::glue:startJobRun",
            "Parameters": {
              "JobName": aws_glue_job.s3_source_glue_job.arn
              "Arguments" : {
                  "--src_type.$" : "$.src_type",
                  "--src_db.$" : "$.src_db",
                  "--src_schema.$" : "$.src_schema",
                  "--src_table.$" : "$.src_table",
                  "--snowflake_db.$" : "$.snowflake_db",
                  "--snowflake_schema.$" : "$.snowflake_schema",
                  "--snowflake_table.$" : "$.snowflake_table",
                  "--primary_key.$" : "$.primary_key"
                }
            },
            "End": true
          },
            "Snowflake data replication" : {
              "Type" : "Task",
               "Catch": [
              {
                "ErrorEquals": [
                  "States.TaskFailed"
                ],
                "Next": "Pass"
              }
            ],
              "Retry" : [
                {
                  "ErrorEquals" : ["Glue.AWSGlueException"],
                  "BackoffRate" : 2,
                  "IntervalSeconds" : 10,
                  "MaxAttempts" : 3
                }
              ],
              "Resource" : "arn:aws:states:::glue:startJobRun.sync",
              "Parameters" : {
                "WorkerType.$":"$.worker_type",
                "NumberOfWorkers":2,
                "JobName" : aws_glue_job.glue_job.name
                "Arguments" : {
                  "--src_type.$" : "$.src_type",
                  "--src_db.$" : "$.src_db",
                  "--src_schema.$" : "$.src_schema",
                  "--src_table.$" : "$.src_table",
                  "--snowflake_db.$" : "$.snowflake_db",
                  "--snowflake_schema.$" : "$.snowflake_schema",
                  "--snowflake_table.$" : "$.snowflake_table",
                  "--primary_key.$" : "$.primary_key"
                }
              },
              "End" : true
            },
            "Pass": {
            "Type": "Pass",
            "End": true
          }
          }
        },
        "Next" : "EKS RunJob",
        "Retry" : [
          {
            "ErrorEquals" : ["States.TaskFailed"],
            "BackoffRate" : 2,
            "MaxAttempts" : 3,
            "IntervalSeconds" : 60,
            "Comment" : "Incase of Throttling exception",
            "MaxDelaySeconds" : 100
          }
        ],
        "MaxConcurrency" : 200,
        "ItemsPath" : "$.body",
        "Catch" : [
          {
            "ErrorEquals" : ["States.ALL"],
            "Next" : "SNS Publish"
          }
        ],
        "ResultPath": null,
        "OutputPath": null
      },
       "EKS RunJob": {
        "Type": "Task",
           "Catch": [
        {
          "ErrorEquals": [
            "States.ALL"
          ],
          "Next": "SNS Publish"
        }
      ]
        "Resource": "arn:aws:states:::eks:runJob.sync",
        "Parameters": {
          "ClusterName": data.aws_eks_cluster.stg_cluster.name,
          "CertificateAuthority": var.certificate_authority,
          "Endpoint": data.aws_eks_cluster.stg_cluster.endpoint,
          "Namespace": var.eks_cluster_namespace,
          "Job": {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
              "name.$": "States.Format('dbt-{}',States.UUID())"
            },
            "spec": {
              "ttlSecondsAfterFinished": 100,
              "template": {
                "metadata": {
                  "name": "Job_name_with_timestamp"
                },
                "spec": {
                  "containers": [
                    {
                      "name": "dbt",
                      "image": "${var.account_id}.dkr.ecr.${var.region}.amazonaws.com/${var.aws_ecr_repository}-${terraform.workspace}:latest",
                      "command": [
                        "dbt",
                        "build"
                      ],
                      "args": []
                    }
                  ],
                  "restartPolicy": "Never"
                }
              }
            }
          }
        },
        "Next": "SNS Publish"
      },
      "SNS Publish" : {
        "Type" : "Task",
        "Resource" : "arn:aws:states:::sns:publish",
        "Parameters" : {
         "Message": {
          "Source": "Step Functions!",
          "status.$": "$.status.conditions",
          "succeeded.$": "$.status.succeeded"
        },
          "TopicArn" : aws_sns_topic.step_function_sns.arn
        },
        "End" : true
      }
    }
  })
}

