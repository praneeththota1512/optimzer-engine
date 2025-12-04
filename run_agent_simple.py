"""
Simple agent runner with Ollama - standalone script
"""

import sys
import os

# Set up Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Now run the imports
if __name__ == "__main__":
    # Change to script directory
    os.chdir(current_dir)
    
    # Import and run
    import pandas as pd
    import json
    import argparse
    import copy
    from datetime import datetime, timedelta
    from typing import Dict, List, Any, Tuple
    
    # Import modules directly
    exec(open('src/engine/data_load.py').read(), globals())
    exec(open('src/engine/precompute.py').read(), globals())
    exec(open('src/engine/greedy_scheduler.py').read(), globals())
    exec(open('src/engine/validator.py').read(), globals())
    exec(open('src/agent/llm_client.py').read(), globals())
    exec(open('src/agent/prompt_templates.py').read(), globals())
    exec(open('src/agent/schemas.py').read(), globals())
    
    # Now import controller
    exec(open('src/agent/controller.py').read(), globals())
    
    # Run main
    main()
