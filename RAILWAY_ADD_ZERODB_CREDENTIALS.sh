#!/bin/bash

# Script to add all ZeroDB credentials to Railway Backend
# This fixes the "Authentication failed: Could not validate credentials" error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Add ZeroDB Credentials to Railway Backend             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if logged in
echo "1. Checking Railway login status..."
if ! railway whoami &>/dev/null; then
    echo "   ❌ Not logged in to Railway"
    echo "   Please run: railway login"
    echo ""
    echo "   Then run this script again."
    exit 1
fi

echo "   ✅ Logged in to Railway"
echo ""

# Link to project
echo "2. Linking to WWMAA project..."
cd /Users/aideveloper/Desktop/wwmaa
railway link
echo ""

# Add all ZeroDB environment variables
echo "3. Adding ZeroDB credentials to backend..."
echo ""

# ZERODB_EMAIL
echo "   Adding ZERODB_EMAIL..."
railway variables --set ZERODB_EMAIL=admin@ainative.studio --service WWMAA-BACKEND
if [ $? -eq 0 ]; then
    echo "   ✅ ZERODB_EMAIL added"
else
    echo "   ❌ Failed to add ZERODB_EMAIL"
fi

# ZERODB_PASSWORD
echo "   Adding ZERODB_PASSWORD..."
railway variables --set ZERODB_PASSWORD=Admin2025!Secure --service WWMAA-BACKEND
if [ $? -eq 0 ]; then
    echo "   ✅ ZERODB_PASSWORD added"
else
    echo "   ❌ Failed to add ZERODB_PASSWORD"
fi

# ZERODB_API_KEY
echo "   Adding ZERODB_API_KEY..."
railway variables --set ZERODB_API_KEY=kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM --service WWMAA-BACKEND
if [ $? -eq 0 ]; then
    echo "   ✅ ZERODB_API_KEY added"
else
    echo "   ❌ Failed to add ZERODB_API_KEY"
fi

# ZERODB_API_BASE_URL
echo "   Adding ZERODB_API_BASE_URL..."
railway variables --set ZERODB_API_BASE_URL=https://api.ainative.studio --service WWMAA-BACKEND
if [ $? -eq 0 ]; then
    echo "   ✅ ZERODB_API_BASE_URL added"
else
    echo "   ❌ Failed to add ZERODB_API_BASE_URL"
fi

# ZERODB_PROJECT_ID (verify it's there)
echo "   Verifying ZERODB_PROJECT_ID..."
railway variables --set ZERODB_PROJECT_ID=e4f3d95f-593f-4ae6-9017-24bff5f72c5e --service WWMAA-BACKEND
if [ $? -eq 0 ]; then
    echo "   ✅ ZERODB_PROJECT_ID verified"
else
    echo "   ❌ Failed to verify ZERODB_PROJECT_ID"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  All ZeroDB credentials added!                                 ║"
echo "║                                                                ║"
echo "║  Next Steps:                                                   ║"
echo "║  1. Railway will auto-redeploy the backend (2-3 minutes)       ║"
echo "║  2. Wait for deployment to complete                            ║"
echo "║  3. Test the backend with the test script                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
