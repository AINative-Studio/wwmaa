# Member Newsletter Auto-Subscribe System (US-059)

## Overview

The Member Newsletter Auto-Subscribe system automatically manages BeeHiiv newsletter subscriptions based on membership lifecycle events. Members are automatically added to appropriate newsletter lists when they join, upgraded when their tier changes, and removed when they cancel.

## Architecture

### Services

1. **NewsletterService** (`backend/services/newsletter_service.py`)
   - Core BeeHiiv API integration
   - Auto-subscription methods
   - Email change sync
   - Unsubscribe preference management

2. **MembershipWebhookHandler** (`backend/services/membership_webhook_handler.py`)
   - Processes membership lifecycle events
   - Triggers newsletter operations
   - Audit logging

3. **SubscriptionService** (`backend/services/subscription_service.py`)
   - Subscription lifecycle management
   - Newsletter integration on subscription changes

4. **UserService** (`backend/services/user_service.py`)
   - User account management
   - Email change sync to newsletter

5. **NewsletterSyncJob** (`backend/services/newsletter_sync_job.py`)
   - Daily sync job (runs at 3 AM)
   - Ensures consistency between ZeroDB and BeeHiiv
   - Error recovery and reporting

## Newsletter Lists

### List Structure

1. **General List**
   - Public subscribers only
   - Requires double opt-in
   - Public newsletter signup flow

2. **Members Only List**
   - All active members (basic, premium, instructor)
   - Auto-subscribed on approval/first payment
   - No double opt-in (implied consent through membership)
   - Removed on subscription cancellation

3. **Instructors List**
   - Members with Instructor tier (lifetime)
   - Auto-subscribed on tier upgrade
   - Removed on tier downgrade

### List Membership Rules

- **Cascade**: Instructors are also in Members Only list
- **Cancellation**: Canceled members removed from Members Only and Instructors, but stay in General if they opted in publicly
- **Deduplication**: System prevents duplicate subscriptions across lists

## Workflows

### 1. Application Approval Flow

```
Application Approved
    ↓
Approval Service triggers newsletter subscription
    ↓
MembershipWebhookHandler.handle_application_approved()
    ↓
NewsletterService.auto_subscribe_member()
    ↓
- Check unsubscribe preferences
- Add to Members Only list
- Add to Instructors list (if tier is lifetime)
- Create audit log
```

### 2. Subscription Creation Flow

```
Stripe Payment Successful
    ↓
Subscription Created
    ↓
SubscriptionService.create_subscription()
    ↓
MembershipWebhookHandler.handle_subscription_created()
    ↓
NewsletterService.auto_subscribe_member()
    ↓
Member added to appropriate lists
```

### 3. Tier Upgrade Flow

```
Subscription Upgraded to Instructor
    ↓
SubscriptionService.upgrade_subscription()
    ↓
MembershipWebhookHandler.handle_tier_upgrade()
    ↓
NewsletterService.upgrade_to_instructor()
    ↓
Member added to Instructors list
```

### 4. Subscription Cancellation Flow

```
Subscription Canceled
    ↓
SubscriptionService.cancel_subscription()
    ↓
MembershipWebhookHandler.handle_subscription_canceled()
    ↓
NewsletterService.handle_subscription_canceled()
    ↓
- Remove from Members Only list
- Remove from Instructors list
- Keep in General list (if publicly opted in)
```

### 5. Email Change Flow

```
User Updates Email
    ↓
UserService.update_user_email()
    ↓
MembershipWebhookHandler.handle_email_changed()
    ↓
NewsletterService.sync_email_change()
    ↓
Email updated across all BeeHiiv lists
```

## Daily Sync Job

### Purpose
Ensures consistency between ZeroDB member database and BeeHiiv newsletter lists.

### Schedule
Runs daily at 3:00 AM UTC via APScheduler

### Operations

1. **Sync Active Members**
   - Query all active subscriptions from ZeroDB
   - For each member:
     - Check if in correct BeeHiiv lists
     - Add if missing
     - Update tier-based list membership

2. **Remove Canceled Members**
   - Query all canceled subscriptions
   - Remove from Members Only and Instructors lists
   - Keep in General if publicly subscribed

