# HSTS Preload Submission Guide

This guide explains how to submit the WWMAA domain to the HSTS preload list, including requirements, risks, and rollback procedures.

## Table of Contents

1. [What is HSTS Preload?](#what-is-hsts-preload)
2. [Benefits](#benefits)
3. [Requirements](#requirements)
4. [Risks and Considerations](#risks-and-considerations)
5. [Pre-Submission Checklist](#pre-submission-checklist)
6. [Submission Process](#submission-process)
7. [Verification](#verification)
8. [Rollback Procedures](#rollback-procedures)
9. [Timeline](#timeline)

## What is HSTS Preload?

HSTS (HTTP Strict Transport Security) Preload is a list of domains that browsers should only access via HTTPS, even on the first visit. This list is hardcoded into major browsers (Chrome, Firefox, Safari, Edge, etc.).

### How It Works

**Without HSTS Preload:**
1. User types `wwmaa.com` in browser
2. Browser tries HTTP first: `http://wwmaa.com`
3. Server redirects to HTTPS: `https://wwmaa.com`
4. Browser connects via HTTPS
5. **Problem:** First connection is vulnerable to SSL stripping

**With HSTS Preload:**
1. User types `wwmaa.com` in browser
2. Browser knows (from preload list) to use HTTPS
3. Browser connects directly to HTTPS: `https://wwmaa.com`
4. **Benefit:** No insecure connection, even on first visit

## Benefits

### 1. Enhanced Security
- **No SSL stripping attacks:** Even first-time visitors use HTTPS
- **No downgrade attacks:** Browsers refuse HTTP connections
- **Man-in-the-middle protection:** Encrypted from first connection

### 2. Better User Experience
- **Faster connections:** No HTTP → HTTPS redirect
- **No mixed content warnings:** Browser knows to upgrade
- **Consistent security:** Works across all browsers

### 3. Trust Signals
- **Demonstrates security commitment:** Shows you take security seriously
- **Compliance requirement:** Many standards require HSTS preload
- **SEO benefits:** Google favors secure sites

## Requirements

To be eligible for HSTS preload, your domain must meet these requirements:

### 1. Valid HTTPS Certificate
```bash
# Check certificate
openssl s_client -connect wwmaa.com:443 -servername wwmaa.com
```

Requirements:
- Valid, trusted certificate (not self-signed)
- Not expired
- Covers the domain and subdomains
- Strong encryption (TLS 1.2+ recommended)

### 2. HTTPS Redirect
All HTTP requests must redirect to HTTPS:

```bash
# Test redirect
curl -I http://wwmaa.com
# Should return: 301 Moved Permanently
# Location: https://wwmaa.com/
```

### 3. HSTS Header on Base Domain
The base domain must serve HSTS header via HTTPS:

```bash
curl -I https://wwmaa.com | grep Strict-Transport-Security
# Should return: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

Requirements:
- `max-age` must be at least 31536000 (1 year)
- Must include `includeSubDomains`
- Must include `preload`

### 4. HSTS Header on All Subdomains
All subdomains must also serve HSTS header:

```bash
curl -I https://api.wwmaa.com | grep Strict-Transport-Security
curl -I https://www.wwmaa.com | grep Strict-Transport-Security
```

### 5. All Subdomains HTTPS-Ready
Every subdomain (including wildcards) must support HTTPS:

- `www.wwmaa.com`
- `api.wwmaa.com`
- `admin.wwmaa.com`
- Any other subdomains

**Warning:** This includes subdomains you might create in the future!

## Risks and Considerations

### ⚠️ Critical Risks

#### 1. Irreversibility (Effectively)
Once preloaded, it's extremely difficult to remove:
- Takes 6-12 months to propagate removal
- Existing users won't be updated for months/years
- May break site if HTTPS configuration fails

#### 2. All Subdomains Affected
The `includeSubDomains` directive affects:
- All current subdomains
- All future subdomains
- Even internal/development subdomains

**Example problem scenarios:**
```
# These would all be forced to HTTPS:
http://test.wwmaa.com          ❌ Can't use HTTP
http://internal.wwmaa.com      ❌ Can't use HTTP
http://dev-john.wwmaa.com      ❌ Can't use HTTP
```

#### 3. Certificate Requirements
You must maintain valid certificates for:
- Base domain
- All subdomains
- Forever (or until removed from preload list)

**Failure scenarios:**
- Certificate expires → site inaccessible
- Wildcard certificate issues → all subdomains down
- Certificate misconfiguration → complete outage

#### 4. No HTTP Fallback
There is no fallback to HTTP:
- If HTTPS breaks, site is completely inaccessible
- No way to temporarily disable
- Must fix HTTPS issues before site works again

### 🔍 Important Considerations

#### 1. Development Impact
Local development might require HTTPS:
```bash
# Might not work anymore:
http://localhost:3000

# Might need to use:
https://localhost:3000
```

#### 2. Third-Party Services
All integrated services must support HTTPS:
- APIs
- Webhooks
- CDNs
- Payment processors

#### 3. Monitoring Requirements
Must monitor:
- Certificate expiration
- HTTPS configuration
- All subdomain HTTPS status

## Pre-Submission Checklist

Before submitting to HSTS preload, complete this checklist:

### Phase 1: HTTPS Setup (Complete First)

- [ ] Valid SSL/TLS certificate installed
- [ ] Certificate covers base domain and all subdomains
- [ ] Certificate auto-renewal configured
- [ ] All HTTP traffic redirects to HTTPS
- [ ] No mixed content warnings
- [ ] Test HTTPS on all subdomains

### Phase 2: HSTS Configuration (Our Current State)

- [ ] HSTS header configured in backend
- [ ] `max-age` set to 31536000 (1 year)
- [ ] `includeSubDomains` directive present
- [ ] `preload` directive present
- [ ] Test header on all subdomains

```bash
# Verify HSTS header
curl -I https://api.wwmaa.com | grep Strict-Transport-Security
# Should return: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

### Phase 3: Testing Period (Recommended: 3-6 months)

- [ ] Run in production with HSTS header for 3-6 months
- [ ] Monitor for HSTS-related issues
- [ ] Verify all subdomains work correctly
- [ ] Test certificate renewal process
- [ ] Document any HTTPS issues encountered
- [ ] Train team on HTTPS-only requirements

### Phase 4: Subdomain Audit

- [ ] List all current subdomains
- [ ] Verify each subdomain supports HTTPS
- [ ] Plan for future subdomains (will require HTTPS)
- [ ] Check development/staging subdomains
- [ ] Verify internal tools support HTTPS

Current known subdomains:
```
- www.wwmaa.com
- api.wwmaa.com
- admin.wwmaa.com (if exists)
- staging.wwmaa.com (if exists)
- staging-api.wwmaa.com (if exists)
```

### Phase 5: Team Preparation

- [ ] Train team on HTTPS-only requirement
- [ ] Update documentation
- [ ] Prepare incident response plan
- [ ] Set up monitoring/alerts
- [ ] Document rollback procedures

## Submission Process

### Step 1: Final Verification

Use the HSTS preload checker:

```
https://hstspreload.org/?domain=wwmaa.com
```

This will show:
- ✅ All requirements met
- ❌ Any issues to fix

### Step 2: Submit Domain

If all checks pass:

1. Go to https://hstspreload.org/
2. Enter your domain: `wwmaa.com`
3. Check "I understand..." checkbox
4. Click "Submit"

### Step 3: Confirm Submission

You'll receive:
- Confirmation email
- Submission ID
- Estimated timeline

### Step 4: Wait for Inclusion

Timeline:
- **Pending review:** 1-2 weeks
- **Added to Chromium source:** Next release (6-8 weeks)
- **In Chrome stable:** 10-12 weeks from submission
- **Other browsers:** 3-6 months
- **Full propagation:** 6-12 months

## Verification

### Check Preload Status

```
https://hstspreload.org/?domain=wwmaa.com
```

Shows:
- Pending
- In Chromium source
- In browser versions

### Check Browser Implementation

#### Chrome
```
chrome://net-internals/#hsts
```
Query: `wwmaa.com`

Should show:
```
static_sts_domain: wwmaa.com
static_upgrade_mode: STRICT
static_sts_include_subdomains: true
```

#### Firefox
Built into browser, check:
```
https://searchfox.org/mozilla-central/source/security/manager/ssl/nsSTSPreloadList.inc
```

### Verify HTTPS Enforcement

```bash
# Should immediately redirect to HTTPS (no HTTP connection)
curl -v http://wwmaa.com 2>&1 | grep -i "strict-transport"
```

## Rollback Procedures

### ⚠️ Removal is Difficult

Removing from preload list:
- Takes 6-12 months minimum
- Requires submitting removal request
- No immediate effect on existing users
- Users' browsers keep cached HSTS for up to 1 year

### Emergency Procedures

#### If HTTPS Breaks

**DO NOT** try to remove from preload list. Instead:

1. **Fix HTTPS immediately:**
   ```bash
   # Check certificate
   openssl s_client -connect wwmaa.com:443

   # Renew certificate
   certbot renew --force-renewal

   # Restart web server
   systemctl restart nginx
   ```

2. **Temporary subdomain:**
   Create new subdomain not in preload list:
   ```
   https://emergency.otherdomain.com
   ```

3. **Communicate with users:**
   - Status page
   - Social media
   - Email notifications

#### Requesting Removal

Only if absolutely necessary:

1. Remove HSTS header from domain
2. Wait for max-age to expire (1 year for us)
3. Submit removal request:
   ```
   https://hstspreload.org/removal/
   ```
4. Wait 6-12 months for propagation
5. Users may still have cached HSTS

### Why Removal is Last Resort

- Takes 6-12 months minimum
- No quick fix
- Damages user trust
- Better to fix HTTPS than remove

## Timeline

### Recommended Approach

#### Phase 1: Current State (Done ✅)
- HSTS headers configured
- All requirements met
- Security headers implemented

#### Phase 2: Testing Period (3-6 months)
**Start:** After deployment
**Duration:** 3-6 months
**Activities:**
- Monitor HSTS compliance
- Test certificate renewals
- Verify all subdomain HTTPS
- Train team
- Document issues

**Verification:**
```bash
# Weekly checks
python scripts/test_security_headers.py --url https://api.wwmaa.com
```

#### Phase 3: Pre-Submission Review (1-2 weeks)
**Activities:**
- Final subdomain audit
- Team sign-off
- Stakeholder approval
- Risk assessment
- Go/no-go decision

#### Phase 4: Submission (1 day)
**Activities:**
- Submit to hstspreload.org
- Document submission
- Set up monitoring

#### Phase 5: Propagation (6-12 months)
**Timeline:**
- Week 1-2: Pending review
- Week 6-8: Added to Chromium
- Week 10-12: In Chrome stable
- Month 3-6: Other browsers
- Month 6-12: Full propagation

## Decision Matrix

### Submit to Preload If:

✅ All HTTPS infrastructure is stable
✅ Team understands implications
✅ All subdomains support HTTPS
✅ Certificate auto-renewal working
✅ Monitoring in place
✅ Tested for 3-6 months
✅ Incident response plan ready

### DO NOT Submit If:

❌ Any subdomains use HTTP
❌ Team not trained on HTTPS-only
❌ Certificate management uncertain
❌ Development needs HTTP
❌ Haven't tested HSTS for 3+ months
❌ Any doubts about readiness

## Recommendation

**Our Recommendation:** Wait 3-6 months before submitting to HSTS preload.

**Reasoning:**
1. Recently implemented HSTS headers
2. Need to verify stability
3. Test certificate renewal process
4. Ensure all subdomains ready
5. Train team on implications
6. Monitor for any issues

**Next Steps:**
1. Deploy current HSTS configuration ✅
2. Monitor for 3 months minimum
3. Review this guide again
4. Make submission decision with team
5. If approved, follow submission process

## Resources

- [HSTS Preload Official Site](https://hstspreload.org/)
- [Chrome HSTS Preload List](https://chromium.googlesource.com/chromium/src/net/+/master/http/transport_security_state_static.json)
- [MDN HSTS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security)
- [RFC 6797: HTTP Strict Transport Security](https://tools.ietf.org/html/rfc6797)

## Questions?

Before submitting:
- Review all requirements
- Complete testing period
- Get team sign-off
- Consider risks carefully
- Have rollback plan ready

**Remember:** HSTS preload is a one-way door. Make sure you're ready before entering.
