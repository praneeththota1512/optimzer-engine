"""
Agent controller - main agent loop
Orchestrates LLM proposals, validation, and schedule improvements
"""

import pandas as pd
import json
import argparse
import copy
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.engine.data_load import load_all, load_config
from src.engine.precompute import precompute_all
from src.engine.greedy_scheduler import greedy_schedule, compute_metrics
from src.engine.validator import validate_schedule

from src.agent.llm_client import LLMClient, MockLLMClient
from src.agent.prompt_templates import build_state_snapshot, build_optimization_prompt
from src.agent.schemas import parse_proposal, validate_candidate




def apply_move(schedule: List[Dict], move: Dict[str, Any], data: Dict[str, pd.DataFrame],
               precomp: Dict[str, Any]) -> Tuple[List[Dict], bool]:
    """
    Apply a move to the schedule
    
    Args:
        schedule: Current schedule
        move: Move to apply
        data: Loaded data
        precomp: Precomputed structures
        
    Returns:
        (new_schedule, success)
    """
    new_schedule = copy.deepcopy(schedule)
    move_type = move.get('type')
    
    if move_type == 'delay_ship':
        ship_id = move['ship']
        delay_minutes = move['delay_minutes']
        
        # Find ship in schedule
        for assignment in new_schedule:
            if assignment['ship_id'] == ship_id:
                # Delay start and end times
                delay_slots = delay_minutes // precomp['slot_minutes']
                assignment['start_slot'] += delay_slots
                assignment['end_slot'] += delay_slots
                
                # Update timestamps
                start_time = pd.to_datetime(assignment['start_time_iso']) + timedelta(minutes=delay_minutes)
                end_time = pd.to_datetime(assignment['end_time_iso']) + timedelta(minutes=delay_minutes)
                assignment['start_time_iso'] = start_time.isoformat()
                assignment['end_time_iso'] = end_time.isoformat()
                return new_schedule, True
        
        return schedule, False
    
    elif move_type == 'swap_berth':
        ship_a = move['ship_a']
        ship_b = move['ship_b']
        
        # Find both ships
        assignment_a = None
        assignment_b = None
        
        for assignment in new_schedule:
            if assignment['ship_id'] == ship_a:
                assignment_a = assignment
            if assignment['ship_id'] == ship_b:
                assignment_b = assignment
        
        if assignment_a and assignment_b:
            # Swap berths
            assignment_a['berth_id'], assignment_b['berth_id'] = assignment_b['berth_id'], assignment_a['berth_id']
            return new_schedule, True
        
        return schedule, False
    
    elif move_type == 'reassign_berth':
        ship_id = move['ship']
        new_berth = move['new_berth']
        
        for assignment in new_schedule:
            if assignment['ship_id'] == ship_id:
                assignment['berth_id'] = new_berth
                return new_schedule, True
        
        return schedule, False
    
    elif move_type == 'advance_ship':
        ship_id = move['ship']
        advance_minutes = move['advance_minutes']
        
        for assignment in new_schedule:
            if assignment['ship_id'] == ship_id:
                # Advance start and end times
                advance_slots = advance_minutes // precomp['slot_minutes']
                assignment['start_slot'] -= advance_slots
                assignment['end_slot'] -= advance_slots
                
                # Ensure non-negative
                if assignment['start_slot'] < 0:
                    return schedule, False
                
                # Update timestamps
                start_time = pd.to_datetime(assignment['start_time_iso']) - timedelta(minutes=advance_minutes)
                end_time = pd.to_datetime(assignment['end_time_iso']) - timedelta(minutes=advance_minutes)
                assignment['start_time_iso'] = start_time.isoformat()
                assignment['end_time_iso'] = end_time.isoformat()
                return new_schedule, True
        
        return schedule, False
    
    return schedule, False


def apply_candidate(schedule: List[Dict], candidate: Dict[str, Any],
                   data: Dict[str, pd.DataFrame], precomp: Dict[str, Any]) -> Tuple[List[Dict], bool]:
    """
    Apply all moves in a candidate
    
    Args:
        schedule: Current schedule
        candidate: Candidate with moves
        data: Loaded data
        precomp: Precomputed structures
        
    Returns:
        (new_schedule, all_successful)
    """
    new_schedule = copy.deepcopy(schedule)
    
    for move in candidate['moves']:
        new_schedule, success = apply_move(new_schedule, move, data, precomp)
        if not success:
            return schedule, False
    
    return new_schedule, True


