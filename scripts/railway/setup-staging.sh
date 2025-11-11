#!/bin/bash

# ==========================================
# WWMAA - Railway Staging Setup Script
# ==========================================
# Sets up Railway staging environment with all required services
#
# Prerequisites:
# - Railway CLI installed: npm i -g @railway/cli
# - Logged in to Railway: railway login
#
# Usage:
#   ./scripts/railway/setup-staging.sh

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

# Check Railway CLI
check_railway_cli() {
    log_info "Checking Railway CLI installation..."

    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI not found. Install with: npm i -g @railway/cli"
        exit 1
    fi

    log_success "Railway CLI found"
}

# Create Railway project
create_project() {
    log_info "Creating Railway project: wwmaa-staging..."

    # Create new project
    railway init --name wwmaa-staging

    log_success "Railway project created"
}

# Add Redis service
add_redis_service() {
    log_info "Adding Redis service..."

    # Add Redis from template
    log_info "Please add Redis service manually from Railway dashboard:"
    log_info "  1. Go to https://railway.app/new/template/redis"
    log_info "  2. Select your wwmaa-staging project"
    log_info "  3. Deploy Redis service"
    log_info ""

    read -p "Press Enter once Redis service is added..."

    log_success "Redis service setup complete"
}

# Set environment variables
set_environment_variables() {
    log_info "Setting up environment variables..."

    log_warning "Please configure the following environment variables in Railway dashboard:"
    log_warning "  https://railway.app/project/[your-project-id]/settings"
    log_warning ""
    log_warning "Required variables (see .env.staging.example):"
    log_warning "  - PYTHON_ENV=staging"
    log_warning "  - ZERODB_API_KEY"
    log_warning "  - JWT_SECRET"
    log_warning "  - STRIPE_SECRET_KEY"
    log_warning "  - POSTMARK_API_KEY"
    log_warning "  - OPENAI_API_KEY"
    log_warning "  - And all other required keys from .env.staging.example"
    log_warning ""

    read -p "Press Enter once environment variables are configured..."

    log_success "Environment variables setup acknowledged"
}

# Configure domains
configure_domains() {
    log_info "Configuring custom domains..."

    log_warning "Please configure custom domains in Railway dashboard:"
    log_warning "  Backend:  api-staging.wwmaa.com"
    log_warning "  Frontend: staging.wwmaa.com"
    log_warning ""
    log_warning "Steps:"
    log_warning "  1. Go to your service settings in Railway dashboard"
    log_warning "  2. Click 'Settings' > 'Domains'"
    log_warning "  3. Add custom domain"
    log_warning "  4. Update DNS records as instructed by Railway"
    log_warning ""

    read -p "Press Enter once domains are configured..."

    log_success "Domain configuration acknowledged"
}

# Create staging environment
create_staging_environment() {
    log_info "Creating staging environment..."

    # Create staging environment
    railway environment create staging

    log_success "Staging environment created"
}

# Link project
link_project() {
    log_info "Linking Railway project to local directory..."

    railway link

    log_success "Project linked"
}

# Main execution
main() {
    echo "=========================================="
    echo "WWMAA Railway Staging Setup"
    echo "=========================================="
    echo ""
    echo "This script will guide you through:"
    echo "  1. Creating Railway project"
    echo "  2. Adding required services (Redis)"
    echo "  3. Configuring environment variables"
    echo "  4. Setting up custom domains"
    echo "  5. Creating staging environment"
    echo ""

    read -p "Continue with setup? (y/n) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Setup cancelled by user"
        exit 0
    fi

    # Run setup steps
    check_railway_cli
    create_project
    create_staging_environment
    link_project
    add_redis_service
    set_environment_variables
    configure_domains

    echo ""
    echo "=========================================="
    echo "Railway Staging Setup Complete!"
    echo "=========================================="
    echo ""

    log_info "Next steps:"
    echo "  1. Deploy backend: ./scripts/railway/deploy-staging.sh"
    echo "  2. Verify health check: curl https://api-staging.wwmaa.com/api/health"
    echo "  3. Run seed data: python scripts/seed-staging-data.py"
    echo "  4. Test application end-to-end"
    echo ""

    log_success "Setup complete! Check Railway dashboard for details."
}

# Run main function
main "$@"
