variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for deployment"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Deployment environment (production, staging, dev)"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Master password for RDS PostgreSQL instance"
}

variable "secret_key" {
  type        = string
  sensitive   = true
  description = "Application JWT signing key (at least 32 characters)"
  validation {
    condition     = length(var.secret_key) >= 32
    error_message = "secret_key must contain at least 32 characters."
  }
}

variable "webhook_signing_secret" {
  type        = string
  sensitive   = true
  description = "Webhook HMAC signing secret"
  validation {
    condition     = length(var.webhook_signing_secret) >= 16
    error_message = "webhook_signing_secret must contain at least 16 characters."
  }
}

variable "redis_auth_token" {
  type        = string
  sensitive   = true
  description = "ElastiCache transit-auth token"
  validation {
    condition     = length(var.redis_auth_token) >= 16
    error_message = "redis_auth_token must contain at least 16 characters."
  }
}

variable "certificate_arn" {
  type        = string
  description = "ACM certificate ARN for the public HTTPS listener"
  validation {
    condition     = can(regex("^arn:aws[a-z-]*:acm:", var.certificate_arn))
    error_message = "certificate_arn must be an ACM certificate ARN."
  }
}

variable "public_hostname" {
  type        = string
  description = "TLS hostname for the IncidentGraph console and API"
}

variable "route53_zone_id" {
  type        = string
  default     = ""
  description = "Optional Route53 hosted-zone ID; leave empty when DNS is managed elsewhere"
}

variable "monthly_budget_usd" {
  type        = number
  default     = 150
  description = "Monthly AWS cost guardrail"
}

variable "db_username" {
  type        = string
  default     = "incidentgraph"
  description = "RDS application username"
}

variable "db_name" {
  type        = string
  default     = "incidentgraph_db"
  description = "RDS application database"
}

variable "image_tag" {
  type        = string
  description = "Immutable application image tag (normally the git SHA)"
  validation {
    condition     = var.image_tag != "latest" && length(var.image_tag) > 0
    error_message = "image_tag must be immutable and may not be latest."
  }
}

variable "offline_validation" {
  type        = bool
  default     = false
  description = "Disable AWS API credential checks only for local static plan validation"
}
