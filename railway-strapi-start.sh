#!/bin/bash
set -e

echo "=========================================="
echo "Strapi CMS Starting on Railway"
echo "=========================================="
echo "Date: $(date)"
echo "Region: ${RAILWAY_REGION:-unknown}"
echo "Port: ${PORT:-1337}"
echo "Environment: ${NODE_ENV:-not-set}"
echo "=========================================="

# Check critical environment variables
echo ""
echo "Checking Environment Variables..."
echo "=========================================="

check_var() {
    if [ -z "${!1}" ]; then
        echo "MISSING: $1"
        return 1
    else
        echo "Found: $1"
        return 0
    fi
}

MISSING=0

# Check Strapi secrets
check_var "ADMIN_JWT_SECRET" || MISSING=$((MISSING+1))
check_var "API_TOKEN_SALT" || MISSING=$((MISSING+1))
check_var "APP_KEYS" || MISSING=$((MISSING+1))
check_var "JWT_SECRET" || MISSING=$((MISSING+1))

# Check database configuration
echo ""
echo "Database Configuration:"
check_var "DATABASE_CLIENT" || MISSING=$((MISSING+1))

# For Railway PostgreSQL plugin, these should be set automatically
if [ -z "$DATABASE_HOST" ] && [ ! -z "$DATABASE_URL" ]; then
    echo "Found: DATABASE_URL (Railway PostgreSQL plugin detected)"
    echo "Parsing connection details..."

    # Parse DATABASE_URL if provided by Railway
    # Format: postgresql://user:password@host:port/database
    export DATABASE_HOST=$(echo $DATABASE_URL | sed -E 's/.*@(.+):.+\/.+/\1/')
    export DATABASE_PORT=$(echo $DATABASE_URL | sed -E 's/.*:([0-9]+)\/.+/\1/')
    export DATABASE_NAME=$(echo $DATABASE_URL | sed -E 's/.*\/(.+)(\?.*)?$/\1/' | cut -d'?' -f1)
    export DATABASE_USERNAME=$(echo $DATABASE_URL | sed -E 's/.*:\/\/(.+):.+@.+/\1/')
    export DATABASE_PASSWORD=$(echo $DATABASE_URL | sed -E 's/.*:\/\/.+:(.+)@.+/\1/')

    echo "Parsed DATABASE_HOST: ${DATABASE_HOST}"
    echo "Parsed DATABASE_PORT: ${DATABASE_PORT}"
    echo "Parsed DATABASE_NAME: ${DATABASE_NAME}"
else
    check_var "DATABASE_HOST" || MISSING=$((MISSING+1))
    check_var "DATABASE_PORT" || MISSING=$((MISSING+1))
    check_var "DATABASE_NAME" || MISSING=$((MISSING+1))
    check_var "DATABASE_USERNAME" || MISSING=$((MISSING+1))
    check_var "DATABASE_PASSWORD" || MISSING=$((MISSING+1))
fi

# PORT is optional - Railway sets it automatically
if [ -z "${PORT}" ]; then
    echo "PORT not set by Railway, using default: 1337"
    export PORT=1337
else
    echo "Found: PORT=${PORT}"
fi

echo "=========================================="
if [ $MISSING -gt 0 ]; then
    echo "ERROR: $MISSING required environment variables are missing!"
    echo "Please configure them in Railway Variables tab"
    echo "=========================================="
    exit 1
fi
echo "All required environment variables present"
echo "=========================================="

# Test PostgreSQL connectivity
echo ""
echo "Testing PostgreSQL Connection..."
echo "=========================================="

if [ ! -z "$DATABASE_HOST" ]; then
    echo "Connecting to: ${DATABASE_HOST}:${DATABASE_PORT}"

    # Wait for PostgreSQL to be ready
    RETRIES=30
    until PGPASSWORD=${DATABASE_PASSWORD} psql -h ${DATABASE_HOST} -U ${DATABASE_USERNAME} -d ${DATABASE_NAME} -c '\q' 2>/dev/null || [ $RETRIES -eq 0 ]; do
        echo "Waiting for PostgreSQL to be ready... ($RETRIES attempts remaining)"
        RETRIES=$((RETRIES-1))
        sleep 2
    done

    if [ $RETRIES -eq 0 ]; then
        echo "PostgreSQL connection failed after 60 seconds"
        echo "Continuing anyway - Strapi will retry on startup"
    else
        echo "PostgreSQL connection successful!"
    fi
else
    echo "DATABASE_HOST not set, skipping connection test"
fi

echo "=========================================="

# Run database migrations
echo ""
echo "Running Database Migrations..."
echo "=========================================="

# Strapi will automatically run migrations on startup in production mode
# No manual migration step needed

# Start Strapi
echo ""
echo "Starting Strapi CMS..."
echo "=========================================="
echo "Host: 0.0.0.0"
echo "Port: ${PORT}"
echo "Mode: Production"
echo "=========================================="
echo ""

# Execute Strapi start command
exec node_modules/.bin/strapi start
