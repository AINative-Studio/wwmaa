# Custom Domain Quick Reference - wwmaa.com

## One-Page Cheat Sheet

### Current URLs
- **Frontend (Railway):** https://wwmaa.ainative.studio
- **Frontend (Custom):** https://wwmaa.com (after setup)
- **Backend:** https://athletic-curiosity-production.up.railway.app

### Setup Sequence

```
1. Railway: Add custom domains (5 min)
2. DNS: Add records at registrar (10 min)
3. Wait: DNS propagation (5-60 min)
4. Wait: SSL certificate (5-15 min after DNS)
5. Config: Update environment variables (5 min)
6. Deploy: Redeploy services (5 min)
7. Test: Verify functionality (15 min)
```

### Railway Configuration

**Add domains:**
```
Service: WWMAA-FRONTEND
Settings → Domains → + Custom Domain
- wwmaa.com
- www.wwmaa.com
```

**DNS records Railway provides:**
```
Type: A or CNAME
Name: @
Value: [copy from Railway]

Type: CNAME
Name: www
Value: [copy from Railway]
```

### DNS Configuration

**Cloudflare (Recommended):**
```
Type: CNAME, Name: @, Target: [railway-value], Proxy: On
Type: CNAME, Name: www, Target: [railway-value], Proxy: On
SSL/TLS: Full (strict)
```

**GoDaddy:**
```
Type: A, Host: @, Points to: [railway-ip]
Type: CNAME, Host: www, Points to: [railway-cname]
```

**Namecheap:**
```
Type: A Record, Host: @, Value: [railway-ip]
Type: CNAME, Host: www, Value: [railway-cname]
```

### Environment Variables

**Frontend (WWMAA-FRONTEND):**
```env
NEXT_PUBLIC_SITE_URL=https://wwmaa.com
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
PYTHON_ENV=production
```

**Backend (WWMAA-BACKEND):**
```env
PYTHON_ENV=production  # Must be set for correct CORS
```

Note: Backend CORS already configured in code for custom domains.

### Verification Commands

**Check DNS:**
```bash
dig wwmaa.com
dig www.wwmaa.com
nslookup wwmaa.com
```

**Check SSL:**
```bash
curl -I https://wwmaa.com
openssl s_client -connect wwmaa.com:443 -servername wwmaa.com
```

**Check CORS:**
```bash
curl -H "Origin: https://wwmaa.com" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     https://athletic-curiosity-production.up.railway.app/api/health
```

**Check backend:**
```bash
curl https://athletic-curiosity-production.up.railway.app/health
```

### Common Issues & Quick Fixes

**DNS not resolving:**
```bash
# Clear cache
sudo dscacheutil -flushcache  # macOS
ipconfig /flushdns             # Windows

# Check global propagation
# Visit: https://dnschecker.org
```

**CORS errors:**
```bash
# Verify backend environment
railway vars --service wwmaa-backend | grep PYTHON_ENV

# Should show: PYTHON_ENV=production
# If not, set it:
railway vars set PYTHON_ENV=production --service wwmaa-backend

# Then redeploy backend
```

**SSL pending:**
```
1. Verify DNS resolves (see above)
2. Wait 15 minutes after DNS propagates
3. Check Railway logs for SSL errors
```

**Mixed content warnings:**
```
1. Verify NEXT_PUBLIC_API_URL uses https://
2. Search for hardcoded http:// URLs in code
3. Update to https:// or relative URLs
4. Redeploy frontend
```

### Rollback (Emergency)

**Quick rollback - Frontend only:**
```bash
# Update environment variable in Railway dashboard
NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio

# Or via CLI:
railway vars set NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio --service wwmaa-frontend

# Save and redeploy (automatic)
```

Railway subdomain continues working immediately.

### Testing Checklist

```
□ https://wwmaa.com loads
□ https://www.wwmaa.com loads
□ SSL certificate valid (green padlock)
□ No CORS errors in browser console
□ Login works
□ Logout works
□ API calls succeed
□ All pages navigate correctly
□ No security warnings
□ Mobile works
```

### Post-Deployment Updates

```
□ Update README.md
□ Update Google Search Console
□ Update Google Analytics
□ Update OAuth redirect URIs (if applicable)
□ Update Stripe webhooks (if applicable)
□ Update email templates
□ Update social media links
□ Set up uptime monitoring
```

### Important Notes

1. **Backend stays on Railway subdomain** - Only frontend uses custom domain
2. **CORS already configured** - No code changes needed, just ensure `PYTHON_ENV=production`
3. **DNS propagation varies** - Can take 5-60 minutes, sometimes longer
4. **SSL is automatic** - Railway provisions via Let's Encrypt
5. **Railway subdomain always works** - Keeps working as fallback

### Timeline

| Task | Time |
|------|------|
| Railway + DNS setup | 15 min |
| DNS propagation | 5-60 min |
| SSL provisioning | 5-15 min |
| Configuration | 10 min |
| Testing | 15 min |
| **Total** | **50-115 min** |

### Key URLs & Resources

- **Railway Dashboard:** https://railway.app/
- **DNS Checker:** https://dnschecker.org
- **SSL Test:** https://www.ssllabs.com/ssltest/
- **Railway Docs:** https://docs.railway.app/deploy/custom-domains

### File Locations

- **Backend CORS:** `/Users/aideveloper/Desktop/wwmaa/backend/config.py` (lines 512-543)
- **Documentation:** `/Users/aideveloper/Desktop/wwmaa/docs/DOMAIN_*.md`

### Support

If issues persist after following troubleshooting:
1. Check Railway status page
2. Review Railway logs: `railway logs`
3. Contact Railway support
4. Review detailed guide: `docs/DOMAIN_DEPLOYMENT_GUIDE.md`
