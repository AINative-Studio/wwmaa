# Cloudflare WAF Configuration for wwmaa.com
# Terraform configuration for infrastructure-as-code management
# Version: 1.0
# Last Updated: 2025-01-10

terraform {
  required_version = ">= 1.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }

  # Backend configuration for state management
  # Uncomment and configure for production use
  # backend "s3" {
  #   bucket = "wwmaa-terraform-state"
  #   key    = "cloudflare/waf/terraform.tfstate"
  #   region = "us-west-2"
  #   encrypt = true
  # }
}

# Provider configuration
provider "cloudflare" {
  # API token should be set via environment variable: CLOUDFLARE_API_TOKEN
  # Never commit API tokens to git!
}

# Variables
variable "cloudflare_account_id" {
  description = "Cloudflare account ID"
  type        = string
  sensitive   = true
}

variable "domain" {
  description = "Primary domain name"
  type        = string
  default     = "wwmaa.com"
}

variable "environment" {
  description = "Environment (production or staging)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["production", "staging"], var.environment)
    error_message = "Environment must be either 'production' or 'staging'."
  }
}

# Locals for environment-specific configuration
locals {
  # Rate limiting thresholds by environment
  api_rate_limit = var.environment == "production" ? 100 : 10
  login_rate_limit = var.environment == "production" ? 5 : 10
  registration_rate_limit = var.environment == "production" ? 3 : 10
  search_rate_limit = var.environment == "production" ? 10 : 20
  admin_rate_limit = var.environment == "production" ? 200 : 50

  # WAF mode by environment
  waf_mode = var.environment == "production" ? "block" : "log"

  # Common tags
  common_tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = "wwmaa"
    Component   = "WAF"
  }
}

# Data source: Get zone information
data "cloudflare_zone" "main" {
  name = var.domain
}

# SSL/TLS Configuration
resource "cloudflare_zone_settings_override" "main" {
  zone_id = data.cloudflare_zone.main.id

  settings {
    # SSL/TLS Mode: Full (Strict)
    ssl = "strict"

    # Always Use HTTPS
    always_use_https = "on"

    # Automatic HTTPS Rewrites
    automatic_https_rewrites = "on"

    # Minimum TLS Version
    min_tls_version = "1.2"

    # TLS 1.3
    tls_1_3 = "on"

    # HTTP/2
    http2 = "on"

    # HTTP/3 (QUIC)
    http3 = "on"

    # HSTS
    security_header {
      enabled = true
      max_age = 31536000  # 12 months
      include_subdomains = true
      preload = var.environment == "production" ? true : false
      nosniff = true
    }

    # Security Level
    security_level = var.environment == "production" ? "high" : "medium"

    # Challenge TTL
    challenge_ttl = 1800  # 30 minutes

    # Browser Check
    browser_check = "on"

    # Opportunistic Encryption
    opportunistic_encryption = "on"

    # Always Online
    always_online = "on"
  }
}

# Rate Limiting Rule: API General
resource "cloudflare_rate_limit" "api_general" {
  zone_id = data.cloudflare_zone.main.id

  description = "General API rate limit to prevent abuse"

  threshold = local.api_rate_limit
  period    = 60  # seconds

  match {
    request {
      url_pattern = "${var.domain}/api/*"
    }
  }

  action {
    mode    = "ban"
    timeout = 3600  # 1 hour

    response {
      content_type = "application/json"
      body         = jsonencode({
        error = "Rate limit exceeded. Please try again later."
        code  = "RATE_LIMIT_EXCEEDED"
      })
    }
  }

  # Don't rate limit verified API clients (if using specific headers)
  bypass_url_patterns = []
}

# Rate Limiting Rule: Login Endpoint
resource "cloudflare_rate_limit" "login" {
  zone_id = data.cloudflare_zone.main.id

  description = "Login endpoint rate limit to prevent brute force attacks"

  threshold = local.login_rate_limit
  period    = 60

  match {
    request {
      url_pattern = "${var.domain}/api/auth/login"
      methods     = ["POST"]
    }
  }

  action {
    mode    = "ban"
    timeout = 1800  # 30 minutes

    response {
      content_type = "application/json"
      body         = jsonencode({
        error = "Too many login attempts. Please try again later."
        code  = "LOGIN_RATE_LIMIT_EXCEEDED"
      })
    }
  }
}

# Rate Limiting Rule: Registration Endpoint
resource "cloudflare_rate_limit" "registration" {
  zone_id = data.cloudflare_zone.main.id

  description = "Registration endpoint rate limit to prevent automated account creation"

  threshold = local.registration_rate_limit
  period    = 60

  match {
    request {
      url_pattern = "${var.domain}/api/auth/register"
      methods     = ["POST"]
    }
  }

  action {
    mode    = "ban"
    timeout = 3600  # 1 hour

    response {
      content_type = "application/json"
      body         = jsonencode({
        error = "Too many registration attempts. Please try again later."
        code  = "REGISTRATION_RATE_LIMIT_EXCEEDED"
      })
    }
  }
}

