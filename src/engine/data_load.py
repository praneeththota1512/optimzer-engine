"""
Data loading and schema validation module
Loads CSV inputs and validates schemas
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import yaml


def load_config(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_all(inputs_dir: str) -> Dict[str, pd.DataFrame]:
    """
    Load all CSV files from inputs directory
    
    Args:
        inputs_dir: Path to inputs directory
        
    Returns:
        Dictionary mapping table name to DataFrame
    """
    inputs_path = Path(inputs_dir)
    
    # Load all CSV files
    data = {}
    
    # Ships
    ships = pd.read_csv(inputs_path / 'ships.csv')
    ships['eta_iso'] = pd.to_datetime(ships['eta_iso'])
    data['ships'] = ships
    
    # Berths
    berths = pd.read_csv(inputs_path / 'berths.csv')
    data['berths'] = berths
    
    # Tugs
    tugs = pd.read_csv(inputs_path / 'tugs.csv')
    data['tugs'] = tugs
    
    # Anchorages
    anchorages = pd.read_csv(inputs_path / 'anchorages.csv')
    data['anchorages'] = anchorages
    
    # Cranes
    cranes = pd.read_csv(inputs_path / 'cranes.csv')
    data['cranes'] = cranes
    
    # Trains
    trains = pd.read_csv(inputs_path / 'trains.csv')
    data['trains'] = trains
    
    # Yards
    yards = pd.read_csv(inputs_path / 'yards.csv')
    data['yards'] = yards
    
    # Demand
    demand = pd.read_csv(inputs_path / 'demand_theta.csv')
    demand['required_delivery_iso'] = pd.to_datetime(demand['required_delivery_iso'])
    data['demand'] = demand
    
    # Costs
    costs = pd.read_csv(inputs_path / 'costs.csv')
    data['costs'] = costs
    
    # Historical events (optional)
    hist_path = inputs_path / 'historical_events.csv'
    if hist_path.exists():
        historical = pd.read_csv(hist_path)
        historical['timestamp_iso'] = pd.to_datetime(historical['timestamp_iso'])
        data['historical_events'] = historical
    
    return data


def validate_schemas(data: Dict[str, pd.DataFrame]) -> bool:
    """
    Validate that all required columns are present
    
    Args:
        data: Dictionary of DataFrames
        
    Returns:
        True if valid, raises ValueError otherwise
    """
    required_columns = {
        'ships': ['ship_id', 'eta_iso', 'loa_meters', 'draft_meters', 'cargo_type', 'cargo_tonnes'],
        'berths': ['berth_id', 'max_loa_meters', 'max_draft_meters', 'allowed_cargo_types'],
        'tugs': ['tug_id', 'capacity_ships_per_slot'],
        'cranes': ['crane_id', 'berth_id', 'throughput_tonnes_per_hour', 'operational'],
        'trains': ['train_id', 'destination_plant', 'capacity_tonnes'],
    }
    
    for table_name, required_cols in required_columns.items():
        if table_name not in data:
            raise ValueError(f"Missing required table: {table_name}")
        
        df = data[table_name]
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Table {table_name} missing columns: {missing_cols}")
    
    return True


if __name__ == "__main__":
    import sys
    
    # Test loading
    inputs_dir = sys.argv[1] if len(sys.argv) > 1 else "inputs/"
    
    print(f"Loading data from {inputs_dir}...")
    data = load_all(inputs_dir)
    
    print("\nLoaded tables:")
    for name, df in data.items():
        print(f"  {name}: {len(df)} rows")
    
    print("\nValidating schemas...")
    validate_schemas(data)
    print("✓ All schemas valid")
