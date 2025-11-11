# CI/CD Notifications Guide

## Overview

This guide explains how to set up and configure notifications for CI/CD pipeline events in the WWMAA project.

## Table of Contents

1. [Notification Channels](#notification-channels)
2. [Slack Integration](#slack-integration)
3. [Email Notifications](#email-notifications)
4. [GitHub Notifications](#github-notifications)
5. [Custom Webhooks](#custom-webhooks)
6. [Troubleshooting](#troubleshooting)

---

## Notification Channels

The WWMAA CI/CD pipeline supports multiple notification channels:

| Channel | Events Supported | Setup Difficulty | Status |
|---------|------------------|------------------|--------|
| GitHub PR Comments | All checks | Built-in | ✅ Active |
| Slack | Failures, Deployments | Easy | ⚙️ Optional |
| Email | Failures | Easy | 🔔 GitHub Default |
| Discord | All events | Medium | ⏸️ Not configured |
| Microsoft Teams | All events | Medium | ⏸️ Not configured |
| PagerDuty | Critical failures | Medium | ⏸️ Not configured |
| Custom Webhooks | All events | Advanced | ⏸️ Not configured |

---

## Slack Integration

### Overview

Slack integration provides real-time notifications for CI/CD events directly in your team's Slack workspace.

### Prerequisites

- Slack workspace admin access
- GitHub repository admin access
- Slack workspace with appropriate channel

### Setup Instructions

#### Step 1: Create Slack Incoming Webhook

1. **Go to Slack API:**
   - Visit [https://api.slack.com/apps](https://api.slack.com/apps)
   - Click **Create New App**

2. **Configure App:**
   - Choose **From scratch**
   - **App Name:** `WWMAA CI/CD`
   - **Workspace:** Select your workspace
   - Click **Create App**

3. **Enable Incoming Webhooks:**
   - In left sidebar, click **Incoming Webhooks**
   - Toggle **Activate Incoming Webhooks** to **On**
   - Click **Add New Webhook to Workspace**

4. **Select Channel:**
   - Choose channel (e.g., `#ci-notifications`, `#engineering`, `#alerts`)
   - Click **Allow**

5. **Copy Webhook URL:**
   - Copy the webhook URL (starts with `https://hooks.slack.com/services/...`)
   - Keep this secure - it's a secret!

#### Step 2: Add Webhook to GitHub Secrets

1. **Navigate to Repository Settings:**
   - Go to your GitHub repository
   - Click **Settings** > **Secrets and variables** > **Actions**

2. **Create New Secret:**
   - Click **New repository secret**
   - **Name:** `SLACK_WEBHOOK_URL`
   - **Value:** Paste the webhook URL from Step 1
   - Click **Add secret**

#### Step 3: Verify Configuration

The webhook is already integrated in `.github/workflows/ci.yml`:

```yaml
notify-failure:
  name: Notify on Failure
  runs-on: ubuntu-latest
  needs: [backend-unit-tests, backend-integration-tests, frontend-build-test]
  if: failure() && github.ref == 'refs/heads/main'

  steps:
    - name: Send Slack notification
      if: ${{ secrets.SLACK_WEBHOOK_URL != '' }}
      uses: slackapi/slack-github-action@v1.26.0
      with:
        payload: |
          {
            "text": "❌ CI Pipeline Failed",
            "blocks": [
              {
                "type": "header",
                "text": {
                  "type": "plain_text",
                  "text": "❌ CI Pipeline Failed on ${{ github.repository }}"
                }
              },
              {
                "type": "section",
                "fields": [
                  {
                    "type": "mrkdwn",
                    "text": "*Branch:*\n${{ github.ref_name }}"
                  },
                  {
                    "type": "mrkdwn",
                    "text": "*Commit:*\n<${{ github.event.head_commit.url }}|${{ github.event.head_commit.message }}>"
                  },
                  {
                    "type": "mrkdwn",
                    "text": "*Author:*\n${{ github.actor }}"
                  },
                  {
                    "type": "mrkdwn",
                    "text": "*Workflow:*\n<${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Run>"
                  }
                ]
              }
            ]
          }
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        SLACK_WEBHOOK_TYPE: INCOMING_WEBHOOK
```

#### Step 4: Test Notification

1. **Trigger a failure:**
   ```bash
   # Create a failing test
   git checkout -b test/slack-notification
   # Add a failing test or lint error
   git commit -am "test: trigger slack notification"
   git push origin test/slack-notification
   ```

2. **Merge to main** (or push directly to main if you have permission)

3. **Check Slack channel** for notification

### Customizing Slack Notifications

#### Notify on Success

To add success notifications, create a new job:

```yaml
notify-success:
  name: Notify on Success
  runs-on: ubuntu-latest
  needs: [ci-status]
  if: success() && github.ref == 'refs/heads/main'

  steps:
    - name: Send Slack notification
      if: ${{ secrets.SLACK_WEBHOOK_URL != '' }}
      uses: slackapi/slack-github-action@v1.26.0
      with:
        payload: |
          {
            "text": "✅ CI Pipeline Passed",
            "blocks": [
              {
                "type": "header",
                "text": {
                  "type": "plain_text",
                  "text": "✅ CI Pipeline Passed on ${{ github.repository }}"
                }
              },
              {
                "type": "section",
                "fields": [
                  {
                    "type": "mrkdwn",
                    "text": "*Branch:*\n${{ github.ref_name }}"
                  },
                  {
                    "type": "mrkdwn",
                    "text": "*Commit:*\n${{ github.event.head_commit.message }}"
                  }
                ]
              }
            ]
          }
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        SLACK_WEBHOOK_TYPE: INCOMING_WEBHOOK
```

#### Notify on Deployment

For deployment notifications:

```yaml
notify-deployment:
  name: Notify on Deployment
  runs-on: ubuntu-latest
  needs: [deploy]
  if: always()

  steps:
    - name: Send Slack notification
      if: ${{ secrets.SLACK_WEBHOOK_URL != '' }}
      uses: slackapi/slack-github-action@v1.26.0
      with:
        payload: |
          {
            "text": "🚀 Deployment to Production",
            "blocks": [
              {
                "type": "header",
                "text": {
                  "type": "plain_text",
                  "text": "🚀 Deployed to Production"
                }
              },
              {
                "type": "section",
                "fields": [
                  {
                    "type": "mrkdwn",
                    "text": "*Environment:*\nProduction"
                  },
                  {
                    "type": "mrkdwn",
                    "text": "*Status:*\n${{ needs.deploy.result }}"
                  },
                  {
                    "type": "mrkdwn",
                    "text": "*Version:*\n${{ github.sha }}"
                  },
                  {
                    "type": "mrkdwn",
                    "text": "*Deployed By:*\n${{ github.actor }}"
                  }
                ]
              },
              {
                "type": "actions",
                "elements": [
                  {
                    "type": "button",
                    "text": {
                      "type": "plain_text",
                      "text": "View Deployment"
                    },
                    "url": "https://your-production-url.com"
                  }
                ]
              }
            ]
          }
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        SLACK_WEBHOOK_TYPE: INCOMING_WEBHOOK
```

#### Advanced Slack Features

**Mentioning Users:**

```yaml
"text": "<!here> CI Pipeline Failed"  # Mention @here
"text": "<@U123456> CI Pipeline Failed"  # Mention specific user
"text": "<!channel> CI Pipeline Failed"  # Mention @channel
```

**Adding Rich Formatting:**

```yaml
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": "*Bold* ~strikethrough~ _italic_ `code`"
  }
}
```

**Adding Context:**

```yaml
{
  "type": "context",
  "elements": [
    {
      "type": "mrkdwn",
      "text": "Last updated: <!date^1234567890^{date_short}|fallback>"
    }
  ]
}
```

---

## Email Notifications

### GitHub Default Email Notifications

GitHub automatically sends email notifications for:

- Failed workflows (to commit author)
- Workflow status changes
- Pull request reviews
- Mentions in PR comments

### Configure Email Preferences

1. **Go to GitHub Settings:**
   - Click profile icon > **Settings**
   - Click **Notifications** in sidebar

2. **Configure Workflow Notifications:**
   - ✅ **Actions** > **Failed workflows only**
   - ✅ **Watching** > Repositories you're watching
   - ✅ **Participating** > Repositories you contribute to

3. **Choose Notification Method:**
   - ✅ Email
   - ✅ Web
   - ⬜ Mobile (GitHub Mobile app)

### Custom Email Notifications

To send custom emails, use a third-party action:

```yaml
- name: Send email notification
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: CI Pipeline Failed - ${{ github.repository }}
    to: team@example.com
    from: ci-notifications@example.com
    body: |
      CI Pipeline failed on ${{ github.repository }}

      Branch: ${{ github.ref_name }}
      Commit: ${{ github.sha }}
      Author: ${{ github.actor }}

      View details: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

---

## GitHub Notifications

### Pull Request Comments

Already configured in `.github/workflows/ci.yml`:

```yaml
- name: Post status to PR
  if: github.event_name == 'pull_request'
  uses: actions/github-script@v7
  with:
    script: |
      const status = '${{ needs.backend-lint.result }}' === 'success' &&
                    '${{ needs.backend-unit-tests.result }}' === 'success' &&
                    '${{ needs.backend-integration-tests.result }}' === 'success' &&
                    '${{ needs.frontend-lint.result }}' === 'success' &&
                    '${{ needs.frontend-build-test.result }}' === 'success';

      const emoji = status ? '✅' : '❌';
      const message = status ? 'All CI checks passed!' : 'Some CI checks failed. Please review the logs.';

      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: `## ${emoji} CI Pipeline Status\n\n${message}\n\n` +
              `- Backend Linting: ${{ needs.backend-lint.result }}\n` +
              `- Backend Unit Tests: ${{ needs.backend-unit-tests.result }}\n` +
              `- Backend Integration Tests: ${{ needs.backend-integration-tests.result }}\n` +
              `- Frontend Linting: ${{ needs.frontend-lint.result }}\n` +
              `- Frontend Build & Test: ${{ needs.frontend-build-test.result }}`
      });
```

### GitHub Status Checks

Status checks automatically appear on:
- Pull request pages
- Commit pages
- Branch protection checks

No additional configuration needed.

### GitHub Discussions

To post to GitHub Discussions:

```yaml
- name: Post to Discussions
  uses: actions/github-script@v7
  with:
    script: |
      await github.rest.teams.createDiscussionInOrg({
        org: context.repo.owner,
        team_slug: 'engineering',
        title: 'CI Pipeline Failed',
        body: 'CI pipeline failed on main branch. Please investigate.'
      });
```

---

## Custom Webhooks

### Overview

Send notifications to any HTTP endpoint using webhooks.

### Setup

1. **Create webhook endpoint** (your server)
2. **Add endpoint URL to GitHub Secrets**
3. **Configure workflow:**

```yaml
- name: Send webhook notification
  run: |
    curl -X POST ${{ secrets.WEBHOOK_URL }} \
      -H "Content-Type: application/json" \
      -d '{
        "event": "ci_failed",
        "repository": "${{ github.repository }}",
        "branch": "${{ github.ref_name }}",
        "commit": "${{ github.sha }}",
        "author": "${{ github.actor }}",
        "workflow_url": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
      }'
```

### Webhook Payload Example

```json
{
  "event": "ci_failed",
  "repository": "your-org/wwmaa",
  "branch": "main",
  "commit": "abc123def456",
  "author": "johndoe",
  "workflow_url": "https://github.com/your-org/wwmaa/actions/runs/123456",
  "timestamp": "2025-11-10T20:00:00Z",
  "checks": {
    "backend-lint": "success",
    "backend-unit-tests": "failure",
    "backend-integration-tests": "success",
    "frontend-lint": "success",
    "frontend-build-test": "success"
  }
}
```

---

## Integration Examples

### Discord Integration

```yaml
- name: Send Discord notification
  uses: sarisia/actions-status-discord@v1
  if: always()
  with:
    webhook: ${{ secrets.DISCORD_WEBHOOK }}
    status: ${{ job.status }}
    title: "CI Pipeline"
    description: "Build and test completed"
    color: 0x0000ff
```

### Microsoft Teams Integration

```yaml
- name: Send Teams notification
  uses: jdcargile/ms-teams-notification@v1.3
  with:
    github-token: ${{ github.token }}
    ms-teams-webhook-uri: ${{ secrets.TEAMS_WEBHOOK }}
    notification-summary: CI Pipeline Failed
    notification-color: dc3545
```

### PagerDuty Integration

```yaml
- name: Trigger PagerDuty incident
  if: failure()
  uses: machulav/create-pagerduty-incident@v1
  with:
    token: ${{ secrets.PAGERDUTY_TOKEN }}
    service_id: ${{ secrets.PAGERDUTY_SERVICE_ID }}
    title: "CI Pipeline Failed on ${{ github.repository }}"
    body: |
      CI pipeline failed on main branch

      Repository: ${{ github.repository }}
      Commit: ${{ github.sha }}
      Author: ${{ github.actor }}
    urgency: high
```

---

## Troubleshooting

### Problem: Slack Notifications Not Received

**Solutions:**

1. **Verify webhook URL:**
   ```bash
   # Test webhook manually
   curl -X POST $SLACK_WEBHOOK_URL \
     -H 'Content-Type: application/json' \
     -d '{"text":"Test notification"}'
   ```

2. **Check GitHub Secret:**
   - Ensure `SLACK_WEBHOOK_URL` is set
   - Verify secret name matches workflow

3. **Check workflow condition:**
   - Verify `if: failure() && github.ref == 'refs/heads/main'`
   - Test by pushing to main branch

4. **Check Slack app permissions:**
   - Verify app is still installed
   - Check channel permissions

### Problem: Email Notifications Not Received

**Solutions:**

1. **Check GitHub notification settings:**
   - Profile > Settings > Notifications
   - Verify email address is confirmed

2. **Check spam folder:**
   - GitHub notifications may be flagged

3. **Whitelist GitHub email:**
   - Add `notifications@github.com` to contacts

### Problem: Too Many Notifications

**Solutions:**

1. **Reduce notification frequency:**
   ```yaml
   # Only notify on main branch
   if: failure() && github.ref == 'refs/heads/main'
   ```

2. **Use notification digests:**
   - Configure in Slack/Email settings
   - Group notifications by time period

3. **Filter by severity:**
   ```yaml
   # Only notify on critical failures
   if: failure() && contains(needs.*.result, 'failure') && github.ref == 'refs/heads/main'
   ```

---

## Best Practices

### 1. Notification Hierarchy

- **Critical:** Main branch failures, deployment failures
- **Important:** PR failures, security vulnerabilities
- **Informational:** PR comments, successful deployments

### 2. Avoid Notification Fatigue

- Don't notify on every event
- Group related notifications
- Use different channels for different severities

### 3. Actionable Notifications

Include:
- What failed
- Where to find logs
- How to fix (if known)
- Who to contact

### 4. Test Notifications

- Test webhook URLs before deploying
- Verify notifications in development first
- Have a rollback plan

### 5. Security

- Never commit webhook URLs
- Use GitHub Secrets
- Rotate secrets regularly
- Limit webhook permissions

---

## Summary Checklist

When setting up notifications:

- ✅ Slack webhook created and tested
- ✅ GitHub Secret configured
- ✅ Workflow updated with notification step
- ✅ Tested with actual failure
- ✅ Team notified about new notifications
- ✅ Notification channel monitored
- ✅ Escalation path defined
- ✅ Documentation updated

---

## Additional Resources

- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [GitHub Actions Notifications](https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/notifications-for-workflow-runs)
- [GitHub Script Action](https://github.com/actions/github-script)
- [Slack GitHub Action](https://github.com/slackapi/slack-github-action)

---

**Last Updated:** November 10, 2025
**Maintainer:** WWMAA Development Team