# Rate Limiting Rule: Search Endpoint
resource "cloudflare_rate_limit" "search" {
  zone_id = data.cloudflare_zone.main.id

  description = "Search endpoint rate limit to prevent scraping"

  threshold = local.search_rate_limit
  period    = 60

  match {
    request {
      url_pattern = "${var.domain}/api/search/*"
    }
  }

  action {
    mode    = "challenge"  # Use challenge instead of ban for search
    timeout = 1800  # 30 minutes
  }
}

# Rate Limiting Rule: Password Reset
resource "cloudflare_rate_limit" "password_reset" {
  zone_id = data.cloudflare_zone.main.id

  description = "Password reset rate limit to prevent abuse"

  threshold = 3
  period    = 300  # 5 minutes

  match {
    request {
      url_pattern = "${var.domain}/api/auth/reset-password"
      methods     = ["POST"]
    }
  }

  action {
    mode    = "ban"
    timeout = 3600  # 1 hour

    response {
      content_type = "application/json"
      body         = jsonencode({
        error = "Too many password reset attempts. Please try again later."
        code  = "PASSWORD_RESET_RATE_LIMIT_EXCEEDED"
      })
    }
  }
}

# IP Lists: Malicious IPs
resource "cloudflare_list" "malicious_ips" {
  account_id  = var.cloudflare_account_id
  name        = "malicious_ips_${var.environment}"
  kind        = "ip"
  description = "List of known malicious IP addresses for ${var.environment}"

  # Example items - update with actual malicious IPs
  # Items should be managed through Cloudflare dashboard or API
  # to avoid committing sensitive data to git
}

# IP Lists: Trusted IPs (Allowlist)
resource "cloudflare_list" "trusted_ips" {
  account_id  = var.cloudflare_account_id
  name        = "trusted_ips_${var.environment}"
  kind        = "ip"
  description = "List of trusted IP addresses (API clients, partners) for ${var.environment}"

  # Example: Office IPs, API clients, monitoring services
  # Manage through dashboard or API
}

# Firewall Rule: Block Malicious IPs
resource "cloudflare_ruleset" "waf_custom_rules" {
  zone_id     = data.cloudflare_zone.main.id
  name        = "WAF Custom Rules - ${var.environment}"
  description = "Custom firewall rules for ${var.environment} environment"
  kind        = "zone"
  phase       = "http_request_firewall_custom"

  # Rule 1: Block Malicious IPs
  rules {
    action = "block"
    expression = "(ip.src in $malicious_ips_${var.environment})"
    description = "Block known malicious IPs"
    enabled = true
  }

  # Rule 2: Challenge Sensitive Endpoints
  rules {
    action = "managed_challenge"
    expression = "(http.request.uri.path contains \"/api/admin\" or http.request.uri.path contains \"/api/payment\" or http.request.uri.path contains \"/api/billing\")"
    description = "Add extra verification for sensitive endpoints"
    enabled = true
  }

  # Rule 3: Block Missing User-Agent
  rules {
    action = "block"
    expression = "(http.user_agent eq \"\")"
    description = "Block requests without User-Agent header"
    enabled = var.environment == "production"
  }

  # Rule 4: Block Security Scanners
  rules {
    action = "block"
    expression = "(http.user_agent contains \"sqlmap\" or http.user_agent contains \"nikto\" or http.user_agent contains \"nmap\" or http.user_agent contains \"masscan\" or http.user_agent contains \"acunetix\" or http.user_agent contains \"netsparker\")"
    description = "Block common security scanning tools"
    enabled = true
  }

  # Rule 5: Block Suspicious Query Strings (Basic SQL Injection Patterns)
  rules {
    action = "block"
    expression = "(http.request.uri.query contains \"UNION SELECT\" or http.request.uri.query contains \"DROP TABLE\" or http.request.uri.query contains \"1=1\" or http.request.uri.query contains \"OR 1=1\")"
    description = "Block obvious SQL injection attempts in query strings"
    enabled = true
  }

  # Rule 6: Geo-Blocking (Optional - Uncomment and configure if needed)
  # rules {
  #   action = "block"
  #   expression = "(ip.geoip.country in {\"CN\" \"RU\" \"KP\"} and not ip.src in $trusted_ips_${var.environment})"
  #   description = "Block traffic from high-risk countries except trusted IPs"
  #   enabled = false  # Set to true to enable
  # }

  # Rule 7: Allow Trusted IPs (Process first)
  rules {
    action = "skip"
    action_parameters {
      ruleset = "current"
    }
    expression = "(ip.src in $trusted_ips_${var.environment})"
    description = "Skip WAF rules for trusted IPs"
    enabled = true
  }
}

