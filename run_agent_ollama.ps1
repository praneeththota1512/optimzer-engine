# Run Agent with Ollama
# PowerShell script to run the agent optimizer

Write-Host "=== Antigravity Agent Optimizer with Ollama ===" -ForegroundColor Blue

# Set environment variable for Python path
$env:PYTHONPATH = "$PSScriptRoot"

# Run the agent
Write-Host "`nRunning agent with Mistral 7B..." -ForegroundColor Green

& "$PSScriptRoot\.venv\Scripts\python.exe" -c @"
import sys
import os
os.chdir('$PSScriptRoot')
sys.path.insert(0, '$PSScriptRoot')

# Import all required modules
exec(open('src/engine/data_load.py').read(), globals())
exec(open('src/engine/precompute.py').read(), globals())  
exec(open('src/engine/greedy_scheduler.py').read(), globals())
exec(open('src/engine/validator.py').read(), globals())
exec(open('src/agent/llm_client.py').read(), globals())
exec(open('src/agent/prompt_templates.py').read(), globals())
exec(open('src/agent/schemas.py').read(), globals())

# Import and run controller
import argparse
sys.argv = ['controller.py', '--inputs', 'inputs/', '--output', 'outputs/', '--config', 'config.yaml']
exec(open('src/agent/controller.py').read(), globals())
"@

Write-Host "`n=== Agent run complete ===" -ForegroundColor Blue
