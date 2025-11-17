# WWMAA Platform - Client Credentials & Service Transition Checklist

**Purpose:** Transition from development/test credentials to client production credentials
**Date:** November 14, 2025
**Status:** ⚠️ Awaiting Client Action

---

## 🎯 Executive Summary

The WWMAA platform is currently running with **development and test credentials** provided by AINative Studio. To enable full production functionality, we need the client to provide production credentials for the following services, or authorize AINative Studio to create accounts on the client's behalf.

**Impact:** Until production credentials are provided:
- ⚠️ Payments are in **test mode** (no real transactions)
- ⚠️ Emails may not send properly
- ⚠️ Newsletter subscriptions not captured
- ⚠️ Analytics not tracking to client's account
- ⚠️ Domain using temporary subdomain

---

## 📋 Required Services & Credentials

### 1. 🔴 CRITICAL - Stripe Payment Processing

**Current Status:** Test mode with AINative Studio development keys

**Required for Production:**
- [ ] Stripe Account (client must create or provide access)
- [ ] Publishable Key (`pk_live_...`)
- [ ] Secret Key (`sk_live_...`)
- [ ] Webhook Signing Secret (`whsec_...`)
- [ ] Optional: Restricted API key for enhanced security

**Purpose:**
- Process membership subscription payments
- Handle recurring billing
- Manage payment disputes and refunds
- Generate invoices and receipts

**Impact if Not Provided:**
- ❌ **No real payments can be processed**
- ❌ Members cannot pay for subscriptions
- ❌ Renewal payments will fail
- ❌ Invoices will show "TEST MODE"

**How to Provide:**
1. **Option A (Recommended):** Client creates Stripe account and provides keys
   - Go to https://stripe.com
   - Create business account for WWMAA
   - Navigate to Developers → API Keys
   - Copy Publishable and Secret keys
   - Navigate to Developers → Webhooks
   - Create endpoint: `https://wwmaa.ainative.studio/api/webhooks/stripe`
   - Copy Webhook Signing Secret

2. **Option B:** Grant AINative Studio access to existing Stripe account
   - Add `dev@ainative.studio` as team member (restricted access)

3. **Option C:** AINative Studio creates account on client's behalf
   - Client provides business details (EIN, bank account)
   - AINative creates and configures account
   - Transfers ownership to client

**Configuration Location:** Admin Settings → Payment Gateway

---

### 2. 🟠 HIGH PRIORITY - Email Service (SMTP/SendGrid)

**Current Status:** Using development SMTP (limited sending)

**Required for Production:**
- [ ] Email service provider choice:
  - **Option A:** SMTP Server credentials (if client has existing email server)
  - **Option B:** SendGrid account (recommended for transactional emails)
  - **Option C:** AWS SES account
  - **Option D:** Mailgun account

**Credentials Needed (varies by provider):**

**If SMTP:**
- [ ] SMTP Host (e.g., `smtp.gmail.com`)
- [ ] SMTP Port (usually 587 or 465)
- [ ] SMTP Username
- [ ] SMTP Password
- [ ] From Name (e.g., "World Wide Martial Arts Association")
- [ ] From Email (e.g., `noreply@wwmaa.com`)

**If SendGrid:**
- [ ] SendGrid API Key
- [ ] Verified Sender Email
- [ ] Optional: Domain Authentication (DNS records)

**Purpose:**
- Send welcome emails to new members
- Password reset emails
- Application status notifications
- Payment receipt emails
- Event RSVP confirmations
- Newsletter confirmations

**Impact if Not Provided:**
- ⚠️ Emails may not send reliably
- ⚠️ Users cannot reset passwords
- ⚠️ No email notifications for critical events
- ⚠️ Poor user experience

**How to Provide:**
1. **SendGrid (Recommended):**
   - Sign up at https://sendgrid.com
   - Verify email domain (requires DNS records)
   - Create API key with "Mail Send" permissions
   - Provide API key to AINative Studio

2. **SMTP:**
   - Provide credentials via secure method (password manager, encrypted email)

**Configuration Location:** Admin Settings → Email Configuration

---

### 3. 🟠 HIGH PRIORITY - Domain Transfer (wwmaa.com)

**Current Status:** Using temporary subdomain `wwmaa.ainative.studio`

**Required for Production:**
- [ ] Domain registrar access (where wwmaa.com is registered)
- [ ] DNS management access OR transfer to Cloudflare
- [ ] SSL certificate (auto-provisioned by Cloudflare)

