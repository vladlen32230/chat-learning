#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Installing formatting dependencies...${NC}"
pip install black isort

echo -e "\n${YELLOW}=== FORMATTING BACKEND ===${NC}"
cd backend

echo -e "\n${YELLOW}Formatting backend code with black...${NC}"
black .
echo -e "${GREEN}✓ Backend code formatted${NC}"

echo -e "\n${YELLOW}Sorting backend imports with isort...${NC}"
isort .
echo -e "${GREEN}✓ Backend imports sorted${NC}"

cd ..

echo -e "\n${YELLOW}=== FORMATTING FRONTEND ===${NC}"
cd frontend

echo -e "\n${YELLOW}Formatting frontend code with black...${NC}"
black .
echo -e "${GREEN}✓ Frontend code formatted${NC}"

echo -e "\n${YELLOW}Sorting frontend imports with isort...${NC}"
isort .
echo -e "${GREEN}✓ Frontend imports sorted${NC}"

cd ..

echo -e "\n${GREEN}🎉 All code has been formatted!${NC}"
