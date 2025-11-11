# Cloudflare Calls & Stream Setup Guide

## Overview
This guide covers setup and configuration of Cloudflare Calls for live video sessions and Cloudflare Stream for video on demand (VOD) recording playback.

## Prerequisites
- Cloudflare account with Calls and Stream enabled
- API token with Calls and Stream permissions
- Account ID from Cloudflare dashboard

## Environment Configuration

Add these variables to your `.env` file:

```bash
# Cloudflare Account Configuration
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
CLOUDFLARE_API_TOKEN=your_api_token_here
CLOUDFLARE_CALLS_APP_ID=your_app_id_here  # Optional
```

### Getting Your Credentials

1. **Account ID:**
   - Log in to Cloudflare Dashboard
   - Navigate to any domain > Overview
   - Scroll to right sidebar - Account ID is listed

2. **API Token:**
   - Go to `My Profile` > `API Tokens`
   - Click `Create Token`
   - Use `Custom token` template
   - Permissions needed:
     - `Account` > `Stream` > `Edit`
     - `Account` > `Calls` > `Edit`
   - Zone Resources: `All zones`
   - Click `Continue to summary` > `Create Token`
   - Copy and save the token (shown only once)

3. **Calls App ID (Optional):**
   - Navigate to `Calls` in left sidebar
   - Click `Create Application`
   - Copy the Application ID

## Cloudflare Calls Setup

### 1. Enable Cloudflare Calls
1. Log in to Cloudflare Dashboard
2. Navigate to `Calls` in left sidebar
3. Click `Enable Calls` if not already enabled
4. Create a new Calls application or use existing

### 2. Configure Recording Settings
1. In Calls dashboard, go to your application
2. Enable `Recording` feature
3. Set recording quality: `1080p` (recommended)
4. Enable `Automatic Upload to Stream`
5. Save settings

### 3. Configure Webhooks
Set up webhooks to receive recording completion events:

1. In Calls application settings, find `Webhooks` section
2. Add webhook endpoint:
   ```
   URL: https://api.wwmaa.com/api/webhooks/cloudflare/recordings
   Events: recording.complete, recording.failed
   ```
3. Copy the webhook secret (for signature verification)
4. Save webhook configuration

### 4. Test Webhook Endpoint
```bash
curl -X POST https://api.wwmaa.com/api/webhooks/cloudflare/health
# Should return: {"status": "healthy", "service": "cloudflare_webhooks"}
```

## Cloudflare Stream Setup

### 1. Enable Stream
1. In Cloudflare Dashboard, go to `Stream`
2. Enable Stream if not already active
3. Review pricing and storage limits

### 2. Configure Signed URLs (Production Only)
For members-only recordings, enable signed URLs:

1. In Stream dashboard, go to `Settings`
2. Enable `Require signed URLs`
3. Generate signing keys:
   ```bash
   # Generate RSA key pair
   openssl genrsa -out stream_private.pem 2048
   openssl rsa -in stream_private.pem -pubout -out stream_public.pem
   ```
4. Upload public key to Cloudflare Stream dashboard
5. Store private key securely (used by backend for signing)

### 3. Configure Storage Retention
1. In Stream settings, set retention policy:
   - Retain recordings for: `365 days` (recommended)
   - Automatic deletion after expiry: `Enabled`
2. Set up lifecycle rules for cost optimization

## Recording Workflow

### Automatic Recording (US-046)
When a training session starts:

1. **Session Start:**
   - Backend creates Cloudflare Calls room
   - Recording starts automatically if `recording_enabled=True`
   - Session updated with `recording_status=RECORDING`

2. **During Session:**
   - Cloudflare captures video, audio, screen share, and chat
   - Participants join via generated room tokens
   - Recording continues until session ends

3. **Session End:**
   - Backend stops recording via API
   - Cloudflare begins processing (5-10 minutes)
   - Session updated with `recording_status=PROCESSING`

4. **Processing Complete:**
   - Cloudflare sends webhook to `/api/webhooks/cloudflare/recordings`
   - Backend attaches VOD to session
   - Session updated with `recording_status=READY`
   - Email notifications sent to instructor and participants

5. **VOD Playback:**
   - Members request signed URL (24-hour expiry)
   - Cloudflare Stream delivers video
   - Access control enforced by backend

## Webhook Event Format

### recording.complete
```json
{
  "event": "recording.complete",
  "data": {
    "recordingId": "rec_123abc",
    "roomId": "room_456def",
    "streamId": "stream_789ghi",
    "streamUrl": "https://customer-xxx.cloudflarestream.com/stream_789ghi/manifest/video.m3u8",
    "duration": 3600,
    "fileSize": 524288000,
    "timestamp": "2025-11-10T11:00:00Z"
  }
}
```

### recording.failed
```json
{
  "event": "recording.failed",
  "data": {
    "recordingId": "rec_123abc",
    "roomId": "room_456def",
    "error": "Processing failed: insufficient storage",
    "timestamp": "2025-11-10T11:00:00Z"
  }
}
```

## API Integration

### Create Live Session Room
```python
from backend.services.cloudflare_calls_service import get_cloudflare_calls_service

calls_service = get_cloudflare_calls_service()

# Create room with recording enabled
room = calls_service.create_room(
    session_id="session_123",
    max_participants=50,
    enable_recording=True
)

# Returns:
# {
#   "room_id": "room_456def",
#   "room_url": "https://calls.cloudflare.com/room_456def",
#   "session_id": "session_123",
#   "created_at": "2025-11-10T10:00:00Z"
# }
```

