"""
CSV utilities for parsing custom fields
"""

import pandas as pd
from typing import List


def parse_comma_separated_list(value: str) -> List[str]:
    """Parse comma-separated string into list"""
    if pd.isna(value) or value == '':
        return []
    return [item.strip() for item in value.split(',')]


def parse_iso_datetime_list(value: str) -> List[str]:
    """Parse comma-separated ISO datetime strings"""
    if pd.isna(value) or value == '':
        return []
    return [dt.strip() for dt in value.split(',')]


def format_list_for_csv(items: List[str]) -> str:
    """Format list as comma-separated string for CSV"""
    return ','.join(str(item) for item in items)
