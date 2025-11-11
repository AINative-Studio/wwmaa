# Cloudflare WAF Terraform Configuration

This directory contains Terraform configuration for managing Cloudflare WAF settings for wwmaa.com.

## Prerequisites

1. **Terraform** installed (>= 1.0)
   ```bash
   brew install terraform
   ```

2. **Cloudflare Account** with API token
   - Create API token at: https://dash.cloudflare.com/profile/api-tokens
   - Required permissions:
     - Zone: Read, Edit
     - Zone WAF: Read, Edit
     - Zone Settings: Read, Edit
     - Account Settings: Read
     - Account Firewall Access Rules: Read, Edit

3. **Cloudflare Zone** for wwmaa.com already created

## Setup

### 1. Set Environment Variables

```bash
# Cloudflare API Token (required)
export CLOUDFLARE_API_TOKEN="your_cloudflare_api_token_here"

# Cloudflare Account ID (required)
export TF_VAR_cloudflare_account_id="your_cloudflare_account_id"

# Optional: Set environment (defaults to production)
export TF_VAR_environment="production"  # or "staging"
```

**Security Note:** Never commit API tokens to git! Always use environment variables or a secrets manager.

### 2. Initialize Terraform

```bash
cd infrastructure/cloudflare
terraform init
```

### 3. Review Configuration

```bash
# View what will be created
terraform plan
```

### 4. Apply Configuration

```bash
# Apply changes
terraform apply

# Or with auto-approve (use with caution)
terraform apply -auto-approve
```

## Usage

### Managing Multiple Environments

Use Terraform workspaces to manage separate production and staging configurations:

```bash
# Create and switch to production workspace
terraform workspace new production
terraform workspace select production

# Apply production configuration
terraform apply -var="environment=production"

# Create and switch to staging workspace
terraform workspace new staging
terraform workspace select staging

# Apply staging configuration
terraform apply -var="environment=staging"
```

### Updating Configuration

1. Edit `waf.tf` with your changes
2. Review changes: `terraform plan`
3. Apply changes: `terraform apply`
4. Commit configuration to git (never commit sensitive data)

### Viewing Current Configuration

```bash
# Show current state
terraform show

# List resources
terraform state list

# View specific resource
terraform state show cloudflare_rate_limit.api_general
```

### Destroying Resources (Use with Caution!)

```bash
# Destroy all managed resources
terraform destroy

# This will remove ALL WAF configuration!
# Only use in development/testing environments
```

## Configuration Details

### SSL/TLS Settings

- Mode: Full (Strict)
- Minimum TLS: 1.2
- TLS 1.3: Enabled
- HSTS: Enabled with 12-month max-age
- Always Use HTTPS: Enabled
- Automatic HTTPS Rewrites: Enabled

### Rate Limiting

**Production:**
- API General: 100 requests/minute
- Login: 5 requests/minute
- Registration: 3 requests/minute
- Search: 10 requests/minute
- Password Reset: 3 requests/5 minutes

**Staging:**
- API General: 10 requests/minute
- Login: 10 requests/minute
- Registration: 10 requests/minute
- Search: 20 requests/minute
- Password Reset: 3 requests/5 minutes

### Custom Firewall Rules

1. Block Malicious IPs (from IP list)
2. Challenge Sensitive Endpoints (admin, payment, billing)
3. Block Missing User-Agent
4. Block Security Scanners
5. Block SQL Injection Patterns
6. Allow Trusted IPs (skip WAF)

### Managed Rulesets

- OWASP Core Ruleset (enabled)
- HTTP DDoS Attack Protection (enabled)

### Bot Management

- Bot Fight Mode (enabled in production)
- JavaScript challenges for suspected bots
- Auto-update bot detection models

## IP List Management

IP lists (malicious IPs, trusted IPs) should be managed through:

1. **Cloudflare Dashboard**: Security → WAF → Tools → Lists
2. **Cloudflare API**: For programmatic updates
3. **Terraform**: For infrastructure-as-code (if storing non-sensitive IPs)

### Adding IPs via Cloudflare API

```bash
# Add IP to malicious list
curl -X POST "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/rules/lists/${LIST_ID}/items" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '[
    {
      "ip": "1.2.3.4",
      "comment": "Blocked during incident INC-12345"
    }
  ]'

# Remove IP from list
curl -X DELETE "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/rules/lists/${LIST_ID}/items" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{
    "items": [
      {"id": "item_id_to_remove"}
    ]
  }'
```

## Troubleshooting

### Issue: "Error: Invalid API Token"

