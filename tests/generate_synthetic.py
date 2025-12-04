"""
Generate synthetic test data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


def generate_synthetic_ships(num_ships: int = 20) -> pd.DataFrame:
    """Generate synthetic ship data"""
    np.random.seed(42)
    
    cargo_types = ['iron_ore', 'coal', 'containers']
    priorities = ['high', 'medium', 'low']
    plants = ['PLANT_A', 'PLANT_B', 'PLANT_C']
    
    base_time = datetime(2025, 12, 5, 6, 0, 0)
    
    ships = []
    for i in range(num_ships):
        ship_id = f"S{i+1:03d}"
        eta = base_time + timedelta(hours=np.random.exponential(12))
        loa = np.random.uniform(180, 320)
        draft = np.random.uniform(9, 14)
        cargo_type = np.random.choice(cargo_types)
        cargo_tonnes = np.random.randint(20000, 90000)
        priority = np.random.choice(priorities)
        service_hours = cargo_tonnes / np.random.uniform(8000, 12000)
        destination = np.random.choice(plants)
        
        ships.append({
            'ship_id': ship_id,
            'name': f'MV Ship {i+1}',
            'eta_iso': eta.isoformat() + 'Z',
            'loa_meters': round(loa, 1),
            'draft_meters': round(draft, 1),
            'cargo_type': cargo_type,
            'cargo_tonnes': cargo_tonnes,
            'priority': priority,
            'service_hours': round(service_hours, 1),
            'destination_plant': destination,
        })
    
    return pd.DataFrame(ships)


def generate_synthetic_dataset(output_dir: str = 'inputs_synthetic/'):
    """Generate complete synthetic dataset"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Ships
    ships = generate_synthetic_ships(20)
    ships.to_csv(output_path / 'ships.csv', index=False)
    
    print(f"Generated {len(ships)} ships")
    print(f"Saved to {output_dir}")


if __name__ == "__main__":
    generate_synthetic_dataset()
