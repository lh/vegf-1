#!/bin/bash
# Setup script to create a virtual environment for the project

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up virtual environment for macular-simulation project...${NC}"

# Check if Python 3.12 is available
if command -v python3.12 &>/dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1-2)
    if [ "$PYTHON_VERSION" = "3.12" ] || [ "$PYTHON_VERSION" = "3.11" ] || [ "$PYTHON_VERSION" = "3.10" ]; then
        PYTHON_CMD="python3"
    else
        echo -e "${YELLOW}Warning: Python version $PYTHON_VERSION detected.${NC}"
        echo -e "${YELLOW}This project was developed with Python 3.12.${NC}"
        echo -e "${YELLOW}Continuing with python3, but you may encounter issues.${NC}"
        PYTHON_CMD="python3"
    fi
else
    echo -e "${RED}Error: Python 3.x not found. Please install Python 3.10+ before continuing.${NC}"
    exit 1
fi

echo -e "${GREEN}Using $PYTHON_CMD for environment setup${NC}"

# Create a virtual environment
VENV_DIR="venv"
$PYTHON_CMD -m venv $VENV_DIR
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create virtual environment. Please check your Python installation.${NC}"
    exit 1
fi

echo -e "${GREEN}Virtual environment created at $VENV_DIR${NC}"

# Activate virtual environment
source $VENV_DIR/bin/activate

# Upgrade pip
echo -e "${GREEN}Upgrading pip...${NC}"
pip install --upgrade pip

# Install project dependencies
echo -e "${GREEN}Installing project dependencies...${NC}"
pip install -r requirements_minimal.txt

# Install development dependencies if needed
if [ "$1" = "--with-dev" ]; then
    echo -e "${GREEN}Installing development dependencies...${NC}"
    pip install pytest black mypy pylint pydantic
fi

echo -e "${GREEN}Environment setup complete!${NC}"
echo ""
echo -e "${YELLOW}To activate the environment, run:${NC}"
echo -e "    ${GREEN}source $VENV_DIR/bin/activate${NC}"
echo ""
echo -e "${YELLOW}To run the streamgraph test:${NC}"
echo -e "    ${GREEN}python run_streamgraph_phase_test.py --patients 50 --years 3 --plot${NC}"
echo ""
echo -e "${YELLOW}To deactivate the environment when done:${NC}"
echo -e "    ${GREEN}deactivate${NC}"

# Keep environment active
echo -e "${GREEN}Environment is now active.${NC}"