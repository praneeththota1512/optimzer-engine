"""
Agent Runner - Simplified version that works with imports
"""
import os
import sys

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add to path
sys.path.insert(0, os.getcwd())

# Set up arguments
sys.argv = ['agent', '--inputs', 'inputs/', '--output', 'outputs/', '--config', 'config.yaml']

# Import everything we need
import pandas as pd
import json
import argparse
import copy
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import yaml
import numpy as np
import requests
from pydantic import BaseModel, Field, validator

# Load and execute each module in order
print("Loading modules...")

# Data load
with open('src/engine/data_load.py', 'r', encoding='utf-8') as f:
    code = f.read()
    # Remove if __name__ == "__main__" block
    code = code.split('if __name__ == "__main__":')[0]
    exec(code, globals())

# Precompute
with open('src/engine/precompute.py', 'r', encoding='utf-8') as f:
    code = f.read()
    code = code.split('if __name__ == "__main__":')[0]
    exec(code, globals())

# Greedy scheduler
with open('src/engine/greedy_scheduler.py', 'r', encoding='utf-8') as f:
    code = f.read()
    code = code.split('def main():')[0]  # Remove main function
    exec(code, globals())

# Validator
with open('src/engine/validator.py', 'r', encoding='utf-8') as f:
    code = f.read()
    code = code.split('def main():')[0]
    exec(code, globals())

# LLM client
with open('src/agent/llm_client.py', 'r', encoding='utf-8') as f:
    code = f.read()
    code = code.split('if __name__ == "__main__":')[0]
    exec(code, globals())

# Schemas
with open('src/agent/schemas.py', 'r', encoding='utf-8') as f:
    code = f.read()
    code = code.split('if __name__ == "__main__":')[0]
    exec(code, globals())

# Prompt templates
with open('src/agent/prompt_templates.py', 'r', encoding='utf-8') as f:
    code = f.read()
    code = code.split('if __name__ == "__main__":')[0]
    exec(code, globals())

# Controller - get the main function
with open('src/agent/controller.py', 'r', encoding='utf-8') as f:
    code = f.read()
    # Remove imports at the top
    lines = code.split('\n')
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('def ') or line.startswith('class '):
            start_idx = i
            break
    code = '\n'.join(lines[start_idx:])
    exec(code, globals())

# Run main
print("\nStarting agent optimizer...")
main()