**Solution:** Verify your API token has correct permissions and is set in environment:
```bash
echo $CLOUDFLARE_API_TOKEN
```

### Issue: "Error: Zone not found"

**Solution:** Ensure wwmaa.com zone exists in Cloudflare and domain variable is correct:
```bash
terraform apply -var="domain=wwmaa.com"
```

### Issue: "Error: Account ID required"

**Solution:** Set account ID environment variable:
```bash
export TF_VAR_cloudflare_account_id="your_account_id"
```

### Issue: Rate limit already exists

**Solution:** Import existing rate limit into Terraform state:
```bash
terraform import cloudflare_rate_limit.api_general <zone_id>/<rate_limit_id>
```

### Issue: Changes not applying

**Solution:** Check for drift between Terraform state and actual configuration:
```bash
terraform refresh
terraform plan
```

## State Management

### Local State (Default)

By default, Terraform stores state locally in `terraform.tfstate`. This is suitable for:
- Development environments
- Single-user management
- Testing

**Backup:** Always commit `terraform.tfstate` to secure, private storage (NOT public git repos)

### Remote State (Recommended for Production)

For team collaboration and production use, configure remote state backend:

**Option 1: AWS S3**

Uncomment backend configuration in `waf.tf`:

```hcl
backend "s3" {
  bucket = "wwmaa-terraform-state"
  key    = "cloudflare/waf/terraform.tfstate"
  region = "us-west-2"
  encrypt = true
  dynamodb_table = "terraform-state-lock"  # For state locking
}
```

**Option 2: Terraform Cloud**

```hcl
backend "remote" {
  organization = "wwmaa"

  workspaces {
    name = "cloudflare-waf-production"
  }
}
```

**Option 3: HashiCorp Consul**

```hcl
backend "consul" {
  address = "consul.example.com:8500"
  scheme  = "https"
  path    = "terraform/wwmaa/cloudflare/waf"
}
```

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/terraform-cloudflare.yml`:

```yaml
name: Terraform Cloudflare WAF

on:
  push:
    branches:
      - main
    paths:
      - 'infrastructure/cloudflare/**'
  pull_request:
    paths:
      - 'infrastructure/cloudflare/**'

jobs:
  terraform:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.0

      - name: Terraform Init
        working-directory: infrastructure/cloudflare
        run: terraform init
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}

      - name: Terraform Validate
        working-directory: infrastructure/cloudflare
        run: terraform validate

      - name: Terraform Plan
        working-directory: infrastructure/cloudflare
        run: terraform plan
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          TF_VAR_cloudflare_account_id: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          TF_VAR_environment: production

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        working-directory: infrastructure/cloudflare
        run: terraform apply -auto-approve
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          TF_VAR_cloudflare_account_id: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          TF_VAR_environment: production
```

**Required GitHub Secrets:**
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

## Best Practices

1. **Version Control:**
   - Commit `.tf` files to git
   - NEVER commit `.tfstate` files to public repos
   - NEVER commit API tokens or secrets
   - Use `.gitignore` for sensitive files

2. **Testing:**
   - Always run `terraform plan` before `apply`
   - Test in staging environment first
   - Use workspaces for multiple environments

3. **Security:**
   - Use API tokens with minimum required permissions
   - Rotate API tokens regularly
   - Use remote state with encryption
   - Enable state locking to prevent concurrent modifications

4. **Documentation:**
   - Document all configuration changes
   - Update this README with new resources
   - Maintain change log

5. **Monitoring:**
   - Review Terraform state regularly
   - Monitor for configuration drift
   - Set up alerts for unauthorized changes

## Maintenance

### Regular Tasks

**Weekly:**
- Review and update IP lists
- Check for new Cloudflare provider versions
- Review rate limiting effectiveness

**Monthly:**
- Update Terraform provider version
- Review and optimize rules
- Check for deprecated resources

**Quarterly:**
- Full configuration audit
- Review security best practices
- Update documentation

## Additional Resources

- [Cloudflare Terraform Provider Documentation](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)
- [Cloudflare API Documentation](https://developers.cloudflare.com/api/)
- [WAF Configuration Guide](../../docs/security/waf-configuration.md)

## Support

For issues with:
- **Terraform configuration**: Contact DevOps team
- **Cloudflare WAF**: See [WAF Configuration Guide](../../docs/security/waf-configuration.md)
- **Security incidents**: See [Incident Response Playbook](../../docs/security/waf-incident-response.md)

---

**Last Updated:** 2025-01-10
**Maintained By:** DevOps Team
**Review Schedule:** Quarterly
