# Antigravity Optimization Engine - Run Script (PowerShell)

Write-Host "=== Antigravity Optimization Engine ===" -ForegroundColor Blue

# Create virtual environment if it doesn't exist
if (-Not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
.\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Green
pip install -r requirements.txt

# Create outputs directory if it doesn't exist
if (-Not (Test-Path "outputs")) {
    New-Item -ItemType Directory -Path "outputs"
}

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To run the optimizer:"
Write-Host "  1. Greedy baseline:    python src/engine/greedy_scheduler.py"
Write-Host "  2. MILP solver:        python src/engine/milp_model.py"
Write-Host "  3. LNS hybrid:         python src/engine/lns_manager.py"
Write-Host "  4. Agent (mock):       python src/agent/controller.py --mode=mock"
Write-Host "  5. Agent (Ollama):     python src/agent/controller.py"
Write-Host ""
Write-Host "To run tests:"
Write-Host "  pytest tests/"
Write-Host ""
Write-Host "=== Ollama Setup Instructions ===" -ForegroundColor Blue
Write-Host "1. Install Ollama from https://ollama.ai"
Write-Host "2. Pull a model: ollama pull mistral"
Write-Host "3. Verify it's running: curl http://localhost:11434/api/tags"
Write-Host ""
