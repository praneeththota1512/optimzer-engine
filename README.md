# Antigravity — Optimization Engine + Agent

**Purpose**: Local Optimization Engine + Agent for Port+Rail scheduling with privacy-safe, local LLM integration.

## Features

- **Greedy Baseline**: Fast, deterministic scheduler as fallback
- **MILP Solver**: OR-Tools CP-SAT for optimal small instances
- **LNS Hybrid**: Large Neighborhood Search for scalability
- **Local LLM Agent**: Ollama-powered optimization suggestions
- **Validator**: Hard constraint checking
- **Simulator**: Monte Carlo robustness testing
- **Full Privacy**: All processing runs locally, no external API calls

## Quick Start

### 1. Setup Environment

```bash
# On Linux/Mac
bash run.sh

# On Windows (PowerShell)
.\run.ps1
```

### 2. Install Ollama (if not already installed)

```bash
# Download from https://ollama.ai or use:
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model (Mistral recommended)
ollama pull mistral

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### 3. Run the Optimizer

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Run greedy baseline
python src/engine/greedy_scheduler.py --inputs inputs/ --output outputs/ --config config.yaml

# Validate the schedule
python src/engine/validator.py --schedule outputs/schedule.json --inputs inputs/

# Run MILP (small instances)
python src/engine/milp_model.py --inputs inputs/ --output outputs/ --config config.yaml

# Run LNS hybrid
python src/engine/lns_manager.py --inputs inputs/ --output outputs/ --config config.yaml

# Run agent with mock LLM (for testing)
python src/agent/controller.py --mode=mock --inputs inputs/ --output outputs/ --config config.yaml

# Run agent with Ollama
python src/agent/controller.py --inputs inputs/ --output outputs/ --config config.yaml
```

### 4. Run Tests

```bash
pytest tests/ -v
```

## Project Structure

```
opt_agent_engine/
├── config.yaml              # Main configuration
├── requirements.txt         # Python dependencies
├── run.sh / run.ps1        # Setup scripts
├── inputs/                  # Sample CSV data
├── outputs/                 # Generated schedules and logs
├── src/
│   ├── engine/             # Core optimization logic
│   │   ├── data_load.py
│   │   ├── precompute.py
│   │   ├── greedy_scheduler.py
│   │   ├── milp_model.py
│   │   ├── lns_manager.py
│   │   ├── simulator.py
│   │   └── validator.py
│   ├── agent/              # LLM agent integration
│   │   ├── llm_client.py
│   │   ├── prompt_templates.py
│   │   ├── controller.py
│   │   └── schemas.py
│   └── utils/              # Helper utilities
├── tests/                   # Unit and integration tests
└── docs/                    # Documentation
```

## Configuration

Edit `config.yaml` to customize:

- **Time horizon**: `horizon_hours`, `time_slot_minutes`
- **Solver budgets**: `solver_time_budget_seconds`
- **Objective weights**: `cost`, `delay`, `delivery_violation`
- **Agent settings**: `model_name`, `temperature`, `max_candidates_per_iteration`

## Outputs

All runs produce:

- `outputs/schedule.json` — Final schedule
- `outputs/metrics.json` — Objective values and KPIs
- `outputs/debug_trace.csv` — Detailed execution log
- `outputs/fallback_flag.txt` — Indicates if fallback was used
- `outputs/run_meta.json` — Run metadata

## Agent Design

The agent uses a local LLM (via Ollama) to propose schedule improvements:

1. **State Snapshot**: Current schedule + metrics
2. **Prompt Generation**: Structured prompt with JSON schema
3. **LLM Proposal**: Agent suggests moves (swap, delay, reassign)
4. **Validation**: Check hard constraints
5. **Scoring**: Evaluate objective improvement
6. **Accept/Reject**: Apply best move and iterate

See [docs/agent_design.md](docs/agent_design.md) for details.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_greedy_vs_trivial.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Acceptance Criteria

✅ Greedy baseline produces valid schedule with no hard constraint violations  
✅ MILP finds better solution than greedy on small instances  
✅ Agent (mock mode) produces valid proposals and accepts improvements  
✅ All unit tests pass  
✅ Runs fully locally with no external API calls  

## Documentation

- [Quickstart Guide](docs/quickstart.md)
- [Model Description](docs/model_description.md)
- [Agent Design](docs/agent_design.md)

## License

MIT
