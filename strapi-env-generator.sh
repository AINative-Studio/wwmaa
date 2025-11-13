#!/bin/bash
# ==========================================
# WWMAA Strapi - Environment Variable Generator
# ==========================================
# Generates secure random secrets for Strapi deployment
# Run this script once to generate all required secrets

set -e

echo "=========================================="
echo "Strapi Environment Variables Generator"
echo "=========================================="
echo ""

# Function to generate secure random string
generate_secret() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-64
}

# Function to generate hex string
generate_hex() {
    openssl rand -hex 32
}

echo "Generating secure secrets..."
echo ""

# Generate all required secrets
ADMIN_JWT_SECRET=$(generate_secret)
API_TOKEN_SALT=$(generate_secret)
JWT_SECRET=$(generate_secret)
TRANSFER_TOKEN_SALT=$(generate_secret)
APP_KEY_1=$(generate_hex)
APP_KEY_2=$(generate_hex)
APP_KEY_3=$(generate_hex)
APP_KEY_4=$(generate_hex)

# Output environment variables
echo "=========================================="
echo "COPY THESE TO RAILWAY STRAPI SERVICE"
echo "=========================================="
echo ""
echo "# ===== Strapi Secrets ====="
echo "ADMIN_JWT_SECRET=${ADMIN_JWT_SECRET}"
echo "API_TOKEN_SALT=${API_TOKEN_SALT}"
echo "JWT_SECRET=${JWT_SECRET}"
echo "TRANSFER_TOKEN_SALT=${TRANSFER_TOKEN_SALT}"
echo "APP_KEYS=${APP_KEY_1},${APP_KEY_2},${APP_KEY_3},${APP_KEY_4}"
echo ""
echo "# ===== Database Configuration ====="
echo "# These will be automatically set by Railway PostgreSQL plugin"
echo "DATABASE_CLIENT=postgres"
echo "# DATABASE_HOST=<Railway will provide>"
echo "# DATABASE_PORT=<Railway will provide>"
echo "# DATABASE_NAME=<Railway will provide>"
echo "# DATABASE_USERNAME=<Railway will provide>"
echo "# DATABASE_PASSWORD=<Railway will provide>"
echo "DATABASE_SSL=false"
echo "DATABASE_POOL_MIN=2"
echo "DATABASE_POOL_MAX=10"
echo ""
echo "# ===== Application Configuration ====="
echo "NODE_ENV=production"
echo "# PORT=<Railway will provide>"
echo "HOST=0.0.0.0"
echo ""
echo "# ===== Frontend Integration ====="
echo "# Replace with your actual Railway frontend URL"
echo "STRAPI_ADMIN_CLIENT_URL=https://wwmaa-frontend.railway.app"
echo "STRAPI_ADMIN_CLIENT_PREVIEW_SECRET=$(generate_secret)"
echo ""
echo "# ===== Admin Panel Configuration ====="
echo "# Replace with your actual Strapi service URL"
echo "ADMIN_URL=/admin"
echo "PUBLIC_URL=https://wwmaa-strapi.railway.app"
echo ""
echo "# ===== CORS & Security ====="
echo "CORS_ORIGIN=https://wwmaa-frontend.railway.app,https://yourdomain.com"
echo ""
echo "# ===== File Upload Configuration ====="
echo "# For local storage (default)"
echo "UPLOAD_PROVIDER=local"
echo "# For Cloudflare R2 (recommended for production)"
echo "# UPLOAD_PROVIDER=cloudflare-r2"
echo "# CF_R2_ACCOUNT_ID=your-account-id"
echo "# CF_R2_ACCESS_KEY_ID=your-access-key"
echo "# CF_R2_SECRET_ACCESS_KEY=your-secret-key"
echo "# CF_R2_BUCKET=strapi-uploads"
echo "# CF_R2_REGION=auto"
echo ""
echo "=========================================="
echo ""
echo "Save these values securely!"
echo "Add them to Railway > Strapi Service > Variables"
echo ""
