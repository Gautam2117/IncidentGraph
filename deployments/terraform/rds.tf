resource "aws_db_subnet_group" "rds" {
  name       = "incidentgraph-rds-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "incidentgraph-rds-subnet-group"
  }
}

resource "aws_db_instance" "postgres" {
  identifier                = "incidentgraph-db"
  allocated_storage         = 20
  engine                    = "postgres"
  engine_version            = "16"
  instance_class            = "db.t4g.micro"
  db_name                   = "incidentgraph_db"
  username                  = var.db_username
  password                  = var.db_password
  db_subnet_group_name      = aws_db_subnet_group.rds.name
  vpc_security_group_ids    = [aws_security_group.rds.id]
  storage_encrypted         = true
  publicly_accessible       = false
  backup_retention_period   = 7
  deletion_protection       = var.environment == "production"
  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "incidentgraph-${var.environment}-final" : null

  tags = {
    Name = "incidentgraph-postgres-rds"
  }
}

resource "aws_security_group" "rds" {
  name        = "incidentgraph-rds-sg"
  description = "PostgreSQL access from IncidentGraph ECS tasks only"
  vpc_id      = aws_vpc.main.id

  ingress {
    protocol        = "tcp"
    from_port       = 5432
    to_port         = 5432
    security_groups = [aws_security_group.ecs_tasks.id]
  }

}
