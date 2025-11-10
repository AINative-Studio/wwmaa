#!/bin/bash
# WWMAA Backend - Test Runner Script
# This script provides convenient commands for running tests

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to backend directory
cd "$(dirname "$0")"

echo -e "${GREEN}WWMAA Backend Test Runner${NC}"
echo "================================"

# Parse command line arguments
COMMAND=${1:-"all"}

case $COMMAND in
  "all")
    echo -e "${YELLOW}Running all tests with coverage...${NC}"
    pytest --cov=backend --cov-report=term-missing --cov-report=html --cov-fail-under=80
    ;;

  "unit")
    echo -e "${YELLOW}Running unit tests only...${NC}"
    pytest -m unit -v
    ;;

  "integration")
    echo -e "${YELLOW}Running integration tests only...${NC}"
    pytest -m integration -v
    ;;

  "fast")
    echo -e "${YELLOW}Running fast tests (no coverage)...${NC}"
    pytest -v
    ;;

  "coverage")
    echo -e "${YELLOW}Generating coverage report...${NC}"
    pytest --cov=backend --cov-report=html
    echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
    ;;

  "watch")
    echo -e "${YELLOW}Running tests in watch mode...${NC}"
    pytest-watch -- --cov=backend
    ;;

  "parallel")
    echo -e "${YELLOW}Running tests in parallel...${NC}"
    pytest -n auto --cov=backend --cov-report=term-missing
    ;;

  "specific")
    if [ -z "$2" ]; then
      echo -e "${RED}Error: Please provide a test file or function${NC}"
      echo "Usage: ./run_tests.sh specific tests/test_unit/test_approval_workflow.py"
      exit 1
    fi
    echo -e "${YELLOW}Running specific test: $2${NC}"
    pytest "$2" -v
    ;;

  "help"|"-h"|"--help")
    echo "Usage: ./run_tests.sh [command]"
    echo ""
    echo "Commands:"
    echo "  all         - Run all tests with coverage (default)"
    echo "  unit        - Run only unit tests"
    echo "  integration - Run only integration tests"
    echo "  fast        - Run all tests without coverage"
    echo "  coverage    - Generate HTML coverage report"
    echo "  parallel    - Run tests in parallel"
    echo "  specific    - Run specific test file (requires path)"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh all"
    echo "  ./run_tests.sh unit"
    echo "  ./run_tests.sh specific tests/test_unit/test_approval_workflow.py"
    ;;

  *)
    echo -e "${RED}Unknown command: $COMMAND${NC}"
    echo "Run './run_tests.sh help' for usage information"
    exit 1
    ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Tests completed successfully${NC}"
else
  echo -e "${RED}✗ Tests failed${NC}"
  exit 1
fi
