# Cloudflare WAF Quick Start Guide

**5-Minute Setup Overview for wwmaa.com**

## Prerequisites Checklist

```
□ Cloudflare account created
□ Credit card on file (for paid features if needed)
□ Domain registrar access (to update nameservers)
□ Railway backend access (to install SSL certificate)
□ 2-3 hours available for initial setup
```

## Quick Setup (Step-by-Step)

### Step 1: Add Domain to Cloudflare (5 minutes)

1. Go to https://dash.cloudflare.com
2. Click "Add a Site"
3. Enter: `wwmaa.com`
4. Select plan: **Free** (can upgrade later)
5. Click "Add Site"

### Step 2: Update Nameservers (5 minutes + 24h propagation)

1. Cloudflare shows two nameservers:
   ```
   ns1.cloudflare.com
   ns2.cloudflare.com
   ```
2. Log in to domain registrar (GoDaddy, Namecheap, etc.)
3. Find DNS/Nameserver settings
4. Replace existing nameservers with Cloudflare's
5. Save changes
6. Wait for DNS propagation (up to 24 hours)

### Step 3: Configure SSL/TLS (10 minutes)

1. In Cloudflare Dashboard → **SSL/TLS** → **Overview**
2. Select: **Full (Strict)**
3. Navigate to **SSL/TLS** → **Edge Certificates**
4. Enable:
   - ✓ Always Use HTTPS
   - ✓ Automatic HTTPS Rewrites
   - ✓ TLS 1.3
5. Set Minimum TLS Version: **1.2**

### Step 4: Generate Origin Certificate (5 minutes)

1. Go to **SSL/TLS** → **Origin Server**
2. Click "Create Certificate"
3. Leave default settings (15 years, both *.wwmaa.com and wwmaa.com)
4. Click "Create"
5. Copy both:
   - Origin Certificate
   - Private Key
6. Save to password manager (DO NOT COMMIT TO GIT)

### Step 5: Install Certificate on Railway (10 minutes)

1. Log in to Railway Dashboard
2. Select project: **wwmaa**
3. Select service: **backend**
4. Go to **Variables** tab
5. Add variables:
   ```
   SSL_CERTIFICATE=[paste full certificate]
   SSL_PRIVATE_KEY=[paste full private key]
   USE_SSL=true
   ```
6. Restart service

### Step 6: Enable WAF Managed Rulesets (5 minutes)

1. Navigate to **Security** → **WAF** → **Managed Rules**
2. Enable:
   - ✓ **Cloudflare OWASP Core Ruleset** → Action: Block
   - ✓ **Cloudflare Managed Ruleset** → Action: Block
3. Click "Deploy"

### Step 7: Configure Rate Limiting (15 minutes)

Create 5 rate limiting rules:

**Rule 1: API General**
- Go to **Security** → **WAF** → **Rate Limiting Rules**
- Click "Create"
- Name: `API Rate Limit`
- Expression: `(http.request.uri.path contains "/api/")`
- Requests: `100` per `60` seconds
- Action: `Block` for `3600` seconds
- Save

**Rule 2: Login**
- Name: `Login Rate Limit`
- Expression: `(http.request.uri.path eq "/api/auth/login" and http.request.method eq "POST")`
- Requests: `5` per `60` seconds
- Action: `Block` for `1800` seconds
- Save

**Rule 3: Registration**
- Name: `Registration Rate Limit`
- Expression: `(http.request.uri.path eq "/api/auth/register" and http.request.method eq "POST")`
- Requests: `3` per `60` seconds
- Action: `Block` for `3600` seconds
- Save

**Rule 4: Search**
- Name: `Search Rate Limit`
- Expression: `(http.request.uri.path contains "/api/search/")`
- Requests: `10` per `60` seconds
- Action: `Challenge` for `1800` seconds
- Save

**Rule 5: Password Reset**
- Name: `Password Reset Rate Limit`
- Expression: `(http.request.uri.path eq "/api/auth/reset-password" and http.request.method eq "POST")`
- Requests: `3` per `300` seconds
- Action: `Block` for `3600` seconds
- Save

### Step 8: Enable Bot Protection (3 minutes)

1. Navigate to **Security** → **Bots**
2. Toggle **Bot Fight Mode** to **ON**
3. Verify settings:
   - Definitely Automated: Block
   - Verified Bots: Allow

### Step 9: Create Custom Firewall Rules (15 minutes)

Go to **Security** → **WAF** → **Custom Rules** → **Create Firewall Rule**

**Rule 1: Challenge Sensitive Endpoints**
- Name: `Challenge Sensitive Endpoints`
- Expression:
  ```
  (http.request.uri.path contains "/api/admin" or
   http.request.uri.path contains "/api/payment" or
   http.request.uri.path contains "/api/billing")
  ```
- Action: `Managed Challenge`
- Deploy

**Rule 2: Block Missing User-Agent**
- Name: `Block Missing User-Agent`
- Expression: `(http.user_agent eq "")`
- Action: `Block`
- Deploy

**Rule 3: Block Security Scanners**
- Name: `Block Security Scanners`
- Expression:
  ```
  (http.user_agent contains "sqlmap" or
   http.user_agent contains "nikto" or
   http.user_agent contains "nmap" or
   http.user_agent contains "masscan" or
   http.user_agent contains "acunetix")
  ```
