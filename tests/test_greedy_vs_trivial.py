"""
Test greedy scheduler vs trivial baseline
"""

import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from engine.data_load import load_all, load_config
from engine.precompute import precompute_all
from engine.greedy_scheduler import greedy_schedule, compute_metrics
from engine.validator import validate_schedule


def test_greedy_produces_schedule():
    """Test greedy scheduler produces a schedule"""
    data = load_all('inputs/')
    config = load_config('config.yaml')
    precomp = precompute_all(data, config)
    
    result = greedy_schedule(data, precomp, config)
    
    assert 'schedule' in result
    assert 'unassigned' in result
    assert isinstance(result['schedule'], list)


def test_greedy_schedule_is_valid():
    """Test greedy schedule passes validation"""
    data = load_all('inputs/')
    config = load_config('config.yaml')
    precomp = precompute_all(data, config)
    
    result = greedy_schedule(data, precomp, config)
    schedule = result['schedule']
    
    is_valid, violations = validate_schedule(schedule, data)
    
    assert is_valid, f"Schedule has violations: {violations}"


def test_greedy_assigns_ships():
    """Test greedy scheduler assigns at least some ships"""
    data = load_all('inputs/')
    config = load_config('config.yaml')
    precomp = precompute_all(data, config)
    
    result = greedy_schedule(data, precomp, config)
    
    # Should assign at least one ship
    assert len(result['schedule']) > 0


def test_metrics_computation():
    """Test metrics are computed correctly"""
    data = load_all('inputs/')
    config = load_config('config.yaml')
    precomp = precompute_all(data, config)
    
    result = greedy_schedule(data, precomp, config)
    metrics = compute_metrics(result, data, precomp, config)
    
    assert 'objective' in metrics
    assert 'total_cost' in metrics
    assert 'total_delay_hours' in metrics
    assert metrics['objective'] >= 0


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
