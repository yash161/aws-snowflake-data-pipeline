#resource "aws_glue_connection" "glue_connection" {
#
#  name = "predict-etl-${terraform.workspace}-glue-connection"
#
#  physical_connection_requirements {
#    availability_zone = "us-east-1a"
#      subnet_id = data.aws_subnet.predict-subnet-private1-us-east-1a.id
#     security_group_id_list = [data.aws_security_group.predict-lmb-sg.id]
#  }
#}

#data "aws_glue_connection" "glue_connection" {
#  id="600762086688:ch-stg-postgres-reader"
#}

resource "aws_glue_connection" "glue_connection" {
  connection_properties = {
    JDBC_CONNECTION_URL = var.glue_connection_JDBC_CONNECTION_URL
    PASSWORD            = ""
    USERNAME            = var.glue_connection_username
  }

  name = "predict-elt-${terraform.workspace}-glue-connection"

  physical_connection_requirements {
    availability_zone      = var.glue_connection_availability_zone
    security_group_id_list = [var.glue_connection_sg]
    subnet_id              = var.glue_connection_subnet
  }
}