**DNS Records Needed:**
```
Type    Name    Value                           TTL
A       @       76.76.21.21 (Railway IP)       Auto
CNAME   www     wwmaa.ainative.studio          Auto
TXT     @       (verification records)          Auto
```

**Purpose:**
- Serve platform at wwmaa.com (primary domain)
- Professional email addresses (@wwmaa.com)
- SSL certificate for secure connections
- SEO and branding

**Impact if Not Provided:**
- ⚠️ Users must access via `wwmaa.ainative.studio`
- ⚠️ Less professional branding
- ⚠️ Email addresses cannot use @wwmaa.com
- ⚠️ SEO impact (domain authority)

**How to Provide:**
1. **Option A:** Transfer DNS to Cloudflare (recommended)
   - Client adds wwmaa.com to Cloudflare account
   - Updates nameservers at registrar
   - AINative configures DNS records

2. **Option B:** Provide DNS management access
   - Client provides login credentials to current DNS provider
   - AINative adds required DNS records

3. **Option C:** Client adds records manually
   - AINative provides list of DNS records
   - Client adds them to current DNS provider

**Configuration Location:** Domain registrar + Cloudflare dashboard

---

### 4. 🟡 MEDIUM PRIORITY - BeeHiiv Newsletter Platform

**Current Status:** Test integration with development API key

**Required for Production:**
- [ ] BeeHiiv Account
- [ ] Production API Key
- [ ] Publication ID
- [ ] Optional: Custom domain for newsletter

**Purpose:**
- Newsletter subscription management
- Automated email campaigns
- Blog content distribution
- Member communication

**Impact if Not Provided:**
- ⚠️ Newsletter subscriptions not captured
- ⚠️ Blog content not synced
- ⚠️ No automated email campaigns

**How to Provide:**
1. Sign up at https://beehiiv.com
2. Create publication for WWMAA
3. Navigate to Settings → API
4. Generate API key
5. Provide to AINative Studio

**Configuration Location:** Environment variables or Admin Settings

---

### 5. 🟡 MEDIUM PRIORITY - Google Analytics 4

