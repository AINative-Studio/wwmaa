#!/bin/bash
# ==========================================
# WWMAA Local Docker Testing Script
# ==========================================
# This script builds and runs the WWMAA app in Docker containers
# Backend runs on port 8080, Redis on 6380

set -e  # Exit on error

echo "🐳 WWMAA Docker Local Test"
echo "=========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please create a .env file with required environment variables"
    exit 1
fi

echo -e "${GREEN}✅ Found .env file${NC}"
echo ""

# Function to display menu
show_menu() {
    echo "What would you like to do?"
    echo "1) Build Docker images"
    echo "2) Start services (backend + redis)"
    echo "3) Stop services"
    echo "4) View logs"
    echo "5) Restart services"
    echo "6) Build and start (recommended for first run)"
    echo "7) Clean up (remove containers and volumes)"
    echo "8) Test backend health"
    echo "9) Exit"
    echo ""
}

# Function to build images
build_images() {
    echo -e "${YELLOW}🔨 Building Docker images...${NC}"
    docker-compose build --no-cache
    echo -e "${GREEN}✅ Build complete${NC}"
    echo ""
}

# Function to start services
start_services() {
    echo -e "${YELLOW}🚀 Starting services...${NC}"
    docker-compose up -d
    echo ""
    echo -e "${GREEN}✅ Services started${NC}"
    echo ""
    echo "📝 Service URLs:"
    echo "   Backend API: http://localhost:8080"
    echo "   Health Check: http://localhost:8080/api/health"
    echo "   API Docs: http://localhost:8080/docs"
    echo "   Redis: localhost:6380"
    echo ""
    echo "Use 'docker-compose logs -f backend' to view logs"
    echo ""
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Services stopped${NC}"
    echo ""
}

# Function to view logs
view_logs() {
    echo -e "${YELLOW}📋 Viewing logs (Ctrl+C to exit)...${NC}"
    echo ""
    docker-compose logs -f
}

# Function to restart services
restart_services() {
    echo -e "${YELLOW}🔄 Restarting services...${NC}"
    docker-compose restart
    echo -e "${GREEN}✅ Services restarted${NC}"
    echo ""
}

# Function to build and start
build_and_start() {
    build_images
    start_services
}

# Function to clean up
cleanup() {
    echo -e "${RED}⚠️  This will remove all containers, networks, and volumes${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🧹 Cleaning up...${NC}"
        docker-compose down -v
        echo -e "${GREEN}✅ Cleanup complete${NC}"
    else
        echo "Cancelled"
    fi
    echo ""
}

# Function to test backend health
test_health() {
    echo -e "${YELLOW}🏥 Testing backend health...${NC}"
    echo ""

    # Check if backend is running
    if ! docker-compose ps | grep -q "wwmaa-backend.*Up"; then
        echo -e "${RED}❌ Backend container is not running${NC}"
        echo "Start services first with option 2 or 6"
        return 1
    fi

    # Wait a bit for service to be ready
    echo "Waiting for backend to be ready..."
    sleep 3

    # Test health endpoint
    echo "Testing http://localhost:8080/api/health"
    if curl -f -s http://localhost:8080/api/health > /dev/null; then
        echo -e "${GREEN}✅ Backend is healthy!${NC}"
        echo ""
        echo "Response:"
        curl -s http://localhost:8080/api/health | python3 -m json.tool
    else
        echo -e "${RED}❌ Backend health check failed${NC}"
        echo ""
        echo "Showing recent logs:"
        docker-compose logs --tail=50 backend
    fi
    echo ""
}

# Main menu loop
while true; do
    show_menu
    read -p "Enter your choice [1-9]: " choice
    echo ""

    case $choice in
        1) build_images ;;
        2) start_services ;;
        3) stop_services ;;
        4) view_logs ;;
        5) restart_services ;;
        6) build_and_start ;;
        7) cleanup ;;
        8) test_health ;;
        9)
            echo "Goodbye! 👋"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            echo ""
            ;;
    esac
done
