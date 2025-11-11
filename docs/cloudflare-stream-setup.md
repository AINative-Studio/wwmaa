# Cloudflare Stream Setup Guide

## Overview

This guide walks through setting up Cloudflare Stream for Video on Demand (VOD) in the WWMAA backend. Cloudflare Stream provides scalable video hosting, transcoding, and delivery with global CDN distribution.

**Features:**
- Automatic video transcoding to multiple formats
- Adaptive bitrate streaming (HLS and DASH)
- Global CDN distribution
- Signed URLs for access control
- Caption/subtitle support
- Thumbnail generation
- Analytics and insights

---

## Prerequisites

- Cloudflare account
- Domain configured in Cloudflare (optional, for custom domains)
- Credit card for Cloudflare Stream pricing

---

## Step 1: Enable Cloudflare Stream

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **Stream** in the sidebar
3. Click **Enable Stream**
4. Accept the pricing terms:
   - $5 per 1,000 minutes of video stored
   - $1 per 1,000 minutes of video delivered

---

## Step 2: Get API Credentials

### Account ID

1. In Cloudflare Dashboard, click on your profile (top right)
2. Go to **My Profile** > **API Tokens**
3. Your **Account ID** is displayed on the right side
4. Copy it - you'll need this for `CLOUDFLARE_ACCOUNT_ID`

### API Token

1. In **API Tokens** page, click **Create Token**
2. Use the **Create Custom Token** option
3. Configure the token:
   - **Token name**: `WWMAA Stream API`
   - **Permissions**:
     - Account > Stream > Edit
     - Account > Stream > Read
   - **Account Resources**:
     - Include > Your Account
   - **TTL**: Permanent (or set expiry as needed)
4. Click **Continue to Summary**
5. Click **Create Token**
6. **IMPORTANT**: Copy the token immediately - you won't be able to see it again
7. Save this as `CLOUDFLARE_STREAM_API_TOKEN`

---

## Step 3: Configure Signed URLs (Optional but Recommended)

Signed URLs provide time-limited, secure access to member-only videos.

### Generate Signing Key

1. In Cloudflare Dashboard, go to **Stream** > **Signing Keys**
2. Click **Generate Signing Keys**
3. Copy the **Key ID** and **PEM Key**
4. Save the **PEM Key** as `CLOUDFLARE_STREAM_SIGNING_KEY`

**Example PEM Key:**
```
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA1234567890...
...
-----END RSA PRIVATE KEY-----
```

### Enable Signed URLs on Videos

When uploading videos, set `requireSignedURLs: true` in metadata:

```python
stream_service.upload_video(
    file_path="/path/to/video.mp4",
    metadata={
        "requireSignedURLs": True
    }
)
```

---

## Step 4: Configure Webhooks

Webhooks notify your backend when video processing completes or fails.

### Generate Webhook Secret

```bash
# Generate a random secret
openssl rand -hex 32
```

Save this as `CLOUDFLARE_STREAM_WEBHOOK_SECRET`.

### Register Webhook URL

1. In Cloudflare Dashboard, go to **Stream** > **Webhooks**
2. Click **Add Webhook**
3. Enter your webhook URL:
   ```
   https://your-domain.com/api/webhooks/cloudflare/stream
   ```
4. Select events to receive:
   - `video.ready` - Video processing completed
   - `video.error` - Video processing failed
5. Enter your webhook secret
6. Click **Save**

### Test Webhook

Upload a test video and verify your backend receives the webhook:

```bash
# Check webhook logs
tail -f /var/log/wwmaa/webhooks.log
```

---

## Step 5: Configure Environment Variables

Add these environment variables to your `.env` file:

```bash
# Cloudflare Stream Configuration
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
CLOUDFLARE_STREAM_API_TOKEN=your_api_token_here
CLOUDFLARE_STREAM_SIGNING_KEY=-----BEGIN RSA PRIVATE KEY-----\nMIIE...-----END RSA PRIVATE KEY-----
CLOUDFLARE_STREAM_WEBHOOK_SECRET=your_webhook_secret_here
```

**Important Notes:**
- Replace all placeholder values with your actual credentials
- For `CLOUDFLARE_STREAM_SIGNING_KEY`, replace newlines with `\n`
- Keep these values secure - never commit them to version control
- Use a secrets management service in production (AWS Secrets Manager, HashiCorp Vault, etc.)

