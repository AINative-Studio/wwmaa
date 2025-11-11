# WWMAA Data Export Guide

## Overview

As a WWMAA platform user, you have the right to receive a copy of all your personal data in a structured, machine-readable format. This guide explains how to request and download your data export.

This feature is provided in compliance with:
- **GDPR Article 20**: Right to data portability
- **GDPR Article 15**: Right of access by the data subject

---

## What Data is Included?

Your data export includes **all personal information** we have collected about you:

### 1. Profile Information
- Account details
- Personal information
- Contact information
- Profile settings
- Account creation date

### 2. Membership Applications
- All submitted applications
- Application status history
- Supporting documents metadata
- Submission timestamps

### 3. Subscription & Payment History
- Subscription tier information
- Payment transaction records
- Billing history
- Invoice details
- Subscription start/end dates

### 4. Event Participation
- Event RSVPs
- Check-in records
- Event feedback
- Participation history

### 5. Training Records
- Training session attendance
- Session participation
- Training progress
- Instructor interactions

### 6. Search History
- Search queries
- Search timestamps
- Content interactions
- Browse history

### 7. Activity Logs
- Login history
- Account actions
- Security events
- System interactions

---

## How to Request Your Data

### Via User Settings (Recommended)

1. **Log in** to your WWMAA account
2. Navigate to **Settings** → **Privacy & Security**
3. Scroll to **Data Export** section
4. Click **"Export My Data"** button
5. Confirm your request

### Via API (Advanced Users)

```bash
curl -X POST https://api.wwmaa.com/api/privacy/export-data \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "export_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "Your data export has been generated successfully.",
  "download_url": "https://api.zerodb.io/storage/exports/...",
  "expiry_date": "2025-01-11T12:00:00Z",
  "file_size_bytes": 1024000,
  "record_counts": {
    "profiles": 1,
    "applications": 2,
    "subscriptions": 1,
    "payments": 5,
    "rsvps": 10,
    "search_queries": 50,
    "attendees": 20,
    "audit_logs": 100
  }
}
```

---

## Export Process

### Processing Time
- **Immediate**: Most exports are generated within seconds
- **Large Accounts**: May take up to 5 minutes for accounts with extensive history

### Email Notification
You will receive an email at your registered email address when your export is ready:
- **Subject**: "Your WWMAA Data Export is Ready"
- **Contains**: Secure download link
- **Validity**: 24 hours from generation

### Download Link Expiry
- Export files are available for **24 hours**
- After 24 hours, files are automatically deleted for security
- You can request a new export anytime

---

## Downloading Your Data

### Option 1: Email Link
1. Open the email notification
2. Click the **"Download Your Data"** button
3. Save the JSON file to your computer

### Option 2: API Download
```bash
# Check export status
curl -X GET https://api.wwmaa.com/api/privacy/export-status/EXPORT_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Download will be available via the download_url in response
```

---

## Understanding Your Export

### File Format
- **Format**: JSON (JavaScript Object Notation)
- **Encoding**: UTF-8
- **Structure**: Hierarchical, human-readable
- **Size**: Varies (typically 100KB - 10MB)

### File Structure
```json
{
  "export_metadata": {
    "export_id": "550e8400-e29b-41d4-a716-446655440000",
    "export_date": "2025-01-10T12:00:00Z",
    "expiry_date": "2025-01-11T12:00:00Z",
    "user_id": "user_123",
    "format_version": "1.0",
    "gdpr_article": "Article 20 - Right to data portability"
  },
  "cover_letter": {
    "title": "Your Personal Data Export from WWMAA",
    "introduction": "...",
    "data_included": "...",
    "privacy_notice": "..."
  },
  "data": {
    "profiles": {
      "description": "Profile Information",
      "record_count": 1,
      "records": [...]
    },
    "applications": {
      "description": "Membership Applications",
      "record_count": 2,
      "records": [...]
    },
    ...
  }
}
```

---

## Working with Your Data

### Opening JSON Files

#### Option 1: Text Editor
- **Windows**: Notepad++, Visual Studio Code
- **Mac**: TextEdit, Visual Studio Code
- **Linux**: gedit, vim, Visual Studio Code