def agent_optimize(data: Dict[str, pd.DataFrame], precomp: Dict[str, Any],
                   config: Dict[str, Any], mode: str = 'ollama') -> Dict[str, Any]:
    """
    Run agent-based optimization
    
    Args:
        data: Loaded data
        precomp: Precomputed structures
        config: Configuration
        mode: 'ollama', 'mock', or other backend
        
    Returns:
        Best schedule result with agent log
    """
    agent_config = config.get('agent', {})
    time_budget = agent_config.get('agent_time_budget_seconds', 60)
    
    # Initialize LLM client
    if mode == 'mock':
        llm_client = MockLLMClient(agent_config)
    else:
        llm_client = LLMClient(agent_config)
    
    # Start with greedy baseline
    print("Computing initial greedy solution...")
    current_result = greedy_schedule(data, precomp, config)
    current_schedule = current_result['schedule']
    current_metrics = compute_metrics(current_result, data, precomp, config)
    best_objective = current_metrics['objective']
    
    print(f"Initial objective: {best_objective:.2f}")
    
    agent_log = []
    start_time = datetime.now()
    iteration = 0
    
    while (datetime.now() - start_time).total_seconds() < time_budget:
        iteration += 1
        print(f"\n--- Agent Iteration {iteration} ---")
        
        # Build state snapshot
        state = build_state_snapshot(current_schedule, data, current_metrics, precomp)
        
        # Build prompt
        prompt = build_optimization_prompt(state, config)
        
        # Call LLM
        try:
            print("Calling LLM...")
            llm_start = datetime.now()
            response_dict = llm_client.call_structured(prompt)
            llm_time = (datetime.now() - llm_start).total_seconds()
            print(f"LLM responded in {llm_time:.2f}s")
            
            # Parse proposals
            candidates = parse_proposal(response_dict)
            print(f"Received {len(candidates)} valid candidates")
            
            if not candidates:
                print("No valid candidates, stopping")
                break
            
            # Evaluate each candidate
            best_candidate = None
            best_candidate_schedule = None
            best_candidate_objective = best_objective
            
            for candidate in candidates:
                print(f"\nEvaluating candidate {candidate['id']}: {candidate.get('rationale', '')}")
                
                # Apply candidate
                new_schedule, success = apply_candidate(current_schedule, candidate, data, precomp)
                
                if not success:
                    print("  ✗ Failed to apply moves")
                    agent_log.append({
                        'iteration': iteration,
                        'candidate_id': candidate['id'],
                        'status': 'apply_failed',
                        'llm_time': llm_time,
                    })
                    continue
                
                # Validate
                is_valid, violations = validate_schedule(new_schedule, data)
                
                if not is_valid:
                    print(f"  ✗ Validation failed: {len(violations)} violations")
                    agent_log.append({
                        'iteration': iteration,
                        'candidate_id': candidate['id'],
                        'status': 'validation_failed',
                        'violations': violations[:3],  # First 3
                        'llm_time': llm_time,
                    })
                    continue
                
                # Compute metrics
                new_result = {'schedule': new_schedule, 'unassigned': current_result['unassigned']}
                new_metrics = compute_metrics(new_result, data, precomp, config)
                new_objective = new_metrics['objective']
                
                delta = new_objective - best_objective
                print(f"  Objective: {new_objective:.2f} (Δ = {delta:.2f})")
                
                if new_objective < best_candidate_objective:
                    best_candidate = candidate
                    best_candidate_schedule = new_schedule
                    best_candidate_objective = new_objective
            
            # Accept best candidate if it improves
            if best_candidate and best_candidate_objective < best_objective:
                improvement = best_objective - best_candidate_objective
                print(f"\n✓ Accepting candidate {best_candidate['id']} (improvement: {improvement:.2f})")
                
                current_schedule = best_candidate_schedule
                current_result['schedule'] = current_schedule
                current_metrics = compute_metrics(current_result, data, precomp, config)
                best_objective = current_metrics['objective']
                
                agent_log.append({
                    'iteration': iteration,
                    'candidate_id': best_candidate['id'],
                    'status': 'accepted',
                    'objective': best_objective,
                    'improvement': improvement,
                    'llm_time': llm_time,
                })
            else:
                print("\n✗ No improving candidates found")
                agent_log.append({
                    'iteration': iteration,
                    'status': 'no_improvement',
                    'llm_time': llm_time,
                })
                break  # Stop if no improvement
                
        except Exception as e:
            print(f"✗ Error in agent iteration: {e}")
            agent_log.append({
                'iteration': iteration,
                'status': 'error',
                'error': str(e),
            })
            break
    
    total_time = (datetime.now() - start_time).total_seconds()
    print(f"\n✓ Agent completed in {total_time:.2f}s after {iteration} iterations")
    print(f"Final objective: {best_objective:.2f}")
    
    return {
        'schedule': current_schedule,
        'unassigned': current_result['unassigned'],
        'metrics': current_metrics,
        'agent_log': agent_log,
        'total_time': total_time,
        'iterations': iteration,
    }


def main():
    parser = argparse.ArgumentParser(description='Agent controller')
    parser.add_argument('--inputs', default='inputs/', help='Input directory')
    parser.add_argument('--output', default='outputs/', help='Output directory')
    parser.add_argument('--config', default='config.yaml', help='Config file')
    parser.add_argument('--mode', default='ollama', help='LLM mode: ollama, mock, llama_cpp, vllm')
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("Loading data...")
    data = load_all(args.inputs)
    config = load_config(args.config)
    
    print("Precomputing...")
    precomp = precompute_all(data, config)
    
    result = agent_optimize(data, precomp, config, mode=args.mode)
    
    # Write outputs
    print(f"\nWriting outputs to {args.output}...")
    
    with open(output_path / 'schedule_agent.json', 'w') as f:
        json.dump(result['schedule'], f, indent=2)
    
    with open(output_path / 'agent_log.json', 'w') as f:
        json.dump(result['agent_log'], f, indent=2)
    
    with open(output_path / 'agent_metrics.json', 'w') as f:
        json.dump({
            'final_objective': result['metrics']['objective'],
            'total_time': result['total_time'],
            'iterations': result['iterations'],
            'num_assigned': result['metrics']['num_assigned'],
            'num_unassigned': result['metrics']['num_unassigned'],
        }, f, indent=2)
    
    print("✓ Done!")


if __name__ == "__main__":
    main()