3. **Error Handling**
   - Log all errors
   - Continue processing remaining members
   - Report summary at completion

4. **Audit Logging**
   - Log sync start/completion
   - Record statistics
   - Document discrepancies

### Manual Sync Trigger

Admin can trigger manual sync via:
```
POST /api/admin/newsletter/sync
```

## Unsubscribe Preferences

### Storage
User unsubscribe preferences stored in `user_newsletter_preferences` collection:

```json
{
  "user_id": "uuid",
  "unsubscribed_lists": ["members_only", "instructors"],
  "last_unsubscribe_at": "2025-01-10T...",
  "last_unsubscribe_reason": "Too many emails",
  "allow_marketing": false,
  "allow_product_updates": true,
  "allow_member_communications": true
}
```

### Behavior

- **Respect Preferences**: Auto-subscribe checks preferences before adding to lists
- **Granular Control**: Users can unsubscribe from specific lists
- **Persistent**: Preferences persist across subscription changes

## Admin Management

### Endpoints

1. **Trigger Manual Sync**
   ```
   POST /api/admin/newsletter/sync
   ```
   Runs immediate sync job

2. **Get Sync Status**
   ```
   GET /api/admin/newsletter/sync/status
   ```
   Returns last sync job status and statistics

3. **Force Subscribe Member**
   ```
   POST /api/admin/newsletter/member/{user_id}/subscribe
   ```
   Manually subscribe member to lists

4. **Force Unsubscribe Member**
   ```
   DELETE /api/admin/newsletter/member/{user_id}/unsubscribe
   ```
   Manually unsubscribe member from list

5. **Find Discrepancies**
   ```
   GET /api/admin/newsletter/discrepancies
   ```
   Identify members in ZeroDB not in BeeHiiv (or vice versa)

6. **Get List Members**
   ```
   GET /api/admin/newsletter/members/list/{list_name}
   ```
   View all members in a specific list

7. **Get Newsletter Stats**
   ```
   GET /api/admin/newsletter/stats
   ```
   View subscription statistics

## Error Handling

### BeeHiiv API Errors

1. **Retry Logic**
   - 3 retries with exponential backoff
   - 1 second initial delay
   - Timeout: 30 seconds per request

2. **Rate Limiting**
   - Respects BeeHiiv API rate limits
   - Implements backoff on 429 responses

3. **Error Types**
   - `404`: Email not found (treated as success for unsubscribe)
   - `409`: Already exists (treated as success)
   - `500+`: Server errors trigger retry

### Failure Recovery

1. **Graceful Degradation**
   - Membership operations succeed even if newsletter subscription fails
   - Errors logged but don't block critical workflows

2. **Manual Recovery**
   - Admin can manually sync missed subscriptions
   - Sync job catches up on failures

3. **Audit Trail**
   - All operations logged to `audit_logs` collection
   - Errors include full context for debugging

## Testing

### Test Coverage
Target: 80%+ coverage

### Test Files
- `backend/tests/test_member_auto_subscribe.py`

### Test Categories

1. **Unit Tests**
   - NewsletterService methods
   - MembershipWebhookHandler event handling
   - SubscriptionService lifecycle
   - UserService email sync
   - NewsletterSyncJob operations

2. **Integration Tests**
   - Full application-to-newsletter flow
   - Subscription lifecycle with newsletter
   - Email change end-to-end

3. **Edge Cases**
   - Duplicate subscription prevention
   - Unsubscribe preference respect
   - BeeHiiv API failures
   - Missing user data
   - Network timeouts

### Running Tests

```bash
# Run all newsletter tests
pytest backend/tests/test_member_auto_subscribe.py -v

# With coverage
pytest backend/tests/test_member_auto_subscribe.py --cov=backend/services --cov-report=html

# Specific test class
pytest backend/tests/test_member_auto_subscribe.py::TestNewsletterService -v
```

## Configuration

### Environment Variables

```bash
# Required
BEEHIIV_API_KEY=your_api_key_here
BEEHIIV_PUBLICATION_ID=your_publication_id

# Optional
NEWSLETTER_SYNC_INTERVAL_HOURS=24  # Default: 24 hours
```

