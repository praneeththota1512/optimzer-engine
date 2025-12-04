"""
Validator - checks hard constraints on schedules
"""

import json
import pandas as pd
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

from data_load import load_all


def validate_schedule(schedule: List[Dict], data: Dict[str, pd.DataFrame]) -> Tuple[bool, List[str]]:
    """
    Validate schedule against hard constraints
    
    Args:
        schedule: List of assignments
        data: Loaded data
        
    Returns:
        (is_valid, list_of_violations)
    """
    violations = []
    
    ships = data['ships']
    berths = data['berths']
    cranes = data['cranes']
    
    # 1. Check berth overlap
    berth_intervals = {}
    for assignment in schedule:
        berth_id = assignment['berth_id']
        start_slot = assignment['start_slot']
        end_slot = assignment['end_slot']
        ship_id = assignment['ship_id']
        
        if berth_id not in berth_intervals:
            berth_intervals[berth_id] = []
        
        # Check for overlaps with existing intervals
        for existing_start, existing_end, existing_ship in berth_intervals[berth_id]:
            if not (end_slot <= existing_start or start_slot >= existing_end):
                violations.append(
                    f"Berth overlap: {berth_id} has {ship_id} [{start_slot},{end_slot}) "
                    f"overlapping with {existing_ship} [{existing_start},{existing_end})"
                )
        
        berth_intervals[berth_id].append((start_slot, end_slot, ship_id))
    
    # 2. Check LOA and draft constraints
    for assignment in schedule:
        ship_id = assignment['ship_id']
        berth_id = assignment['berth_id']
        
        ship = ships[ships['ship_id'] == ship_id].iloc[0]
        berth = berths[berths['berth_id'] == berth_id].iloc[0]
        
        if ship['loa_meters'] > berth['max_loa_meters']:
            violations.append(
                f"LOA violation: {ship_id} ({ship['loa_meters']}m) exceeds "
                f"{berth_id} max ({berth['max_loa_meters']}m)"
            )
        
        if ship['draft_meters'] > berth['max_draft_meters']:
            violations.append(
                f"Draft violation: {ship_id} ({ship['draft_meters']}m) exceeds "
                f"{berth_id} max ({berth['max_draft_meters']}m)"
            )
    
    # 3. Check cargo type compatibility
    for assignment in schedule:
        ship_id = assignment['ship_id']
        berth_id = assignment['berth_id']
        
        ship = ships[ships['ship_id'] == ship_id].iloc[0]
        berth = berths[berths['berth_id'] == berth_id].iloc[0]
        
        allowed_types = berth['allowed_cargo_types'].split(',')
        if ship['cargo_type'] not in allowed_types:
            violations.append(
                f"Cargo type violation: {ship_id} ({ship['cargo_type']}) "
                f"not allowed at {berth_id} ({allowed_types})"
            )
    
    # 4. Check crane availability
    for assignment in schedule:
        berth_id = assignment['berth_id']
        
        berth_cranes = cranes[(cranes['berth_id'] == berth_id) & (cranes['operational'] == True)]
        if len(berth_cranes) == 0:
            violations.append(
                f"No operational cranes at {berth_id}"
            )
    
    is_valid = len(violations) == 0
    return is_valid, violations


def main():
    parser = argparse.ArgumentParser(description='Validate schedule')
    parser.add_argument('--schedule', default='outputs/schedule.json', help='Schedule file')
    parser.add_argument('--inputs', default='inputs/', help='Input directory')
    args = parser.parse_args()
    
    print(f"Loading schedule from {args.schedule}...")
    with open(args.schedule, 'r') as f:
        schedule = json.load(f)
    
    print(f"Loading data from {args.inputs}...")
    data = load_all(args.inputs)
    
    print("Validating...")
    is_valid, violations = validate_schedule(schedule, data)
    
    if is_valid:
        print("✓ Schedule is VALID - no hard constraint violations")
        return 0
    else:
        print(f"✗ Schedule is INVALID - {len(violations)} violations found:")
        for i, violation in enumerate(violations, 1):
            print(f"  {i}. {violation}")
        return 1


if __name__ == "__main__":
    exit(main())
