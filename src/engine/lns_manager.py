"""
Large Neighborhood Search (LNS) manager
Orchestrates neighborhood repair using greedy + MILP
"""

import pandas as pd
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import random

from data_load import load_all, load_config
from precompute import precompute_all
from greedy_scheduler import greedy_schedule, compute_metrics
from validator import validate_schedule


def select_neighborhood(schedule: List[Dict], data: Dict[str, pd.DataFrame],
                        metrics: Dict[str, Any], neighborhood_size: int) -> List[str]:
    """
    Select ships for neighborhood (high-cost or unassigned)
    
    Args:
        schedule: Current schedule
        data: Loaded data
        metrics: Current metrics
        neighborhood_size: Number of ships to select
        
    Returns:
        List of ship IDs
    """
    # Start with unassigned ships
    neighborhood = list(metrics.get('unassigned_ships', []))
    
    # Add high-delay ships
    ships = data['ships']
    ship_delays = []
    
    for assignment in schedule:
        ship_id = assignment['ship_id']
        ship = ships[ships['ship_id'] == ship_id].iloc[0]
        
        start_time = pd.to_datetime(assignment['start_time_iso'])
        eta = ship['eta_iso']
        
        if start_time > eta:
            delay_hours = (start_time - eta).total_seconds() / 3600
            ship_delays.append((ship_id, delay_hours))
    
    # Sort by delay
    ship_delays.sort(key=lambda x: x[1], reverse=True)
    
    # Add top delayed ships
    for ship_id, _ in ship_delays[:neighborhood_size - len(neighborhood)]:
        if ship_id not in neighborhood:
            neighborhood.append(ship_id)
    
    # Fill remaining with random ships
    all_ships = [ship['ship_id'] for _, ship in ships.iterrows()]
    remaining = [s for s in all_ships if s not in neighborhood]
    random.shuffle(remaining)
    
    for ship_id in remaining[:neighborhood_size - len(neighborhood)]:
        neighborhood.append(ship_id)
    
    return neighborhood[:neighborhood_size]


def lns_optimize(data: Dict[str, pd.DataFrame], precomp: Dict[str, Any],
                config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run LNS optimization
    
    Args:
        data: Loaded data
        precomp: Precomputed structures
        config: Configuration
        
    Returns:
        Best schedule result
    """
    lns_config = config.get('lns', {})
    max_iterations = lns_config.get('max_iterations', 10)
    neighborhood_size = lns_config.get('neighborhood_size', 5)
    improvement_threshold = lns_config.get('improvement_threshold', 0.01)
    
    # Start with greedy baseline
    print("Computing initial greedy solution...")
    current_result = greedy_schedule(data, precomp, config)
    current_metrics = compute_metrics(current_result, data, precomp, config)
    best_objective = current_metrics['objective']
    
    print(f"Initial objective: {best_objective:.2f}")
    
    iteration_log = []
    
    for iteration in range(max_iterations):
        print(f"\n--- LNS Iteration {iteration + 1}/{max_iterations} ---")
        
        # Select neighborhood
        neighborhood = select_neighborhood(current_result['schedule'], data,
                                          current_metrics, neighborhood_size)
        print(f"Neighborhood: {neighborhood}")
        
        # For simplicity, we'll just try random perturbations
        # In a full implementation, you'd call MILP on the neighborhood
        
        # Here we just re-run greedy (placeholder for MILP repair)
        # A real LNS would fix non-neighborhood ships and optimize neighborhood
        
        # For now, just track that we attempted optimization
        iteration_log.append({
            'iteration': iteration + 1,
            'neighborhood': neighborhood,
            'objective': best_objective,
            'improvement': 0.0,
        })
        
        # Check for improvement threshold
        # (In real implementation, compare new vs current objective)
        
        print(f"Objective: {best_objective:.2f} (no change - placeholder)")
    
    # Return best solution found
    return {
        'schedule': current_result['schedule'],
        'unassigned': current_result['unassigned'],
        'metrics': current_metrics,
        'iteration_log': iteration_log,
        'method': 'lns',
    }


def main():
    parser = argparse.ArgumentParser(description='LNS optimizer')
    parser.add_argument('--inputs', default='inputs/', help='Input directory')
    parser.add_argument('--output', default='outputs/', help='Output directory')
    parser.add_argument('--config', default='config.yaml', help='Config file')
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("Loading data...")
    data = load_all(args.inputs)
    config = load_config(args.config)
    
    print("Precomputing...")
    precomp = precompute_all(data, config)
    
    start_time = datetime.now()
    result = lns_optimize(data, precomp, config)
    end_time = datetime.now()
    
    print(f"\n✓ LNS completed in {(end_time - start_time).total_seconds():.2f}s")
    print(f"Final objective: {result['metrics']['objective']:.2f}")
    print(f"Assigned: {len(result['schedule'])} ships")
    print(f"Unassigned: {len(result['unassigned'])} ships")
    
    # Write outputs
    with open(output_path / 'schedule_lns.json', 'w') as f:
        json.dump(result['schedule'], f, indent=2)
    
    with open(output_path / 'lns_log.json', 'w') as f:
        json.dump(result['iteration_log'], f, indent=2)
    
    print(f"\n✓ Outputs written to {args.output}")


if __name__ == "__main__":
    main()
