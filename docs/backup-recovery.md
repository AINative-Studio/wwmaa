# ZeroDB Backup & Recovery Documentation

**Version:** 1.0.0
**Last Updated:** January 9, 2025
**Responsible Team:** Backend Engineering / DevOps

---

## Table of Contents

1. [Overview](#overview)
2. [Backup Strategy](#backup-strategy)
3. [Retention Policy](#retention-policy)
4. [Backup Procedures](#backup-procedures)
5. [Recovery Procedures](#recovery-procedures)
6. [Automated Scheduling](#automated-scheduling)
7. [Monitoring & Alerts](#monitoring--alerts)
8. [Testing & Validation](#testing--validation)
9. [Disaster Recovery](#disaster-recovery)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The WWMAA platform uses a comprehensive backup and recovery system for all ZeroDB collections. This system ensures data resilience, enables point-in-time recovery, and provides protection against data loss incidents.

### Key Features

- **Full and Incremental Backups**: Support for complete and differential backups
- **Automated Compression**: Gzip compression reduces storage costs by ~70%
- **Cloud Storage**: Backups stored in ZeroDB Object Storage
- **Retention Policy**: Automated lifecycle management (7 daily, 4 weekly, 12 monthly)
- **Point-in-Time Recovery**: Restore to any previous backup
- **Validation**: Integrity checks before and after restore
- **All 14 Collections**: Comprehensive coverage of entire database

### Collections Covered

All 14 ZeroDB collections are backed up:

1. **users** - User authentication and basic info
2. **applications** - Membership applications
3. **approvals** - Application approval workflow
4. **subscriptions** - Membership subscription tiers
5. **payments** - Payment transactions
6. **profiles** - Extended user profile data
7. **events** - Community events
8. **rsvps** - Event RSVPs
9. **training_sessions** - Training session metadata
10. **session_attendance** - Training attendance records
11. **search_queries** - AI search query logs
12. **content_index** - Searchable content with embeddings
13. **media_assets** - Media file metadata
14. **audit_logs** - System audit trail

---

## Backup Strategy

### Backup Types

#### Full Backup
- **Description**: Complete export of all documents in a collection
- **Frequency**: Daily (automated)
- **Use Case**: Primary backup method, disaster recovery
- **Storage**: ZeroDB Object Storage
- **Format**: Gzip-compressed JSON

#### Incremental Backup
- **Description**: Export only documents changed since last full backup
- **Frequency**: Hourly (optional, for high-traffic collections)
- **Use Case**: Minimize backup time and storage for large collections
- **Requirement**: Must have a previous full backup

### Backup File Structure

```
backups/
├── users_full_20250109_143000.json.gz
├── users_incremental_20250109_150000.json.gz
├── profiles_full_20250109_143015.json.gz
├── events_full_20250109_143030.json.gz
└── ...
```

### Backup Metadata

Each backup includes comprehensive metadata:

```json
{
  "backup_id": "users_full_20250109_143000",
  "collection": "users",
  "backup_type": "full",
  "file_name": "users_full_20250109_143000.json.gz",
  "object_path": "backups/users_full_20250109_143000.json.gz",
  "file_size": 1048576,
  "document_count": 1250,
  "status": "completed",
  "version": "1.0.0",
  "created_at": "2025-01-09T14:30:00.000000",
  "completed_at": "2025-01-09T14:30:45.123456"
}
```

---

## Retention Policy

### Retention Schedule

The system automatically enforces a tiered retention policy:

| Backup Age | Retention Policy | Rationale |
|-----------|-----------------|-----------|
| 0-7 days | **Keep all daily backups** | Recent data recovery, rollback support |
| 8-28 days | **Keep first backup of each week** | Weekly snapshots, trend analysis |
| 29-365 days | **Keep first backup of each month** | Long-term compliance, historical data |
| 365+ days | **Delete** | Cost optimization, compliance limits |

### Storage Estimates

Approximate storage requirements (with compression):

| Collection | Avg Docs | Compressed Size | Weekly Storage |
|-----------|----------|----------------|----------------|
| users | 5,000 | 2 MB | 14 MB |
| profiles | 5,000 | 5 MB | 35 MB |
| events | 2,000 | 3 MB | 21 MB |
| audit_logs | 50,000 | 15 MB | 105 MB |
| **Total** | **~75,000** | **~80 MB** | **~560 MB** |

**Monthly Storage**: ~2.4 GB
**Annual Storage**: ~15 GB (with retention policy)

---

## Backup Procedures

### Manual Backup - All Collections

```bash
# Full backup of all 14 collections
python scripts/backup.py --backup

# Incremental backup of all collections
python scripts/backup.py --backup --incremental

# Dry run (test without uploading)
python scripts/backup.py --backup --dry-run
```

### Manual Backup - Specific Collections

```bash
# Backup specific collections
python scripts/backup.py --backup --collections users,profiles,events

# Incremental backup of specific collections
python scripts/backup.py --backup --incremental --collections audit_logs,search_queries
```

### List Available Backups

```bash
# List all backups
python scripts/backup.py --list

# List backups for specific collection
python scripts/backup.py --list --collection users

# List only full backups
python scripts/backup.py --list --backup-type full

# Show detailed information
python scripts/backup.py --list --verbose
```

### Example Output

```
================================================================================
  AVAILABLE BACKUPS
================================================================================

Total Backups: 145
Collections: 14

USERS (12 backups):
--------------------------------------------------------------------------------
Backup ID                                     Collection          Type          Date                  Docs      Size
--------------------------------------------------------------------------------------------------------------------
users_full_20250109_143000                    users               full          2025-01-09 14:30:00   1250      2.1 MB
users_incremental_20250109_150000             users               incremental   2025-01-09 15:00:00   45        125 KB
users_full_20250108_143000                    users               full          2025-01-08 14:30:00   1245      2.0 MB
...
```

---

## Recovery Procedures

### Validate Backup Before Restore

**ALWAYS** validate a backup before restoring to production:

```bash
# Validate backup integrity
python scripts/backup.py --restore users_full_20250109_143000 --validate-only
```

### Restore Single Collection

```bash
# Step 1: DRY RUN (simulates restore without changes)
python scripts/backup.py --restore users_full_20250109_143000 --dry-run

# Step 2: Review dry run output, then restore
python scripts/backup.py --restore users_full_20250109_143000

# Step 3: Verify restoration
# Check document counts, sample data, application functionality
```

### Restore with Merge Mode

By default, restore **replaces** existing documents. Use `--merge` to combine with existing data:

```bash
# Merge restored data with existing documents
python scripts/backup.py --restore users_full_20250109_143000 --merge
```

**Merge Mode Behavior:**
- Existing fields are **preserved** unless explicitly in backup
- New fields from backup are **added**
- Use for partial restoration or selective recovery

### Point-in-Time Recovery

Restore specific collections to a previous state:

```bash
# Restore users collection to state at specific time
python scripts/backup.py --restore users_full_20250109_120000

# Find backup ID closest to desired timestamp
python scripts/backup.py --list --collection users
```

### Full System Recovery

For complete disaster recovery:

```bash
#!/bin/bash
# full_system_restore.sh

# Step 1: Get latest backups for all collections
python scripts/backup.py --list > available_backups.txt

# Step 2: Restore each collection (use latest full backup)
for collection in users applications approvals subscriptions payments profiles events rsvps training_sessions session_attendance search_queries content_index media_assets audit_logs; do
    # Find latest full backup for collection
    BACKUP_ID=$(python scripts/backup.py --list --collection $collection --backup-type full | head -n 1 | awk '{print $1}')

    echo "Restoring $collection from $BACKUP_ID..."
    python scripts/backup.py --restore $BACKUP_ID

    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to restore $collection"
        exit 1
    fi
done

echo "Full system recovery completed successfully"
```

---

## Automated Scheduling

### Railway Cron Jobs (Production)

Configure automated backups in Railway deployment settings:

```yaml
# railway.toml
[deploy]
  cron:
    # Daily full backup at 2 AM UTC
    - schedule: "0 2 * * *"
      command: "python3 backend/scripts/backup.py --backup"

    # Hourly incremental backup (9 AM - 5 PM UTC)
    - schedule: "0 9-17 * * *"
      command: "python3 backend/scripts/backup.py --backup --incremental --collections users,events,payments"

    # Weekly cleanup of old backups (Sunday 3 AM UTC)
    - schedule: "0 3 * * 0"
      command: "python3 backend/scripts/backup.py --cleanup --days 30"
```

### Cron Setup (Self-Hosted)

```bash
# Edit crontab
crontab -e

# Add backup jobs
# Daily full backup at 2 AM
0 2 * * * cd /path/to/wwmaa/backend && python3 scripts/backup.py --backup >> /var/log/zerodb_backup.log 2>&1

# Hourly incremental during business hours (9 AM - 5 PM)
0 9-17 * * * cd /path/to/wwmaa/backend && python3 scripts/backup.py --backup --incremental --collections users,events,payments >> /var/log/zerodb_backup.log 2>&1

# Weekly cleanup (Sunday 3 AM)
0 3 * * 0 cd /path/to/wwmaa/backend && python3 scripts/backup.py --cleanup --days 30 >> /var/log/zerodb_backup.log 2>&1
```

### GitHub Actions (Alternative)

```yaml
# .github/workflows/backup.yml
name: ZeroDB Backup

on:
  schedule:
    # Daily at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  backup:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run backup
        env:
          ZERODB_API_KEY: ${{ secrets.ZERODB_API_KEY }}
          ZERODB_API_BASE_URL: ${{ secrets.ZERODB_API_BASE_URL }}
        run: |
          cd backend
          python scripts/backup.py --backup
```

---

## Monitoring & Alerts

### Backup Success Monitoring

Monitor backup completion and success rate:

```bash
# Check recent backup status
python scripts/backup.py --list --limit 20

# Look for failed backups in logs
tail -100 /tmp/zerodb_backup_cli.log | grep "ERROR"
```

### Recommended Metrics

Track these metrics for backup health:

1. **Backup Completion Rate**: % of successful backups per day
2. **Backup Duration**: Time taken for full backup cycle
3. **Backup Size Growth**: Track collection growth trends
4. **Recovery Test Success**: Quarterly restore test results
5. **Storage Usage**: Total backup storage consumed

### Alert Conditions

Configure alerts for:

- ❌ Backup failure (any collection)
- ⚠️ Backup duration > 30 minutes
- ⚠️ Backup size increase > 50% week-over-week
- ⚠️ Storage usage > 90% of quota
- ❌ Restore test failure
- ⚠️ No backup completed in 24 hours

---

## Testing & Validation

### Quarterly Restore Testing

**CRITICAL**: Test restore procedure every quarter (Q1, Q2, Q3, Q4):

```bash
#!/bin/bash
# quarterly_restore_test.sh

echo "=== Quarterly Restore Test ==="
echo "Date: $(date)"
echo "Tester: $USER"

# Step 1: Create test backup
echo "Creating test backup..."
python scripts/backup.py --backup --collections users

# Step 2: Get backup ID
BACKUP_ID=$(python scripts/backup.py --list --collection users --limit 1 | grep users | awk '{print $1}')

# Step 3: Validate backup
echo "Validating backup..."
python scripts/backup.py --restore $BACKUP_ID --validate-only

if [ $? -ne 0 ]; then
    echo "FAIL: Backup validation failed"
    exit 1
fi

# Step 4: Test restore to staging environment
echo "Testing restore (dry run)..."
python scripts/backup.py --restore $BACKUP_ID --dry-run

if [ $? -ne 0 ]; then
    echo "FAIL: Restore dry run failed"
    exit 1
fi

echo "PASS: Quarterly restore test completed successfully"
echo "Test completed at: $(date)"
```

### Monthly Backup Verification

```bash
# Verify all collections have recent backups (< 24 hours old)
python scripts/backup.py --list | grep $(date -d "yesterday" +%Y%m%d)
```

---

## Disaster Recovery

### Recovery Time Objective (RTO)

- **Single Collection**: 5-15 minutes
- **Full System**: 1-2 hours
- **Target RTO**: < 4 hours

### Recovery Point Objective (RPO)

- **Production**: 1 hour (hourly incremental)
- **Staging**: 24 hours (daily full)
- **Target RPO**: < 1 hour

### Disaster Scenarios

#### Scenario 1: Accidental Data Deletion

```bash
# Identify when data was deleted
python scripts/backup.py --list --collection users

# Restore from backup before deletion
python scripts/backup.py --restore users_full_[TIMESTAMP]
```

#### Scenario 2: Database Corruption

```bash
# Step 1: Stop application
railway down

# Step 2: Restore all collections from latest backup
./full_system_restore.sh

# Step 3: Verify data integrity
# Run application tests, check sample data

# Step 4: Resume application
railway up
```

#### Scenario 3: Complete Infrastructure Loss

```bash
# Step 1: Provision new infrastructure
# Setup ZeroDB instance, Railway environment

# Step 2: Configure environment variables
# ZERODB_API_KEY, ZERODB_API_BASE_URL, etc.

# Step 3: List available backups (from Object Storage)
python scripts/backup.py --list

# Step 4: Full system restore
./full_system_restore.sh

# Step 5: Verify all services operational
```

---

## Troubleshooting

### Issue: Backup Takes Too Long

**Symptoms**: Backup exceeds 30 minutes

**Solutions**:
1. Check collection sizes: `python scripts/backup.py --list --verbose`
2. Use incremental backups for large collections
3. Exclude non-critical collections temporarily
4. Increase timeout in backup configuration

```bash
# Backup only critical collections
python scripts/backup.py --backup --collections users,payments,subscriptions
```

### Issue: Restore Validation Fails

**Symptoms**: `--validate-only` returns errors

**Solutions**:
1. Check backup file integrity
2. Verify backup metadata matches contents
3. Try alternate backup from same day
4. Contact DevOps if all backups from period are invalid

```bash
# Try previous day's backup
python scripts/backup.py --list --collection users | grep 20250108
python scripts/backup.py --restore users_full_20250108_143000 --validate-only
```

### Issue: Out of Storage Space

**Symptoms**: Upload fails with "quota exceeded"

**Solutions**:
1. Run cleanup immediately: `python scripts/backup.py --cleanup --days 30`
2. Reduce retention to 20 days temporarily
3. Request storage quota increase
4. Review backup sizes for anomalies

```bash
# Emergency cleanup - delete backups older than 20 days
python scripts/backup.py --cleanup --days 20

# Check storage usage
python scripts/backup.py --list --verbose | grep "Size" | awk '{sum+=$NF} END {print sum " MB total"}'
```

### Issue: Backup Metadata Missing

**Symptoms**: Cannot find backup in `--list` output

**Solutions**:
1. Check ZeroDB connection
2. Verify backup_metadata collection exists
3. Query object storage directly for backup files
4. Restore metadata from backup file if needed

```bash
# Verify ZeroDB connection
python3 -c "from backend.services.zerodb_service import ZeroDBClient; client = ZeroDBClient(); print('Connected:', client.base_url)"
```

### Issue: Restore Partially Fails

**Symptoms**: Some documents fail to restore

**Solutions**:
1. Check error details in restore output
2. Verify document schema matches current version
3. Run restore with `--merge` mode for problematic documents
4. Manual data migration may be required for schema changes

```bash
# Restore with merge mode (safer for schema mismatches)
python scripts/backup.py --restore users_full_20250109_143000 --merge
```

---

## Best Practices

### DO ✅

- **Always** validate backups before critical restores
- **Always** test restores in staging environment first
- **Always** use `--dry-run` for unfamiliar operations
- **Test** restore procedure quarterly
- **Monitor** backup success rates daily
- **Document** any manual interventions
- **Automate** backups via cron/Railway
- **Verify** backup file sizes periodically

### DON'T ❌

- **Never** delete backups manually from Object Storage
- **Never** restore to production without validation
- **Never** skip testing after major changes
- **Never** ignore backup failure alerts
- **Never** store backups only in single location
- **Avoid** running backups during peak hours
- **Avoid** incremental backups without recent full backup

---

## Support & Escalation

### Backup Issues

- **Level 1**: Check documentation, run diagnostics
- **Level 2**: Review logs (`/tmp/zerodb_backup_cli.log`)
- **Level 3**: Contact Backend Team Lead
- **Level 4**: Emergency - Contact DevOps on-call

### Emergency Contacts

- **Backend Team Lead**: backend-lead@wwmaa.com
- **DevOps On-Call**: devops-oncall@wwmaa.com
- **Slack Channel**: #infrastructure-alerts

---

## Appendix

### Backup Service API Reference

```python
from backend.services.backup_service import BackupService

# Initialize service
backup_service = BackupService()

# Backup single collection
result = backup_service.backup_collection("users", incremental=False)

# Backup all collections
result = backup_service.backup_all_collections()

# List backups
backups = backup_service.list_backups(collection="users", backup_type="full")

# Restore collection
result = backup_service.restore_collection("users", "users_full_20250109_143000")

# Cleanup old backups
result = backup_service.cleanup_old_backups(days=30)
```

### Related Documentation

- [ZeroDB API Documentation](https://docs.zerodb.io)
- [Railway Deployment Guide](https://docs.railway.app)
- [WWMAA System Architecture](./architecture.md)
- [Incident Response Runbook](./runbook.md)

---

**Document Version**: 1.0.0
**Last Review**: January 9, 2025
**Next Review**: April 9, 2025 (Quarterly)
**Owner**: Backend Engineering Team
