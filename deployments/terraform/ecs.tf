resource "aws_ecs_cluster" "main" {
  name = "incidentgraph-cluster"
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "incidentgraph-ecsTaskExecutionRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

locals {
  runtime_secrets = [
    { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.runtime.arn}:database_url::" },
    { name = "REDIS_URL", valueFrom = "${aws_secretsmanager_secret.runtime.arn}:redis_url::" },
    { name = "SECRET_KEY", valueFrom = "${aws_secretsmanager_secret.runtime.arn}:secret_key::" },
    { name = "WEBHOOK_SIGNING_SECRET", valueFrom = "${aws_secretsmanager_secret.runtime.arn}:webhook_signing_secret::" }
  ]
}

resource "aws_ecs_task_definition" "control_plane" {
  family                   = "incidentgraph-control-plane"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "control-plane"
      image     = "${aws_ecr_repository.control_plane.repository_url}:${var.image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
        }
      ]
      environment = [
        { name = "ENVIRONMENT", value = "production" },
        { name = "GIT_SHA", value = var.image_tag }
      ]
      secrets = local.runtime_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/incidentgraph-control-plane"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "console" {
  family                   = "incidentgraph-console"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "console"
      image     = "${aws_ecr_repository.console.repository_url}:${var.image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
        }
      ]
      environment = [
        {
          name  = "NEXT_PUBLIC_API_URL"
          value = "https://${var.public_hostname}"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/incidentgraph-console"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "control_plane" {
  name            = "incidentgraph-control-plane"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.control_plane.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.control_plane.arn
    container_name   = "control-plane"
    container_port   = 8000
  }

  depends_on = [aws_secretsmanager_secret_version.runtime, aws_lb_listener.https]
}

resource "aws_ecs_service" "console" {
  name            = "incidentgraph-console"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.console.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.console.arn
    container_name   = "console"
    container_port   = 3000
  }

  depends_on = [aws_lb_listener.https]
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "incidentgraph-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([{
    name      = "worker"
    image     = "${aws_ecr_repository.control_plane.repository_url}:${var.image_tag}"
    essential = true
    command   = ["celery", "-A", "app.worker.celery_app", "worker", "--loglevel=INFO"]
    environment = [
      { name = "ENVIRONMENT", value = "production" },
      { name = "GIT_SHA", value = var.image_tag }
    ]
    secrets = local.runtime_secrets
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.worker.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "migration" {
  family                   = "incidentgraph-migration"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([{
    name      = "migration"
    image     = "${aws_ecr_repository.control_plane.repository_url}:${var.image_tag}"
    essential = true
    command   = ["alembic", "-c", "services/control-plane/alembic.ini", "upgrade", "head"]
    environment = [
      { name = "ENVIRONMENT", value = "production" },
      { name = "GIT_SHA", value = var.image_tag }
    ]
    secrets = local.runtime_secrets
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.worker.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "migration"
      }
    }
  }])
}

resource "aws_ecs_service" "worker" {
  name            = "incidentgraph-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  depends_on = [aws_secretsmanager_secret_version.runtime]
}

# Tasks need outbound TLS through the NAT gateway for configured model APIs and
# AWS service endpoints; all non-TLS database/cache/DNS egress stays VPC-bound.
# trivy:ignore:AWS-0104
resource "aws_security_group" "ecs_tasks" {
  name        = "incidentgraph-ecs-tasks-sg"
  description = "Allow inbound access from the ALB only"
  vpc_id      = aws_vpc.main.id

  ingress {
    protocol        = "tcp"
    from_port       = 8000
    to_port         = 8000
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    protocol        = "tcp"
    from_port       = 3000
    to_port         = 3000
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol    = "tcp"
    from_port   = 5432
    to_port     = 5432
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
    protocol    = "tcp"
    from_port   = 6379
    to_port     = 6379
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
    protocol    = "udp"
    from_port   = 53
    to_port     = 53
    cidr_blocks = [aws_vpc.main.cidr_block]
  }
}
