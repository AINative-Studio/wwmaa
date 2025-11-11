# Cloudflare WAF Configuration Guide

## Overview

This document provides complete setup and configuration instructions for Cloudflare Web Application Firewall (WAF) protecting the wwmaa.com application. The WAF provides protection against common web attacks, DDoS attacks, malicious bots, and rate-based abuse.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Cloudflare Setup](#initial-cloudflare-setup)
3. [Domain Configuration](#domain-configuration)
4. [SSL/TLS Configuration](#ssltls-configuration)
5. [WAF Managed Rulesets](#waf-managed-rulesets)
6. [Rate Limiting Rules](#rate-limiting-rules)
7. [Bot Protection](#bot-protection)
8. [DDoS Protection](#ddos-protection)
9. [Custom Firewall Rules](#custom-firewall-rules)
10. [Analytics and Logging](#analytics-and-logging)
11. [Monitoring and Alerts](#monitoring-and-alerts)
12. [Maintenance](#maintenance)

## Prerequisites

- Cloudflare account (Free or Pro plan recommended)
- Access to domain registrar for nameserver updates
- Railway backend with origin certificate capability
- Admin access to Cloudflare dashboard

## Initial Cloudflare Setup

### Step 1: Create Cloudflare Account

1. Go to https://dash.cloudflare.com/sign-up
2. Create account with admin email
3. Verify email address
4. Enable 2FA for security

### Step 2: Add Domain to Cloudflare

1. Log in to Cloudflare Dashboard
2. Click "Add a Site"
3. Enter domain: `wwmaa.com`
4. Select plan (Free or Pro)
5. Click "Add Site"

### Step 3: DNS Record Import

Cloudflare will automatically scan and import existing DNS records:

```
A     wwmaa.com              -> [Railway IP]        [Proxied]
CNAME www.wwmaa.com          -> wwmaa.com           [Proxied]
CNAME staging.wwmaa.com      -> [Railway Staging]  [Proxied]
A     @                      -> [Railway IP]        [Proxied]
```

Ensure all web traffic records are set to "Proxied" (orange cloud) to enable WAF protection.

### Step 4: Update Nameservers

1. Cloudflare will provide two nameservers:
   ```
   ns1.cloudflare.com
   ns2.cloudflare.com
   ```
2. Log in to your domain registrar (e.g., GoDaddy, Namecheap)
3. Update nameservers to Cloudflare's nameservers
4. Save changes
5. Wait for DNS propagation (typically 24-48 hours, often faster)

### Step 5: Verify Active Status

1. Return to Cloudflare Dashboard
2. Wait for status to change from "Pending" to "Active"
3. Verify DNS resolution:
   ```bash
   dig wwmaa.com
   nslookup wwmaa.com
   ```

## Domain Configuration

### Production Domain: wwmaa.com

**Configuration:**
- Proxied through Cloudflare: Yes
- SSL/TLS Mode: Full (Strict)
- WAF Mode: Block
- Bot Protection: Enabled
- Rate Limiting: Production limits

### Staging Domain: staging.wwmaa.com

**Configuration:**
- Proxied through Cloudflare: Yes
- SSL/TLS Mode: Full (Strict)
- WAF Mode: Log (initially), then Block
- Bot Protection: Challenge only
- Rate Limiting: Lower limits for testing

## SSL/TLS Configuration

See detailed guide in `/docs/security/ssl-tls-setup.md`

### Quick Setup:

1. Navigate to **SSL/TLS** → **Overview**
2. Select encryption mode: **Full (Strict)**
3. Enable settings:
   - Always Use HTTPS: On
   - Automatic HTTPS Rewrites: On
   - Minimum TLS Version: 1.2
   - TLS 1.3: Enabled
   - HSTS: Enabled (see SSL/TLS guide)

### Origin Certificate:

1. Go to **SSL/TLS** → **Origin Server**
2. Click "Create Certificate"
3. Use default settings (15 year validity)
4. Copy certificate and private key
5. Install on Railway backend (see SSL/TLS guide)

## WAF Managed Rulesets

Cloudflare provides multiple managed rulesets that protect against common vulnerabilities and attacks.

### Step 1: Enable OWASP Core Ruleset

1. Navigate to **Security** → **WAF**
2. Click **Managed Rules** tab
3. Find "Cloudflare OWASP Core Ruleset"
4. Toggle to **Enabled**
5. Set default action: **Block**

**Protection Coverage:**
- SQL Injection (SQLi)
- Cross-Site Scripting (XSS)
- Local File Inclusion (LFI)
- Remote File Inclusion (RFI)
- Remote Code Execution (RCE)
- PHP Injection
- Session Fixation
- HTTP Protocol Violations

**Configuration:**
```
Ruleset: Cloudflare OWASP Core Ruleset
Status: Enabled
Default Action: Block
Sensitivity: High
```

### Step 2: Enable Cloudflare Managed Ruleset

1. In **WAF** → **Managed Rules**
2. Find "Cloudflare Managed Ruleset"
3. Toggle to **Enabled**
4. Set default action: **Block**

**Protection Coverage:**
- Known CVE exploits
- Zero-day vulnerabilities
- Application-specific attacks
- Malicious payloads
- Directory traversal
- Command injection

**Configuration:**
```
Ruleset: Cloudflare Managed Ruleset
Status: Enabled
Default Action: Block
Auto-update: Enabled
```

### Step 3: Configure Rule Overrides (Optional)

For specific rules causing false positives:

1. Click on ruleset name
2. Find specific rule ID
3. Click "Configure"
4. Override action:
   - Block → Log (for testing)
   - Block → Challenge (less aggressive)
   - Disable (only if necessary)

**Example Override:**
```
Rule ID: 100001
Name: SQL Injection - UNION Attack
Override Action: Log
Reason: Testing database queries in staging
Environment: staging.wwmaa.com only
```

## Rate Limiting Rules

Protect against abuse and brute-force attacks with rate limiting.

### Navigation:

**Security** → **WAF** → **Rate Limiting Rules**

### Rule 1: General API Rate Limit

```
Rule Name: API Rate Limit
Description: Limit API requests to prevent abuse

Match:
  - URI Path: /api/*
  - Method: All

Rate:
  - Requests: 100 per minute
  - Period: 60 seconds
  - Counting Method: IP Address

Action:
  - Type: Block
  - Duration: 3600 seconds (1 hour)
  - Response Code: 429
  - Response Body: "Rate limit exceeded. Please try again later."
```

**Configuration Steps:**
1. Click "Create Rate Limiting Rule"
2. Name: "API Rate Limit"
3. Expression: `(http.request.uri.path contains "/api/")`
4. Characteristics: IP Address
5. Rate: 100 requests per 60 seconds
6. Action: Block for 3600 seconds
7. Save

### Rule 2: Login Endpoint Protection

```
Rule Name: Login Rate Limit
Description: Prevent brute-force login attacks

Match:
  - URI Path: /api/auth/login
  - Method: POST

Rate:
  - Requests: 5 per minute
  - Period: 60 seconds
  - Counting Method: IP Address

Action:
  - Type: Block
  - Duration: 1800 seconds (30 minutes)
  - Response Code: 429
```

**Expression:**
```
(http.request.uri.path eq "/api/auth/login" and http.request.method eq "POST")
```

### Rule 3: Registration Endpoint Protection

```
Rule Name: Registration Rate Limit
Description: Prevent automated account creation

Match:
  - URI Path: /api/auth/register
  - Method: POST

Rate:
  - Requests: 3 per minute
  - Period: 60 seconds
  - Counting Method: IP Address

Action:
  - Type: Block
  - Duration: 3600 seconds (1 hour)
```

**Expression:**
```
(http.request.uri.path eq "/api/auth/register" and http.request.method eq "POST")
```

### Rule 4: Search Rate Limit

```
Rule Name: Search Rate Limit
Description: Prevent search abuse and scraping

Match:
  - URI Path: /api/search/*
  - Method: All

Rate:
  - Requests: 10 per minute
  - Period: 60 seconds
  - Counting Method: IP Address

Action:
  - Type: Challenge (JS Challenge)
  - Duration: 1800 seconds (30 minutes)
```

**Expression:**
```
(http.request.uri.path contains "/api/search/")
```

### Rule 5: Admin Endpoint Protection

```
Rule Name: Admin Rate Limit
Description: Higher limits for admin users, still protected

Match:
  - URI Path: /api/admin/*
  - Method: All

Rate:
  - Requests: 200 per minute
  - Period: 60 seconds
  - Counting Method: IP Address

Action:
  - Type: Challenge (Managed Challenge)
  - Duration: 600 seconds (10 minutes)
```

**Expression:**
```
(http.request.uri.path contains "/api/admin/")
```

### Rule 6: Password Reset Protection

```
Rule Name: Password Reset Rate Limit
Description: Prevent password reset abuse

Match:
  - URI Path: /api/auth/reset-password
  - Method: POST

Rate:
  - Requests: 3 per 5 minutes
  - Period: 300 seconds
  - Counting Method: IP Address

Action:
  - Type: Block
  - Duration: 3600 seconds (1 hour)
```

## Bot Protection

Protect against automated attacks and malicious bots.

### Navigate to Bot Protection:

**Security** → **Bots**

### Free Plan: Bot Fight Mode

1. Toggle "Bot Fight Mode" to **On**
2. Configuration:
   ```
   Definitely Automated: Block
   Verified Bots: Allow (Google, Bing, etc.)
   Likely Automated: Challenge
   ```

### Pro Plan and Above: Super Bot Fight Mode

1. Enable "Super Bot Fight Mode"
2. Configure bot score threshold: 30 (lower = more strict)
3. Actions:
   - Definitely Automated: Block
   - Likely Automated: Managed Challenge
   - Verified Bots: Allow

### Allow Verified Bots

Ensure legitimate crawlers can access public content:

```
Allowed Bots:
- Googlebot
- Bingbot
- LinkedInBot
- FacebookExternalHit
- WhatsApp
```

Navigate to **Security** → **Bots** → **Configure** → **Verified Bot Allow List**

## DDoS Protection

Cloudflare provides automatic DDoS protection.

### HTTP DDoS Attack Protection

1. Navigate to **Security** → **DDoS**
2. Enable "HTTP DDoS Attack Protection"
3. Sensitivity: **High**
4. Action: **Block**

### Network-layer DDoS Protection

Automatically enabled on all Cloudflare plans.

**Features:**
- SYN flood protection
- UDP flood protection
- ACK flood protection
- Volumetric attack mitigation

### Advanced TCP Protection (Pro+ plans)

1. Navigate to **Security** → **DDoS** → **Advanced TCP Protection**
2. Enable for prefixes
3. Configure sensitivity

### DDoS Alerts

1. Navigate to **Notifications**
2. Add notification: "DDoS Attack Alert"
3. Delivery method: Email + Webhook (Slack/PagerDuty)
4. Threshold: Any attack detected

## Custom Firewall Rules

Create custom rules for specific security requirements.

### Navigate to:

**Security** → **WAF** → **Custom Rules**

### Rule 1: Block Known Malicious IPs

```
Rule Name: Block Malicious IPs
Description: Block IPs from threat intelligence feeds

Expression:
(ip.src in $malicious_ips_list)

Action: Block
```

**Setup:**
1. Create IP List: **Security** → **WAF** → **Tools** → **Lists**
2. Name: `malicious_ips_list`
3. Add IPs manually or via API
4. Create firewall rule referencing the list

### Rule 2: Challenge Sensitive Endpoints

```
Rule Name: Challenge Sensitive Endpoints
Description: Add extra verification for admin and payment pages

Expression:
(http.request.uri.path contains "/api/admin" or
 http.request.uri.path contains "/api/payment" or
 http.request.uri.path contains "/api/billing")

Action: Managed Challenge
```

**Configuration:**
1. Click "Create Firewall Rule"
2. Name: "Challenge Sensitive Endpoints"
3. Add expression (use Expression Editor)
4. Action: Managed Challenge
5. Save

### Rule 3: Geo-Blocking (Optional)

```
Rule Name: Geo-block High-Risk Countries
Description: Block traffic from high-risk regions (adjust as needed)

Expression:
(ip.geoip.country in {"CN" "RU" "KP"}) and
not (ip.src in $trusted_ips)

Action: Block
```

**Note:** Only implement geo-blocking if required by security policy. Review legal and business implications.

### Rule 4: Block Requests Without User-Agent

```
Rule Name: Block Missing User-Agent
Description: Block requests without User-Agent header (likely bots)

Expression:
(http.user_agent eq "")

Action: Block
```

### Rule 5: Block Suspicious Query Strings

```
Rule Name: Block SQL Injection in Query Strings
Description: Block obvious SQL injection attempts

Expression:
(http.request.uri.query contains "UNION SELECT" or
 http.request.uri.query contains "DROP TABLE" or
 http.request.uri.query contains "1=1" or
 http.request.uri.query contains "OR 1=1")

Action: Block
```

### Rule 6: Challenge Unusual Accept Headers

```
Rule Name: Challenge Unusual Accept Headers
Description: Verify requests with non-browser Accept headers

Expression:
(not http.request.headers["accept"][0] contains "text/html" and
 not http.request.uri.path contains "/api/")

Action: JS Challenge
```

### Rule 7: Protect Against Scanner Tools

```
Rule Name: Block Security Scanners
Description: Block common security scanning tools

Expression:
(http.user_agent contains "sqlmap" or
 http.user_agent contains "nikto" or
 http.user_agent contains "nmap" or
 http.user_agent contains "masscan" or
 http.user_agent contains "acunetix")

Action: Block
```

## Analytics and Logging

### Enable Cloudflare Analytics

1. Navigate to **Analytics & Logs** → **Security**
2. Review dashboards:
   - WAF Events
   - Rate Limiting Events
   - Bot Score Distribution
   - Firewall Events by Action

### Configure Logpush

**For Pro+ Plans:**

1. Navigate to **Analytics & Logs** → **Logpush**
2. Click "Add Logpush Job"
3. Dataset: **HTTP Requests** or **Firewall Events**
4. Destination options:
   - AWS S3
   - Google Cloud Storage
   - Azure Blob Storage
   - Datadog
   - Splunk

**Example S3 Configuration:**
```
Destination: S3
Bucket: s3://wwmaa-cloudflare-logs
Region: us-west-2
Path: /waf-logs/
Format: JSON
Frequency: Every 5 minutes
```

### Logpull API (All Plans)

For programmatic log access:

```bash
curl -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}/logs/received?start=2025-01-01T00:00:00Z&end=2025-01-01T01:00:00Z" \
  -H "X-Auth-Email: your-email@example.com" \
  -H "X-Auth-Key: your-api-key"
```

### Forward Logs to Monitoring Systems

**Option 1: Cloudflare Workers**

Create a Worker to forward WAF events to external systems:

```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const response = await fetch(request)

  // Log to external system
  if (request.cf && request.cf.threatScore > 10) {
    await fetch('https://your-logging-endpoint.com/waf-event', {
      method: 'POST',
      body: JSON.stringify({
        timestamp: Date.now(),
        ip: request.headers.get('CF-Connecting-IP'),
        country: request.cf.country,
        threatScore: request.cf.threatScore,
        path: new URL(request.url).pathname
      })
    })
  }

  return response
}
```

**Option 2: Webhook Notifications**

1. Navigate to **Notifications**
2. Add notification for "Firewall Events"
3. Delivery: Webhook
4. URL: Your Slack/Discord/PagerDuty webhook

## Monitoring and Alerts

### Create Alert Policies

#### Alert 1: High Rate of Blocked Requests

```
Alert Name: High WAF Block Rate
Description: Triggered when block rate exceeds threshold

Condition:
  - Blocked requests > 1000 per minute
  - Duration: 5 minutes

Actions:
  - Email: security@wwmaa.com
  - Slack: #security channel
  - PagerDuty: On-call engineer
```

#### Alert 2: DDoS Attack Detected

```
Alert Name: DDoS Attack Detected
Description: Immediate notification of DDoS attack

Condition:
  - DDoS attack detected by Cloudflare

Actions:
  - Email: security@wwmaa.com + ops@wwmaa.com
  - SMS: Security team lead
  - PagerDuty: P1 incident
  - Slack: #incidents channel
```

#### Alert 3: Repeated IP Blocks

```
Alert Name: Repeated IP Blocks
Description: Same IP getting blocked multiple times

Condition:
  - Single IP blocked > 10 times in 10 minutes

Actions:
  - Log to security dashboard
  - Email: security@wwmaa.com
  - Consider adding to permanent blocklist
```

#### Alert 4: New Attack Pattern

```
Alert Name: New Attack Pattern Detected
Description: Unusual spike in specific WAF rule triggers

Condition:
  - Single WAF rule triggered > 100 times in 5 minutes
  - Rule not typically triggered

Actions:
  - Email: security@wwmaa.com
  - Slack: #security channel
  - Create incident ticket
```

### Create Monitoring Dashboard

**Recommended Metrics:**

1. **Request Volume**
   - Total requests per minute
   - Requests by country
   - Requests by endpoint

2. **Security Events**
   - WAF blocks per minute
   - Rate limit triggers
   - Bot challenges issued
   - Challenge pass/fail rate

3. **Attack Types**
   - SQL injection attempts
   - XSS attempts
   - DDoS events
   - Bot attacks

4. **Performance Impact**
   - Challenge solve time
   - Average response time
   - Cache hit ratio
   - Origin server load

**Dashboard Tools:**
- Cloudflare native dashboard
- Grafana with Cloudflare API
- Datadog integration
- Custom internal dashboard

## Maintenance

### Daily Tasks

- Monitor WAF dashboard for anomalies
- Review blocked request spikes
- Check alert notifications
- Verify system health

### Weekly Tasks

See `/docs/security/waf-review-schedule.md` for detailed weekly review process.

**Weekly Review Checklist:**
- [ ] Review WAF analytics (blocked requests, top rules, top IPs)
- [ ] Check for false positives in logs
- [ ] Update malicious IP blocklist
- [ ] Review rate limiting effectiveness
- [ ] Check bot protection metrics
- [ ] Update custom firewall rules if needed
- [ ] Review and acknowledge security alerts
- [ ] Document any configuration changes

### Monthly Tasks

- Review and update geo-blocking rules
- Audit custom firewall rules for effectiveness
- Review rate limiting thresholds (adjust if needed)
- Check for new Cloudflare managed ruleset updates
- Review SSL/TLS configuration and certificate validity
- Test incident response procedures
- Update documentation with lessons learned

### Quarterly Tasks

- Full security audit of WAF configuration
- Penetration testing (see `/docs/security/waf-testing.md`)
- Review and update incident response playbook
- Training for new security team members
- Review compliance with security policies
- Evaluate Cloudflare plan (upgrade if needed)

### Emergency Procedures

**Under Active Attack:**

1. Verify attack via Cloudflare dashboard
2. Enable "I'm Under Attack Mode" (temporary):
   - Navigate to **Security** → **Settings**
   - Toggle "I'm Under Attack Mode" to **On**
   - This shows JavaScript challenge to all visitors
3. Monitor attack mitigation
4. Document attack details for post-mortem
5. Disable "I'm Under Attack Mode" when attack subsides

**False Positive Causing Outage:**

1. Identify problematic WAF rule via logs
2. Navigate to rule configuration
3. Change action to "Log" temporarily
4. Monitor for 30 minutes
5. If issue resolved, investigate proper fix
6. Update rule with proper exception or disable if necessary
7. Document incident and resolution

## Environment-Specific Configuration

### Production (wwmaa.com)

```yaml
Domain: wwmaa.com
SSL/TLS Mode: Full (Strict)
WAF Rulesets:
  - OWASP Core Ruleset: Enabled (Block)
  - Cloudflare Managed Ruleset: Enabled (Block)
Rate Limiting:
  - API: 100 req/min
  - Login: 5 req/min
  - Registration: 3 req/min
  - Search: 10 req/min
  - Admin: 200 req/min
Bot Protection: Enabled (Block/Challenge)
DDoS Protection: High Sensitivity
Custom Rules: All enabled (Block mode)
Geo-Blocking: As configured
I'm Under Attack Mode: Off (unless active incident)
```

### Staging (staging.wwmaa.com)

```yaml
Domain: staging.wwmaa.com
SSL/TLS Mode: Full (Strict)
WAF Rulesets:
  - OWASP Core Ruleset: Enabled (Log initially, then Block)
  - Cloudflare Managed Ruleset: Enabled (Log initially, then Block)
Rate Limiting:
  - API: 10 req/min (lower for testing)
  - Login: 10 req/min (higher for testing)
  - Registration: 10 req/min (higher for testing)
  - Search: 20 req/min
  - Admin: 50 req/min
Bot Protection: Challenge only (not block)
DDoS Protection: Medium Sensitivity
Custom Rules: Log mode (for testing)
Geo-Blocking: Disabled
I'm Under Attack Mode: Off
```

## Testing and Validation

See `/docs/security/waf-testing.md` for complete testing procedures.

**Quick Validation:**

1. **Test SSL/TLS:**
   ```bash
   curl -I https://wwmaa.com
   # Should return 200 with proper security headers
   ```

2. **Test WAF (SQL Injection):**
   ```bash
   curl "https://wwmaa.com/api/search?q=1' OR '1'='1"
   # Should return 403 Forbidden
   ```

3. **Test Rate Limiting:**
   ```bash
   for i in {1..101}; do curl https://wwmaa.com/api/users; done
   # Should return 429 after 100 requests
   ```

4. **Check SSL Labs Rating:**
   - Go to: https://www.ssllabs.com/ssltest/
   - Enter: wwmaa.com
   - Target: A+ rating

## Troubleshooting

### Issue: Legitimate Traffic Being Blocked

**Diagnosis:**
1. Check WAF Events in Analytics
2. Identify rule causing blocks
3. Review request patterns

**Solution:**
- Add IP to allowlist (IP Access Rules)
- Create exception for specific rule
- Adjust rule sensitivity
- Change action from Block to Challenge

### Issue: Rate Limiting Too Aggressive

**Diagnosis:**
1. Review Rate Limiting Events
2. Check if legitimate users affected
3. Analyze request patterns

**Solution:**
- Increase rate limit threshold
- Adjust time window
- Add exceptions for known IPs
- Use Challenge instead of Block

### Issue: False Positives from OWASP Rules

**Diagnosis:**
1. Review OWASP ruleset events
2. Identify specific rule ID
3. Analyze blocked requests

**Solution:**
- Create rule exception for specific patterns
- Override rule action to Log or Challenge
- Disable specific rule if necessary (last resort)
- Report false positive to Cloudflare

### Issue: Bot Protection Blocking APIs

**Diagnosis:**
1. Check Bot Score of blocked requests
2. Review User-Agent patterns

**Solution:**
- Create firewall rule to bypass bot protection for API endpoints
- Use verified API authentication (tokens)
- Add API client IPs to allowlist
- Adjust bot score threshold

## Security Best Practices

1. **Never disable WAF entirely** - Use Log mode for testing instead
2. **Review logs regularly** - Catch issues early
3. **Keep allowlists minimal** - Only add trusted IPs
4. **Use Managed Challenges** - Better UX than CAPTCHA
5. **Test in staging first** - Validate rules before production
6. **Document all changes** - Maintain audit trail
7. **Monitor actively** - Set up proper alerting
8. **Regular security reviews** - Weekly and monthly audits
9. **Stay updated** - Review Cloudflare security blog
10. **Have rollback plan** - Know how to quickly disable problematic rules

## Additional Resources

- [Cloudflare WAF Documentation](https://developers.cloudflare.com/waf/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Cloudflare Security Center](https://developers.cloudflare.com/security-center/)
- [Rate Limiting Best Practices](https://developers.cloudflare.com/waf/rate-limiting-rules/)
- [Bot Management](https://developers.cloudflare.com/bots/)

## Support and Escalation

**Cloudflare Support:**
- Free Plan: Community forums
- Pro Plan: Standard support
- Business+ Plan: 24/7 support

**Internal Contacts:**
- Security Team Lead: security@wwmaa.com
- DevOps Team: ops@wwmaa.com
- On-Call Engineer: via PagerDuty

**Emergency Contact:**
- Cloudflare Enterprise Support (if applicable)
- DDoS Mitigation Team (Business+ plans)

## Compliance and Audit

This WAF configuration supports compliance with:
- OWASP Top 10 protection
- PCI DSS requirements (for payment processing)
- GDPR (with proper logging and data handling)
- SOC 2 (with audit logs and access controls)

Maintain documentation of:
- Configuration changes
- Security incidents
- Review schedules
- Audit logs

---

**Document Version:** 1.0
**Last Updated:** 2025-01-10
**Maintained By:** Security Team
**Review Schedule:** Monthly
