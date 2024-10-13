#resource "aws_ecs_cluster" "dbt_runner" {
#  name = "ch-dbt-runner-${terraform.workspace}"
#
#  setting {
#    name  = "containerInsights"
#    value = "enabled"
#  }
#}
#
#resource "aws_ecs_task_definition" "my_task_definition" {
#  family             = "dbt-runner-${terraform.workspace}"
#  execution_role_arn = aws_iam_role.ecs_task_execution_role.arn
#  network_mode       = "awsvpc"
#  cpu                = 512
#  memory             = 1024
#  container_definitions = jsonencode([
#    {
#      name  = "dbt-runner"
#      image = "${var.account_id}.dkr.ecr.${var.region}.amazonaws.com/ch-dbt-serverless-${terraform.workspace}:${var.tag}"
#      memory      = 1024
#      cpu         = 512
#      networkMode = "awsvpc"
#      logConfiguration = {
#        logDriver = "awslogs"
#        options = {
#          "awslogs-create-group"  = "true"
#          "awslogs-group"         = aws_cloudwatch_log_group.ecs_log_group.name
#          "awslogs-region"        = var.region
#          "awslogs-stream-prefix" = "dbt-runner "
#        }
#      }
#    }
#  ])
#  requires_compatibilities = ["FARGATE"]
#}
#
#
####ecs service
#
#resource "aws_ecs_service" "my_service" {
#  name                = "dbt-runner-service-${terraform.workspace}"
#  cluster             = aws_ecs_cluster.dbt_runner.id
#  task_definition     = aws_ecs_task_definition.my_task_definition.arn
#  launch_type         = "FARGATE"
#  scheduling_strategy = "REPLICA"
#  desired_count       = 1
#  network_configuration {
#    subnets          = var.subnet_ids
#    security_groups  = var.security_group_ids
#    assign_public_ip = true
#  }
#}