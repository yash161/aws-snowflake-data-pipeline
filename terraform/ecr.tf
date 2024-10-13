#resource "aws_ecr_repository" "example" {
#  name = "ch-dbt-serverless-${terraform.workspace}"
#  # Optionally, you can specify additional configuration options here
#}
#
## Output the repository URL
#output "ecr_repository_url" {
#  value = aws_ecr_repository.example.repository_url
#}