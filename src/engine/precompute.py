"""
Precomputation module
Computes service durations, berth compatibility, and candidate slots
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any


def compute_service_duration_slots(ship: pd.Series, cranes: pd.DataFrame, 
                                   berth_id: str, slot_minutes: int) -> int:
    """
    Compute service duration in time slots for a ship at a berth
    
    Args:
        ship: Ship row from DataFrame
        cranes: Cranes DataFrame
        berth_id: Berth ID
        slot_minutes: Minutes per time slot
        
    Returns:
        Number of time slots needed
    """
    # Get operational cranes at this berth
    berth_cranes = cranes[(cranes['berth_id'] == berth_id) & (cranes['operational'] == True)]
    
    if len(berth_cranes) == 0:
        return 999999  # No cranes available
    
    # Total throughput (tonnes/hour)
    total_throughput = berth_cranes['throughput_tonnes_per_hour'].sum()
    
    # Service time in hours
    service_hours = ship['cargo_tonnes'] / total_throughput
    
    # Convert to slots (round up)
    service_slots = int(np.ceil(service_hours * 60 / slot_minutes))
    
    return service_slots


def check_berth_compatibility(ship: pd.Series, berth: pd.Series) -> bool:
    """
    Check if ship can physically use berth
    
    Args:
        ship: Ship row
        berth: Berth row
        
    Returns:
        True if compatible
    """
    # Check LOA
    if ship['loa_meters'] > berth['max_loa_meters']:
        return False
    
    # Check draft
    if ship['draft_meters'] > berth['max_draft_meters']:
        return False
    
    # Check cargo type
    allowed_types = berth['allowed_cargo_types'].split(',')
    if ship['cargo_type'] not in allowed_types:
        return False
    
    return True


def generate_candidate_slots(ship: pd.Series, berth: pd.Series, cranes: pd.DataFrame,
                            horizon_start: datetime, horizon_end: datetime,
                            slot_minutes: int) -> List[int]:
    """
    Generate candidate start slots for a ship at a berth
    
    Args:
        ship: Ship row
        berth: Berth row
        cranes: Cranes DataFrame
        horizon_start: Planning horizon start
        horizon_end: Planning horizon end
        slot_minutes: Minutes per slot
        
    Returns:
        List of candidate start slot indices
    """
    if not check_berth_compatibility(ship, berth):
        return []
    
    # Earliest start is ship ETA
    eta = ship['eta_iso']
    
    # Convert to slot index
    eta_slot = int((eta - horizon_start).total_seconds() / 60 / slot_minutes)
    eta_slot = max(0, eta_slot)
    
    # Total slots in horizon
    total_slots = int((horizon_end - horizon_start).total_seconds() / 60 / slot_minutes)
    
    # Service duration
    service_slots = compute_service_duration_slots(ship, cranes, berth['berth_id'], slot_minutes)
    
    # Latest start slot (must finish before horizon end)
    latest_slot = total_slots - service_slots
    
    if latest_slot < eta_slot:
        return []  # Cannot fit in horizon
    
    # Generate candidates (sparse: every 4 slots to reduce search space)
    candidates = list(range(eta_slot, latest_slot + 1, 4))
    
    return candidates


def precompute_all(data: Dict[str, pd.DataFrame], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Precompute all derived data structures
    
    Args:
        data: Loaded data dictionary
        config: Configuration dictionary
        
    Returns:
        Dictionary with precomputed structures
    """
    ships = data['ships']
    berths = data['berths']
    cranes = data['cranes']
    
    # Determine horizon
    horizon_start = ships['eta_iso'].min()
    horizon_hours = config['horizon_hours']
    horizon_end = horizon_start + timedelta(hours=horizon_hours)
    slot_minutes = config['time_slot_minutes']
    
    total_slots = int(horizon_hours * 60 / slot_minutes)
    
    # Precompute compatibility matrix
    compatibility = {}
    service_durations = {}
    candidate_slots = {}
    
    for _, ship in ships.iterrows():
        ship_id = ship['ship_id']
        compatibility[ship_id] = {}
        service_durations[ship_id] = {}
        candidate_slots[ship_id] = {}
        
        for _, berth in berths.iterrows():
            berth_id = berth['berth_id']
            
            compat = check_berth_compatibility(ship, berth)
            compatibility[ship_id][berth_id] = compat
            
            if compat:
                duration = compute_service_duration_slots(ship, cranes, berth_id, slot_minutes)
                service_durations[ship_id][berth_id] = duration
                
                candidates = generate_candidate_slots(ship, berth, cranes, 
                                                      horizon_start, horizon_end, slot_minutes)
                candidate_slots[ship_id][berth_id] = candidates
            else:
                service_durations[ship_id][berth_id] = 0
                candidate_slots[ship_id][berth_id] = []
    
    return {
        'horizon_start': horizon_start,
        'horizon_end': horizon_end,
        'total_slots': total_slots,
        'slot_minutes': slot_minutes,
        'compatibility': compatibility,
        'service_durations': service_durations,
        'candidate_slots': candidate_slots,
    }


if __name__ == "__main__":
    import sys
    from data_load import load_all, load_config
    
    inputs_dir = sys.argv[1] if len(sys.argv) > 1 else "inputs/"
    config_path = sys.argv[2] if len(sys.argv) > 2 else "config.yaml"
    
    print("Loading data...")
    data = load_all(inputs_dir)
    config = load_config(config_path)
    
    print("Precomputing...")
    precomp = precompute_all(data, config)
    
    print(f"\nHorizon: {precomp['horizon_start']} to {precomp['horizon_end']}")
    print(f"Total slots: {precomp['total_slots']}")
    print(f"Slot duration: {precomp['slot_minutes']} minutes")
    
    print("\nCompatibility matrix:")
    for ship_id, berth_dict in precomp['compatibility'].items():
        compatible_berths = [b for b, c in berth_dict.items() if c]
        print(f"  {ship_id}: {compatible_berths}")
