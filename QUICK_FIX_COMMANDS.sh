#!/bin/bash

# Quick Fix Script for Railway Deployment Issues
# Run this after logging in to Railway CLI

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Railway Quick Fix Script                               ║"
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
railway link
echo ""

# Add backend environment variable
echo "3. Adding ZERODB_PROJECT_ID to backend..."
railway variables --set ZERODB_PROJECT_ID=e4f3d95f-593f-4ae6-9017-24bff5f72c5e --service WWMAA-BACKEND

if [ $? -eq 0 ]; then
    echo "   ✅ Variable added successfully!"
    echo "   Railway will auto-redeploy the backend."
else
    echo "   ❌ Failed to add variable"
    echo "   Please add manually via Railway Dashboard"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Next Steps:                                                   ║"
echo "║  1. Wait for backend to redeploy (2-3 minutes)                 ║"
echo "║  2. Go to Railway Dashboard → WWMAA-FRONTEND → Settings        ║"
echo "║  3. Clear Build Cache                                          ║"
echo "║  4. Click Deploy                                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

