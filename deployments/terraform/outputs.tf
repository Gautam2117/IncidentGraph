output "vpc_id" {
  value       = aws_vpc.main.id
  description = "ID of created AWS VPC"
}

output "rds_endpoint" {
  value       = aws_db_instance.postgres.endpoint
  description = "Endpoint address of RDS PostgreSQL database instance"
}

output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "Application Load Balancer DNS name for Console and Control Plane"
}

output "application_url" {
  value       = "https://${var.public_hostname}"
  description = "Public TLS URL (DNS record is created when route53_zone_id is set)"
}

output "redis_primary_endpoint" {
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  description = "Private ElastiCache primary endpoint"
}

output "migration_task_definition_arn" {
  value       = aws_ecs_task_definition.migration.arn
  description = "Run this one-shot Fargate task before updating ECS services"
}
