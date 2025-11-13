#!/bin/bash

# Generate Secure Keys for Strapi CMS
# Usage: ./generate-keys.sh

echo "========================================="
echo "Strapi CMS - Secure Key Generator"
echo "========================================="
echo ""
echo "Generating 5 secure random keys..."
echo ""

echo "# Strapi Security Keys (Generated: $(date))" > .env.keys
echo "# Copy these values to your .env file" >> .env.keys
echo "" >> .env.keys

echo "1. APP_KEYS (use all 4 keys separated by commas):"
APP_KEY1=$(openssl rand -base64 32)
APP_KEY2=$(openssl rand -base64 32)
APP_KEY3=$(openssl rand -base64 32)
APP_KEY4=$(openssl rand -base64 32)
echo "APP_KEYS=$APP_KEY1,$APP_KEY2,$APP_KEY3,$APP_KEY4"
echo "APP_KEYS=$APP_KEY1,$APP_KEY2,$APP_KEY3,$APP_KEY4" >> .env.keys
echo ""

echo "2. API_TOKEN_SALT:"
API_TOKEN_SALT=$(openssl rand -base64 32)
echo "API_TOKEN_SALT=$API_TOKEN_SALT"
echo "API_TOKEN_SALT=$API_TOKEN_SALT" >> .env.keys
echo ""

echo "3. ADMIN_JWT_SECRET:"
ADMIN_JWT_SECRET=$(openssl rand -base64 32)
echo "ADMIN_JWT_SECRET=$ADMIN_JWT_SECRET"
echo "ADMIN_JWT_SECRET=$ADMIN_JWT_SECRET" >> .env.keys
echo ""

echo "4. TRANSFER_TOKEN_SALT:"
TRANSFER_TOKEN_SALT=$(openssl rand -base64 32)
echo "TRANSFER_TOKEN_SALT=$TRANSFER_TOKEN_SALT"
echo "TRANSFER_TOKEN_SALT=$TRANSFER_TOKEN_SALT" >> .env.keys
echo ""

echo "5. JWT_SECRET:"
JWT_SECRET=$(openssl rand -base64 32)
echo "JWT_SECRET=$JWT_SECRET"
echo "JWT_SECRET=$JWT_SECRET" >> .env.keys
echo ""

echo "========================================="
echo "Keys saved to: .env.keys"
echo "========================================="
echo ""
echo "IMPORTANT:"
echo "1. Copy the values from .env.keys to your .env file"
echo "2. For production, also update the root .env file with STRAPI_* prefixed variables"
echo "3. Delete .env.keys after copying (it's in .gitignore)"
echo "4. NEVER commit these keys to git!"
echo ""
echo "Example .env format:"
echo "APP_KEYS=key1,key2,key3,key4"
echo "API_TOKEN_SALT=your_salt_here"
echo "ADMIN_JWT_SECRET=your_secret_here"
echo "TRANSFER_TOKEN_SALT=your_salt_here"
echo "JWT_SECRET=your_secret_here"
echo ""
