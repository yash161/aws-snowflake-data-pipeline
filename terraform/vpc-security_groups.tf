data "aws_security_group" "predict-lmb-sg" {
  id = var.vpc_sg
}