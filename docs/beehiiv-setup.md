# BeeHiiv Newsletter Setup Guide

Complete guide for setting up and configuring BeeHiiv newsletter integration with the WWMAA platform.

## Table of Contents

1. [Overview](#overview)
2. [Account Creation](#account-creation)
3. [API Key Generation](#api-key-generation)
4. [Email List Setup](#email-list-setup)
5. [Custom Domain Configuration](#custom-domain-configuration)
6. [DNS Records Setup](#dns-records-setup)
7. [Email Template Creation](#email-template-creation)
8. [Running the Setup Script](#running-the-setup-script)
9. [Testing the Integration](#testing-the-integration)
10. [Troubleshooting](#troubleshooting)
11. [Cost Breakdown](#cost-breakdown)

## Overview

BeeHiiv is our newsletter platform for managing email communications with members, instructors, and the general public. This integration enables:

- Automated subscriber management
- Newsletter publishing and distribution
- Email template management
- Subscriber analytics and engagement tracking
- Custom domain email sending

## Account Creation

### Step 1: Sign Up for BeeHiiv

1. Visit [beehiiv.com](https://www.beehiiv.com)
2. Click "Start for Free"
3. Choose the **Launch** plan (free tier) to get started
4. Complete account registration with:
   - Organization name: "World Wing Martial Arts Association"
   - Publication name: "WWMAA Newsletter"
   - Email domain: wwmaa.com

### Step 2: Verify Email

1. Check your email for verification link
2. Click verification link to activate account
3. Complete onboarding wizard

## API Key Generation

### Step 1: Access API Settings

1. Log into your BeeHiiv dashboard
2. Navigate to **Settings** → **Integrations**
3. Scroll to **API Access**

### Step 2: Generate API Key

1. Click "Create New API Key"
2. Name: "WWMAA Platform Integration"
3. Permissions: Select all (Read & Write)
4. Click "Generate Key"
5. **IMPORTANT**: Copy the API key immediately - it won't be shown again

### Step 3: Get Publication ID

1. Navigate to **Settings** → **Publication**
2. Find your Publication ID (format: `pub_xxxxxxxxxxxxx`)
3. Copy this ID for configuration

### Step 4: Store Credentials Securely

Add to your `.env` file:

```bash
BEEHIIV_API_KEY=your_api_key_here
BEEHIIV_PUBLICATION_ID=pub_xxxxxxxxxxxxx
```

**Security Note**: Never commit the `.env` file to version control. The API key should be treated as a password.

## Email List Setup

BeeHiiv allows list segmentation through the dashboard. We use three main lists:

### 1. General List (Public Newsletter)

**Purpose**: General newsletter for all subscribers (members and non-members)

**Setup**:
1. Go to **Audience** → **Segments**
2. Click "Create Segment"
3. Name: "General Newsletter"
4. Description: "Public newsletter for all subscribers"
5. Criteria: All subscribers
6. Save segment

**Environment Variable**:
```bash
BEEHIIV_LIST_ID_GENERAL=seg_xxxxxxxxxxxxx
```

### 2. Members Only List

**Purpose**: Exclusive content for paid members

**Setup**:
1. Create new segment: "Members Only"
2. Description: "Exclusive content for WWMAA members"
3. Criteria: Custom field `member_status = active`
4. Save segment

**Environment Variable**:
```bash
BEEHIIV_LIST_ID_MEMBERS=seg_xxxxxxxxxxxxx
```

### 3. Instructors List

**Purpose**: Instructor-specific communications and training updates

**Setup**:
1. Create new segment: "Instructors"
2. Description: "WWMAA certified instructors"
3. Criteria: Custom field `role = instructor`
4. Save segment

**Environment Variable**:
```bash
BEEHIIV_LIST_ID_INSTRUCTORS=seg_xxxxxxxxxxxxx
```

## Custom Domain Configuration

Using a custom domain (newsletter.wwmaa.com) improves deliverability and brand consistency.

### Step 1: BeeHiiv Domain Setup

1. Navigate to **Settings** → **Sending Domain**
2. Click "Add Custom Domain"
3. Enter: `newsletter.wwmaa.com`
4. Click "Verify Domain"

BeeHiiv will provide DNS records to add. Keep this page open.

### Step 2: Configure Sending Email

1. From Email: `newsletter@wwmaa.com`
2. From Name: `WWMAA Team`

Add to `.env`:
```bash
NEWSLETTER_CUSTOM_DOMAIN=newsletter.wwmaa.com
NEWSLETTER_FROM_EMAIL=newsletter@wwmaa.com
NEWSLETTER_FROM_NAME=WWMAA Team
```

## DNS Records Setup

You'll need to add several DNS records to verify domain ownership and ensure email deliverability.

### DKIM Record (Domain Authentication)

**Purpose**: Authenticates emails sent from your domain

**Record Details**:
- **Type**: TXT
- **Host**: `beehiiv._domainkey`
- **Value**: (Provided by BeeHiiv - looks like `v=DKIM1; k=rsa; p=MIGfMA0GCS...`)
- **TTL**: 3600

**Example**:
```
Type: TXT
Name: beehiiv._domainkey.newsletter.wwmaa.com
Value: v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC...
```

### SPF Record (Sender Authorization)

**Purpose**: Authorizes BeeHiiv to send emails on behalf of your domain

**Record Details**:
- **Type**: TXT
- **Host**: `@` (or `newsletter.wwmaa.com`)
- **Value**: `v=spf1 include:beehiiv.com ~all`
- **TTL**: 3600

**If you already have an SPF record**, add `include:beehiiv.com` to it:
```
v=spf1 include:_spf.google.com include:beehiiv.com ~all
```

### DMARC Record (Email Policy)

**Purpose**: Specifies how to handle authentication failures

**Record Details**:
- **Type**: TXT
- **Host**: `_dmarc`
- **Value**: `v=DMARC1; p=none; rua=mailto:dmarc@wwmaa.com`
- **TTL**: 3600

**Full Record**:
```
Type: TXT
Name: _dmarc.newsletter.wwmaa.com
Value: v=DMARC1; p=none; rua=mailto:dmarc@wwmaa.com; pct=100; adkim=r; aspf=r
```

### CNAME Record (Optional - Tracking)

**Purpose**: Enables click and open tracking

**Record Details**:
- **Type**: CNAME
- **Host**: `track`
- **Value**: `track.beehiiv.com`
- **TTL**: 3600

### Verification Steps

1. Add all DNS records through your domain registrar (e.g., Cloudflare, GoDaddy)
2. Wait 15-30 minutes for DNS propagation
3. Return to BeeHiiv dashboard
4. Click "Verify DNS Records"
5. If successful, status will show "Verified ✓"

### DNS Propagation Check

Use online tools to verify:
- [DNS Checker](https://dnschecker.org)
- [MXToolbox](https://mxtoolbox.com/SuperTool.aspx)

Example check:
```bash
# Check DKIM
dig TXT beehiiv._domainkey.newsletter.wwmaa.com

# Check SPF
dig TXT newsletter.wwmaa.com

# Check DMARC
dig TXT _dmarc.newsletter.wwmaa.com
```

## Email Template Creation

Templates are stored in `/backend/templates/email/` and can be customized.

### Available Templates

1. **welcome.html** - Welcome email for new subscribers
2. **weekly_digest.html** - Weekly newsletter digest
3. **event_announcement.html** - Event announcement emails

### Template Variables

Templates use Mustache syntax for variables:

```html
{{subscriber_name}}     - Subscriber's name
{{website_url}}         - Main website URL
{{unsubscribe_url}}     - Unsubscribe link
{{current_date}}        - Current date
{{event_title}}         - Event name
{{event_date}}          - Event date/time
```

### Creating Templates in BeeHiiv

1. Go to **Content** → **Email Templates**
2. Click "Create Template"
3. Name the template (e.g., "WWMAA Welcome Email")
4. Copy content from `/backend/templates/email/welcome.html`
5. Customize branding, colors, and content
6. Save template

### Template Best Practices

- Keep email width at 600px for mobile compatibility
- Use inline CSS for styling
- Test templates across email clients (Gmail, Outlook, Apple Mail)
- Include unsubscribe link in footer (required by law)
- Use alt text for images
- Keep subject lines under 50 characters

## Running the Setup Script

After completing the above steps, run the automated setup script.

### Prerequisites

1. All environment variables set in `.env`
2. DNS records configured
3. API key generated

### Execute Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run setup script
python scripts/setup_beehiiv.py

# With test email
python scripts/setup_beehiiv.py --test-email your.email@example.com
```

### Setup Process

The script will:
1. ✓ Validate API key
2. ✓ Connect to ZeroDB
3. ✓ Fetch publication information
4. ✓ Check DNS records (DKIM, SPF, DMARC)
5. ✓ Save configuration to database
6. ✓ Send test email (if requested)

### Expected Output

```
============================================================
Starting BeeHiiv Setup
============================================================
Validating BeeHiiv API key...
API key is valid
Connecting to ZeroDB...
Connected to ZeroDB successfully
Fetching publication information...
Publication: WWMAA Newsletter
Checking DKIM configuration...
DKIM record found for beehiiv._domainkey.newsletter.wwmaa.com
Checking SPF configuration...
SPF record correctly configured for newsletter.wwmaa.com
Checking DMARC configuration...
DMARC record found for _dmarc.newsletter.wwmaa.com
Saving configuration to ZeroDB...
Created new configuration (ID: a1b2c3d4-...)
Sending test email to test@example.com...
Test email sent successfully
============================================================
Setup Summary
============================================================
API Key: Valid
Publication ID: pub_xxxxxxxxxxxxx
Custom Domain: newsletter.wwmaa.com
From Email: newsletter@wwmaa.com
DKIM: Configured
SPF: Configured
DMARC: Configured
============================================================
Setup completed successfully!
```

## Testing the Integration

### 1. Test API Connection

```bash
curl -X GET https://api.beehiiv.com/v2/publications/{publication_id} \
  -H "Authorization: Bearer {api_key}"
```

### 2. Send Test Email via API

```python
from services.beehiiv_service import BeeHiivService

service = BeeHiivService()
result = service.send_test_email(
    email="test@example.com",
    subject="BeeHiiv Test",
    content="<h1>Test Email</h1><p>Integration working!</p>"
)
print(result)
```

### 3. Add Test Subscriber

```python
result = service.add_subscriber(
    email="test@example.com",
    name="Test User",
    metadata={"source": "setup_test"}
)
```

### 4. Check Subscriber Stats

```bash
# Via admin API
curl -X GET http://localhost:8000/api/admin/newsletter/stats \
  -H "Authorization: Bearer {admin_token}"
```

### 5. Verify Email Deliverability

1. Send test email to multiple email providers:
   - Gmail: test@gmail.com
   - Outlook: test@outlook.com
   - Yahoo: test@yahoo.com
2. Check spam folders
3. Verify DKIM signature in email headers
4. Check SPF pass/fail in headers

## Troubleshooting

### Issue: API Key Invalid

**Symptoms**: Setup script fails with "Invalid API key"

**Solutions**:
1. Verify API key is copied correctly (no extra spaces)
2. Check key hasn't been revoked in BeeHiiv dashboard
3. Ensure key has correct permissions (Read & Write)
4. Generate new API key if needed

### Issue: DNS Records Not Verifying

**Symptoms**: BeeHiiv shows "DNS records not found"

**Solutions**:
1. Wait longer for DNS propagation (up to 48 hours)
2. Verify records are added to correct subdomain (newsletter.wwmaa.com)
3. Check for typos in record values
4. Use `dig` or online DNS checker to verify records exist
5. Clear DNS cache: `sudo dscacheutil -flushcache` (macOS)

### Issue: Emails Going to Spam

**Symptoms**: Test emails land in spam folder

**Solutions**:
1. Verify DKIM, SPF, and DMARC are passing
2. Check sender reputation (use [mail-tester.com](https://www.mail-tester.com))
3. Warm up domain by sending gradually increasing volume
4. Avoid spam trigger words in subject/content
5. Ensure unsubscribe link is present
6. Ask recipients to whitelist sender address

### Issue: Rate Limit Exceeded

**Symptoms**: API returns 429 error

**Solutions**:
1. BeeHiiv allows 1000 requests/hour
2. Implement exponential backoff (already in service)
3. Batch operations where possible
4. Contact BeeHiiv support for rate limit increase

### Issue: Subscriber Sync Failing

**Symptoms**: Subscribers not syncing between ZeroDB and BeeHiiv

**Solutions**:
1. Check API key permissions
2. Verify list IDs are correct
3. Check error logs: `tail -f logs/app.log`
4. Run manual sync: `POST /api/admin/newsletter/sync`
5. Verify database connectivity

### Issue: Templates Not Rendering

**Symptoms**: Email templates show broken HTML or missing variables

**Solutions**:
1. Verify template syntax (Mustache format: `{{variable}}`)
2. Check all required variables are provided
3. Test HTML in email testing tool (Litmus, Email on Acid)
4. Ensure inline CSS is used (not external stylesheets)
5. Validate HTML with W3C validator

### Getting Help

1. **BeeHiiv Documentation**: [developers.beehiiv.com](https://developers.beehiiv.com)
2. **BeeHiiv Support**: support@beehiiv.com
3. **Internal Logs**: Check `/backend/logs/beehiiv.log`
4. **Admin Dashboard**: Monitor stats at `/api/admin/newsletter/stats`

## Cost Breakdown

### BeeHiiv Pricing Tiers

#### Launch (Free)
- Up to 2,500 subscribers
- Unlimited email sends
- Basic analytics
- No custom domain
- **Best for**: Initial testing and small lists

#### Grow ($42/month)
- Up to 10,000 subscribers
- Custom domain
- Advanced analytics
- Remove BeeHiiv branding
- Priority support
- **Best for**: Growing organization

#### Scale ($84/month)
- Up to 25,000 subscribers
- Everything in Grow
- API access
- Advanced segmentation
- Custom integrations
- **Best for**: WWMAA (recommended)

#### Max ($250/month)
- Up to 100,000 subscribers
- Everything in Scale
- Dedicated account manager
- Custom SLA
- White-glove onboarding
- **Best for**: Large organizations

### Cost Recommendations

**Current Stage**: Start with **Launch (Free)** for setup and testing

**When to Upgrade**:
- Reach 2,000 subscribers → Upgrade to **Grow**
- Need custom domain → Upgrade to **Grow**
- Reach 8,000 subscribers → Upgrade to **Scale**
- Need API access → Upgrade to **Scale**

### Additional Costs

- **Domain Registration**: $12/year (newsletter.wwmaa.com)
- **Email Deliverability Services**: Optional (SendGrid, Postmark)
- **Template Design**: One-time ($0 - $500 for professional design)

### Return on Investment

- Automated member communications
- Increased event attendance through targeted emails
- Higher member engagement
- Professional brand image
- Reduced manual email management time

## Next Steps

After successful setup:

1. ✓ Subscribe test users to each list
2. ✓ Create first newsletter draft
3. ✓ Schedule weekly digest automation
4. ✓ Set up subscriber sync cron job
5. ✓ Configure welcome email automation
6. ✓ Monitor analytics and engagement
7. ✓ Implement US-058 (Subscriber Management)
8. ✓ Implement US-059 (Newsletter Composition)

## Appendix

### API Rate Limits

- 1000 requests per hour
- Resets every hour
- 429 error when exceeded

### Webhook Events

BeeHiiv supports webhooks for:
- Subscriber added
- Subscriber unsubscribed
- Email opened
- Link clicked
- Bounce reported

Configure at: Settings → Webhooks

### Supported Email Clients

Tested and optimized for:
- Gmail (Web & Mobile)
- Apple Mail (iOS & macOS)
- Outlook (Web, Desktop & Mobile)
- Yahoo Mail
- Samsung Email
- Thunderbird

### Resources

- [BeeHiiv API Documentation](https://developers.beehiiv.com/docs/v2/)
- [Email Design Best Practices](https://www.emailonacid.com/blog/)
- [DMARC Analyzer](https://dmarc.org/)
- [Email Testing Tools](https://www.mail-tester.com/)
