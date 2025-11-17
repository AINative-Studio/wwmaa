# DNS Configuration Checklist for wwmaa.com

## Pre-Configuration
- [ ] Verify domain ownership of wwmaa.com
- [ ] Access to domain registrar dashboard
- [ ] Access to Railway dashboard
- [ ] Identify which registrar (Cloudflare, GoDaddy, Namecheap, etc.)

## Railway Configuration
- [ ] Login to Railway dashboard
- [ ] Navigate to WWMAA-FRONTEND service
- [ ] Go to Settings → Domains
- [ ] Click "+ Custom Domain"
- [ ] Add `wwmaa.com`
- [ ] Add `www.wwmaa.com`
- [ ] Copy DNS records provided by Railway

## DNS Records to Add

Record the values Railway provides:

### For wwmaa.com (root domain):
```
Type: A (or ALIAS/CNAME depending on registrar)
Name: @ (or blank, or wwmaa.com)
Value: [Railway provides this]
TTL: 300 or Auto
```

### For www.wwmaa.com:
```
Type: CNAME
Name: www
Value: [Railway provides this]
TTL: 300 or Auto
```

## Registrar-Specific Steps

### Cloudflare:
1. DNS → Records → Add Record
2. Add CNAME for @ (root) - Cloudflare allows this
3. Add CNAME for www
4. Enable Proxy (orange cloud) - Optional but recommended
5. SSL/TLS → Full (strict)

### GoDaddy:
1. DNS Management → Add Record
2. Add A record for @ (root domain)
3. Add CNAME for www
4. TTL: 600 seconds (10 minutes)

### Namecheap:
1. Advanced DNS → Add New Record
2. Add A record for @ (root)
3. Add CNAME for www
4. TTL: Automatic or 300

### Route53 (AWS):
1. Hosted Zones → Select wwmaa.com
2. Create Record Set
3. For root: Use A or ALIAS record
4. For www: Use CNAME record

## Verification Steps

### Step 1: Wait for Propagation (5-60 min)
```bash
dig wwmaa.com
dig www.wwmaa.com
```

### Step 2: Check DNS Resolution
```bash
nslookup wwmaa.com
nslookup www.wwmaa.com
```

### Step 3: Check from Multiple Locations
- Visit: https://dnschecker.org
- Enter: wwmaa.com
- Check propagation globally

### Step 4: Verify Railway Shows "Active"
- Railway dashboard → WWMAA-FRONTEND → Settings → Domains
- Status should show "Active" for both domains

### Step 5: Check SSL Certificate
- Railway automatically provisions SSL
- Wait 5-15 minutes after DNS propagates
- Status should show "SSL Certificate: Active"

### Step 6: Test HTTPS Access
```bash
curl -I https://wwmaa.com
curl -I https://www.wwmaa.com
```

Should return:
- Status: 200 OK
- Valid SSL certificate
- No warnings

## Post-Configuration

- [ ] Update environment variables (NEXT_PUBLIC_SITE_URL)
- [ ] Update CORS in backend
- [ ] Redeploy frontend
- [ ] Redeploy backend
- [ ] Test login functionality
- [ ] Test API calls (check Network tab)
- [ ] Verify no CORS errors
- [ ] Update documentation

## Troubleshooting

### DNS not resolving:
- Wait longer (up to 60 minutes)
- Clear DNS cache: `sudo dscacheutil -flushcache`
- Check multiple DNS checkers

### SSL pending:
- Ensure DNS points to Railway
- Wait 15 minutes
- Check Railway logs

### CORS errors:
- Verify backend CORS includes new domain
- Redeploy backend
- Clear browser cache

## Timeline

| Task | Duration |
|------|----------|
| Railway configuration | 5 min |
| Add DNS records | 10 min |
| DNS propagation | 5-60 min |
| SSL provisioning | 5-15 min |
| Testing & verification | 15 min |
| **Total** | **40-105 min** |

## Detailed Railway Configuration Steps

### Step 1: Access Railway Dashboard
1. Go to https://railway.app/
2. Login with your credentials
3. Select the WWMAA project

### Step 2: Configure Frontend Service
1. Click on "WWMAA-FRONTEND" service card
2. Click "Settings" in the top navigation
3. Scroll to "Domains" section
4. You should see the current Railway subdomain listed

### Step 3: Add Custom Domain
1. Click the "+ Custom Domain" button
2. Enter `wwmaa.com` in the domain field
3. Click "Add Domain"
4. Railway will show the DNS records you need to add

