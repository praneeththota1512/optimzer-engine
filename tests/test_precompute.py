"""
Test precomputation logic
"""

import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from engine.data_load import load_all, load_config
from engine.precompute import precompute_all, check_berth_compatibility


def test_precompute_runs():
    """Test precomputation completes"""
    data = load_all('inputs/')
    config = load_config('config.yaml')
    
    precomp = precompute_all(data, config)
    
    assert 'horizon_start' in precomp
    assert 'total_slots' in precomp
    assert 'compatibility' in precomp
    assert precomp['total_slots'] > 0


def test_compatibility_matrix():
    """Test compatibility matrix is populated"""
    data = load_all('inputs/')
    config = load_config('config.yaml')
    
    precomp = precompute_all(data, config)
    
    ships = data['ships']
    berths = data['berths']
    
    for _, ship in ships.iterrows():
        ship_id = ship['ship_id']
        assert ship_id in precomp['compatibility']
        
        for _, berth in berths.iterrows():
            berth_id = berth['berth_id']
            assert berth_id in precomp['compatibility'][ship_id]


def test_service_durations():
    """Test service durations are computed"""
    data = load_all('inputs/')
    config = load_config('config.yaml')
    
    precomp = precompute_all(data, config)
    
    ships = data['ships']
    
    for _, ship in ships.iterrows():
        ship_id = ship['ship_id']
        assert ship_id in precomp['service_durations']
        
        # At least one berth should have a duration
        durations = list(precomp['service_durations'][ship_id].values())
        assert len(durations) > 0


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
