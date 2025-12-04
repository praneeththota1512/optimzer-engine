#!/bin/bash

# Antigravity Optimization Engine - Run Script

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Antigravity Optimization Engine ===${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r requirements.txt

# Create outputs directory if it doesn't exist
mkdir -p outputs

echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "To run the optimizer:"
echo "  1. Greedy baseline:    python src/engine/greedy_scheduler.py"
echo "  2. MILP solver:        python src/engine/milp_model.py"
echo "  3. LNS hybrid:         python src/engine/lns_manager.py"
echo "  4. Agent (mock):       python src/agent/controller.py --mode=mock"
echo "  5. Agent (Ollama):     python src/agent/controller.py"
echo ""
echo "To run tests:"
echo "  pytest tests/"
echo ""
echo -e "${BLUE}=== Ollama Setup Instructions ===${NC}"
echo "1. Install Ollama from https://ollama.ai"
echo "2. Pull a model: ollama pull mistral"
echo "3. Verify it's running: curl http://localhost:11434/api/tags"
echo ""