### Step 4: Note the DNS Record Values
Railway will provide something like:

**For apex domain (wwmaa.com):**
```
Type: A
Name: @
Value: 104.238.123.45  # Example IP - yours will be different
```

OR

```
Type: CNAME
Name: @
Value: unique-identifier.up.railway.app
```

**For www subdomain:**
```
Type: CNAME
Name: www
Value: unique-identifier.up.railway.app
```

### Step 5: Add www Subdomain
1. Click "+ Custom Domain" again
2. Enter `www.wwmaa.com`
3. Click "Add Domain"
4. Note these DNS records as well

### Step 6: Implement DNS Records at Registrar

Now you need to add these records at your domain registrar (Cloudflare, GoDaddy, etc.)

#### Example for Cloudflare:

1. Login to Cloudflare
2. Click on "wwmaa.com" domain
3. Go to "DNS" in the left sidebar
4. Click "Add record"

**Add root domain record:**
- Type: A or CNAME (use what Railway specified)
- Name: @
- Target/Value: [value from Railway]
- Proxy status: Proxied (orange cloud)
- TTL: Auto
- Click "Save"

**Add www subdomain record:**
- Type: CNAME
- Name: www
- Target: [value from Railway]
- Proxy status: Proxied (orange cloud)
- TTL: Auto
- Click "Save"

### Step 7: Verify DNS Propagation

Wait 5-10 minutes, then check:

```bash
# Check apex domain
dig wwmaa.com

# Should show something like:
# wwmaa.com.  300  IN  A  104.238.123.45

# Check www subdomain
dig www.wwmaa.com

# Should show something like:
# www.wwmaa.com.  300  IN  CNAME  unique-id.up.railway.app
```

### Step 8: Wait for SSL Certificate

1. Go back to Railway dashboard
2. Check the "Domains" section
3. You should see "SSL Certificate: Pending" change to "SSL Certificate: Active"
4. This usually takes 5-15 minutes after DNS propagates

### Step 9: Verify Everything Works

```bash
# Test apex domain
curl -I https://wwmaa.com

# Expected response:
HTTP/2 200
server: nginx
content-type: text/html
...

# Test www subdomain
curl -I https://www.wwmaa.com

# Should also return 200 OK
```

## Advanced Configuration Options

### Setting up www → non-www Redirect

If you want www.wwmaa.com to redirect to wwmaa.com:

1. In Cloudflare, create a Page Rule:
   - URL: `www.wwmaa.com/*`
   - Setting: Forwarding URL (301 Permanent Redirect)
   - Destination: `https://wwmaa.com/$1`

2. Or in Next.js, add middleware to handle redirects

### Setting up non-www → www Redirect

If you prefer www.wwmaa.com as the canonical domain:

1. Set up the page rule in reverse:
   - URL: `wwmaa.com/*`
   - Setting: Forwarding URL (301 Permanent Redirect)
   - Destination: `https://www.wwmaa.com/$1`

## Security Considerations

### Enable DNSSEC (if supported by registrar)
1. In registrar settings, enable DNSSEC
2. Add DS records from registrar to parent zone
3. Verify with: `dig +dnssec wwmaa.com`

### Enable CAA Records
Add CAA records to specify which Certificate Authorities can issue certificates:

```
Type: CAA
Name: @
Value: 0 issue "letsencrypt.org"
```

### Enable HSTS
Once SSL is working, enable HSTS:

In Cloudflare:
1. SSL/TLS → Edge Certificates
2. Enable "Always Use HTTPS"
3. Enable "HSTS"
4. Set Max Age: 12 months
5. Include subdomains: Yes
6. Preload: Yes

## Monitoring and Maintenance

### Set up Monitoring
- Use UptimeRobot or similar to monitor domain availability
- Set up SSL certificate expiration alerts
- Monitor DNS propagation status

### Regular Checks
- [ ] Verify SSL certificate auto-renewal (every 90 days)
- [ ] Check DNS record accuracy monthly
- [ ] Monitor Railway logs for SSL issues
- [ ] Test domain functionality after Railway updates

## Emergency Rollback

If you need to rollback to Railway subdomain:

1. Update environment variables:
```env
NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio
```

2. Redeploy frontend
3. Old domain will continue working
4. Custom domain can remain configured for future use

The Railway subdomain (wwmaa.ainative.studio) will always remain active as a fallback.
