"""
Run agent optimizer with Ollama
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.controller import main

if __name__ == "__main__":
    main()