**Current Status:** No analytics tracking (or using AINative's GA4)

**Required for Production:**
- [ ] Google Analytics 4 account
- [ ] Measurement ID (`G-XXXXXXXXXX`)
- [ ] Optional: Google Tag Manager container ID

**Purpose:**
- Website traffic analytics
- User behavior tracking
- Conversion tracking
- Marketing campaign performance

**Impact if Not Provided:**
- ⚠️ No analytics data collected
- ⚠️ Cannot measure user engagement
- ⚠️ No conversion tracking
- ⚠️ Missing marketing insights

**How to Provide:**
1. Create GA4 account at https://analytics.google.com
2. Set up property for wwmaa.com
3. Copy Measurement ID
4. Provide to AINative Studio

**Configuration Location:** Environment variables

---

### 6. 🟢 OPTIONAL - Cloudflare Account Access

**Current Status:** Using AINative Studio's Cloudflare account

**Required for Client Ownership:**
- [ ] Cloudflare account (free or pro tier)
- [ ] Add AINative Studio as collaborator OR
- [ ] Transfer zone to AINative Studio account (temporary)

**Services Configured:**
- Cloudflare WAF (Web Application Firewall)
- Cloudflare Stream (video hosting)
- Cloudflare Calls (WebRTC live sessions)
- DDoS protection
- SSL/TLS encryption

**Impact if Not Provided:**
- ✅ Platform works fine with current setup
- ⚠️ Client doesn't own/control CDN settings
- ⚠️ Billing goes through AINative Studio

**How to Transition:**
1. Client creates Cloudflare account
2. Adds AINative as collaborator
3. AINative migrates configuration
4. Client takes over billing

**Configuration Location:** Cloudflare dashboard

---

### 7. 🟢 OPTIONAL - Strapi CMS Hosting

**Current Status:** Strapi deployed on Railway, using AINative credentials

**Required for Client Ownership:**
- [ ] Railway account OR separate Strapi hosting
- [ ] Database for Strapi (PostgreSQL recommended)
- [ ] Media storage (S3, Cloudflare R2, etc.)

**Purpose:**
- Content management for blog posts
- Manage site pages (Programs, About, etc.)
- Media library
- SEO metadata

**Impact if Not Provided:**
- ✅ Current setup works
- ⚠️ Client doesn't own CMS
- ⚠️ Billing through AINative

**How to Transition:**
- AINative can transfer Strapi instance to client's Railway account
- Or migrate to client's preferred hosting

**Configuration Location:** Railway dashboard or client hosting

---

### 8. 🟢 OPTIONAL - Error Tracking (Sentry)

**Current Status:** Not configured (using Railway logs)

**Required if Desired:**
- [ ] Sentry account
- [ ] DSN (Data Source Name)
- [ ] Project setup

**Purpose:**
- Real-time error tracking
- Performance monitoring
- User session replay
- Alert notifications

**Impact if Not Provided:**
- ✅ Logging works via Railway
- ⚠️ Less sophisticated error tracking
- ⚠️ No alerting system

**How to Provide:**
1. Sign up at https://sentry.io
2. Create project
3. Copy DSN
4. Provide to AINative Studio

**Configuration Location:** Environment variables

---

## 📅 Timeline & Priority

### Week 1 (This Week) - URGENT
- [ ] **Stripe Production Keys** - Needed for any payment testing
- [ ] **Email Service** - Needed for user notifications

### Week 2 (Next Week) - HIGH PRIORITY
- [ ] **Domain Transfer** - For professional branding
- [ ] **BeeHiiv API** - For newsletter functionality
- [ ] **Google Analytics** - For traffic tracking

### Week 3 (Before Launch) - NICE TO HAVE
- [ ] **Cloudflare Transfer** - For client ownership
- [ ] **Strapi Ownership** - For CMS control
- [ ] **Sentry Setup** - For advanced monitoring

---

## 🔐 Security Best Practices

When sharing credentials:
1. **DO NOT** send credentials via plain email
2. **DO** use a password manager with sharing (1Password, LastPass)
3. **DO** use encrypted communication (Signal, ProtonMail)
4. **DO** enable 2FA on all accounts
5. **DO** use environment-specific keys (separate test/production)
6. **DO** rotate keys after sharing with contractors

---

## 📧 How to Submit Credentials to AINative Studio

**Secure Methods:**

1. **Recommended: 1Password** (if client has account)
   - Create shared vault
   - Invite `dev@ainative.studio`
   - Add credentials to vault

2. **Alternative: Encrypted Email**
   - Use ProtonMail or other encrypted email
   - Send to `dev@ainative.studio`
   - Include: Service name, environment (prod/test), credential type

3. **Via Project Management Tool**
   - If client uses Asana/Monday/Jira
   - Create secure task with credentials
   - Assign to AINative Studio

4. **Screen Share Setup Call**
   - Schedule call with AINative team
   - Client logs into services
   - AINative configures on behalf of client
   - No credentials shared directly

---

## 🚀 Next Steps

1. **Client Reviews This Checklist** (30 minutes)
2. **Client Chooses Approach for Each Service** (1-2 hours)
3. **Credentials Shared Securely** (1-3 days)
4. **AINative Configures Production** (1-2 hours per service)
5. **Testing & Verification** (1 day)
6. **Production Go-Live** (Week 3)

---

## ❓ FAQ

**Q: Can AINative Studio create these accounts on our behalf?**
A: Yes! We can create accounts for most services (Stripe, SendGrid, GA4, BeeHiiv) using client's business information. We'll transfer ownership immediately after setup.

**Q: What if we already have some of these services?**
A: Perfect! Just provide the credentials for existing accounts. We'll integrate with what you have.

**Q: Do we need all of these services immediately?**
A: No. Stripe and Email are critical for Week 2. Others can wait until Week 3 or post-launch.

**Q: Will there be ongoing costs for these services?**
A: Most have free tiers sufficient for early stage:
- Stripe: Free (charges 2.9% + $0.30 per transaction)
- SendGrid: Free tier (100 emails/day)
- BeeHiiv: Free tier available
- GA4: Completely free
- Cloudflare: Free tier sufficient

**Q: Who pays for these services after launch?**
A: Client pays directly once accounts are transferred to client ownership.

**Q: What happens if we don't provide credentials by Week 3?**
A: Platform will remain in test mode. Payments won't work, emails may be unreliable, and we can't launch publicly.

---

## 📞 Contact

**For Questions About This Checklist:**
- Email: dev@ainative.studio
- Subject: "WWMAA Credentials - [Service Name]"

**To Submit Credentials:**
- Use secure method outlined above
- Include: Service name, environment, all required fields
- CC project manager if applicable

---

*Document Prepared By: AINative Studio*
*Date: November 14, 2025*
*Last Updated: November 14, 2025*
*Version: 1.0*
