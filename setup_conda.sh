#!/bin/bash
# Setup script to create a conda environment for the project

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up conda environment for macular-simulation project...${NC}"

# Check if conda is available
if ! command -v conda &>/dev/null; then
    echo -e "${RED}Error: conda not found. Please install Anaconda or Miniconda before continuing.${NC}"
    echo -e "${YELLOW}Download from: https://docs.conda.io/en/latest/miniconda.html${NC}"
    exit 1
fi

# Create a new conda environment from environment.yaml
echo -e "${GREEN}Creating conda environment from environment.yaml...${NC}"
conda env create -f environment.yaml
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create conda environment. Please check your conda installation and environment.yaml file.${NC}"
    exit 1
fi

echo -e "${GREEN}Conda environment 'macular-simulation' created successfully!${NC}"

# Additional pip installs for streamlit and other dependencies
echo -e "${GREEN}Installing additional dependencies with pip...${NC}"
echo -e "${YELLOW}Activating conda environment...${NC}"
eval "$(conda shell.bash hook)"
conda activate macular-simulation

# Install project dependencies
echo -e "${GREEN}Installing remaining project dependencies...${NC}"
pip install -r requirements_minimal.txt

echo -e "${GREEN}Environment setup complete!${NC}"
echo ""
echo -e "${YELLOW}To activate the environment, run:${NC}"
echo -e "    ${GREEN}conda activate macular-simulation${NC}"
echo ""
echo -e "${YELLOW}To run the streamgraph test:${NC}"
echo -e "    ${GREEN}python run_streamgraph_phase_test.py --patients 50 --years 3 --plot${NC}"
echo ""
echo -e "${YELLOW}To deactivate the environment when done:${NC}"
echo -e "    ${GREEN}conda deactivate${NC}"

# Keep environment active
echo -e "${GREEN}Environment is now active.${NC}"