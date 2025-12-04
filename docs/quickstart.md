# Quickstart Guide

## Prerequisites

- Python 3.10 or higher
- Ollama (for local LLM)
- 8GB+ RAM recommended

## Installation

### 1. Setup Python Environment

**Windows (PowerShell):**
```powershell
.\run.ps1
```

**Linux/Mac:**
```bash
bash run.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Create output directories

### 2. Install Ollama

**Linux/Mac:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from [ollama.ai](https://ollama.ai)

### 3. Pull a Model

```bash
ollama pull mistral
```

Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

## Running the Optimizer

### Activate Environment

**Windows:**
```powershell
.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### Run Greedy Baseline

```bash
python src/engine/greedy_scheduler.py --inputs inputs/ --output outputs/ --config config.yaml
```

**Expected output:**
```
Loading data...
Precomputing...
Running greedy scheduler...
Completed in 0.45s
Assigned: 8 ships
Unassigned: 0 ships
Objective: 15234.56
```

### Validate Schedule

```bash
python src/engine/validator.py --schedule outputs/schedule.json --inputs inputs/
```

**Expected output:**
```
✓ Schedule is VALID - no hard constraint violations
```

### Run MILP Solver

```bash
python src/engine/milp_model.py --inputs inputs/ --output outputs/ --config config.yaml
```

### Run Agent with Ollama

```bash
python src/agent/controller.py --inputs inputs/ --output outputs/ --config config.yaml
```

**Expected output:**
```
Loading data...
Precomputing...
Computing initial greedy solution...
Initial objective: 15234.56

--- Agent Iteration 1 ---
Calling LLM...
LLM responded in 2.3s
Received 2 valid candidates
✓ Accepting candidate C1 (improvement: 523.45)

✓ Agent completed in 8.5s after 3 iterations
Final objective: 14711.11
```

### Run Agent with Mock LLM (Testing)

```bash
python src/agent/controller.py --mode=mock
```

## Understanding Outputs

All runs produce files in `outputs/`:

### `schedule.json`
```json
[
  {
    "ship_id": "S001",
    "berth_id": "B001",
    "start_slot": 12,
    "end_slot": 28,
    "start_time_iso": "2025-12-05T12:00:00",
    "end_time_iso": "2025-12-05T20:00:00"
  }
]
```

### `metrics.json`
```json
{
  "objective": 15234.56,
  "total_cost": 12500.00,
  "total_delay_hours": 4.5,
  "num_assigned": 8,
  "num_unassigned": 0
}
```

### `debug_trace.csv`
Detailed execution log with timestamps and actions.

### `agent_log.json` (agent runs only)
```json
[
  {
    "iteration": 1,
    "candidate_id": "C1",
    "status": "accepted",
    "objective": 14711.11,
    "improvement": 523.45,
    "llm_time": 2.3
  }
]
```

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/test_greedy_vs_trivial.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## Configuration

Edit `config.yaml` to customize:

```yaml
# Time discretization
horizon_hours: 48
time_slot_minutes: 30

# Solver budgets
solver_time_budget_seconds: 600

# Objective weights
objective_weights:
  cost: 1.0
  delay: 0.5
  delivery_violation: 2.0

# Agent settings
agent:
  enable: true
  backend: "ollama"
  model_name: "mistral"
  temperature: 0.0
  max_candidates_per_iteration: 3
```

## Troubleshooting

### Ollama Connection Failed

**Error:** `Ollama API call failed: Connection refused`

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama (if not running)
ollama serve
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'ortools'`

**Solution:**
```bash
pip install -r requirements.txt
```

### No Improvements from Agent

**Possible causes:**
1. Greedy baseline is already optimal
2. LLM temperature too high (use 0.0)
3. Time budget too short

**Solution:**
- Increase `agent_time_budget_seconds`
- Try different model: `ollama pull llama2`
- Check `agent_log.json` for details

## Next Steps

1. **Customize inputs**: Edit CSV files in `inputs/`
2. **Tune configuration**: Adjust weights and budgets in `config.yaml`
3. **Experiment with models**: Try different Ollama models
4. **Scale up**: Generate larger datasets with `tests/generate_synthetic.py`
5. **Read documentation**: See `docs/` for detailed guides

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python src/engine/greedy_scheduler.py` | Run greedy baseline |
| `python src/engine/validator.py --schedule outputs/schedule.json` | Validate schedule |
| `python src/engine/milp_model.py` | Run MILP solver |
| `python src/agent/controller.py` | Run agent with Ollama |
| `python src/agent/controller.py --mode=mock` | Run agent with mock LLM |
| `pytest tests/ -v` | Run all tests |

## Support

For issues or questions:
1. Check `docs/agent_design.md` for agent details
2. Check `docs/model_description.md` for optimization model
3. Review test files in `tests/` for examples
