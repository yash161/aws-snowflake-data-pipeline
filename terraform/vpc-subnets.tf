data "aws_subnet" "predict-subnet-private2-us-east-1b" {
  vpc_id = data.aws_vpc.predict-vpc.id
  id     = var.vpc_subnet2
}
data "aws_subnet" "predict-subnet-private1-us-east-1a" {
  vpc_id = data.aws_vpc.predict-vpc.id
    id     = var.vpc_subnet1
}