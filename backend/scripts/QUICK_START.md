# Integration Tests - Quick Start

## TL;DR

```bash
# 1. Update .env with real credentials
vim .env

# 2. Run tests
python3 backend/scripts/test_integrations.py

# 3. Check results
cat integration-test-results.txt
```

## Required Credentials

Add these to your `.env` file:

```bash
# Cloudflare
CLOUDFLARE_ACCOUNT_ID=your-actual-account-id
CLOUDFLARE_API_TOKEN=your-actual-api-token

# BeeHiiv
BEEHIIV_API_KEY=your-actual-api-key
BEEHIIV_PUBLICATION_ID=your-actual-publication-id

# ZeroDB (already configured)
ZERODB_API_KEY=kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM
ZERODB_API_BASE_URL=https://api.ainative.studio
```

## Get Credentials

### Cloudflare
1. Login: https://dash.cloudflare.com/
2. Get Account ID from any website's overview page
3. Create API Token: https://dash.cloudflare.com/profile/api-tokens
   - Permissions: Calls (Edit), Stream (Edit)

### BeeHiiv
1. Login: https://app.beehiiv.com/
2. Go to Settings > Integrations > API
3. Create API Key with "Subscriptions: Read & Write"
4. Get Publication ID from Settings > General

## What Gets Tested

✅ Cloudflare Calls - Create room & generate token
✅ Cloudflare Stream - Upload video & generate URL
✅ BeeHiiv - Add & remove subscriber
✅ ZeroDB - Connection & query collections

## Expected Cost

~$0.03 per test run

## Exit Codes

- `0` = All passed
- `1` = Some failed

## Troubleshooting

**Missing credentials?**
```bash
# Check .env file
cat .env | grep CLOUDFLARE
cat .env | grep BEEHIIV
```

**Tests failing?**
- Verify credentials are correct (not placeholders)
- Check API token permissions
- Ensure internet connectivity

**Need help?**
Read the full docs:
- `README_INTEGRATION_TESTS.md` - Detailed documentation
- `INTEGRATION_TESTS_SETUP.md` - Setup guide

## Example Output

```
╔══════════════════════════════════════════════╗
║   Sprint 6 Integration Tests - Real API      ║
╚══════════════════════════════════════════════╝

[1/4] Testing Cloudflare Calls...
  ✅ PASSED (2.3s)

[2/4] Testing Cloudflare Stream...
  ✅ PASSED (5.1s)

[3/4] Testing BeeHiiv...
  ✅ PASSED (1.8s)

[4/4] Testing ZeroDB...
  ✅ PASSED (0.5s)

Status: ✅ ALL TESTS PASSED
Cost: $0.03
```

---

**Full Documentation**: See `README_INTEGRATION_TESTS.md`
