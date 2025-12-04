"""
JSON schemas and validation for agent proposals
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator


class SwapBerthMove(BaseModel):
    """Swap two ships' berth assignments"""
    type: str = Field(default="swap_berth")
    ship_a: str
    ship_b: str


class DelayShipMove(BaseModel):
    """Delay a ship's start time"""
    type: str = Field(default="delay_ship")
    ship: str
    delay_minutes: int
    
    @validator('delay_minutes')
    def delay_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('delay_minutes must be positive')
        return v


class ReassignBerthMove(BaseModel):
    """Reassign ship to different berth"""
    type: str = Field(default="reassign_berth")
    ship: str
    new_berth: str


class AdvanceShipMove(BaseModel):
    """Advance a ship's start time (if possible)"""
    type: str = Field(default="advance_ship")
    ship: str
    advance_minutes: int
    
    @validator('advance_minutes')
    def advance_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('advance_minutes must be positive')
        return v


class Candidate(BaseModel):
    """A candidate schedule modification"""
    id: str
    moves: List[Dict[str, Any]]
    rationale: str
    expected_delta_estimate: float


class ProposalResponse(BaseModel):
    """Response from LLM with candidate proposals"""
    candidates: List[Candidate]


def validate_move(move: Dict[str, Any]) -> bool:
    """
    Validate a move dictionary
    
    Args:
        move: Move dictionary
        
    Returns:
        True if valid
    """
    move_type = move.get('type')
    
    if move_type == 'swap_berth':
        return 'ship_a' in move and 'ship_b' in move
    elif move_type == 'delay_ship':
        return 'ship' in move and 'delay_minutes' in move and move['delay_minutes'] > 0
    elif move_type == 'reassign_berth':
        return 'ship' in move and 'new_berth' in move
    elif move_type == 'advance_ship':
        return 'ship' in move and 'advance_minutes' in move and move['advance_minutes'] > 0
    else:
        return False


def validate_candidate(candidate: Dict[str, Any]) -> bool:
    """
    Validate a candidate dictionary
    
    Args:
        candidate: Candidate dictionary
        
    Returns:
        True if valid
    """
    if 'id' not in candidate or 'moves' not in candidate:
        return False
    
    if not isinstance(candidate['moves'], list):
        return False
    
    for move in candidate['moves']:
        if not validate_move(move):
            return False
    
    return True


def parse_proposal(response_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse and validate LLM proposal response
    
    Args:
        response_dict: Parsed JSON from LLM
        
    Returns:
        List of valid candidates
    """
    if 'candidates' not in response_dict:
        return []
    
    valid_candidates = []
    for candidate in response_dict['candidates']:
        if validate_candidate(candidate):
            valid_candidates.append(candidate)
    
    return valid_candidates


# Example schema for LLM prompt
PROPOSAL_SCHEMA = """
{
  "candidates": [
    {
      "id": "C1",
      "moves": [
        {"type": "swap_berth", "ship_a": "S001", "ship_b": "S003"},
        {"type": "delay_ship", "ship": "S002", "delay_minutes": 120}
      ],
      "rationale": "Short explanation of why this improves the schedule",
      "expected_delta_estimate": -1234.56
    }
  ]
}
"""

MOVE_TYPES = """
Available move types:
1. swap_berth: {"type": "swap_berth", "ship_a": "S001", "ship_b": "S002"}
2. delay_ship: {"type": "delay_ship", "ship": "S001", "delay_minutes": 60}
3. reassign_berth: {"type": "reassign_berth", "ship": "S001", "new_berth": "B002"}
4. advance_ship: {"type": "advance_ship", "ship": "S001", "advance_minutes": 30}
"""


if __name__ == "__main__":
    # Test validation
    test_candidate = {
        "id": "C1",
        "moves": [
            {"type": "delay_ship", "ship": "S001", "delay_minutes": 60}
        ],
        "rationale": "Reduce waiting time",
        "expected_delta_estimate": -500.0
    }
    
    print("Testing candidate validation...")
    is_valid = validate_candidate(test_candidate)
    print(f"Valid: {is_valid}")
    
    test_response = {
        "candidates": [test_candidate]
    }
    
    candidates = parse_proposal(test_response)
    print(f"Parsed {len(candidates)} valid candidates")
