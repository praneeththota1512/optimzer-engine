"""
MILP model using OR-Tools CP-SAT
Time-indexed model for small instances
"""

import pandas as pd
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from ortools.sat.python import cp_model

from data_load import load_all, load_config
from precompute import precompute_all


def build_and_solve_milp(data: Dict[str, pd.DataFrame], precomp: Dict[str, Any],
                         config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build and solve MILP model
    
    Args:
        data: Loaded data
        precomp: Precomputed structures
        config: Configuration
        
    Returns:
        Schedule result dictionary
    """
    ships = data['ships']
    berths = data['berths']
    
    model = cp_model.CpModel()
    
    # Decision variables: x[ship_id][berth_id][start_slot] = 1 if ship assigned to berth starting at slot
    x = {}
    for _, ship in ships.iterrows():
        ship_id = ship['ship_id']
        x[ship_id] = {}
        
        for _, berth in berths.iterrows():
            berth_id = berth['berth_id']
            x[ship_id][berth_id] = {}
            
            candidates = precomp['candidate_slots'][ship_id][berth_id]
            for start_slot in candidates:
                x[ship_id][berth_id][start_slot] = model.NewBoolVar(
                    f'x_{ship_id}_{berth_id}_{start_slot}'
                )
    
    # Constraint: each ship assigned to at most one (berth, start_slot) pair
    for _, ship in ships.iterrows():
        ship_id = ship['ship_id']
        
        assignments = []
        for berth_id in x[ship_id]:
            for start_slot in x[ship_id][berth_id]:
                assignments.append(x[ship_id][berth_id][start_slot])
        
        if assignments:
            model.Add(sum(assignments) <= 1)
    
    # Constraint: no berth overlap
    for _, berth in berths.iterrows():
        berth_id = berth['berth_id']
        
        for slot in range(precomp['total_slots']):
            # For each slot, at most one ship can occupy this berth
            occupying_vars = []
            
            for _, ship in ships.iterrows():
                ship_id = ship['ship_id']
                
                if berth_id not in x[ship_id]:
                    continue
                
                service_duration = precomp['service_durations'][ship_id][berth_id]
                
                for start_slot in x[ship_id][berth_id]:
                    end_slot = start_slot + service_duration
                    
                    # Check if this assignment occupies current slot
                    if start_slot <= slot < end_slot:
                        occupying_vars.append(x[ship_id][berth_id][start_slot])
            
            if occupying_vars:
                model.Add(sum(occupying_vars) <= 1)
    
    # Objective: minimize cost + delay
    objective_terms = []
    
    # Berth costs
    for _, ship in ships.iterrows():
        ship_id = ship['ship_id']
        
        for _, berth in berths.iterrows():
            berth_id = berth['berth_id']
            
            if berth_id not in x[ship_id]:
                continue
            
            service_duration = precomp['service_durations'][ship_id][berth_id]
            duration_hours = service_duration * precomp['slot_minutes'] / 60
            berth_cost = int(berth['hourly_cost'] * duration_hours)
            
            for start_slot in x[ship_id][berth_id]:
                objective_terms.append(berth_cost * x[ship_id][berth_id][start_slot])
    
    # Delay costs
    for _, ship in ships.iterrows():
        ship_id = ship['ship_id']
        eta = ship['eta_iso']
        eta_slot = int((eta - precomp['horizon_start']).total_seconds() / 60 / precomp['slot_minutes'])
        eta_slot = max(0, eta_slot)
        
        for berth_id in x[ship_id]:
            for start_slot in x[ship_id][berth_id]:
                if start_slot > eta_slot:
                    delay_slots = start_slot - eta_slot
                    delay_hours = delay_slots * precomp['slot_minutes'] / 60
                    delay_cost = int(delay_hours * 200)  # ship_waiting_per_hour
                    
                    objective_terms.append(delay_cost * x[ship_id][berth_id][start_slot])
    
    # Penalty for unassigned ships
    unassigned_penalty = 50000
    for _, ship in ships.iterrows():
        ship_id = ship['ship_id']
        
        assignments = []
        for berth_id in x[ship_id]:
            for start_slot in x[ship_id][berth_id]:
                assignments.append(x[ship_id][berth_id][start_slot])
        
        if assignments:
            # If sum(assignments) == 0, ship is unassigned
            is_assigned = model.NewBoolVar(f'assigned_{ship_id}')
            model.Add(sum(assignments) >= 1).OnlyEnforceIf(is_assigned)
            model.Add(sum(assignments) == 0).OnlyEnforceIf(is_assigned.Not())
            
            # Add penalty for unassigned
            objective_terms.append(unassigned_penalty * (1 - is_assigned))
    
    if objective_terms:
        model.Minimize(sum(objective_terms))
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = config.get('solver_time_budget_seconds', 600)
    solver.parameters.num_search_workers = 4
    
    print("Solving MILP...")
    status = solver.Solve(model)
    
    # Extract solution
    schedule = []
    unassigned = []
    
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for _, ship in ships.iterrows():
            ship_id = ship['ship_id']
            assigned = False
            
            for berth_id in x[ship_id]:
                for start_slot in x[ship_id][berth_id]:
                    if solver.Value(x[ship_id][berth_id][start_slot]) == 1:
                        service_duration = precomp['service_durations'][ship_id][berth_id]
                        end_slot = start_slot + service_duration
                        
                        start_time = precomp['horizon_start'] + timedelta(
                            minutes=start_slot * precomp['slot_minutes']
                        )
                        end_time = precomp['horizon_start'] + timedelta(
                            minutes=end_slot * precomp['slot_minutes']
                        )
                        
                        schedule.append({
                            'ship_id': ship_id,
                            'berth_id': berth_id,
                            'start_slot': int(start_slot),
                            'end_slot': int(end_slot),
                            'start_time_iso': start_time.isoformat(),
                            'end_time_iso': end_time.isoformat(),
                        })
                        assigned = True
                        break
                if assigned:
                    break
            
            if not assigned:
                unassigned.append(ship_id)
    
    return {
        'schedule': schedule,
        'unassigned': unassigned,
        'solver_status': solver.StatusName(status),
        'objective_value': solver.ObjectiveValue() if status in [cp_model.OPTIMAL, cp_model.FEASIBLE] else None,
        'solve_time': solver.WallTime(),
    }


def main():
    parser = argparse.ArgumentParser(description='MILP solver')
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
    result = build_and_solve_milp(data, precomp, config)
    end_time = datetime.now()
    
    print(f"\nSolver status: {result['solver_status']}")
    print(f"Solve time: {result['solve_time']:.2f}s")
    print(f"Assigned: {len(result['schedule'])} ships")
    print(f"Unassigned: {len(result['unassigned'])} ships")
    if result['objective_value'] is not None:
        print(f"Objective value: {result['objective_value']:.2f}")
    
    # Write outputs
    with open(output_path / 'schedule_milp.json', 'w') as f:
        json.dump(result['schedule'], f, indent=2)
    
    with open(output_path / 'milp_result.json', 'w') as f:
        json.dump({
            'solver_status': result['solver_status'],
            'objective_value': result['objective_value'],
            'solve_time': result['solve_time'],
            'num_assigned': len(result['schedule']),
            'num_unassigned': len(result['unassigned']),
        }, f, indent=2)
    
    print(f"\n✓ Outputs written to {args.output}")


if __name__ == "__main__":
    main()
