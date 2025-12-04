"""
Test schema validation
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from engine.data_load import load_all, validate_schemas


def test_load_sample_data():
    """Test loading sample CSV data"""
    data = load_all('inputs/')
    
    assert 'ships' in data
    assert 'berths' in data
    assert 'tugs' in data
    assert len(data['ships']) > 0
    assert len(data['berths']) > 0


def test_schema_validation():
    """Test schema validation"""
    data = load_all('inputs/')
    
    # Should not raise
    assert validate_schemas(data) == True


def test_ships_have_required_columns():
    """Test ships have all required columns"""
    data = load_all('inputs/')
    ships = data['ships']
    
    required = ['ship_id', 'eta_iso', 'loa_meters', 'draft_meters', 'cargo_type', 'cargo_tonnes']
    for col in required:
        assert col in ships.columns


def test_berths_have_required_columns():
    """Test berths have all required columns"""
    data = load_all('inputs/')
    berths = data['berths']
    
    required = ['berth_id', 'max_loa_meters', 'max_draft_meters', 'allowed_cargo_types']
    for col in required:
        assert col in berths.columns


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