---

## Step 6: Test Video Upload

### Test via API

```bash
curl -X POST http://localhost:8000/api/media/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@test_video.mp4" \
  -F "title=Test Training Video" \
  -F "description=Test video for Cloudflare Stream" \
  -F "media_type=video" \
  -F "access_level=members_only"
```

### Test via Python

```python
from backend.services.cloudflare_stream_service import CloudflareStreamService

# Initialize service
stream_service = CloudflareStreamService()

# Upload video
result = stream_service.upload_video(
    file_path="/path/to/test_video.mp4",
    metadata={
        "name": "Test Training Video",
        "requireSignedURLs": True,
        "meta": {
            "title": "Karate Training Session",
            "instructor": "John Doe"
        }
    }
)

print(f"Video ID: {result['uid']}")
print(f"Status: {result['status']['state']}")
```

### Verify Upload

1. Check Cloudflare Dashboard > **Stream** > **Videos**
2. Your video should appear with status "processing" or "ready"
3. Check your backend logs for successful upload
4. Verify webhook received when processing completes

---

## Video Format Guidelines

### Supported Formats

Cloudflare Stream accepts most video formats:
- **Containers**: MP4, MOV, MKV, AVI, FLV, WebM
- **Codecs**: H.264, H.265 (HEVC), VP8, VP9, AV1
- **Audio**: AAC, MP3, Vorbis, Opus

### Recommended Settings

For best results, upload videos with these settings:

**Resolution:**
- 1080p (1920x1080) for high quality
- 720p (1280x720) for good quality, smaller file size
- Max resolution: 4K (3840x2160)

**Codec:**
- H.264 (most compatible)
- H.265 for smaller file sizes (modern devices)

**Frame Rate:**
- 24-30 fps for most content
- 60 fps for high-motion content (sports, action)

**Bitrate:**
- 1080p: 5-8 Mbps
- 720p: 2.5-5 Mbps
- 480p: 1-2.5 Mbps

**File Size:**
- Maximum: 30 GB per file
- For files > 200 MB, use chunked upload (TUS protocol)

---

## File Size Limits

### Small Files (< 200 MB)

Use direct upload:

```python
stream_service.upload_video(
    file_path="/path/to/video.mp4",
    metadata={"name": "Training Video"}
)
```

### Large Files (> 200 MB)

Use chunked upload:

```python
from backend.services.upload_service import UploadService

upload_service = UploadService()

# 1. Initiate upload
session = upload_service.initiate_upload(
    file_name="large_video.mp4",
    file_size=500_000_000,  # 500 MB
    user_id=str(user_id),
    metadata={"title": "Large Training Video"}
)

# 2. Upload chunks
with open("/path/to/large_video.mp4", "rb") as f:
    chunk_size = 5 * 1024 * 1024  # 5 MB chunks
    chunk_index = 0

    while True:
        chunk_data = f.read(chunk_size)
        if not chunk_data:
            break

        progress = upload_service.upload_chunk(
            upload_id=session['upload_id'],
            chunk_index=chunk_index,
            chunk_data=chunk_data
        )

        print(f"Progress: {progress['progress_percent']}%")
        chunk_index += 1

# 3. Finalize and process
result = upload_service.finalize_upload(session['upload_id'])
```

---

## Access Control Strategies

### Public Videos

No authentication required:

```python
await media_service.create_media_asset(
    file_path="/path/to/video.mp4",
    media_type=MediaType.VIDEO,
    title="Public Demo Video",
    access_level=MediaAccessLevel.PUBLIC,
    created_by=user_id
)
```

### Members-Only Videos

Requires authenticated member:

```python
await media_service.create_media_asset(
    file_path="/path/to/video.mp4",
    media_type=MediaType.VIDEO,
    title="Member Training Video",
    access_level=MediaAccessLevel.MEMBERS_ONLY,
    created_by=user_id
)
```

### Tier-Specific Videos

Requires specific subscription tier:

```python
await media_service.create_media_asset(
    file_path="/path/to/video.mp4",
    media_type=MediaType.VIDEO,
    title="Premium Seminar Recording",
    access_level=MediaAccessLevel.TIER_SPECIFIC,
    required_tier=SubscriptionTier.PREMIUM,
    created_by=user_id
)
```