### Start Recording
```python
# Start recording for a room
recording = calls_service.start_recording("room_456def")

# Returns:
# {
#   "recording_id": "rec_123abc",
#   "room_id": "room_456def",
#   "status": "recording",
#   "started_at": "2025-11-10T10:00:00Z"
# }
```

### Stop Recording
```python
# Stop recording
result = calls_service.stop_recording("room_456def", "rec_123abc")

# Returns:
# {
#   "recording_id": "rec_123abc",
#   "room_id": "room_456def",
#   "status": "processing",
#   "ended_at": "2025-11-10T11:00:00Z",
#   "duration_seconds": 3600
# }
```

### Generate Signed Playback URL
```python
from backend.services.cloudflare_stream_service import get_cloudflare_stream_service

stream_service = get_cloudflare_stream_service()

# Generate 24-hour signed URL
signed_url = stream_service.generate_signed_url(
    video_id="stream_789ghi",
    expiry_hours=24,
    download_allowed=False
)

# Returns: "https://customer-xxx.cloudflarestream.com/stream_789ghi/manifest/video.m3u8?exp=...&sig=..."
```

## Troubleshooting

### Recording Not Starting
1. **Check Cloudflare Dashboard:**
   - Verify Calls is enabled
   - Check application quota limits
   - Review recent errors in logs

2. **Verify API Credentials:**
   ```bash
   # Test API token
   curl -X GET "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/calls/apps" \
     -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}"
   ```

3. **Check Backend Logs:**
   ```bash
   # Search for recording errors
   grep "RecordingError" /var/log/wwmaa/backend.log
   ```

### Recording Failed
1. **Common Causes:**
   - Insufficient Cloudflare Stream storage quota
   - Network connectivity issues during recording
   - Room deleted before recording finished
   - API rate limits exceeded

2. **Resolution:**
   - Check Cloudflare Stream dashboard for storage usage
   - Increase storage quota if needed
   - Review error details in training_sessions.recording_error field
   - Retry recording manually if possible

### Webhook Not Received
1. **Verify Webhook Configuration:**
   - Check webhook URL is correct
   - Verify webhook is enabled in Cloudflare
   - Test webhook endpoint health

2. **Check Webhook Logs:**
   ```bash
   # Check recent webhook events
   grep "cloudflare_recording_webhook" /var/log/wwmaa/backend.log
   ```

3. **Manual Retry:**
   - Get recording status from Cloudflare
   - Manually call attach_recording() if processing complete

### VOD Not Available
1. **Check Processing Status:**
   - Typical processing time: 5-10 minutes
   - Large files (>1GB) may take longer
   - Check Cloudflare Stream dashboard for video status

2. **Verify Stream Configuration:**
   - Ensure video uploaded successfully
   - Check video is not deleted
   - Verify signed URL requirements match configuration

## Performance Optimization

### Recording Quality vs. Cost
- **1080p HD:** Best quality, higher bandwidth and storage costs
- **720p HD:** Good quality, moderate costs (recommended for most sessions)
- **480p SD:** Lower quality, minimal costs (use for chat-heavy sessions)

### Storage Management
1. **Automatic Cleanup:**
   - Configure retention policy (e.g., 365 days)
   - Enable automatic deletion of old recordings
   - Archive important recordings to separate storage

2. **Cost Monitoring:**
   - Monitor storage usage in Cloudflare dashboard
   - Set up billing alerts for unexpected costs
   - Review usage reports monthly

### Bandwidth Optimization
- Use adaptive bitrate streaming (automatic with Cloudflare Stream)
- Enable CDN caching for popular recordings
- Consider download option for offline viewing (premium feature)

## Security Best Practices

### Webhook Security
1. **Implement Signature Verification:**
   ```python
   # TODO: Add in production
   def verify_cloudflare_webhook(payload, signature, secret):
       computed_sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
       return hmac.compare_digest(computed_sig, signature)
   ```

2. **Rate Limiting:**
   - Implement rate limits on webhook endpoint
   - Prevent webhook flooding attacks

### Access Control
1. **Signed URLs:**
   - Always use signed URLs for members-only content
   - Set appropriate expiry times (24 hours recommended)
   - Rotate signing keys periodically

2. **Role-Based Access:**
   - Verify user role before generating signed URLs
   - Enforce members-only restrictions
   - Log all playback requests for audit

## Monitoring & Alerts

### Key Metrics
- Recording success rate (target: >95%)
- Average time to VOD availability (target: <10 minutes)
- Webhook processing latency (target: <5 seconds)
- Storage usage and growth rate

### Recommended Alerts
1. **Recording Failure Rate >5%:**
   - Alert: Email to engineering team
   - Action: Review error logs and API status

2. **VOD Not Available >15 Minutes:**
   - Alert: Slack notification
   - Action: Check Cloudflare Stream processing queue

3. **Storage >80% of Quota:**
   - Alert: Email to operations team
   - Action: Increase quota or clean up old recordings

## Support & Resources

### Cloudflare Documentation
- Calls API: https://developers.cloudflare.com/calls/
- Stream API: https://developers.cloudflare.com/stream/
- Webhooks: https://developers.cloudflare.com/calls/webhooks/

### WWMAA Backend Code
- RecordingService: `/backend/services/recording_service.py`
- CloudflareCallsService: `/backend/services/cloudflare_calls_service.py`
- CloudflareStreamService: `/backend/services/cloudflare_stream_service.py`
- Webhook Handler: `/backend/routes/webhooks.py`

### Getting Help
- Internal: Slack #engineering channel
- Cloudflare: Support portal (Enterprise plan)
- Community: Cloudflare Discord

---

**Last Updated:** November 10, 2025
**Maintained By:** WWMAA Engineering Team
**Version:** 1.0