### BeeHiiv Setup

1. Create BeeHiiv account
2. Create publication
3. Create three lists:
   - General (public)
   - Members Only (private)
   - Instructors (private)
4. Get API key from Settings > API
5. Get publication ID from Settings > General
6. Add to environment variables

## Monitoring

### Key Metrics

1. **Sync Job Metrics**
   - Members processed
   - Members synced
   - Instructors synced
   - Errors encountered
   - Sync duration

2. **Subscription Metrics**
   - Total active members in Members Only
   - Total instructors in Instructors list
   - Cancellations per day/week/month
   - Auto-subscribe success rate

3. **Error Metrics**
   - BeeHiiv API failures
   - Network timeouts
   - Missing user data errors
   - Duplicate subscription attempts

### Logging

All operations logged to:
- **Application logs**: Standard Python logging
- **Audit logs**: ZeroDB `audit_logs` collection

Log levels:
- `INFO`: Successful operations
- `WARNING`: Recoverable errors (e.g., user already subscribed)
- `ERROR`: Failed operations requiring attention
- `DEBUG`: Detailed operation traces

## Troubleshooting

### Member Not Receiving Emails

1. **Check subscription status**
   ```
   GET /api/admin/newsletter/members/list/members_only
   ```

2. **Check unsubscribe preferences**
   - Query `user_newsletter_preferences` collection
   - Look for member's user_id

3. **Check BeeHiiv directly**
   - Login to BeeHiiv dashboard
   - Search for member's email
   - Verify list membership

4. **Force re-subscribe**
   ```
   POST /api/admin/newsletter/member/{user_id}/subscribe
   ```

### Sync Job Failures

1. **Check last sync status**
   ```
   GET /api/admin/newsletter/sync/status
   ```

2. **Review audit logs**
   - Query `audit_logs` with tags: `["newsletter_sync", "scheduled_job"]`
   - Check for error patterns

3. **Manual sync**
   ```
   POST /api/admin/newsletter/sync
   ```

4. **Check BeeHiiv API status**
   - Visit BeeHiiv status page
   - Verify API key validity

### Discrepancies Between ZeroDB and BeeHiiv

1. **Run discrepancy report**
   ```
   GET /api/admin/newsletter/discrepancies
   ```

2. **Manual sync to reconcile**
   ```
   POST /api/admin/newsletter/sync
   ```

3. **Review specific members**
   - Check member's subscription status in ZeroDB
   - Check member's email in BeeHiiv
   - Compare list memberships

## Security Considerations

### API Key Protection

- BeeHiiv API key stored in environment variables
- Never exposed in API responses
- Masked in logs and admin UI

### Email Privacy

- IP addresses hashed (SHA256) before storage
- Email addresses encrypted at rest (ZeroDB)
- GDPR compliance for EU users

### Access Control

- Admin endpoints require admin or board member role
- Newsletter preferences per-user isolation
- Audit logging for all operations

## Performance

### Optimization Strategies

1. **Batch Operations**
   - Sync job processes members in batches
   - BeeHiiv API calls batched when possible

2. **Caching**
   - Unsubscribe preferences cached
   - User data cached during sync

3. **Async Processing**
   - All newsletter operations async
   - Non-blocking membership workflows

### Scalability

- Handles 10,000+ members
- Sync job completes in < 5 minutes for 10K members
- Horizontal scaling via multiple workers

## Future Enhancements

1. **Webhook Integration**
   - BeeHiiv webhooks for real-time sync
   - Unsubscribe webhook handling

2. **Advanced Segmentation**
   - Event attendance-based lists
   - Location-based lists
   - Interest-based lists

3. **Email Analytics**
   - Open rate tracking
   - Click rate tracking
   - Engagement scoring

4. **A/B Testing**
   - Subject line testing
   - Content testing
   - Send time optimization

## Support

For issues or questions:
- Check logs: `backend/logs/`
- Review audit trail: `audit_logs` collection
- Contact support: support@wwmaa.com
- Documentation: https://docs.wwmaa.com/newsletter
