# Custom Domain Setup for wwmaa.com

## Prerequisites
- Access to domain registrar (GoDaddy, Namecheap, Cloudflare, etc.)
- Access to Railway dashboard
- Domain ownership verified

## Step 1: Railway Custom Domain Configuration

### Frontend Domain Setup
1. Go to Railway dashboard → WWMAA-FRONTEND service
2. Click Settings → Domains
3. Click "+ Custom Domain"
4. Add both domains:
   - `wwmaa.com`
   - `www.wwmaa.com`
5. Railway will provide DNS records (see below)

### Expected DNS Records from Railway
Railway will provide records similar to:
```
Type: CNAME
Name: www
Value: [unique-id].up.railway.app

Type: A (or ALIAS/ANAME)
Name: @
Value: [ip-address] OR [cname-value]
```

## Step 2: DNS Configuration at Registrar

### If using Cloudflare:
1. Login to Cloudflare dashboard
2. Select your domain `wwmaa.com`
3. Go to DNS → Records
4. Add records:
```
Type: CNAME, Name: www, Target: [railway-value], Proxy: On, TTL: Auto
Type: CNAME, Name: @, Target: [railway-value], Proxy: On, TTL: Auto
```
Note: Cloudflare's CNAME flattening allows CNAME for root domain

### If using GoDaddy/Namecheap:
1. Login to registrar
2. Go to DNS Management
3. Add records:
```
Type: CNAME, Host: www, Points to: [railway-value], TTL: 600
Type: A, Host: @, Points to: [railway-ip], TTL: 600
```

### If using Route53:
1. Go to Route53 console
2. Select hosted zone for wwmaa.com
3. Create records:
```
Type: CNAME, Name: www.wwmaa.com, Value: [railway-value]
Type: A, Name: wwmaa.com, Value: [railway-ip]
OR
Type: ALIAS, Name: wwmaa.com, Alias Target: [railway-alias]
```

## Step 3: Wait for DNS Propagation

DNS propagation typically takes 5-60 minutes.

### Check DNS Propagation:
```bash
# Check DNS resolution
dig wwmaa.com
dig www.wwmaa.com

# Check from multiple locations
https://dnschecker.org
```

### Verify DNS is working:
```bash
# Should return Railway IP
nslookup wwmaa.com

# Should return Railway CNAME
nslookup www.wwmaa.com
```

## Step 4: SSL Certificate

Railway automatically provisions SSL certificates via Let's Encrypt:
- Starts after DNS resolves to Railway
- Takes 5-15 minutes
- Check Railway dashboard: "SSL Certificate: Active"

### Verify SSL:
```bash
# Should show valid certificate
curl -I https://wwmaa.com
```

## Step 5: Update Environment Variables

### Frontend Environment Variables (Railway - WWMAA-FRONTEND):
```env
NEXT_PUBLIC_SITE_URL=https://wwmaa.com
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
```

Redeploy frontend after updating environment variables.

## Step 6: Update Backend CORS

Update `backend/config.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "https://wwmaa.com",
    "https://www.wwmaa.com",
    "https://wwmaa.ainative.studio",  # keep as fallback
]
```

Redeploy backend after updating CORS.

## Step 7: Testing

### Manual Testing:
1. Visit `https://wwmaa.com` - should load
2. Visit `https://www.wwmaa.com` - should redirect or load
3. Check SSL certificate (green padlock)
4. Test login functionality
5. Check browser console for CORS errors
6. Test API calls (Network tab)

### Automated Testing:
```bash
# Test homepage loads
curl -I https://wwmaa.com

# Test backend API from new domain
curl -H "Origin: https://wwmaa.com" https://athletic-curiosity-production.up.railway.app/health

# Test SSL certificate
openssl s_client -connect wwmaa.com:443 -servername wwmaa.com
```

## Troubleshooting

### Issue: DNS not resolving
**Solution:**
- Wait 5-60 minutes for propagation
- Clear local DNS cache: `sudo dscacheutil -flushcache` (Mac)
- Check with https://dnschecker.org

### Issue: SSL certificate pending
**Solution:**
- Ensure DNS points to Railway
- Wait for Let's Encrypt validation (5-15 min)
- Check Railway logs for SSL errors

### Issue: CORS errors
**Solution:**
- Update backend CORS allowed origins
- Redeploy backend service
- Clear browser cache and test

### Issue: Mixed content warnings
**Solution:**
- Ensure all assets use HTTPS URLs
- Update API_URL to use HTTPS
- Check for hardcoded HTTP URLs

## Post-Configuration Tasks

- [ ] Update Google Search Console with new domain
- [ ] Update Google Analytics property
- [ ] Update OAuth redirect URLs (if applicable)
- [ ] Update Stripe webhook URLs (if applicable)
- [ ] Update email templates with new domain
- [ ] Update documentation with new domain
- [ ] Update social media links
- [ ] Update README.md

## Verification Checklist

- [ ] `wwmaa.com` resolves to Railway
- [ ] SSL certificate active and valid
- [ ] Homepage loads successfully
- [ ] Login/logout works on custom domain
- [ ] API calls succeed (no CORS errors)
- [ ] All pages load correctly
- [ ] No security warnings in browser
- [ ] www redirects properly (if configured)
- [ ] Environment variables updated
- [ ] Backend CORS configured
- [ ] Documentation updated

## Timeline

- DNS configuration: 15 minutes
- DNS propagation: 5-60 minutes
- SSL certificate: 5-15 minutes after DNS
- Total estimated time: 1-2 hours

## Support Resources

- Railway Docs: https://docs.railway.app/deploy/custom-domains
- Let's Encrypt: https://letsencrypt.org/
- DNS Checker: https://dnschecker.org
