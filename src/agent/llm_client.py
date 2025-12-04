"""
LLM client for local model inference
Supports Ollama, llama.cpp, and vLLM backends
"""

import requests
import json
from typing import Dict, Any, Optional, List


class LLMClient:
    """Client for local LLM inference"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM client
        
        Args:
            config: Agent configuration from config.yaml
        """
        self.backend = config.get('backend', 'ollama')
        self.model_name = config.get('model_name', 'mistral')
        self.ollama_url = config.get('ollama_url', 'http://localhost:11434')
        self.temperature = config.get('temperature', 0.0)
        self.max_tokens = config.get('max_tokens', 512)
        self.max_retries = config.get('max_retries', 2)
    
    def call(self, prompt: str, temperature: Optional[float] = None,
             max_tokens: Optional[int] = None) -> str:
        """
        Call LLM with prompt
        
        Args:
            prompt: Input prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Generated text
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        if self.backend == 'ollama':
            return self._call_ollama(prompt, temp, max_tok)
        elif self.backend == 'llama_cpp':
            return self._call_llama_cpp(prompt, temp, max_tok)
        elif self.backend == 'vllm':
            return self._call_vllm(prompt, temp, max_tok)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
    
    def _call_ollama(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call Ollama API"""
        url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        except Exception as e:
            raise RuntimeError(f"Ollama API call failed: {e}")
    
    def _call_llama_cpp(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call llama.cpp server API"""
        # Assumes llama.cpp server running on localhost:8080
        url = "http://localhost:8080/completion"
        
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "n_predict": max_tokens,
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get('content', '')
        except Exception as e:
            raise RuntimeError(f"llama.cpp API call failed: {e}")
    
    def _call_vllm(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Call vLLM server API"""
        # Assumes vLLM server running on localhost:8000
        url = "http://localhost:8000/generate"
        
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get('text', [''])[0]
        except Exception as e:
            raise RuntimeError(f"vLLM API call failed: {e}")
    
    def call_structured(self, prompt: str, expected_format: str = "json") -> Dict[str, Any]:
        """
        Call LLM and parse structured output
        
        Args:
            prompt: Input prompt (should request JSON output)
            expected_format: Expected format (currently only 'json')
            
        Returns:
            Parsed dictionary
        """
        for attempt in range(self.max_retries + 1):
            try:
                response_text = self.call(prompt)
                
                # Try to extract JSON from response
                # Sometimes LLMs wrap JSON in markdown code blocks
                response_text = response_text.strip()
                
                # Remove markdown code blocks if present
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.startswith('```'):
                    response_text = response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                response_text = response_text.strip()
                
                # Parse JSON
                parsed = json.loads(response_text)
                return parsed
                
            except json.JSONDecodeError as e:
                if attempt < self.max_retries:
                    print(f"JSON parse error (attempt {attempt + 1}/{self.max_retries + 1}): {e}")
                    print(f"Response was: {response_text[:200]}...")
                    continue
                else:
                    raise ValueError(f"Failed to parse JSON after {self.max_retries + 1} attempts: {e}")
        
        return {}


class MockLLMClient(LLMClient):
    """Mock LLM client for testing"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.mock_responses = []
        self.call_count = 0
    
    def set_mock_responses(self, responses: List[str]):
        """Set mock responses to return"""
        self.mock_responses = responses
        self.call_count = 0
    
    def call(self, prompt: str, temperature: Optional[float] = None,
             max_tokens: Optional[int] = None) -> str:
        """Return mock response"""
        if self.call_count < len(self.mock_responses):
            response = self.mock_responses[self.call_count]
            self.call_count += 1
            return response
        else:
            # Default mock response
            return json.dumps({
                "candidates": [
                    {
                        "id": "C1",
                        "moves": [
                            {"type": "delay_ship", "ship": "S001", "delay_minutes": 60}
                        ],
                        "rationale": "Mock improvement",
                        "expected_delta_estimate": -500.0
                    }
                ]
            })


if __name__ == "__main__":
    # Test Ollama connection
    config = {
        'backend': 'ollama',
        'model_name': 'mistral',
        'temperature': 0.0,
        'max_tokens': 100,
    }
    
    client = LLMClient(config)
    
    try:
        response = client.call("Hello, are you working?")
        print(f"✓ Ollama connection successful!")
        print(f"Response: {response[:100]}...")
    except Exception as e:
        print(f"✗ Ollama connection failed: {e}")
        print("Make sure Ollama is running: ollama serve")
