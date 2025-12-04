"""
Quick test of Ollama connectivity and agent
"""
import requests
import json

# Test Ollama
print("Testing Ollama connection...")
try:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": "Hello! Respond with just 'OK' if you're working.",
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 10}
        },
        timeout=30
    )
    result = response.json()
    print(f"✓ Ollama is working! Response: {result.get('response', '')[:50]}")
except Exception as e:
    print(f"✗ Ollama connection failed: {e}")
    exit(1)

print("\n✓ Ollama + Mistral 7B is ready to use!")
print("\nTo run the full agent, use:")
print("  cd src/agent")
print("  python controller.py --inputs ../../inputs/ --output ../../outputs/ --config ../../config.yaml")
