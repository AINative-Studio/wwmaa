# Sprint 6 Integration Tests - Real API Testing

## Overview

The `test_integrations.py` script performs comprehensive integration tests against real external APIs to verify that all Sprint 6 integrations are properly configured and working.

## What It Tests

### 1. Cloudflare Calls Service
- Creates a test video conferencing room
- Generates a participant token
- Deletes the test room (cleanup)
- **Estimated Cost**: ~$0.01 per test run

### 2. Cloudflare Stream Service
- Uploads a small test video from URL
- Checks video processing status
- Generates a signed playback URL
- Deletes the test video (cleanup)
- **Estimated Cost**: ~$0.02 per test run

### 3. BeeHiiv Service
- Adds a test subscriber with timestamped email
- Retrieves subscriber details to verify creation
- Removes the test subscriber (cleanup)
- **Estimated Cost**: Free (within API limits)

### 4. ZeroDB Connection
- Verifies connection to ZeroDB API
- Queries critical collections (users, events, etc.)
- Lists available collections
- **Estimated Cost**: Free (read operations)

## Prerequisites

### Required Environment Variables

Before running the tests, ensure the following environment variables are set in your `.env` file:

#### Cloudflare Configuration
```bash
CLOUDFLARE_ACCOUNT_ID=your-actual-cloudflare-account-id
CLOUDFLARE_API_TOKEN=your-actual-cloudflare-api-token
CLOUDFLARE_CALLS_APP_ID=your-actual-calls-app-id  # Optional
```

#### BeeHiiv Configuration
```bash
BEEHIIV_API_KEY=your-actual-beehiiv-api-key
BEEHIIV_PUBLICATION_ID=your-actual-publication-id
```

#### ZeroDB Configuration
```bash
ZERODB_API_KEY=your-actual-zerodb-api-key
ZERODB_API_BASE_URL=https://api.ainative.studio
```

## How to Run

### Basic Usage

```bash
# From project root
python3 backend/scripts/test_integrations.py

# Or using the shebang
./backend/scripts/test_integrations.py
```

### Expected Output

When all credentials are properly configured, you should see:

```
╔══════════════════════════════════════════════════════════════╗
║        Sprint 6 Integration Tests - Real API Testing         ║
╚══════════════════════════════════════════════════════════════╝

Checking credentials...

  ✓ cloudflare_calls: Credentials available
  ✓ cloudflare_stream: Credentials available
  ✓ beehiiv: Credentials available
  ✓ zerodb: Credentials available

[1/4] Testing Cloudflare Calls...
  ✓ Creating test room (session: integration-test-room-1234567890)
  ✓ Room created successfully (ID: abc123def456)
  ✓ Generating participant token
  ✓ Participant token generated successfully
  ✅ PASSED (2.3s)

[2/4] Testing Cloudflare Stream...
  ✓ Creating test video from URL
  ✓ Video created successfully (ID: xyz789)
  ✓ Checking video processing status
  ✓ Video status: queued
  ✓ Generating playback URL
  ✓ Playback URL generated successfully
  ✅ PASSED (5.1s)

[3/4] Testing BeeHiiv...
  ✓ Adding test subscriber (integration-test-1234567890@example.com)
  ✓ Subscriber added successfully
  ✓ Verifying subscriber exists
  ✓ Subscriber verified successfully
  ✅ PASSED (1.8s)

[4/4] Testing ZeroDB...
  ✓ Testing connection to ZeroDB
  ✓ Querying 'users' collection
  ✓ Successfully connected to ZeroDB
  ✓ Verifying critical collections exist
  ✓ Found 6/6 collections
  ✅ PASSED (0.5s)

Cleaning up test resources...
  ✓ Delete Cloudflare Calls room abc123def456
  ✓ Delete Cloudflare Stream video xyz789
  ✓ Remove BeeHiiv subscriber integration-test-1234567890@example.com

╔══════════════════════════════════════════════════════════════╗
║                      TEST RESULTS                             ║
╠══════════════════════════════════════════════════════════════╣
║ Total Tests:    4                                             ║
║ Passed:         4                                             ║
║ Failed:         0                                             ║
║ Duration:       9.7s                                          ║
║ Status:         ✅ ALL TESTS PASSED                          ║
╚══════════════════════════════════════════════════════════════╝

Estimated API costs for this test run: $0.03

Results saved to: /Users/aideveloper/Desktop/wwmaa/integration-test-results.txt
```

## Output Files

The script generates a detailed test report saved to:
```
/Users/aideveloper/Desktop/wwmaa/integration-test-results.txt
```

This file contains:
- Test execution timestamp
- All test steps and their results
- Error messages for failed tests
- Summary statistics
- Estimated API costs

## Error Handling

### Missing Credentials

If credentials are missing or not properly configured, the script will:
1. Detect the missing credentials
2. Skip the affected tests
3. Display a clear warning message
4. Continue testing other services

Example:
```
⚠ cloudflare_calls: Missing credentials - CLOUDFLARE_ACCOUNT_ID
⊘ SKIPPED (0.0s)
```

