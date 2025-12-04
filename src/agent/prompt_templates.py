"""
Prompt templates for LLM agent
"""

from typing import Dict, List, Any
import json


def build_state_snapshot(schedule: List[Dict], data: Dict[str, Any],
                         metrics: Dict[str, Any], precomp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build state snapshot for LLM
    
    Args:
        schedule: Current schedule
        data: Loaded data
        metrics: Current metrics
        precomp: Precomputed structures
        
    Returns:
        State dictionary
    """
    ships_data = []
    for _, ship in data['ships'].iterrows():
        ships_data.append({
            'ship_id': ship['ship_id'],
            'eta_iso': ship['eta_iso'].isoformat(),
            'cargo_type': ship['cargo_type'],
            'cargo_tonnes': int(ship['cargo_tonnes']),
            'priority': ship['priority'],
        })
    
    berths_data = []
    for _, berth in data['berths'].iterrows():
        berths_data.append({
            'berth_id': berth['berth_id'],
            'max_loa_meters': float(berth['max_loa_meters']),
            'allowed_cargo_types': berth['allowed_cargo_types'],
            'hourly_cost': float(berth['hourly_cost']),
        })
    
    return {
        'ships': ships_data,
        'berths': berths_data,
        'current_schedule': schedule,
        'metrics': {
            'objective': metrics['objective'],
            'total_cost': metrics['total_cost'],
            'total_delay_hours': metrics['total_delay_hours'],
            'num_assigned': metrics['num_assigned'],
            'num_unassigned': metrics['num_unassigned'],
        }
    }


def build_optimization_prompt(state: Dict[str, Any], config: Dict[str, Any]) -> str:
    """
    Build optimization prompt for LLM
    
    Args:
        state: State snapshot
        config: Configuration
        
    Returns:
        Prompt string
    """
    max_candidates = config.get('agent', {}).get('max_candidates_per_iteration', 3)
    weights = config.get('objective_weights', {})
    
    prompt = f"""You are an optimization assistant for a port and rail scheduler.

CURRENT STATE:
{json.dumps(state, indent=2)}

OBJECTIVE:
Minimize: total_cost + {weights.get('delay', 0.5)} * delay_penalty + {weights.get('delivery_violation', 2.0)} * delivery_violation

TASK:
Propose up to {max_candidates} candidate schedule modifications that improve the objective.
Each candidate should contain one or more moves that work together.

AVAILABLE MOVE TYPES:
1. swap_berth: Swap berth assignments of two ships
   {{"type": "swap_berth", "ship_a": "S001", "ship_b": "S002"}}

2. delay_ship: Delay a ship's start time
   {{"type": "delay_ship", "ship": "S001", "delay_minutes": 60}}

3. reassign_berth: Assign ship to a different berth
   {{"type": "reassign_berth", "ship": "S001", "new_berth": "B002"}}

4. advance_ship: Start a ship earlier (if possible)
   {{"type": "advance_ship", "ship": "S001", "advance_minutes": 30}}

OUTPUT FORMAT (JSON only, no commentary):
{{
  "candidates": [
    {{
      "id": "C1",
      "moves": [
        {{"type": "delay_ship", "ship": "S002", "delay_minutes": 120}}
      ],
      "rationale": "Brief one-liner explaining the improvement",
      "expected_delta_estimate": -500.0
    }}
  ]
}}

IMPORTANT:
- Return ONLY valid JSON
- expected_delta_estimate should be negative for improvements
- Consider berth compatibility and ship priorities
- Focus on reducing delays and costs

Return your response now:"""
    
    return prompt


def build_simple_prompt(state_summary: str, max_candidates: int = 3) -> str:
    """
    Build a simpler prompt for faster inference
    
    Args:
        state_summary: Brief summary of current state
        max_candidates: Max candidates to generate
        
    Returns:
        Prompt string
    """
    prompt = f"""Port scheduler optimization task.

Current state: {state_summary}

Suggest up to {max_candidates} schedule improvements as JSON:
{{
  "candidates": [
    {{
      "id": "C1",
      "moves": [{{"type": "delay_ship", "ship": "S001", "delay_minutes": 60}}],
      "rationale": "Reason",
      "expected_delta_estimate": -100.0
    }}
  ]
}}

Move types: swap_berth, delay_ship, reassign_berth, advance_ship
Return JSON only:"""
    
    return prompt


if __name__ == "__main__":
    # Test prompt building
    test_state = {
        'ships': [
            {'ship_id': 'S001', 'eta_iso': '2025-12-05T06:00:00Z', 'cargo_type': 'iron_ore', 
             'cargo_tonnes': 75000, 'priority': 'high'}
        ],
        'berths': [
            {'berth_id': 'B001', 'max_loa_meters': 320, 'allowed_cargo_types': 'iron_ore,coal',
             'hourly_cost': 1200}
        ],
        'current_schedule': [
            {'ship_id': 'S001', 'berth_id': 'B001', 'start_slot': 10, 'end_slot': 26}
        ],
        'metrics': {
            'objective': 15000,
            'total_cost': 12000,
            'total_delay_hours': 2.5,
            'num_assigned': 1,
            'num_unassigned': 0,
        }
    }
    
    config = {
        'objective_weights': {'cost': 1.0, 'delay': 0.5, 'delivery_violation': 2.0},
        'agent': {'max_candidates_per_iteration': 3}
    }
    
    prompt = build_optimization_prompt(test_state, config)
    print("Generated prompt:")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    print(f"Prompt length: {len(prompt)} characters")
