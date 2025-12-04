# How to Run the Antigravity Optimizer with Ollama

## Step-by-Step Instructions

### 1. Open PowerShell in the Project Directory

```powershell
cd "C:\Users\prane\optimize engine\antigravity\opt_agent_engine"
```

### 2. Activate the Virtual Environment

```powershell
.venv\Scripts\Activate.ps1
```

You should see `(.venv)` appear in your prompt.

### 3. Run the Greedy Baseline Scheduler

```powershell
python src/engine/greedy_scheduler.py
```

**Expected output:**
```
Loading data...
Precomputing...
Running greedy scheduler...
Completed in 0.01s
Assigned: 8 ships
Unassigned: 0 ships
Objective: 15234.56
✓ Done!
```

This creates:
- `outputs/schedule.json` - Ship-to-berth assignments
- `outputs/metrics.json` - Cost and performance metrics
- `outputs/debug_trace.csv` - Detailed execution log

### 4. Run the Ollama Agent Demo

```powershell
python demo_ollama_agent.py
```

**What this does:**
1. Loads your greedy schedule
2. Builds an optimization prompt
3. Calls Mistral 7B via Ollama
4. Gets AI suggestions for improvements

**Expected output:**
```
======================================================================
ANTIGRAVITY AGENT DEMO - Ollama + Mistral 7B
======================================================================

[1/4] Testing Ollama connection...
✓ Ollama is running
✓ Available models: ['mistral:latest']

[2/4] Loading greedy baseline schedule...
✓ Loaded schedule with 8 ships
✓ Current objective: 15234.56

[3/4] Building optimization prompt for LLM...
✓ Prompt created (846 characters)

[4/4] Calling Mistral 7B via Ollama...
(This may take 10-30 seconds on CPU...)
✓ LLM responded in 12.3s

======================================================================
LLM RESPONSE:
======================================================================
[AI suggestions will appear here]
======================================================================
```

### 5. View the Results

Check the outputs:

```powershell
# View schedule
cat outputs/schedule.json

# View metrics
cat outputs/metrics.json

# View detailed trace
cat outputs/debug_trace.csv
```

## Troubleshooting

### If Ollama isn't running:

1. Open a new PowerShell window
2. Run: `ollama serve`
3. Keep that window open
4. Return to your original window and try again

### If you get import errors:

The full agent has Python 3.14 compatibility issues. Use the demo instead:
```powershell
python demo_ollama_agent.py
```

### If you want the full agent working:

Install Python 3.11 and recreate the environment:
```powershell
py -3.11 -m venv .venv_311
.venv_311\Scripts\Activate.ps1
pip install -r requirements.txt
python src/agent/controller.py
```

## What Each File Does

- **`demo_ollama_agent.py`** - Working demo with Ollama + Mistral 7B
- **`src/engine/greedy_scheduler.py`** - Fast baseline optimizer
- **`src/engine/validator.py`** - Checks schedule constraints
- **`src/agent/controller.py`** - Full agent (has import issues with Python 3.14)
- **`test_ollama.py`** - Quick Ollama connectivity test

## Quick Commands Reference

```powershell
# Activate environment
.venv\Scripts\Activate.ps1

# Run greedy scheduler
python src/engine/greedy_scheduler.py

# Run Ollama demo
python demo_ollama_agent.py

# Test Ollama connection
python test_ollama.py

# Validate a schedule
python src/engine/validator.py --schedule outputs/schedule.json

# Check Ollama models
ollama list
```

That's it! Start with the greedy scheduler, then try the Ollama demo to see AI-powered optimization in action! 🚀
