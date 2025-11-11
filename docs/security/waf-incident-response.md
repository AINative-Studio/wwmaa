# WAF Incident Response Playbook

## Overview

This playbook provides step-by-step procedures for responding to security incidents related to the Cloudflare Web Application Firewall (WAF) protecting wwmaa.com. It covers incident detection, analysis, response, mitigation, and post-incident activities.

## Table of Contents

1. [Incident Classification](#incident-classification)
2. [Response Team and Contacts](#response-team-and-contacts)
3. [Incident Response Workflow](#incident-response-workflow)
4. [Common Incident Scenarios](#common-incident-scenarios)
5. [Investigation Procedures](#investigation-procedures)
6. [Mitigation Actions](#mitigation-actions)
7. [Communication Protocols](#communication-protocols)
8. [Post-Incident Activities](#post-incident-activities)
9. [Escalation Procedures](#escalation-procedures)
10. [Tools and Resources](#tools-and-resources)

## Incident Classification

### Severity Levels

**P1 - Critical (Response Time: Immediate)**
- Active DDoS attack affecting availability
- Zero-day vulnerability being actively exploited
- Complete WAF failure exposing origin
- Data breach or unauthorized access detected
- Multiple security systems compromised

**P2 - High (Response Time: 15 minutes)**
- Sustained attack blocked by WAF but causing performance issues
- Multiple WAF rules failing
- High rate of blocked requests (>10,000/min)
- Suspicious activity from multiple IPs
- Critical false positive blocking legitimate users

**P3 - Medium (Response Time: 1 hour)**
- Single WAF rule malfunction
- Moderate attack attempts (blocked successfully)
- False positive affecting small user subset
- Unusual traffic patterns
- Rate limiting issues

**P4 - Low (Response Time: 4 hours)**
- Single blocked request requiring investigation
- Configuration drift detected
- Minor false positive
- Routine security alerts
- Documentation needed

### Incident Types

**Attack-Related:**
- DDoS Attack
- Application-layer attack (SQL injection, XSS)
- Bot attack / scraping attempt
- Brute force attack
- Zero-day exploitation attempt

**Configuration-Related:**
- WAF misconfiguration
- Rule false positive
- Rate limiting misconfiguration
- SSL/TLS issues
- Custom rule malfunction

**System-Related:**
- Cloudflare service outage
- Origin server issues
- DNS problems
- Certificate expiration
- Network connectivity issues

## Response Team and Contacts

### Primary Response Team

**Security Team Lead**
- Name: [TBD]
- Email: security@wwmaa.com
- Phone: [TBD]
- Role: Overall incident coordination

**DevOps Engineer (On-Call)**
- Name: [Rotation]
- Email: ops@wwmaa.com
- Phone: [PagerDuty]
- Role: System access and configuration changes

**Security Engineer**
- Name: [TBD]
- Email: seceng@wwmaa.com
- Phone: [TBD]
- Role: Security analysis and investigation

**Engineering Manager**
- Name: [TBD]
- Email: engineering@wwmaa.com
- Phone: [TBD]
- Role: Decision authority, escalation point

### External Contacts

**Cloudflare Support**
- Free Plan: Community forums only
- Pro Plan: Support ticket system
- Business+ Plan: 24/7 phone support
- Enterprise Plan: Dedicated TAM
- Emergency: [Cloudflare Support Portal]

**Legal/Compliance**
- Email: legal@wwmaa.com
- Phone: [TBD]
- When to contact: Data breach, compliance violation

**Public Relations**
- Email: pr@wwmaa.com
- Phone: [TBD]
- When to contact: Public-facing incident, media inquiries

### Communication Channels

**Primary: Slack**
- #incidents - All incidents
- #security - Security team discussion
- #engineering - Engineering coordination

**Secondary: PagerDuty**
- P1/P2 incidents trigger pages
- On-call rotation management

**Tertiary: Email**
- security@wwmaa.com - Security team distribution
- incidents@wwmaa.com - Incident tracking

**Video Conference:**
- Zoom/Google Meet for P1/P2 incidents
- Link: [War room link]

## Incident Response Workflow

### Phase 1: Detection and Triage (0-5 minutes)

**1.1 Incident Detection**

Incidents may be detected through:
- Automated alerts (PagerDuty, email, Slack)
- Cloudflare dashboard anomalies
- User reports of access issues
- Monitoring system alerts
- Manual security reviews

**1.2 Initial Assessment**

When incident detected:

```
✓ Note detection time
✓ Identify incident type
✓ Assess severity level
✓ Check if automated response triggered
✓ Verify incident is real (not false alarm)
```

**1.3 Create Incident Ticket**

Create incident ticket in tracking system:

```
Title: [P1] DDoS Attack - wwmaa.com - 2025-01-10
Severity: P1
Type: DDoS Attack
Start Time: 2025-01-10 14:32:15 UTC
Detected By: Cloudflare Alert
Status: Active
Assigned To: On-call engineer
```

**1.4 Initial Notification**

```bash
# Post to #incidents Slack channel
[P1] INCIDENT: DDoS attack detected on wwmaa.com
- Detected: 14:32 UTC
- Status: Active, response in progress
- Impact: High traffic load, some users experiencing slowness
- Response: On-call engineer investigating
- War room: [Zoom link]
```

### Phase 2: Investigation and Analysis (5-15 minutes)

**2.1 Access Cloudflare Dashboard**

1. Log in: https://dash.cloudflare.com
2. Select domain: wwmaa.com
3. Navigate to **Analytics & Logs** → **Security**

**2.2 Review Security Events**

Check:
- WAF events (blocks, challenges)
- Rate limiting events
- Bot detection events
- DDoS alerts
- Firewall events

**2.3 Identify Attack Characteristics**

Document:
```
Attack Vector: [HTTP flood / SQL injection / etc.]
Source IPs: [List of IPs or "Distributed"]
Source Countries: [Country codes]
Target Endpoints: [URLs being attacked]
Request Rate: [Requests per minute]
Attack Pattern: [Characteristics]
WAF Response: [Block / Challenge / Allow]
```

**2.4 Check Origin Server**

```bash
# SSH to Railway backend (via Railway CLI)
railway shell

# Check server load
top
htop

# Check application logs
tail -f /var/log/application.log

# Check error rate
grep "ERROR" /var/log/application.log | wc -l

# Check active connections
netstat -an | grep ESTABLISHED | wc -l
```

**2.5 Determine Impact**

Assess:
- User-facing impact (availability, performance)
- Affected services/endpoints
- Data exposure risk
- Business impact (revenue, reputation)

### Phase 3: Containment (15-30 minutes)

**3.1 Immediate Actions**

**For DDoS Attack:**
```
1. Enable "I'm Under Attack Mode"
   - Go to Security → Settings
   - Toggle "Under Attack Mode" to ON
   - This shows JavaScript challenge to all visitors

2. Review and enable additional DDoS protection
   - Security → DDoS
   - Set sensitivity to "High"

3. Monitor attack mitigation
   - Check Analytics dashboard
   - Verify request rate decreasing
```

**For SQL Injection / XSS Attack:**
```
1. Verify WAF rules are blocking
   - Security → Events
   - Confirm attacks blocked (403 status)

2. If attacks getting through:
   - Add custom rule to block specific pattern
   - Add source IPs to blocklist

3. Review application logs for any successful exploits
```

**For Brute Force Attack:**
```
1. Verify rate limiting active
   - Security → WAF → Rate Limiting Rules
   - Check if login endpoint rate limit triggered

2. Block source IPs if needed
   - Security → WAF → Tools → IP Access Rules
   - Add IPs with "Block" action

3. Notify users to reset passwords if compromise suspected
```

**For False Positive Incident:**
```
1. Identify problematic rule
   - Security → Events
   - Find rule blocking legitimate traffic

2. Create temporary exception
   - Security → WAF → Custom Rules
   - Add rule to allow specific pattern
   - Set to expire in 24 hours

3. Document for permanent fix
   - Create ticket to adjust rule
   - Update documentation
```

**3.2 Block Malicious Sources**

**Add IPs to Blocklist:**
```
1. Navigate to Security → WAF → Tools → IP Access Rules
2. Click "Add rule"
3. Enter IP or IP range
4. Action: Block
5. Note: "Blocked during [incident-ID] - [reason]"
6. Save
```

**Create Emergency Firewall Rule:**
```
1. Navigate to Security → WAF → Custom Rules
2. Click "Create Firewall Rule"
3. Name: "Emergency Block - [Incident ID]"
4. Expression:
   (ip.src in {IP1 IP2 IP3}) or
   (http.user_agent contains "malicious-bot")
5. Action: Block
6. Deploy
```

**3.3 Protect Critical Assets**

```
1. Increase protection on sensitive endpoints
   - Add additional challenges for /api/admin/*
   - Increase rate limiting on /api/payment/*

2. Temporarily restrict access if needed
   - Block all traffic except trusted IPs
   - Enable Cloudflare Access for admin pages
```

### Phase 4: Eradication (30-60 minutes)

**4.1 Identify Root Cause**

Investigate:
- How did attack bypass initial defenses?
- What vulnerability was targeted?
- Are there other vulnerable areas?
- Is this part of larger campaign?

**4.2 Implement Permanent Fixes**

- Update WAF rules
- Patch application vulnerabilities
- Strengthen rate limiting
- Improve bot detection
- Update security policies

**4.3 Verify Threat Eliminated**

```bash
# Check attack has stopped
curl -I https://wwmaa.com
# Should return 200 OK

# Monitor for 15 minutes
# Watch Cloudflare Analytics for suspicious activity

# Test application functionality
# Ensure legitimate traffic not blocked
```

### Phase 5: Recovery (60-90 minutes)

**5.1 Restore Normal Operations**

```
1. Disable "I'm Under Attack Mode" (if enabled)
   - Security → Settings
   - Toggle OFF

2. Remove temporary restrictions
   - Remove emergency firewall rules
   - Restore normal rate limits

3. Monitor for attack resumption
   - Watch for 30 minutes before declaring recovery
```

**5.2 Verify System Health**

```bash
# Check application health
curl https://wwmaa.com/api/health

# Check origin server
railway status

# Verify all services operational
# Run smoke tests on critical flows
```

**5.3 User Communication**

If users were affected:

```
Subject: Service Restored - wwmaa.com

Dear wwmaa.com users,

We have resolved the service disruption that occurred on [date] at [time] UTC.
All systems are now operating normally.

What happened:
- [Brief description of incident]
- Our security systems detected and mitigated the issue
- No user data was compromised

Actions taken:
- [Summary of fixes]

We apologize for any inconvenience. If you continue to experience issues,
please contact support@wwmaa.com.

Thank you for your patience.

The wwmaa.com Security Team
```

## Common Incident Scenarios

### Scenario 1: DDoS Attack

**Symptoms:**
- Massive spike in traffic (10x+ normal)
- Slow page loads or timeouts
- Cloudflare DDoS alert triggered
- Origin server under heavy load

**Response Checklist:**

```
□ Enable "I'm Under Attack Mode"
□ Verify Cloudflare DDoS protection active
□ Check origin server capacity
□ Review attack characteristics (volumetric vs application-layer)
□ Enable additional rate limiting if needed
□ Monitor attack mitigation
□ Document attack details
□ Wait for attack to subside (usually 1-6 hours)
□ Restore normal operations
□ Conduct post-incident review
```

**Commands:**

```bash
# Check traffic volume in Cloudflare
# Dashboard → Analytics → Traffic

# Monitor origin server
railway logs --tail

# Test site accessibility
curl -I https://wwmaa.com
```

**Resolution Time:** Typically 1-6 hours (attack duration dependent)

### Scenario 2: SQL Injection Attack

**Symptoms:**
- High volume of blocked SQL injection attempts
- Cloudflare WAF alerts for OWASP rules
- Suspicious query parameters in logs
- Possible data exfiltration attempts

**Response Checklist:**

```
□ Verify all attacks blocked by WAF (check for 403 status)
□ Review application logs for any successful queries
□ Check database logs for suspicious activity
□ Identify attack source IPs
□ Add source IPs to blocklist
□ Verify no data breach occurred
□ Review and strengthen WAF rules
□ Scan for application vulnerabilities
□ Patch any identified vulnerabilities
□ Monitor for follow-up attacks
```

**Investigation Commands:**

```bash
# Review WAF blocks
# Cloudflare Dashboard → Security → Events
# Filter: "SQL Injection"

# Check application logs
railway logs | grep -i "sql\|inject\|union\|select"

# Verify no successful exploits
railway logs | grep "ERROR\|EXCEPTION" | grep -i sql
```

**Critical Check:**

```sql
-- Review database for suspicious queries (if logging enabled)
SELECT * FROM query_logs
WHERE query_text LIKE '%UNION%'
   OR query_text LIKE '%1=1%'
ORDER BY timestamp DESC
LIMIT 100;
```

**Resolution Time:** 30 minutes - 2 hours

### Scenario 3: False Positive Blocking Legitimate Users

**Symptoms:**
- User reports unable to access site
- Legitimate requests receiving 403 errors
- Specific feature/functionality blocked
- Reports from specific user group or location

**Response Checklist:**

```
□ Identify affected users (IP, location, behavior)
□ Review WAF events for these users
□ Identify rule causing false positive
□ Determine scope (single user vs many users)
□ Create temporary allowlist rule
□ Test that users can now access
□ Analyze why rule triggered
□ Implement permanent fix (adjust rule sensitivity)
□ Remove temporary allowlist
□ Notify affected users
□ Document false positive for future reference
```

**Investigation:**

```bash
# Find user's recent blocks
# Cloudflare Dashboard → Security → Events
# Filter by IP address or time range

# Identify rule
# Note Rule ID and Rule Name

# Create exception
# Security → WAF → Custom Rules
# Add rule to allow specific pattern
```

**Example Exception Rule:**

```
Name: Allow False Positive - Support Staff VPN
Expression:
  (ip.src in {1.2.3.4/32}) and
  (http.request.uri.path contains "/api/admin")
Action: Allow

Notes: False positive from OWASP rule 949110
Ticket: INC-12345
Expiry: 2025-01-17 (7 days)
```

**Resolution Time:** 15-30 minutes

### Scenario 4: Rate Limit Abuse

**Symptoms:**
- Single IP or user hitting rate limits repeatedly
- Automated behavior detected
- Specific endpoint under excessive load
- Possible credential stuffing or data scraping

**Response Checklist:**

```
□ Review rate limiting events
□ Identify source IPs and patterns
□ Check if legitimate user or attack
□ Verify rate limits appropriate
□ Block source IPs if malicious
□ Adjust rate limits if too restrictive
□ Investigate what attacker is targeting
□ Check if credentials compromised (for login attempts)
□ Monitor for distributed attack (multiple IPs)
□ Implement additional protections if needed
```

**Investigation:**

```bash
# Review rate limit events
# Cloudflare Dashboard → Analytics → Security
# Filter: Rate Limiting

# Identify patterns
# Note: IP addresses, endpoints, timing

# Check if distributed
# If multiple IPs: coordinated attack
# If single IP: automated script
```

**Actions:**

```
For malicious IPs:
1. Add to blocklist (IP Access Rules)
2. Create custom firewall rule if pattern detected

For legitimate users:
1. Increase rate limit for specific endpoint
2. Whitelist known API clients
3. Implement API key authentication
4. Contact user to discuss usage patterns
```

**Resolution Time:** 30 minutes - 1 hour

### Scenario 5: Certificate Expiration

**Symptoms:**
- SSL/TLS errors on site
- Browser warnings about invalid certificate
- 526 error (Invalid SSL Certificate)
- Users cannot access site

**Response Checklist:**

```
□ Check certificate status in Cloudflare
□ Verify certificate expiration date
□ Check edge certificate (Cloudflare to client)
□ Check origin certificate (Cloudflare to server)
□ Regenerate expired certificate
□ Install new certificate on origin server
□ Update Railway environment variables
□ Verify site accessible
□ Test SSL Labs rating
□ Set up better monitoring to prevent recurrence
```

**Quick Fix (Origin Certificate):**

```bash
# 1. Generate new origin certificate
# Cloudflare Dashboard → SSL/TLS → Origin Server
# Click "Create Certificate"
# Copy certificate and private key

# 2. Update Railway environment variables
railway variables set SSL_CERTIFICATE="[paste certificate]"
railway variables set SSL_PRIVATE_KEY="[paste private key]"

# 3. Restart service
railway restart

# 4. Verify
curl -I https://wwmaa.com
# Should return 200 OK
```

**Resolution Time:** 15-30 minutes

### Scenario 6: Cloudflare Service Outage

**Symptoms:**
- Site completely unreachable
- Cloudflare error pages (503, 520, 521)
- Cloudflare status page shows outage
- Multiple domains affected

**Response Checklist:**

```
□ Check Cloudflare status page: https://www.cloudflarestatus.com/
□ Verify issue is Cloudflare-wide (not just our config)
□ If Cloudflare outage: monitor status page
□ Communicate to users (expected timeline)
□ Consider temporary bypass if critical (not recommended)
□ Wait for Cloudflare resolution
□ Verify service restored
□ Review incident impact
```

**Communication Template:**

```
Subject: Service Disruption - External Provider Issue

We are currently experiencing service disruption due to an issue
with our security provider (Cloudflare).

Status: Monitoring
Estimated Resolution: [Per Cloudflare status page]
Current Time: [Time]

We are monitoring the situation and will update as information
becomes available.

For updates: https://www.cloudflarestatus.com/

Thank you for your patience.
```

**Resolution Time:** Dependent on Cloudflare (usually 15-60 minutes)

## Investigation Procedures

### Log Analysis

**Cloudflare Dashboard:**

```
1. Navigate to Analytics & Logs → Security
2. Set time range (last hour, last 24 hours)
3. Review:
   - Top events by rule
   - Top countries
   - Top IPs
   - Top user agents
   - Top paths
4. Click on specific event for details
5. Export data if needed (CSV)
```

**Filtering Events:**

```
Filter by:
- Action: Block, Challenge, Allow
- Source IP: Specific IP or range
- User Agent: Specific bot or browser
- Path: Specific endpoint
- Country: Geographic filter
- Rule: Specific WAF rule
```

**Log Export (Pro+ plans):**

```bash
# Using Cloudflare API
curl -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}/logs/received?start=2025-01-10T00:00:00Z&end=2025-01-10T01:00:00Z" \
  -H "X-Auth-Email: your-email@example.com" \
  -H "X-Auth-Key: your-api-key" \
  -H "Content-Type: application/json" > logs.json

# Analyze with jq
cat logs.json | jq '.[] | select(.EdgeResponseStatus == 403)'
```

### Traffic Pattern Analysis

**Identify Attack Patterns:**

```
Normal traffic:
- Distributed sources
- Various user agents
- Human-like timing
- Multiple pages visited
- Reasonable request rate

Attack traffic:
- Concentrated sources
- Suspicious user agents
- Mechanical timing
- Single endpoint targeted
- Excessive request rate
- Unusual query parameters
```

**Traffic Analysis Script:**

```python
#!/usr/bin/env python3
# analyze-traffic.py

import json
import sys
from collections import Counter

def analyze_logs(logfile):
    with open(logfile) as f:
        logs = [json.loads(line) for line in f]

    # Analyze IPs
    ips = Counter(log['ClientIP'] for log in logs)
    print("Top 10 IPs:")
    for ip, count in ips.most_common(10):
        print(f"  {ip}: {count} requests")

    # Analyze user agents
    uas = Counter(log.get('ClientRequestUserAgent', 'Unknown') for log in logs)
    print("\nTop 10 User Agents:")
    for ua, count in uas.most_common(10):
        print(f"  {ua[:50]}: {count} requests")

    # Analyze paths
    paths = Counter(log['ClientRequestPath'] for log in logs)
    print("\nTop 10 Paths:")
    for path, count in paths.most_common(10):
        print(f"  {path}: {count} requests")

    # Analyze status codes
    statuses = Counter(log['EdgeResponseStatus'] for log in logs)
    print("\nStatus Codes:")
    for status, count in statuses.most_common():
        print(f"  {status}: {count} requests")

if __name__ == '__main__':
    analyze_logs(sys.argv[1])
```

### Threat Intelligence

**Check IP Reputation:**

```bash
# AbuseIPDB
curl -G https://api.abuseipdb.com/api/v2/check \
  --data-urlencode "ipAddress=1.2.3.4" \
  -d maxAgeInDays=90 \
  -H "Key: YOUR_API_KEY" \
  -H "Accept: application/json"

# Check if IP is Tor exit node
curl https://check.torproject.org/torbulkexitlist

# VirusTotal
curl https://www.virustotal.com/api/v3/ip_addresses/1.2.3.4 \
  -H "x-apikey: YOUR_API_KEY"
```

**Threat Intelligence Platforms:**
- AbuseIPDB: https://www.abuseipdb.com/
- AlienVault OTX: https://otx.alienvault.com/
- Talos Intelligence: https://talosintelligence.com/
- URLhaus: https://urlhaus.abuse.ch/

## Mitigation Actions

### Quick Reference: WAF Controls

**Enable Under Attack Mode:**
```
Cloudflare Dashboard → Security → Settings → Under Attack Mode → ON
Effect: Shows JS challenge to all visitors
Use: During active DDoS attack
Duration: Until attack subsides (typically 1-6 hours)
```

**Block IP Address:**
```
Cloudflare Dashboard → Security → WAF → Tools → IP Access Rules
→ Add rule → IP: [address] → Action: Block → Note: [reason]
Effect: Blocks all traffic from IP
Use: Known malicious source
```

**Create Emergency Firewall Rule:**
```
Cloudflare Dashboard → Security → WAF → Custom Rules → Create
Name: Emergency Block [Incident ID]
Expression: (ip.src eq 1.2.3.4) or (http.user_agent contains "badbot")
Action: Block
```

**Adjust Rate Limiting:**
```
Cloudflare Dashboard → Security → WAF → Rate Limiting Rules
→ Select rule → Edit → Adjust threshold or duration
Effect: More/less strict rate limiting
Use: Response to attack or false positives
```

**Enable Additional WAF Rules:**
```
Cloudflare Dashboard → Security → WAF → Managed Rules
→ Enable additional rulesets or increase sensitivity
Effect: More aggressive blocking
Use: Targeted attacks bypassing existing rules
```

### Response Actions by Incident Type

| Incident Type | Immediate Action | Follow-up Action |
|---------------|------------------|------------------|
| DDoS Attack | Enable Under Attack Mode | Review and strengthen DDoS settings |
| SQL Injection | Verify WAF blocking, add IP blocks | Patch application vulnerabilities |
| XSS Attack | Verify WAF blocking | Review input validation |
| Brute Force | Verify rate limiting, block IPs | Implement account lockout policy |
| Bot Attack | Enable stricter bot protection | Implement bot management rules |
| False Positive | Create allow rule exception | Adjust rule sensitivity permanently |
| Rate Limit Abuse | Block source IPs | Adjust rate limits, implement API keys |
| Cert Expiration | Renew certificate immediately | Set up expiration monitoring |
| Config Error | Revert to last known good config | Test changes in staging first |

## Communication Protocols

### Internal Communication

**During Active Incident (P1/P2):**

```
1. Create #incident-[ID] channel in Slack
2. Post updates every 15 minutes minimum
3. Use war room Zoom call for coordination
4. Assign roles: Incident Commander, Scribe, SMEs
5. Document all actions in incident ticket
```

**Status Update Template:**

```
[Time] UPDATE #[N]

Status: [Investigating | Mitigating | Resolved]
Impact: [Description of user impact]
Actions Taken:
  - [Action 1]
  - [Action 2]
Next Steps:
  - [Next action]
ETA: [Estimated resolution time]
```

### External Communication

**Status Page Update:**

```
Title: [Service Disruption | Degraded Performance | Investigating]
Status: [Investigating | Identified | Monitoring | Resolved]

Message:
We are [investigating reports of | experiencing | monitoring]
[description of issue] affecting [scope].

Last Update: [Time] UTC
Next Update: [Time] UTC

Updates will be posted here as they become available.
```

**User Notification (Email):**

```
Subject: [Resolved] Service Disruption - [Date]

Dear wwmaa.com users,

[Resolution announcement or status update]

Timeline:
- [Time]: Issue detected
- [Time]: Investigation began
- [Time]: Mitigation implemented
- [Time]: Service restored

Impact:
- [Description of what was affected]
- [Duration]

Root Cause:
- [Brief non-technical explanation]

Actions Taken:
- [What we did to fix it]
- [What we're doing to prevent recurrence]

We apologize for any inconvenience this may have caused.

If you have questions or continue to experience issues,
please contact support@wwmaa.com.

Thank you,
The wwmaa.com Team
```

### Communication Decision Matrix

| Incident Severity | Status Page | Email Users | Social Media | Press Release |
|-------------------|-------------|-------------|--------------|---------------|
| P1 (Critical) | Yes, immediately | Yes, within 1 hour | Yes, if prolonged | If data breach |
| P2 (High) | Yes, within 15 min | If >30 min impact | If >2 hours | No |
| P3 (Medium) | If >1 hour | If significant subset | No | No |
| P4 (Low) | No | No | No | No |

## Post-Incident Activities

### Incident Debrief (Within 24 hours)

**Participants:**
- Incident Commander
- All responders
- Engineering Manager
- Product Manager (if user-facing)

**Agenda:**
1. Timeline review
2. What went well
3. What could be improved
4. Action items

### Post-Incident Report Template

```markdown
# Post-Incident Report: [Incident ID]

## Summary
Brief description of incident (2-3 sentences)

## Incident Details
- **Date:** 2025-01-10
- **Start Time:** 14:32 UTC
- **End Time:** 16:15 UTC
- **Duration:** 1 hour 43 minutes
- **Severity:** P1
- **Detected By:** Automated alert
- **Services Affected:** wwmaa.com (main site)
- **Users Impacted:** ~5,000 (estimated)

## Timeline
| Time (UTC) | Event |
|------------|-------|
| 14:32 | DDoS attack detected, alert triggered |
| 14:35 | On-call engineer paged |
| 14:40 | Investigation began |
| 14:45 | Under Attack Mode enabled |
| 15:00 | Attack characteristics identified |
| 15:15 | Additional mitigation deployed |
| 15:45 | Attack volume declining |
| 16:00 | Under Attack Mode disabled |
| 16:15 | Services fully restored |

## Root Cause
[Detailed explanation of what caused the incident]

## Impact Assessment
- **Availability:** 15% of requests failed during peak attack
- **Performance:** 3x slower response times
- **Data:** No data loss or breach
- **Revenue:** Minimal impact (some abandoned carts)
- **Reputation:** Moderate (some user complaints)

## Detection and Response
- **Detection Time:** < 1 minute (automated alert)
- **Response Time:** 3 minutes (on-call paged)
- **Mitigation Time:** 13 minutes (Under Attack Mode enabled)
- **Resolution Time:** 1 hour 43 minutes total

## What Went Well
1. Automated detection was immediate and accurate
2. Response time was within SLA (5 minutes)
3. Under Attack Mode effectively mitigated attack
4. No data breach or compromise occurred
5. Team communication was clear and effective

## What Could Be Improved
1. Initial triage took longer than ideal (8 minutes)
2. Documentation for Under Attack Mode was outdated
3. User communication delayed (should have sent sooner)
4. Origin server monitoring not showing clear metrics
5. Post-incident user notification not sent

## Action Items
| # | Action | Owner | Deadline | Status |
|---|--------|-------|----------|--------|
| 1 | Update Under Attack Mode runbook | Security Team | 2025-01-12 | Open |
| 2 | Improve origin server monitoring | DevOps | 2025-01-15 | Open |
| 3 | Create user notification templates | Product | 2025-01-13 | Open |
| 4 | Implement auto-enable Under Attack Mode | Security Team | 2025-01-20 | Open |
| 5 | Conduct tabletop exercise | Security Team | 2025-01-25 | Open |

## Lessons Learned
1. Automated mitigation for known attack patterns should be considered
2. User communication templates should be pre-approved and ready
3. Origin server metrics need better visibility during incidents
4. DDoS attack patterns should be documented for future reference

## Recommendations
1. Upgrade to Cloudflare Pro plan for better DDoS protection
2. Implement automated Under Attack Mode triggers
3. Set up better alerting thresholds (reduce false positives)
4. Conduct quarterly DDoS simulation exercises
5. Review and update incident response playbook monthly

---

**Report Prepared By:** [Name]
**Date:** 2025-01-11
**Reviewed By:** [Security Lead]
**Approved By:** [Engineering Manager]
```

### Follow-up Actions

```
Within 24 hours:
□ Conduct incident debrief meeting
□ Complete post-incident report
□ Create action item tickets
□ Send user apology/explanation email (if applicable)
□ Update runbooks based on lessons learned

Within 1 week:
□ Complete all P1 action items
□ Review and update monitoring/alerting
□ Conduct knowledge sharing session with team
□ Update documentation

Within 1 month:
□ Complete all action items
□ Conduct tabletop exercise based on incident
□ Review incident response metrics
□ Identify process improvements
```

## Escalation Procedures

### When to Escalate

**To Engineering Manager:**
- P1 incident lasting > 1 hour
- P2 incident lasting > 4 hours
- Any data breach suspected
- Need for business decision (e.g., take service offline)
- Conflicting priorities during incident

**To Legal/Compliance:**
- Data breach confirmed
- Potential regulatory reporting required (GDPR, etc.)
- Law enforcement involvement needed
- User PII exposed

**To Executive Team:**
- P1 incident lasting > 4 hours
- Data breach affecting > 1,000 users
- Media attention or PR impact
- Financial impact > $10,000
- Repeat incidents indicating systemic issues

**To Cloudflare Support:**
- WAF not functioning correctly
- Suspect Cloudflare service issue
- Need guidance on complex configuration
- DDoS attack exceeding free/Pro plan capabilities

### Escalation Contacts

```
Level 1: On-Call Engineer
  - Response Time: 5 minutes
  - Authority: Implement standard mitigations

Level 2: Security Team Lead
  - Response Time: 15 minutes
  - Authority: Major configuration changes

Level 3: Engineering Manager
  - Response Time: 30 minutes
  - Authority: Business decisions, take services offline

Level 4: CTO/VP Engineering
  - Response Time: 1 hour
  - Authority: Executive decisions, major expenditures

Level 5: CEO
  - Response Time: 2 hours
  - Authority: All decisions, external communications
```

## Tools and Resources

### Required Access

- Cloudflare Dashboard: https://dash.cloudflare.com
- Railway Dashboard: https://railway.app
- Slack: #incidents, #security channels
- PagerDuty: On-call schedules and alerting
- Incident Tracking: [Your ticket system]

### Useful Commands

```bash
# Check site status
curl -I https://wwmaa.com

# Test from different locations
curl --resolve wwmaa.com:443:1.2.3.4 https://wwmaa.com/

# Check DNS
dig wwmaa.com
nslookup wwmaa.com

# Check SSL
openssl s_client -connect wwmaa.com:443 -servername wwmaa.com

# View Railway logs
railway logs --tail

# Check Railway status
railway status
```

### External Resources

- Cloudflare Status: https://www.cloudflarestatus.com/
- Cloudflare Support: https://support.cloudflare.com/
- OWASP Attack Database: https://owasp.org/
- CVE Database: https://cve.mitre.org/
- Security Advisories: [Your sources]

### Documentation

- WAF Configuration Guide: `/docs/security/waf-configuration.md`
- SSL/TLS Setup: `/docs/security/ssl-tls-setup.md`
- Testing Procedures: `/docs/security/waf-testing.md`
- Review Schedule: `/docs/security/waf-review-schedule.md`

---

**Document Version:** 1.0
**Last Updated:** 2025-01-10
**Maintained By:** Security Team
**Review Schedule:** After each major incident, or quarterly
