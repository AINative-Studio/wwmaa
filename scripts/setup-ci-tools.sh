#!/bin/bash
# Setup script for CI/CD tools
# This script installs and configures local development tools to match CI environment

set -e  # Exit on error

echo "========================================"
echo "WWMAA CI/CD Tools Setup"
echo "========================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the project root
if [ ! -f "package.json" ] || [ ! -f "backend/requirements.txt" ]; then
    echo -e "${RED}Error: This script must be run from the project root directory${NC}"
    exit 1
fi

echo "Step 1: Installing pre-commit hooks..."
echo "----------------------------------------"

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo -e "${YELLOW}pre-commit not found. Installing...${NC}"
    pip install pre-commit
else
    echo -e "${GREEN}✓ pre-commit already installed${NC}"
fi

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg

echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
echo ""

echo "Step 2: Validating Python environment..."
echo "----------------------------------------"

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [ "$PYTHON_VERSION" != "$REQUIRED_VERSION" ]; then
    echo -e "${YELLOW}Warning: Python $REQUIRED_VERSION is recommended (you have $PYTHON_VERSION)${NC}"
else
    echo -e "${GREEN}✓ Python $REQUIRED_VERSION detected${NC}"
fi

# Check if backend dependencies are installed
echo "Checking Python dependencies..."
if python3 -c "import pytest, black, flake8, mypy, isort" 2>/dev/null; then
    echo -e "${GREEN}✓ Python linting tools installed${NC}"
else
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -r backend/requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
fi

echo ""

echo "Step 3: Validating Node.js environment..."
echo "----------------------------------------"

# Check Node version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
REQUIRED_NODE_VERSION="18"

if [ "$NODE_VERSION" -lt "$REQUIRED_NODE_VERSION" ]; then
    echo -e "${YELLOW}Warning: Node.js $REQUIRED_NODE_VERSION+ is recommended (you have $NODE_VERSION)${NC}"
else
    echo -e "${GREEN}✓ Node.js $NODE_VERSION detected${NC}"
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓ Node.js dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Node.js dependencies already installed${NC}"
fi

echo ""

echo "Step 4: Running initial checks..."
echo "----------------------------------------"

echo "Running pre-commit on all files (this may take a while)..."
if pre-commit run --all-files; then
    echo -e "${GREEN}✓ All pre-commit checks passed${NC}"
else
    echo -e "${YELLOW}⚠ Some pre-commit checks failed${NC}"
    echo -e "${YELLOW}  This is normal for the first run. Files have been auto-fixed.${NC}"
    echo -e "${YELLOW}  Run 'git add .' and commit the changes.${NC}"
fi

echo ""

echo "Step 5: Validating configuration files..."
echo "----------------------------------------"

# Validate YAML files
echo "Validating workflow files..."
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo -e "${GREEN}✓ ci.yml valid${NC}"
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/frontend-ci.yml'))" && echo -e "${GREEN}✓ frontend-ci.yml valid${NC}"
python3 -c "import yaml; yaml.safe_load(open('.codecov.yml'))" && echo -e "${GREEN}✓ .codecov.yml valid${NC}"
python3 -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml'))" && echo -e "${GREEN}✓ .pre-commit-config.yaml valid${NC}"

echo ""

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Run tests locally:"
echo "     Backend:  cd backend && pytest tests/ -v"
echo "     Frontend: npm test"
echo ""
echo "  2. Run linting:"
echo "     Backend:  flake8 backend/"
echo "     Frontend: npm run lint"
echo ""
echo "  3. Check pre-commit hooks:"
echo "     pre-commit run --all-files"
echo ""
echo "  4. Read the documentation:"
echo "     docs/development/ci-cd-guide.md"
echo "     docs/development/branch-protection.md"
echo "     docs/development/ci-notifications.md"
echo ""
echo "For more information, see: docs/development/ci-cd-guide.md"
echo ""
