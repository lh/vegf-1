"""
Type definitions for Parquet writer to ensure strict type consistency.

Key principles:
- Dates are ALWAYS stored as datetime objects
- Time deltas are ALWAYS stored as int (days)
- No mixing of formats or implicit conversions
"""

from typing import TypedDict, Optional, Any
from datetime import datetime


class PatientRecord(TypedDict):
    """Strict type definition for patient records."""
    patient_id: str
    enrollment_date: datetime  # MUST be datetime
    enrollment_time_days: int  # Days from simulation start
    baseline_vision: int
    final_vision: int
    final_disease_state: str
    total_injections: int
    total_visits: int
    discontinued: bool
    discontinuation_time: Optional[int]  # Days from simulation start, if discontinued
    discontinuation_type: Optional[str]
    discontinuation_reason: Optional[str]
    pre_discontinuation_vision: Optional[float]
    retreatment_count: int


class VisitRecord(TypedDict):
    """Strict type definition for visit records."""
    patient_id: str
    date: datetime  # MUST be datetime
    time_days: int  # Days from patient enrollment
    vision: int
    injected: bool
    next_interval_days: Optional[int]
    disease_state: str


# Type checking helpers
def ensure_datetime(value: Any, field_name: str) -> datetime:
    """Ensure a value is a datetime object."""
    if not isinstance(value, datetime):
        raise TypeError(
            f"{field_name} must be a datetime object, got {type(value).__name__}: {value}"
        )
    return value


def ensure_int_days(timedelta_seconds: float, field_name: str) -> int:
    """Convert timedelta seconds to integer days with validation."""
    days = timedelta_seconds / (24 * 3600)
    if days < 0:
        raise ValueError(f"{field_name} cannot be negative: {days} days")
    return int(days)