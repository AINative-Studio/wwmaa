#!/bin/bash
set -e

echo "=========================================="
echo "🚀 WWMAA Backend Starting on Railway"
echo "=========================================="
echo "📅 Date: $(date)"
echo "🌍 Region: ${RAILWAY_REGION:-unknown}"
echo "🔌 Port: ${PORT:-8000}"
echo "🏗️  Environment: ${PYTHON_ENV:-not-set}"
echo "=========================================="

# Check critical environment variables
echo ""
echo "🔍 Checking Environment Variables..."
echo "=========================================="

check_var() {
    if [ -z "${!1}" ]; then
        echo "❌ MISSING: $1"
        return 1
    else
        echo "✅ Found: $1"
        return 0
    fi
}

MISSING=0

# Check all critical variables
check_var "ZERODB_API_BASE_URL" || MISSING=$((MISSING+1))
check_var "ZERODB_EMAIL" || MISSING=$((MISSING+1))
check_var "ZERODB_PASSWORD" || MISSING=$((MISSING+1))
check_var "ZERODB_API_KEY" || MISSING=$((MISSING+1))
check_var "JWT_SECRET" || MISSING=$((MISSING+1))
check_var "JWT_ALGORITHM" || MISSING=$((MISSING+1))
check_var "BEEHIIV_API_KEY" || MISSING=$((MISSING+1))
check_var "AINATIVE_API_KEY" || MISSING=$((MISSING+1))
check_var "PORT" || MISSING=$((MISSING+1))

echo "=========================================="
if [ $MISSING -gt 0 ]; then
    echo "❌ ERROR: $MISSING required environment variables are missing!"
    echo "Please configure them in Railway Variables tab"
    echo "=========================================="
    exit 1
fi
echo "✅ All required environment variables present"
echo "=========================================="

# Test ZeroDB connectivity
echo ""
echo "🔗 Testing ZeroDB Connection..."
echo "=========================================="
python3 << 'PYEOF'
import requests
import os
import sys

try:
    url = os.getenv('ZERODB_API_BASE_URL')
    print(f"Connecting to: {url}")
    response = requests.get(f"{url}/health", timeout=10)
    print(f"✅ ZeroDB Status: {response.status_code}")
except Exception as e:
    print(f"⚠️  ZeroDB connection failed: {e}")
    print("Continuing anyway...")
PYEOF

echo "=========================================="

# Start Uvicorn
echo ""
echo "🎯 Starting Uvicorn Server..."
echo "=========================================="
echo "Host: 0.0.0.0"
echo "Port: ${PORT}"
echo "Workers: 1"
echo "=========================================="
echo ""

# Run uvicorn with explicit error handling
exec uvicorn backend.app:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers 1 \
    --log-level info \
    --access-log \
    --use-colors