### API Failures

If an API call fails during testing, the script will:
1. Catch the exception
2. Log the detailed error message
3. Mark the test as failed
4. Attempt to run cleanup tasks
5. Continue with remaining tests

Example:
```
✗ Error: Cloudflare Calls API error: Invalid API token
❌ FAILED (0.2s)
```

## Cleanup Guarantee

The script uses try/finally blocks to ensure cleanup happens even if tests fail:

1. **Cloudflare Calls**: Deletes test rooms
2. **Cloudflare Stream**: Deletes test videos
3. **BeeHiiv**: Removes test subscribers
4. **ZeroDB**: No cleanup needed (read-only operations)

If cleanup fails, the script will:
- Log the cleanup failure
- Continue with other cleanup tasks
- Report cleanup issues in the output

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed
- `130`: Tests interrupted by user (Ctrl+C)

## Cost Tracking

The script estimates API costs for each test run:

| Service | Cost per Test | Notes |
|---------|--------------|-------|
| Cloudflare Calls | ~$0.01 | Room creation |
| Cloudflare Stream | ~$0.02 | 1 minute video upload |
| BeeHiiv | $0.00 | Free within rate limits |
| ZeroDB | $0.00 | Read operations only |

**Total Estimated Cost per Run**: ~$0.03

## Troubleshooting

### Common Issues

#### 1. "command not found: python"
```bash
# Use python3 instead
python3 backend/scripts/test_integrations.py
```

#### 2. "ZERODB_API_KEY is required"
```bash
# Ensure .env file exists and contains valid credentials
cp .env.example .env
# Edit .env with your actual credentials
```

#### 3. "Module not found" errors
```bash
# Install dependencies
pip install -r backend/requirements.txt
```

#### 4. Tests timeout or hang
```bash
# Check network connectivity
# Verify API endpoints are accessible
# Check firewall/proxy settings
```

#### 5. Invalid credentials errors
```bash
# Verify credentials in .env are correct
# Check credential format matches expected pattern
# Ensure credentials have proper permissions
```

### Debug Mode

To see detailed logging from services, edit the script and comment out these lines:

```python
# Comment out to enable debug logging
# logging.getLogger("backend.services").setLevel(logging.CRITICAL)
# logging.getLogger("urllib3").setLevel(logging.CRITICAL)
# logging.getLogger("requests").setLevel(logging.CRITICAL)
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Integration Tests

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
  workflow_dispatch:  # Manual trigger

jobs:
  integration-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt

      - name: Run integration tests
        env:
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          BEEHIIV_API_KEY: ${{ secrets.BEEHIIV_API_KEY }}
          BEEHIIV_PUBLICATION_ID: ${{ secrets.BEEHIIV_PUBLICATION_ID }}
          ZERODB_API_KEY: ${{ secrets.ZERODB_API_KEY }}
          ZERODB_API_BASE_URL: ${{ secrets.ZERODB_API_BASE_URL }}
        run: |
          python3 backend/scripts/test_integrations.py

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: integration-test-results
          path: integration-test-results.txt
```

## Security Considerations

1. **Never commit real credentials** to version control
2. **Use environment variables** for all sensitive data
3. **Rotate API keys regularly** after running tests in public environments
4. **Monitor API usage** to detect unauthorized access
5. **Use separate test accounts** when possible
6. **Implement rate limiting** to avoid excessive API costs

## Maintenance

### Adding New Tests

To add a new integration test:

1. Create a new test method following the pattern:
```python
def test_new_service(self) -> bool:
    """Test NewService integration"""
    service_name = "new_service"
    self.log(f"{Colors.BOLD}[N/M] Testing NewService...{Colors.RESET}")
    start_time = time.time()

    try:
        # Test implementation
        # ...

        # Add cleanup if needed
        self.add_cleanup("Cleanup NewService", cleanup_func)

        # Success
        elapsed = time.time() - start_time
        self.timings[service_name] = elapsed
        self.log(f"  {Colors.GREEN}✅ PASSED{Colors.RESET} ({elapsed:.1f}s)\n")
        return True

    except Exception as e:
        elapsed = time.time() - start_time
        self.timings[service_name] = elapsed
        self.errors[service_name] = str(e)
        self.log_error(f"Error: {str(e)}")
        self.log(f"  {Colors.RED}❌ FAILED{Colors.RESET} ({elapsed:.1f}s)\n")
        return False
```

2. Add credentials check to `check_credentials()` method
3. Add test to the `tests` list in `run_all_tests()`
4. Update estimated costs in `ESTIMATED_COSTS` dict

### Updating Dependencies

When service interfaces change:

1. Update the import statements
2. Modify test method implementations
3. Update cleanup logic if needed
4. Test thoroughly before committing

## Support

For issues or questions:
- Check this README first
- Review test output in `integration-test-results.txt`
- Check service-specific documentation
- Contact the development team

## License

Copyright (c) 2025 WWMAA. All rights reserved.
