"""
Greedy scheduler - deterministic earliest-fit baseline
Produces canonical outputs: schedule.json, metrics.json, debug_trace.csv, fallback_flag.txt
"""

import pandas as pd
import numpy as np
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple

from data_load import load_all, load_config
from precompute import precompute_all


def greedy_schedule(data: Dict[str, pd.DataFrame], precomp: Dict[str, Any], 
                    config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Greedy earliest-fit scheduler
    
    Args:
        data: Loaded data
        precomp: Precomputed structures
        config: Configuration
        
    Returns:
        Schedule dictionary
    """
    ships = data['ships'].copy()
    berths = data['berths']
    
    # Sort ships by priority (high first), then ETA
    priority_map = {'high': 0, 'medium': 1, 'low': 2}
    ships['priority_num'] = ships['priority'].map(priority_map)
    ships = ships.sort_values(['priority_num', 'eta_iso'])
    
    # Track berth occupancy: berth_id -> list of (start_slot, end_slot, ship_id)
    berth_occupancy = {berth['berth_id']: [] for _, berth in berths.iterrows()}
    
    # Schedule: list of assignments
    schedule = []
    unassigned = []
    
    debug_trace = []
    
    for _, ship in ships.iterrows():
        ship_id = ship['ship_id']
        
        # Find first compatible berth with earliest available slot
        best_berth = None
        best_start_slot = None
        best_end_slot = None
        
        for _, berth in berths.iterrows():
            berth_id = berth['berth_id']
            
            # Check compatibility
            if not precomp['compatibility'][ship_id][berth_id]:
                continue
            
            # Get service duration
            service_slots = precomp['service_durations'][ship_id][berth_id]
            
            # Get candidate slots
            candidates = precomp['candidate_slots'][ship_id][berth_id]
            
            if not candidates:
                continue
            
            # Find first available slot
            for start_slot in candidates:
                end_slot = start_slot + service_slots
                
                # Check if berth is free during [start_slot, end_slot)
                is_free = True
                for occupied_start, occupied_end, _ in berth_occupancy[berth_id]:
                    if not (end_slot <= occupied_start or start_slot >= occupied_end):
                        is_free = False
                        break
                
                if is_free:
                    # Found a slot
                    if best_start_slot is None or start_slot < best_start_slot:
                        best_berth = berth_id
                        best_start_slot = start_slot
                        best_end_slot = end_slot
                    break  # Take first available slot for this berth
        
        if best_berth is not None:
            # Assign ship to berth
            berth_occupancy[best_berth].append((best_start_slot, best_end_slot, ship_id))
            
            # Convert slots to timestamps
            start_time = precomp['horizon_start'] + timedelta(
                minutes=best_start_slot * precomp['slot_minutes']
            )
            end_time = precomp['horizon_start'] + timedelta(
                minutes=best_end_slot * precomp['slot_minutes']
            )
            
            assignment = {
                'ship_id': ship_id,
                'berth_id': best_berth,
                'start_slot': int(best_start_slot),
                'end_slot': int(best_end_slot),
                'start_time_iso': start_time.isoformat(),
                'end_time_iso': end_time.isoformat(),
            }
            schedule.append(assignment)
            
            debug_trace.append({
                'timestamp': datetime.now().isoformat(),
                'ship_id': ship_id,
                'action': 'assigned',
                'berth_id': best_berth,
                'start_slot': int(best_start_slot),
            })
        else:
            # Could not assign
            unassigned.append(ship_id)
            debug_trace.append({
                'timestamp': datetime.now().isoformat(),
                'ship_id': ship_id,
                'action': 'unassigned',
                'reason': 'no_available_slot',
            })
    
    return {
        'schedule': schedule,
        'unassigned': unassigned,
        'debug_trace': debug_trace,
    }


def compute_metrics(schedule_result: Dict[str, Any], data: Dict[str, pd.DataFrame],
                   precomp: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute objective and KPIs
    
    Args:
        schedule_result: Schedule from greedy_schedule
        data: Loaded data
        precomp: Precomputed structures
        config: Configuration
        
    Returns:
        Metrics dictionary
    """
    schedule = schedule_result['schedule']
    ships = data['ships']
    berths = data['berths']
    costs = data['costs']
    
    # Get cost parameters
    cost_dict = {row['cost_type']: row['value'] for _, row in costs.iterrows()}
    
    total_cost = 0.0
    total_delay_hours = 0.0
    
    # Berth costs
    for assignment in schedule:
        berth_id = assignment['berth_id']
        berth = berths[berths['berth_id'] == berth_id].iloc[0]
        
        duration_slots = assignment['end_slot'] - assignment['start_slot']
        duration_hours = duration_slots * precomp['slot_minutes'] / 60
        
        berth_cost = berth['hourly_cost'] * duration_hours
        total_cost += berth_cost
    
    # Waiting costs (delay from ETA to start)
    for assignment in schedule:
        ship_id = assignment['ship_id']
        ship = ships[ships['ship_id'] == ship_id].iloc[0]
        
        start_time = pd.to_datetime(assignment['start_time_iso'])
        eta = ship['eta_iso']
        
        if start_time > eta:
            delay_hours = (start_time - eta).total_seconds() / 3600
            total_delay_hours += delay_hours
            
            waiting_cost = delay_hours * cost_dict.get('ship_waiting_per_hour', 200)
            total_cost += waiting_cost
    
    # Penalty for unassigned ships
    unassigned_penalty = len(schedule_result['unassigned']) * 50000
    total_cost += unassigned_penalty
    
    # Weighted objective
    weights = config['objective_weights']
    objective = (weights['cost'] * total_cost + 
                weights['delay'] * total_delay_hours * 1000 +
                weights['delivery_violation'] * unassigned_penalty)
    
    return {
        'objective': float(objective),
        'total_cost': float(total_cost),
        'total_delay_hours': float(total_delay_hours),
        'num_assigned': len(schedule),
        'num_unassigned': len(schedule_result['unassigned']),
        'unassigned_ships': schedule_result['unassigned'],
    }


def main():
    parser = argparse.ArgumentParser(description='Greedy scheduler')
    parser.add_argument('--inputs', default='inputs/', help='Input directory')
    parser.add_argument('--output', default='outputs/', help='Output directory')
    parser.add_argument('--config', default='config.yaml', help='Config file')
    args = parser.parse_args()
    
    # Create output directory
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("Loading data...")
    data = load_all(args.inputs)
    config = load_config(args.config)
    
    print("Precomputing...")
    precomp = precompute_all(data, config)
    
    print("Running greedy scheduler...")
    start_time = datetime.now()
    schedule_result = greedy_schedule(data, precomp, config)
    end_time = datetime.now()
    runtime_seconds = (end_time - start_time).total_seconds()
    
    print(f"Completed in {runtime_seconds:.2f}s")
    print(f"Assigned: {len(schedule_result['schedule'])} ships")
    print(f"Unassigned: {len(schedule_result['unassigned'])} ships")
    
    # Compute metrics
    print("Computing metrics...")
    metrics = compute_metrics(schedule_result, data, precomp, config)
    print(f"Objective: {metrics['objective']:.2f}")
    print(f"Total cost: {metrics['total_cost']:.2f}")
    print(f"Total delay: {metrics['total_delay_hours']:.2f} hours")
    
    # Write outputs
    print(f"\nWriting outputs to {args.output}...")
    
    # schedule.json
    with open(output_path / 'schedule.json', 'w') as f:
        json.dump(schedule_result['schedule'], f, indent=2)
    
    # metrics.json
    with open(output_path / 'metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # debug_trace.csv
    debug_df = pd.DataFrame(schedule_result['debug_trace'])
    debug_df.to_csv(output_path / 'debug_trace.csv', index=False)
    
    # fallback_flag.txt
    with open(output_path / 'fallback_flag.txt', 'w') as f:
        f.write("greedy_baseline\n")
    
    # run_meta.json
    run_meta = {
        'run_id': f"greedy_{start_time.strftime('%Y%m%d_%H%M%S')}",
        'method': 'greedy',
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'runtime_seconds': runtime_seconds,
        'config': config,
    }
    with open(output_path / 'run_meta.json', 'w') as f:
        json.dump(run_meta, f, indent=2)
    
    print("✓ Done!")


if __name__ == "__main__":
    main()
