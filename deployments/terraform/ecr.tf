resource "aws_ecr_repository" "control_plane" {
  name                 = "incidentgraph/control-plane"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_repository" "console" {
  name                 = "incidentgraph/console"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_cloudwatch_log_group" "control_plane" {
  name              = "/ecs/incidentgraph-control-plane"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "console" {
  name              = "/ecs/incidentgraph-console"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/incidentgraph-worker"
  retention_in_days = 30
}
