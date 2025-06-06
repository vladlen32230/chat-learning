#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Installing linting dependencies...${NC}"
pip install flake8 black isort mypy

echo -e "\n${YELLOW}=== BACKEND LINTING ===${NC}"

echo -e "\n${YELLOW}Checking backend with flake8...${NC}"
cd backend
if flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics; then
    echo -e "${GREEN}✓ No critical flake8 errors found${NC}"
else
    echo -e "${RED}✗ Critical flake8 errors found${NC}"
    exit 1
fi

if flake8 . --count --max-complexity=10 --max-line-length=88 --statistics; then
    echo -e "${GREEN}✓ No flake8 style issues found${NC}"
else
    echo -e "${RED}✗ Flake8 style issues found${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Checking backend code formatting with black...${NC}"
if black --check --diff .; then
    echo -e "${GREEN}✓ Backend code is properly formatted${NC}"
else
    echo -e "${RED}✗ Backend code formatting issues found. Run 'black .' to fix${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Checking backend import sorting with isort...${NC}"
if isort --check-only --diff .; then
    echo -e "${GREEN}✓ Backend imports are properly sorted${NC}"
else
    echo -e "${RED}✗ Backend import sorting issues found. Run 'isort .' to fix${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Type checking backend with mypy...${NC}"
pip install -r requirements.txt
if mypy . --ignore-missing-imports --explicit-package-bases --exclude '.*\.venv.*' --exclude '.*venv.*' --exclude '.*__pycache__.*'; then
    echo -e "${GREEN}✓ No mypy type errors found in backend${NC}"
else
    echo -e "${RED}✗ Mypy type errors found in backend${NC}"
    exit 1
fi

cd ..

echo -e "\n${YELLOW}=== FRONTEND LINTING ===${NC}"

echo -e "\n${YELLOW}Checking frontend with flake8...${NC}"
cd frontend
if flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics; then
    echo -e "${GREEN}✓ No critical flake8 errors found${NC}"
else
    echo -e "${RED}✗ Critical flake8 errors found${NC}"
    exit 1
fi

if flake8 . --count --max-complexity=10 --max-line-length=88 --statistics; then
    echo -e "${GREEN}✓ No flake8 style issues found${NC}"
else
    echo -e "${RED}✗ Flake8 style issues found${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Checking frontend code formatting with black...${NC}"
if black --check --diff .; then
    echo -e "${GREEN}✓ Frontend code is properly formatted${NC}"
else
    echo -e "${RED}✗ Frontend code formatting issues found. Run 'black .' to fix${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Checking frontend import sorting with isort...${NC}"
if isort --check-only --diff .; then
    echo -e "${GREEN}✓ Frontend imports are properly sorted${NC}"
else
    echo -e "${RED}✗ Frontend import sorting issues found. Run 'isort .' to fix${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Type checking frontend with mypy...${NC}"
pip install -r requirements.txt
if mypy . --ignore-missing-imports --explicit-package-bases --exclude '.*\.venv.*' --exclude '.*venv.*' --exclude '.*__pycache__.*'; then
    echo -e "${GREEN}✓ No mypy type errors found in frontend${NC}"
else
    echo -e "${RED}✗ Mypy type errors found in frontend${NC}"
    exit 1
fi

cd ..

echo -e "\n${GREEN}🎉 All linting checks passed!${NC}"
