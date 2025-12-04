"""
Test agent integration with mock LLM
"""

import pytest
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from engine.data_load import load_all, load_config
from engine.precompute import precompute_all
from agent.controller import agent_optimize
from agent.schemas import validate_candidate


def test_agent_runs_with_mock():
    """Test agent controller runs with mock LLM"""
    data = load_all('inputs/')
    config = load_config('config.yaml')
    precomp = precompute_all(data, config)
    
    # Run with mock mode
    result = agent_optimize(data, precomp, config, mode='mock')
    
    assert 'schedule' in result
    assert 'agent_log' in result
    assert 'metrics' in result
    assert result['iterations'] >= 0


def test_candidate_validation():
    """Test candidate validation"""
    valid_candidate = {
        "id": "C1",
        "moves": [
            {"type": "delay_ship", "ship": "S001", "delay_minutes": 60}
        ],
        "rationale": "Test",
        "expected_delta_estimate": -100.0
    }
    
    assert validate_candidate(valid_candidate) == True
    
    invalid_candidate = {
        "id": "C2",
        "moves": [
            {"type": "invalid_move"}
        ]
    }
    
    assert validate_candidate(invalid_candidate) == False


def test_mock_llm_response_parsing():
    """Test parsing of mock LLM responses"""
    from agent.schemas import parse_proposal
    
    mock_response = {
        "candidates": [
            {
                "id": "C1",
                "moves": [{"type": "delay_ship", "ship": "S001", "delay_minutes": 30}],
                "rationale": "Reduce delay",
                "expected_delta_estimate": -200.0
            }
        ]
    }
    
    candidates = parse_proposal(mock_response)
    assert len(candidates) == 1
    assert candidates[0]['id'] == 'C1'


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