# WAF Managed Rulesets - OWASP Core Ruleset
resource "cloudflare_ruleset" "owasp_core" {
  zone_id     = data.cloudflare_zone.main.id
  name        = "OWASP Core Ruleset"
  description = "Cloudflare OWASP Core Ruleset for ${var.environment}"
  kind        = "zone"
  phase       = "http_request_firewall_managed"

  rules {
    action = var.environment == "production" ? "execute" : "log"
    action_parameters {
      id = "efb7b8c949ac4650a09736fc376e9aee"  # Cloudflare OWASP Core Ruleset ID
    }
    expression = "true"
    description = "Execute Cloudflare OWASP Core Ruleset"
    enabled = true
  }
}

# DDoS Protection - L7 DDoS Managed Ruleset
resource "cloudflare_ruleset" "ddos_l7" {
  zone_id     = data.cloudflare_zone.main.id
  name        = "DDoS L7 Protection"
  description = "Layer 7 DDoS protection for ${var.environment}"
  kind        = "zone"
  phase       = "ddos_l7"

  rules {
    action = "execute"
    action_parameters {
      id = "4d21379b4f9f4bb088e0729962c8b3cf"  # HTTP DDoS Attack Protection
    }
    expression = "true"
    description = "Execute HTTP DDoS Attack Protection"
    enabled = true
  }
}

# Bot Management (Free Plan - Bot Fight Mode)
# Note: Super Bot Fight Mode requires Pro plan or higher
resource "cloudflare_bot_management" "main" {
  zone_id = data.cloudflare_zone.main.id

  enable_js              = true
  fight_mode            = var.environment == "production" ? true : false
  suppress_session_score = false

  # Auto-update bot detection rules
  auto_update_model = true
}

# Page Rules for Additional Security (Optional)
resource "cloudflare_page_rule" "admin_security" {
  zone_id = data.cloudflare_zone.main.id
  target  = "${var.domain}/admin/*"
  priority = 1

  actions {
    security_level = "high"
    browser_check  = "on"
  }
}

# Notification Policy: DDoS Attack Alert
resource "cloudflare_notification_policy" "ddos_attack" {
  account_id = var.cloudflare_account_id
  name       = "DDoS Attack Alert - ${var.environment}"
  description = "Alert when DDoS attack is detected"
  enabled    = true

  alert_type = "dos_attack_l7"

  email_integration {
    id = "email"  # Use default email integration
  }

  # Add webhook integration for Slack/PagerDuty if configured
  # webhooks_integration {
  #   id = "your_webhook_id"
  # }
}

# Notification Policy: High Rate of Blocked Requests
resource "cloudflare_notification_policy" "high_block_rate" {
  account_id = var.cloudflare_account_id
  name       = "High WAF Block Rate - ${var.environment}"
  description = "Alert when WAF block rate exceeds threshold"
  enabled    = true

  alert_type = "firewall_events_anomaly"

  email_integration {
    id = "email"
  }
}

# Notification Policy: SSL Certificate Expiring
resource "cloudflare_notification_policy" "ssl_expiring" {
  account_id = var.cloudflare_account_id
  name       = "SSL Certificate Expiring - ${var.environment}"
  description = "Alert when SSL certificate is expiring soon"
  enabled    = true

  alert_type = "ssl_verification_days_to_expiration"

  email_integration {
    id = "email"
  }

  filters {
    services = [var.domain]
  }
}

# Outputs
output "zone_id" {
  description = "Cloudflare Zone ID"
  value       = data.cloudflare_zone.main.id
}

output "zone_name" {
  description = "Zone name"
  value       = data.cloudflare_zone.main.name
}

output "nameservers" {
  description = "Cloudflare nameservers"
  value       = data.cloudflare_zone.main.name_servers
}

output "rate_limits" {
  description = "Rate limiting configuration"
  value = {
    api          = local.api_rate_limit
    login        = local.login_rate_limit
    registration = local.registration_rate_limit
    search       = local.search_rate_limit
    admin        = local.admin_rate_limit
  }
}

output "waf_mode" {
  description = "WAF mode (block or log)"
  value       = local.waf_mode
}

output "environment" {
  description = "Environment configuration"
  value       = var.environment
}

# Terraform State Notes
# --------------------
# This configuration should be applied separately for production and staging:
#
# Production:
#   terraform workspace select production
#   terraform apply -var="environment=production" -var="cloudflare_account_id=YOUR_ACCOUNT_ID"
#
# Staging:
#   terraform workspace select staging
#   terraform apply -var="environment=staging" -var="cloudflare_account_id=YOUR_ACCOUNT_ID"
#
# Environment Variables Required:
#   export CLOUDFLARE_API_TOKEN="your_api_token"
#   export TF_VAR_cloudflare_account_id="your_account_id"
#
# Never commit sensitive values to git!