### Generate Signed URLs

```python
# Get signed URL for member access
signed_url = await media_service.generate_access_url(
    asset_id=asset_id,
    user_id=user_id,
    user_role=user_role,
    user_tier=user_tier,
    expiry_seconds=86400  # 24 hours
)
```

---

## Caption/Subtitle Support

### Prepare Caption File

Create a WebVTT (.vtt) file:

```vtt
WEBVTT

00:00:00.000 --> 00:00:05.000
Welcome to the training session.

00:00:05.000 --> 00:00:10.000
Today we'll cover basic techniques.
```

### Upload Captions

```python
await media_service.upload_captions(
    asset_id=asset_id,
    caption_file="/path/to/captions.vtt",
    language="en",
    label="English"
)
```

### Multiple Languages

```python
# English captions
await media_service.upload_captions(
    asset_id=asset_id,
    caption_file="/path/to/captions_en.vtt",
    language="en",
    label="English"
)

# Spanish captions
await media_service.upload_captions(
    asset_id=asset_id,
    caption_file="/path/to/captions_es.vtt",
    language="es",
    label="Español"
)
```

---

## Cost Optimization Tips

### Storage Costs

**$5 per 1,000 minutes stored**

- Delete old or unused videos regularly
- Use appropriate video quality (don't upload 4K if 1080p is sufficient)
- Archive rarely-accessed videos to cheaper storage (S3, R2)

### Delivery Costs

**$1 per 1,000 minutes delivered**

- Use adaptive bitrate streaming (automatic with Stream)
- Implement video analytics to track popular content
- Set appropriate cache headers
- Use signed URLs to prevent unauthorized sharing

### Example Cost Calculation

**Scenario:**
- 100 training videos, average 30 minutes each
- 1,000 members, each watches 10 videos per month

**Costs:**
- Storage: (100 videos × 30 min) ÷ 1,000 × $5 = $15/month
- Delivery: (1,000 members × 10 videos × 30 min) ÷ 1,000 × $1 = $300/month
- **Total: $315/month**

---

## Thumbnail Generation

### Automatic Thumbnails

Cloudflare Stream automatically generates thumbnails at video upload.

### Custom Thumbnail at Specific Time

```python
# Get thumbnail at 30 seconds
thumbnail_url = stream_service.get_thumbnail_url(
    video_id=video_id,
    time_seconds=30,
    width=640,
    height=360
)
```

### Thumbnail Sizes

```python
# Small thumbnail (preview)
small_thumb = stream_service.get_thumbnail_url(
    video_id, width=320, height=180
)

# Medium thumbnail (list view)
medium_thumb = stream_service.get_thumbnail_url(
    video_id, width=640, height=360
)

# Large thumbnail (detail view)
large_thumb = stream_service.get_thumbnail_url(
    video_id, width=1280, height=720
)
```

---

## Troubleshooting

### Issue: Video Upload Fails

**Symptoms:** Upload returns 400 or 500 error

**Solutions:**
1. Check video format is supported
2. Verify file size is under 30GB
3. Check API token has correct permissions
4. Verify `CLOUDFLARE_ACCOUNT_ID` is correct
5. Check network connectivity

### Issue: Webhook Not Received

**Symptoms:** Video processes but backend not updated

**Solutions:**
1. Verify webhook URL is accessible from internet
2. Check webhook secret matches
3. Ensure webhook handler is registered in FastAPI app
4. Check firewall/security group rules
5. Test webhook with Cloudflare's webhook tester

### Issue: Signed URLs Not Working

**Symptoms:** "Invalid token" error when accessing video

**Solutions:**
1. Verify `CLOUDFLARE_STREAM_SIGNING_KEY` is correct
2. Check video has `requireSignedURLs: true`
3. Verify JWT token is not expired
4. Check signing key ID matches video's key
5. Ensure PEM key format is correct

### Issue: Video Processing Stuck

**Symptoms:** Video stays in "processing" state

**Solutions:**
1. Wait - large videos can take 15-30 minutes
2. Check Cloudflare status page for outages
3. Try re-uploading the video
4. Contact Cloudflare support
5. Check video format is supported

---

## Security Best Practices

### API Token Security

- **Never** commit API tokens to version control
- Use environment variables or secrets manager
- Rotate tokens periodically (every 90 days)
- Use minimum required permissions
- Revoke tokens immediately if compromised

### Signed URL Security

- Set reasonable expiry times (default: 24 hours)
- Include user_id in JWT claims for audit trail
- Rotate signing keys periodically
- Monitor for unusual access patterns
- Implement rate limiting on signed URL generation

### Webhook Security

- Always verify webhook signatures
- Use HTTPS only for webhook endpoints
- Implement timestamp validation
- Log all webhook events for audit
- Alert on webhook verification failures

### Video Access Control

- Implement proper authorization checks
- Use signed URLs for member-only content
- Implement tier-based access controls
- Log video access for analytics and audit
- Monitor for unauthorized access attempts

---

## Monitoring & Analytics

### Video Analytics

Access video analytics via API:

```python
# Get analytics for specific video
analytics = stream_service.get_video_analytics(
    video_id="video_123",
    since=datetime.utcnow() - timedelta(days=7),
    until=datetime.utcnow()
)

print(f"Views: {analytics['views']}")
print(f"Minutes watched: {analytics['minutes_watched']}")
```

### Metrics to Monitor

- **Upload success rate**: Track failed uploads
- **Processing time**: Average time from upload to ready
- **Delivery latency**: Time to first byte (TTFB)
- **Playback quality**: Buffering ratio, startup time
- **Cost metrics**: Storage and delivery costs
- **Access patterns**: Popular videos, peak usage times

### Logging

Enable detailed logging:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('cloudflare_stream')
```

---

## Support & Resources

### Official Documentation

- [Cloudflare Stream Docs](https://developers.cloudflare.com/stream/)
- [Stream API Reference](https://developers.cloudflare.com/api/operations/stream-videos-upload-videos-from-a-url)
- [Signed URLs Guide](https://developers.cloudflare.com/stream/viewing-videos/securing-your-stream/)

### WWMAA Backend Docs

- [Media Service Documentation](./media-service.md)
- [API Endpoints](./api-endpoints.md#media)
- [Webhook Integration](./webhooks.md#cloudflare-stream)

### Support Channels

- **Cloudflare Support**: https://support.cloudflare.com/
- **WWMAA Backend Team**: backend@wwmaa.org
- **GitHub Issues**: https://github.com/wwmaa/backend/issues

---

## Appendix: API Examples

### Complete Upload Workflow

```python
from backend.services.media_service import MediaService
from backend.models.schemas import MediaType, SubscriptionTier
from schemas_media_extension import MediaAccessLevel

media_service = MediaService()

# 1. Upload video
asset = await media_service.create_media_asset(
    file_path="/path/to/training_video.mp4",
    media_type=MediaType.VIDEO,
    title="Advanced Karate Techniques",
    description="Learn advanced kata and kumite techniques",
    access_level=MediaAccessLevel.TIER_SPECIFIC,
    required_tier=SubscriptionTier.PREMIUM,
    entity_type="training_session",
    entity_id=session_id,
    created_by=instructor_id,
    metadata={"tags": ["karate", "advanced", "kata"]}
)

print(f"Asset created: {asset['id']}")
print(f"Status: {asset['status']}")

# 2. Wait for processing (webhook will update status)
# Check status periodically
asset = await media_service.get_media_asset(
    asset_id=asset['id'],
    user_id=instructor_id,
    user_role=UserRole.INSTRUCTOR,
    user_tier=SubscriptionTier.PREMIUM
)

if asset['status'] == 'ready':
    print("Video is ready!")
    print(f"Duration: {asset['duration_seconds']} seconds")
    print(f"Thumbnail: {asset['thumbnail_url']}")

    # 3. Upload captions
    await media_service.upload_captions(
        asset_id=asset['id'],
        caption_file="/path/to/captions.vtt",
        language="en",
        label="English"
    )

    # 4. Generate signed URL for member access
    signed_url = await media_service.generate_access_url(
        asset_id=asset['id'],
        user_id=member_id,
        user_role=UserRole.MEMBER,
        user_tier=SubscriptionTier.PREMIUM,
        expiry_seconds=86400  # 24 hours
    )

    print(f"Video URL: {signed_url}")
```

---

**Last Updated:** 2024-01-10
**Version:** 1.0
**Maintained By:** WWMAA Backend Team
