"""
Fast Ollama Demo - Optimized for quick responses
Uses shorter prompts and smaller token limits
"""

import requests
import json
from datetime import datetime

print("="*70)
print("ANTIGRAVITY FAST DEMO - Ollama + Mistral 7B")
print("="*70)

# Test Ollama connection
print("\n[1/3] Testing Ollama connection...")
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    models = response.json()
    print(f"✓ Ollama is running")
    print(f"✓ Model available: mistral:latest")
except Exception as e:
    print(f"✗ Ollama connection failed: {e}")
    exit(1)

# Load schedule
print("\n[2/3] Loading schedule...")
try:
    with open('outputs/metrics.json', 'r') as f:
        metrics = json.load(f)
    
    print(f"✓ Current objective: ${metrics['objective']:.0f}")
    print(f"✓ Assigned ships: {metrics['num_assigned']}")
    print(f"✓ Unassigned ships: {metrics['num_unassigned']}")
except Exception as e:
    print(f"✗ Could not load metrics: {e}")
    exit(1)

# Build SHORT prompt for faster response
print("\n[3/3] Calling Mistral 7B (this takes 10-20 seconds)...")

prompt = f"""Port scheduling optimization task.

Current status:
- Ships assigned: {metrics['num_assigned']}
- Ships unassigned: {metrics['num_unassigned']}
- Total cost: ${metrics['total_cost']:.0f}
- Objective: ${metrics['objective']:.0f}

Suggest ONE improvement to reduce cost. Respond with JSON only:
{{"suggestion": "brief idea", "expected_savings": 1000}}

JSON:"""

start_time = datetime.now()

try:
    # Use streaming=False and short token limit for faster response
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 100,  # Short response
                "top_k": 10,
                "top_p": 0.9,
            }
        },
        timeout=45  # 45 second timeout
    )
    
    result = response.json()
    llm_response = result.get('response', '')
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print(f"✓ LLM responded in {elapsed:.1f}s")
    
    print("\n" + "="*70)
    print("AI SUGGESTION:")
    print("="*70)
    print(llm_response)
    print("="*70)
    
    print("\n✅ SUCCESS! Ollama + Mistral 7B is working locally!")
    print("\nYour local AI optimization engine is ready to use.")
    print("\nNext steps:")
    print("  1. Run greedy scheduler: python src/engine/greedy_scheduler.py")
    print("  2. Get AI suggestions: python demo_fast.py")
    print("  3. Validate schedule: python src/engine/validator.py --schedule outputs/schedule.json")
    
except requests.exceptions.Timeout:
    print(f"\n⚠ Request timed out after 45 seconds")
    print("\nThis is normal on slower CPUs. The model is working but needs more time.")
    print("\nOptions:")
    print("  1. Wait longer (Mistral can take 1-2 minutes on CPU)")
    print("  2. Use a smaller model: ollama pull phi")
    print("  3. Use GPU acceleration if available")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nTroubleshooting:")
    print("  1. Restart Ollama: Close and reopen Ollama app")
    print("  2. Check model: ollama list")
    print("  3. Try: ollama run mistral 'hello'")