- Action: `Block`
- Deploy

### Step 10: Enable DDoS Protection (2 minutes)

1. Navigate to **Security** → **DDoS**
2. Verify **HTTP DDoS Attack Protection** is enabled
3. Set Sensitivity: **High**

### Step 11: Set Up Alerts (10 minutes)

1. Go to **Notifications**
2. Click "Add"
3. Create three alerts:

**Alert 1: DDoS Attack**
- Type: "DDoS Attack"
- Delivery: Email
- Recipients: `security@wwmaa.com`

**Alert 2: SSL Certificate Expiring**
- Type: "SSL Certificate Expiring"
- Notification: 30 days before
- Delivery: Email
- Recipients: `ops@wwmaa.com`

**Alert 3: High Security Event Volume**
- Type: "Firewall Events Anomaly"
- Delivery: Email
- Recipients: `security@wwmaa.com`

### Step 12: Enable HSTS (5 minutes)

1. Navigate to **SSL/TLS** → **Edge Certificates**
2. Find "HTTP Strict Transport Security (HSTS)"
3. Click "Enable HSTS"
4. Configure:
   - Max Age: `12 months` (31536000 seconds)
   - Include Subdomains: ✓ Yes
   - Preload: ☐ No (enable after 30 days)
   - No-Sniff Header: ✓ Yes
5. Accept warning and enable

## Verification Checklist

After setup, verify everything works:

```bash
# Test 1: HTTPS works
curl -I https://wwmaa.com
# Expected: 200 OK

# Test 2: HTTP redirects to HTTPS
curl -I http://wwmaa.com
# Expected: 301/302 redirect to https://

# Test 3: HSTS header present
curl -I https://wwmaa.com | grep -i strict-transport-security
# Expected: strict-transport-security header

# Test 4: WAF blocks SQL injection
curl "https://wwmaa.com/api/search?q=1' OR '1'='1"
# Expected: 403 Forbidden

# Test 5: Rate limiting works (after 101 requests)
for i in {1..101}; do curl -s -o /dev/null -w "%{http_code}\n" https://wwmaa.com/api/health; done
# Expected: First 100 return 200, then 429
```

**Online Tests:**
1. SSL Labs: https://www.ssllabs.com/ssltest/ → Enter `wwmaa.com` → Target: A+
2. Security Headers: https://securityheaders.com/ → Enter `wwmaa.com` → Check score

## Common Issues and Quick Fixes

### Issue: "Too many redirects" error
**Fix:** Check SSL/TLS mode is "Full (Strict)", not "Flexible"

### Issue: Site not accessible after nameserver change
**Fix:** Wait 24 hours for DNS propagation. Check status in Cloudflare dashboard.

### Issue: 526 error (Invalid SSL Certificate)
**Fix:** Verify origin certificate installed correctly on Railway backend

### Issue: Legitimate users getting blocked
**Fix:** Go to Security → Events → Find rule → Create exception or adjust sensitivity

## Terraform Alternative (For DevOps Teams)

If you prefer infrastructure-as-code:

```bash
# 1. Set up Terraform
cd /Users/aideveloper/Desktop/wwmaa/infrastructure/cloudflare
export CLOUDFLARE_API_TOKEN="your_token"
export TF_VAR_cloudflare_account_id="your_account_id"

# 2. Initialize
terraform init

# 3. Review changes
terraform plan

# 4. Apply configuration
terraform apply

# Done! All rules and settings configured automatically.
```

See `/infrastructure/cloudflare/README.md` for detailed Terraform instructions.

## Next Steps After Setup

### Week 1: Monitoring Phase
- Monitor Cloudflare Analytics daily
- Check for false positives
- Adjust rules if needed
- Document any issues

### Week 2-4: Optimization Phase
- Review weekly analytics reports
- Fine-tune rate limiting thresholds
- Add specific IPs to blocklist if needed
- Consider enabling HSTS preload (after 30 days)

### Month 2+: Maintenance Phase
- Follow weekly review schedule
- Conduct monthly maintenance
- Plan quarterly penetration test
- Keep documentation updated

## Complete Documentation

For detailed information, see:

- **Setup:** `/docs/security/waf-configuration.md`
- **SSL/TLS:** `/docs/security/ssl-tls-setup.md`
- **Testing:** `/docs/security/waf-testing.md`
- **Incidents:** `/docs/security/waf-incident-response.md`
- **Reviews:** `/docs/security/waf-review-schedule.md`
- **Summary:** `/docs/US-068-IMPLEMENTATION-SUMMARY.md`

## Support

**Issues during setup?**
- Review troubleshooting sections in main documentation
- Check Cloudflare Community: https://community.cloudflare.com/
- Contact: security@wwmaa.com

**In case of security incident:**
- Follow incident response playbook: `/docs/security/waf-incident-response.md`
- Alert on-call engineer via PagerDuty
- Post in #incidents Slack channel

---

**Estimated Total Setup Time:** 90-120 minutes
**Deployment Window:** Low-traffic period recommended
**Rollback Plan:** Disable WAF rules individually if issues arise

**Last Updated:** 2025-01-10
**Version:** 1.0
