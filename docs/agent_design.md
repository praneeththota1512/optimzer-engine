# Agent Design Documentation

## Overview

The Antigravity optimization engine includes an AI agent that uses a local LLM to propose schedule improvements. The agent operates in a loop, generating candidate modifications, validating them, and accepting improvements.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent Controller                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 1. Load current schedule (greedy baseline)           │  │
│  │ 2. Build state snapshot                              │  │
│  │ 3. Generate prompt with JSON schema                  │  │
│  │ 4. Call local LLM (Ollama/llama.cpp/vLLM)           │  │
│  │ 5. Parse proposals                                    │  │
│  │ 6. Apply & validate each candidate                   │  │
│  │ 7. Score candidates                                   │  │
│  │ 8. Accept best improvement                           │  │
│  │ 9. Repeat until time budget or no improvement        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. LLM Client (`llm_client.py`)

Supports multiple local LLM backends:

- **Ollama** (recommended): Easy setup, good performance
- **llama.cpp**: CPU-optimized, GGUF format
- **vLLM**: GPU-accelerated, best for production

**Key features:**
- Structured JSON parsing with retry logic
- Temperature control for deterministic outputs
- Mock client for testing

### 2. Prompt Templates (`prompt_templates.py`)

Generates structured prompts with:
- Current state snapshot (ships, berths, schedule, metrics)
- Objective function with weights
- Available move types
- JSON output schema
- Examples

**Prompt structure:**
```
You are an optimization assistant...

CURRENT STATE:
{JSON snapshot}

OBJECTIVE:
Minimize: cost + 0.5*delay + 2.0*delivery_violation

AVAILABLE MOVE TYPES:
1. swap_berth
2. delay_ship
3. reassign_berth
4. advance_ship

OUTPUT FORMAT (JSON only):
{schema}
```

### 3. Schemas (`schemas.py`)

Defines and validates move types:

**Move Types:**

1. **swap_berth**: Exchange berth assignments
   ```json
   {"type": "swap_berth", "ship_a": "S001", "ship_b": "S002"}
   ```

2. **delay_ship**: Postpone ship start time
   ```json
   {"type": "delay_ship", "ship": "S001", "delay_minutes": 60}
   ```

3. **reassign_berth**: Move ship to different berth
   ```json
   {"type": "reassign_berth", "ship": "S001", "new_berth": "B002"}
   ```

4. **advance_ship**: Start ship earlier
   ```json
   {"type": "advance_ship", "ship": "S001", "advance_minutes": 30}
   ```

**Candidate Structure:**
```json
{
  "id": "C1",
  "moves": [...],
  "rationale": "Brief explanation",
  "expected_delta_estimate": -500.0
}
```

### 4. Controller (`controller.py`)

Main agent loop:

1. **Initialization**: Load greedy baseline
2. **Iteration loop**:
   - Build state snapshot
   - Generate prompt
   - Call LLM
   - Parse candidates
   - For each candidate:
     - Apply moves
     - Validate constraints
     - Compute objective
   - Accept best improvement
3. **Termination**: Time budget or no improvement

## Configuration

In `config.yaml`:

```yaml
agent:
  enable: true
  backend: "ollama"
  model_name: "mistral"
  ollama_url: "http://localhost:11434"
  agent_time_budget_seconds: 60
  max_candidates_per_iteration: 3
  temperature: 0.0
  max_tokens: 512
  max_retries: 2
```

## Usage

### With Ollama (Recommended)

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull model
ollama pull mistral

# 3. Run agent
python src/agent/controller.py --inputs inputs/ --output outputs/ --config config.yaml
```

### With Mock LLM (Testing)

```bash
python src/agent/controller.py --mode=mock
```

## Performance

**Typical iteration times:**
- Ollama (CPU, Mistral-7B): 2-5 seconds per iteration
- vLLM (GPU, Mistral-7B): 0.5-1 second per iteration
- Mock: < 0.1 seconds per iteration

**Expected improvements:**
- 5-15% objective reduction vs greedy baseline
- Depends on problem complexity and LLM quality

## Debugging

Agent logs are saved to `outputs/agent_log.json`:

```json
[
  {
    "iteration": 1,
    "candidate_id": "C1",
    "status": "accepted",
    "objective": 14500.0,
    "improvement": 500.0,
    "llm_time": 2.3
  }
]
```

**Common issues:**

1. **JSON parse errors**: LLM returns invalid JSON
   - Solution: Increase `max_retries`, use temperature=0.0

2. **Validation failures**: Proposed moves violate constraints
   - Solution: Improve prompt with constraint examples

3. **No improvements**: LLM can't find better solutions
   - Solution: Increase `max_candidates_per_iteration`, try different model

## Model Recommendations

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| Mistral-7B | 7B | Fast | Good | Development, testing |
| Llama-2-13B | 13B | Medium | Better | Production |
| CodeLlama-34B | 34B | Slow | Best | Complex problems |

## Future Enhancements

1. **Multi-step reasoning**: Chain-of-thought prompting
2. **Learning from history**: Fine-tune on successful moves
3. **Hybrid search**: Combine LLM with local search
4. **Parallel candidates**: Evaluate multiple proposals concurrently
5. **Adaptive prompts**: Adjust based on success rate

## References

- [Ollama Documentation](https://ollama.ai/docs)
- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [vLLM Documentation](https://docs.vllm.ai/)
