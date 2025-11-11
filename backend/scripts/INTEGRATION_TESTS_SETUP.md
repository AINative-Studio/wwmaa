# Integration Tests Setup Guide

This guide will help you configure real API credentials to run the Sprint 6 integration tests.

## Quick Setup Checklist

- [ ] Cloudflare Account and API Token
- [ ] BeeHiiv API Key and Publication ID
- [ ] ZeroDB API Key (already configured)
- [ ] Update `.env` file with real credentials

## Step-by-Step Setup

### 1. Cloudflare Setup

#### Get Your Cloudflare Account ID

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Click on any website in your account
3. Scroll down in the Overview page
4. Copy your **Account ID** from the right sidebar
5. Add to `.env`:
   ```bash
   CLOUDFLARE_ACCOUNT_ID=your-actual-account-id-here
   ```

#### Create Cloudflare API Token

1. Go to [API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Click "Create Token"
3. Choose "Create Custom Token"
4. Configure permissions:
   - **Account** > **Cloudflare Calls** > **Edit**
   - **Account** > **Stream** > **Edit**
5. Click "Continue to summary"
6. Click "Create Token"
7. Copy the token (you'll only see it once!)
8. Add to `.env`:
   ```bash
   CLOUDFLARE_API_TOKEN=your-actual-api-token-here
   ```

#### Create Cloudflare Calls App (Optional)

1. Go to [Cloudflare Calls](https://dash.cloudflare.com/?to=/:account/calls)
2. Click "Create Application"
3. Enter a name: "WWMAA Live Sessions"
4. Copy the **App ID**
5. Add to `.env`:
   ```bash
   CLOUDFLARE_CALLS_APP_ID=your-actual-app-id-here
   ```

### 2. BeeHiiv Setup

#### Get Your BeeHiiv API Key

1. Log in to [BeeHiiv](https://app.beehiiv.com/)
2. Go to Settings > Integrations > API
3. Click "Create API Key"
4. Enter a name: "WWMAA Integration Tests"
5. Select permissions:
   - **Subscriptions**: Read & Write
   - **Posts**: Read
6. Click "Create"
7. Copy your API key
8. Add to `.env`:
   ```bash
   BEEHIIV_API_KEY=your-actual-api-key-here
   ```

#### Get Your Publication ID

1. In BeeHiiv dashboard, go to Settings > General
2. Look for "Publication ID" or "Organization ID"
3. Or find it in your publication URL: `app.beehiiv.com/publications/{publication-id}`
4. Add to `.env`:
   ```bash
   BEEHIIV_PUBLICATION_ID=your-actual-publication-id-here
   ```

### 3. ZeroDB Setup

ZeroDB credentials should already be configured in your `.env`:

```bash
ZERODB_API_KEY=kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM
ZERODB_API_BASE_URL=https://api.ainative.studio
ZERODB_EMAIL=admin@ainative.studio
ZERODB_PASSWORD=Admin2025!Secure
```

If these are not set, contact the AINative team for credentials.

### 4. Verify Your `.env` File

Your `.env` file should now look like this:

```bash
# ============================================
# Sprint 6 Integration Test Credentials
# ============================================

# Cloudflare Configuration
CLOUDFLARE_ACCOUNT_ID=abc123def456  # Your actual account ID
CLOUDFLARE_API_TOKEN=xyz789...      # Your actual API token
CLOUDFLARE_CALLS_APP_ID=app123      # Your actual app ID (optional)

# BeeHiiv Configuration
BEEHIIV_API_KEY=bee_live_...        # Your actual API key
BEEHIIV_PUBLICATION_ID=pub_123      # Your actual publication ID

# ZeroDB Configuration (already set)
ZERODB_API_KEY=kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM
ZERODB_API_BASE_URL=https://api.ainative.studio
ZERODB_EMAIL=admin@ainative.studio
ZERODB_PASSWORD=Admin2025!Secure

# Other required credentials...
JWT_SECRET=wwmaa-secret-key-change-in-production-2025
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
POSTMARK_API_KEY=...
```

## Testing Your Setup

### 1. Verify Credentials are Loaded

```bash
# Check if .env file exists
ls -la .env

# Verify environment variables (from project root)
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Cloudflare Account:', os.getenv('CLOUDFLARE_ACCOUNT_ID'))"
```

### 2. Run Integration Tests

```bash
# From project root
python3 backend/scripts/test_integrations.py
```

### 3. Expected Results

All tests should pass:
```
✅ PASSED - Cloudflare Calls
✅ PASSED - Cloudflare Stream
✅ PASSED - BeeHiiv
✅ PASSED - ZeroDB

Status: ✅ ALL TESTS PASSED
```

## Troubleshooting

### Issue: "Missing credentials - CLOUDFLARE_ACCOUNT_ID"

**Solution**: Ensure your `.env` file has the actual account ID, not a placeholder.

```bash
# Wrong
CLOUDFLARE_ACCOUNT_ID=your-cloudflare-account-id

# Correct
CLOUDFLARE_ACCOUNT_ID=abc123def456ghi789
```

### Issue: "Cloudflare Calls API error: Invalid API token"

**Solutions**:
1. Verify token has correct permissions (Calls: Edit, Stream: Edit)
2. Check token is not expired
3. Ensure no extra spaces in `.env` file
4. Regenerate token if needed

### Issue: "BeeHiiv API error: 401 unauthorized"

**Solutions**:
1. Verify API key is correct
2. Check API key has "Subscriptions: Read & Write" permission
3. Ensure publication ID matches your BeeHiiv account
4. Try regenerating the API key

### Issue: "ZeroDB connection timeout"

**Solutions**:
1. Verify internet connectivity
2. Check firewall settings
3. Ensure `ZERODB_API_BASE_URL` is correct
4. Contact AINative support if credentials are invalid

### Issue: Tests hang or timeout

**Solutions**:
1. Check your internet connection
2. Verify API endpoints are accessible:
   ```bash
   curl https://api.cloudflare.com/client/v4/user/tokens/verify \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
3. Increase timeout in script if on slow connection

## Security Best Practices

### 1. Keep Credentials Secret

```bash
# Ensure .env is in .gitignore
echo ".env" >> .gitignore

# Never commit real credentials
git status  # Should NOT show .env as changed
```

### 2. Use Separate Test Credentials

- Create separate API keys for testing
- Use test/sandbox mode where available
- Rotate keys regularly

### 3. Limit Permissions

- Only grant minimum required permissions
- Use read-only where possible
- Enable IP restrictions if available

### 4. Monitor Usage

- Check API usage dashboards regularly
- Set up usage alerts
- Review billing to catch unexpected charges

## Environment-Specific Setup

### Development Environment

```bash
# .env.development
CLOUDFLARE_ACCOUNT_ID=dev-account-123
CLOUDFLARE_API_TOKEN=dev-token-xyz
```

### Staging Environment

```bash
# .env.staging
CLOUDFLARE_ACCOUNT_ID=staging-account-456
CLOUDFLARE_API_TOKEN=staging-token-abc
```

### Production Environment

```bash
# .env.production (stored in secure vault)
CLOUDFLARE_ACCOUNT_ID=prod-account-789
CLOUDFLARE_API_TOKEN=prod-token-def
```

## CI/CD Setup

For GitHub Actions, add credentials as repository secrets:

1. Go to repository Settings > Secrets and variables > Actions
2. Add each credential as a secret:
   - `CLOUDFLARE_ACCOUNT_ID`
   - `CLOUDFLARE_API_TOKEN`
   - `BEEHIIV_API_KEY`
   - `BEEHIIV_PUBLICATION_ID`
   - `ZERODB_API_KEY`
   - `ZERODB_API_BASE_URL`

3. Reference in workflow:
   ```yaml
   env:
     CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
     CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
   ```

## Cost Management

### Estimated Costs

| Service | Test Cost | Monthly (Daily Run) | Notes |
|---------|-----------|---------------------|-------|
| Cloudflare Calls | $0.01 | $0.30 | Per room created |
| Cloudflare Stream | $0.02 | $0.60 | Per video upload |
| BeeHiiv | $0.00 | $0.00 | Free tier |
| ZeroDB | $0.00 | $0.00 | Read operations |
| **Total** | **$0.03** | **$0.90** | Estimated |

### Cost Optimization Tips

1. **Run tests selectively**
   ```bash
   # Only test specific service
   # (modify script to skip others)
   ```

2. **Use test quotas**
   - Set up separate test accounts with limited quotas
   - Monitor usage in dashboards

3. **Schedule wisely**
   - Run daily instead of on every commit
   - Use manual triggers for CI/CD

4. **Clean up aggressively**
   - Verify cleanup tasks complete
   - Manually audit resources weekly

## Getting Help

### Documentation Links

- [Cloudflare Calls API](https://developers.cloudflare.com/calls/)
- [Cloudflare Stream API](https://developers.cloudflare.com/stream/)
- [BeeHiiv API](https://developers.beehiiv.com/docs/v2/)
- [ZeroDB Documentation](https://docs.ainative.studio/)

### Support Channels

- **Cloudflare**: [Community Forum](https://community.cloudflare.com/)
- **BeeHiiv**: support@beehiiv.com
- **ZeroDB**: Contact AINative team
- **WWMAA**: Check project documentation

## Next Steps

Once setup is complete:

1. ✅ Run integration tests: `python3 backend/scripts/test_integrations.py`
2. ✅ Review test output in `integration-test-results.txt`
3. ✅ Add tests to CI/CD pipeline
4. ✅ Schedule regular test runs
5. ✅ Monitor API usage and costs
6. ✅ Document any issues or edge cases

---

**Last Updated**: 2025-11-10
**Maintained By**: WWMAA Backend Team