#### Option 2: Online Viewers
- [jsonviewer.stack.hu](https://jsonviewer.stack.hu/)
- [jsonformatter.org](https://jsonformatter.org/)

#### Option 3: Spreadsheet Software
- Import JSON into Excel, Google Sheets, or LibreOffice
- Use JSON-to-CSV converters for easier viewing

### Analyzing Your Data

#### Python Example
```python
import json

# Load your export
with open('data_export.json', 'r') as f:
    data = json.load(f)

# Access specific data
profile = data['data']['profiles']['records'][0]
payments = data['data']['payments']['records']

# Print summary
print(f"Account created: {profile['created_at']}")
print(f"Total payments: {len(payments)}")
```

#### JavaScript Example
```javascript
// Load the JSON file
fetch('data_export.json')
  .then(response => response.json())
  .then(data => {
    // Access your data
    const profile = data.data.profiles.records[0];
    const payments = data.data.payments.records;

    console.log('Profile:', profile);
    console.log('Total payments:', payments.length);
  });
```

---

## Transferring Your Data

### To Another Service
1. Download your export file
2. Review the data structure
3. Use the service's import functionality
4. Map WWMAA fields to destination service fields

### Common Use Cases
- **Backup**: Save local copies of your data
- **Analysis**: Analyze your usage patterns
- **Migration**: Transfer to another martial arts platform
- **Compliance**: Fulfill your own data retention policies

---

## Security & Privacy

### Download Security
- **Encrypted Connection**: All downloads use HTTPS
- **Signed URLs**: Download links are cryptographically signed
- **Time-Limited**: Links expire after 24 hours
- **One-Time Use**: Links can be used multiple times within 24 hours

### Data Protection
- **Keep Secure**: Store export files in a secure location
- **Don't Share**: Contains all your personal information
- **Delete After Use**: Remove files when no longer needed
- **Password Protect**: Consider encrypting the file

### What's NOT Included
- Password hashes (for security)
- Internal system IDs
- Other users' data
- Derived analytics data

---

## Frequently Asked Questions

### How often can I request an export?
You can request a new export **once every 24 hours**. This limit prevents abuse while ensuring you can access your data whenever needed.

### Can I automate exports?
Yes, using the API endpoint you can automate exports. However, please respect the rate limits (1 request per 24 hours per user).

### What format is the data in?
JSON (JavaScript Object Notation) - a widely-supported, human-readable format that can be opened with any text editor or imported into databases and spreadsheets.

### How large will my export be?
File sizes vary based on your activity:
- **New accounts**: ~10-50 KB
- **Active accounts**: ~100-500 KB
- **Power users**: ~1-10 MB

### Can I cancel an export request?
Exports are generated immediately (within seconds), so there's no cancellation. However, you can delete the export file after generation.

### What happens after 24 hours?
Export files are **automatically and permanently deleted** from our servers. You can request a new export anytime.

### Can I get data in a different format?
Currently, only JSON format is supported. However, JSON can be easily converted to CSV, Excel, XML, or other formats using free tools.

### Is my data secure during export?
Yes:
- All transfers use encryption (HTTPS/TLS)
- Download links are signed and time-limited
- Files are stored in secure, encrypted object storage
- Automatic deletion after 24 hours

---

## Deleting Export Files Early

If you want to delete your export file before the 24-hour expiry (for security):

### Via Settings
1. Go to **Settings** → **Privacy & Security**
2. Find **Recent Exports** section
3. Click **Delete** next to the export

### Via API
```bash
curl -X DELETE https://api.wwmaa.com/api/privacy/export/EXPORT_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Troubleshooting

### Export request failed
- **Check authentication**: Ensure you're logged in
- **Rate limit**: Wait 24 hours since last export
- **Try again**: Temporary issues usually resolve quickly

### Download link expired
- **Request new export**: Generate a fresh export
- **Download within 24 hours**: Set a reminder

### File won't open
- **Use text editor**: Try Notepad++ or VS Code
- **Check file extension**: Should be `.json`
- **Verify download**: Ensure file downloaded completely

### Data seems incomplete
- **Check all sections**: Data is organized by collection
- **Verify filters**: Some data may be in different sections
- **Contact support**: We'll help locate your data

---

## Contact & Support

### Privacy Questions
**Email**: privacy@wwmaa.com
**Subject**: "Data Export Question"

### Technical Support
**Email**: support@wwmaa.com
**Subject**: "Data Export Technical Issue"

### Data Protection Officer
**Email**: dpo@wwmaa.com
**Subject**: "GDPR Data Request"

---

## Related Resources

- [Privacy Policy](https://wwmaa.com/privacy)
- [Terms of Service](https://wwmaa.com/terms)
- [GDPR Compliance Information](https://wwmaa.com/gdpr)
- [Account Security Guide](https://wwmaa.com/security)
- [Data Retention Policy](https://wwmaa.com/data-retention)

---

## Legal Information

### Your Rights Under GDPR

As a WWMAA user, you have the following data rights:

1. **Right to Access** (Article 15): Request access to your personal data
2. **Right to Rectification** (Article 16): Correct inaccurate data
3. **Right to Erasure** (Article 17): Request deletion of your data
4. **Right to Restrict Processing** (Article 18): Limit how we use your data
5. **Right to Data Portability** (Article 20): Receive data in portable format
6. **Right to Object** (Article 21): Object to certain data processing

This data export feature addresses your **Right to Data Portability** and **Right to Access**.

### Compliance Statement

WWMAA is committed to GDPR compliance and data protection. We:
- Process data lawfully, fairly, and transparently
- Collect data only for specified, explicit purposes
- Ensure data accuracy and keep it up to date
- Store data securely and delete it when no longer needed
- Respect your data rights and respond to requests promptly

---

**Last Updated**: January 10, 2025
**Version**: 1.0
