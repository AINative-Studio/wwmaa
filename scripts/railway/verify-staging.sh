#!/bin/bash

# ==========================================
# WWMAA - Railway Staging Verification Script
# ==========================================
# Verifies staging environment is properly configured and functional
#
# Prerequisites:
# - Staging environment deployed to Railway
# - Custom domains configured
#
# Usage:
#   ./scripts/railway/verify-staging.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-https://api-staging.wwmaa.com}"
FRONTEND_URL="${FRONTEND_URL:-https://staging.wwmaa.com}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check health endpoint
check_health() {
    log_info "Checking backend health endpoint..."

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/api/health" || echo "000")

    if [ "$HTTP_STATUS" = "200" ]; then
        log_success "Health check passed (HTTP $HTTP_STATUS)"

        # Get health response
        HEALTH_RESPONSE=$(curl -s "${BACKEND_URL}/api/health")
        echo "$HEALTH_RESPONSE" | jq '.' 2>/dev/null || echo "$HEALTH_RESPONSE"
    else
        log_error "Health check failed (HTTP $HTTP_STATUS)"
        return 1
    fi
}

# Check SSL certificate
check_ssl() {
    log_info "Checking SSL certificate..."

    SSL_CHECK=$(curl -vI "${BACKEND_URL}" 2>&1 | grep "SSL certificate verify ok" || echo "")

    if [ -n "$SSL_CHECK" ]; then
        log_success "SSL certificate valid"
    else
        log_warning "SSL certificate check inconclusive"
    fi
}

# Check CORS headers
check_cors() {
    log_info "Checking CORS configuration..."

    CORS_HEADERS=$(curl -s -I -X OPTIONS "${BACKEND_URL}/api/health" | grep -i "access-control" || echo "")

    if [ -n "$CORS_HEADERS" ]; then
        log_success "CORS headers present"
        echo "$CORS_HEADERS"
    else
        log_warning "CORS headers not detected"
    fi
}

# Check security headers
check_security_headers() {
    log_info "Checking security headers..."

    HEADERS=$(curl -s -I "${BACKEND_URL}/api/health")

    # Check for security headers
    if echo "$HEADERS" | grep -i "x-frame-options" > /dev/null; then
        log_success "X-Frame-Options header present"
    else
        log_warning "X-Frame-Options header missing"
    fi

    if echo "$HEADERS" | grep -i "x-content-type-options" > /dev/null; then
        log_success "X-Content-Type-Options header present"
    else
        log_warning "X-Content-Type-Options header missing"
    fi

    if echo "$HEADERS" | grep -i "strict-transport-security" > /dev/null; then
        log_success "Strict-Transport-Security header present"
    else
        log_warning "Strict-Transport-Security header missing"
    fi
}

# Check metrics endpoint
check_metrics() {
    log_info "Checking Prometheus metrics endpoint..."

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/metrics" || echo "000")

    if [ "$HTTP_STATUS" = "200" ]; then
        log_success "Metrics endpoint accessible (HTTP $HTTP_STATUS)"
    else
        log_warning "Metrics endpoint not accessible (HTTP $HTTP_STATUS)"
    fi
}

# Check authentication endpoint
check_auth() {
    log_info "Checking authentication endpoint..."

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BACKEND_URL}/api/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"invalid"}' || echo "000")

    # Expect 401 for invalid credentials
    if [ "$HTTP_STATUS" = "401" ] || [ "$HTTP_STATUS" = "422" ]; then
        log_success "Authentication endpoint responding correctly (HTTP $HTTP_STATUS)"
    else
        log_warning "Authentication endpoint returned unexpected status (HTTP $HTTP_STATUS)"
    fi
}

# Check frontend
check_frontend() {
    log_info "Checking frontend deployment..."

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" || echo "000")

    if [ "$HTTP_STATUS" = "200" ]; then
        log_success "Frontend accessible (HTTP $HTTP_STATUS)"
    else
        log_error "Frontend not accessible (HTTP $HTTP_STATUS)"
        return 1
    fi
}

# Check DNS resolution
check_dns() {
    log_info "Checking DNS resolution..."

    # Check backend domain
    if host api-staging.wwmaa.com > /dev/null 2>&1; then
        log_success "Backend domain resolves: api-staging.wwmaa.com"
    else
        log_warning "Backend domain does not resolve: api-staging.wwmaa.com"
    fi

    # Check frontend domain
    if host staging.wwmaa.com > /dev/null 2>&1; then
        log_success "Frontend domain resolves: staging.wwmaa.com"
    else
        log_warning "Frontend domain does not resolve: staging.wwmaa.com"
    fi
}

# Check Railway status
check_railway_status() {
    log_info "Checking Railway deployment status..."

    if command -v railway &> /dev/null; then
        railway status --environment staging || log_warning "Could not get Railway status"
    else
        log_warning "Railway CLI not installed, skipping status check"
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "WWMAA Staging Environment Verification"
    echo "=========================================="
    echo ""
    echo "Backend URL:  $BACKEND_URL"
    echo "Frontend URL: $FRONTEND_URL"
    echo ""
    echo "=========================================="
    echo ""

    # Track failures
    FAILURES=0

    # Run checks
    check_dns || ((FAILURES++))
    echo ""

    check_health || ((FAILURES++))
    echo ""

    check_ssl || ((FAILURES++))
    echo ""

    check_cors || ((FAILURES++))
    echo ""

    check_security_headers || ((FAILURES++))
    echo ""

    check_metrics || ((FAILURES++))
    echo ""

    check_auth || ((FAILURES++))
    echo ""

    check_frontend || ((FAILURES++))
    echo ""

    check_railway_status || ((FAILURES++))
    echo ""

    # Summary
    echo "=========================================="
    echo "Verification Complete"
    echo "=========================================="
    echo ""

    if [ $FAILURES -eq 0 ]; then
        log_success "All checks passed! Staging environment is operational."
        echo ""
        log_info "Next steps:"
        echo "  1. Run seed data: python scripts/seed-staging-data.py"
        echo "  2. Test user registration and login"
        echo "  3. Test event RSVP functionality"
        echo "  4. Test semantic search"
        echo "  5. Test payment processing (Stripe test mode)"
        echo ""
        exit 0
    else
        log_error "$FAILURES check(s) failed. Please review and fix issues."
        echo ""
        log_info "Troubleshooting:"
        echo "  1. Check Railway logs: railway logs --environment staging"
        echo "  2. Verify environment variables in Railway dashboard"
        echo "  3. Check DNS configuration for custom domains"
        echo "  4. Verify Redis service is running"
        echo "  5. Check application logs for errors"
        echo ""
        exit 1
    fi
}

# Run main function
main "$@"
