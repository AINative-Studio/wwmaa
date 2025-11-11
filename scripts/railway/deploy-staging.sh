#!/bin/bash

# ==========================================
# WWMAA - Railway Staging Deployment Script
# ==========================================
# Deploys backend and frontend to Railway staging environment
#
# Prerequisites:
# - Railway CLI installed: npm i -g @railway/cli
# - Logged in to Railway: railway login
# - Railway project linked: railway link
#
# Usage:
#   ./scripts/railway/deploy-staging.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Railway CLI is installed
check_railway_cli() {
    log_info "Checking Railway CLI installation..."

    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI not found. Install with: npm i -g @railway/cli"
        exit 1
    fi

    log_success "Railway CLI found: $(railway --version)"
}

# Check if logged in to Railway
check_railway_auth() {
    log_info "Checking Railway authentication..."

    if ! railway whoami &> /dev/null; then
        log_error "Not logged in to Railway. Run: railway login"
        exit 1
    fi

    log_success "Authenticated to Railway: $(railway whoami)"
}

# Check if project is linked
check_railway_project() {
    log_info "Checking Railway project link..."

    if ! railway status &> /dev/null; then
        log_error "No Railway project linked. Run: railway link"
        exit 1
    fi

    log_success "Railway project linked"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check if .env.staging.example exists
    if [ ! -f .env.staging.example ]; then
        log_warning ".env.staging.example not found"
    fi

    # Check if railway.json exists
    if [ ! -f railway.json ]; then
        log_error "railway.json not found. Cannot deploy without configuration."
        exit 1
    fi

    # Check if backend directory exists
    if [ ! -d backend ]; then
        log_error "backend directory not found"
        exit 1
    fi

    log_success "Pre-deployment checks passed"
}

# Deploy to staging
deploy_staging() {
    log_info "Deploying to Railway staging environment..."

    # Deploy using Railway CLI
    log_info "Starting deployment..."
    railway up --environment staging

    log_success "Deployment initiated"
}

# Get deployment URL
get_deployment_url() {
    log_info "Retrieving deployment URL..."

    # Get the deployment URL from Railway
    DEPLOY_URL=$(railway domain --environment staging 2>/dev/null || echo "URL not available yet")

    if [ "$DEPLOY_URL" != "URL not available yet" ]; then
        log_success "Deployment URL: $DEPLOY_URL"
    else
        log_warning "Deployment URL not available. Check Railway dashboard."
    fi
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Wait a bit for deployment to start
    sleep 5

    # Check deployment status
    log_info "Checking deployment status..."
    railway status --environment staging

    log_success "Deployment verification complete"
}

# Main execution
main() {
    echo "=========================================="
    echo "WWMAA Railway Staging Deployment"
    echo "=========================================="
    echo ""

    # Run checks
    check_railway_cli
    check_railway_auth
    check_railway_project
    pre_deployment_checks

    echo ""
    echo "=========================================="
    echo "Ready to deploy to staging environment"
    echo "=========================================="
    echo ""

    # Confirm deployment
    read -p "Continue with deployment? (y/n) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Deployment cancelled by user"
        exit 0
    fi

    # Deploy
    deploy_staging
    get_deployment_url
    verify_deployment

    echo ""
    echo "=========================================="
    echo "Deployment Complete!"
    echo "=========================================="
    echo ""

    log_info "Next steps:"
    echo "  1. Check deployment logs: railway logs --environment staging"
    echo "  2. Verify health check: curl https://api-staging.wwmaa.com/api/health"
    echo "  3. Run seed data script: python scripts/seed-staging-data.py"
    echo "  4. Test end-to-end user flows"
    echo ""
}

# Run main function
main "$@"
