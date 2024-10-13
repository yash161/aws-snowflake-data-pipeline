data "aws_eks_cluster" "stg_cluster" {
  name = var.eks_cluster_name
}