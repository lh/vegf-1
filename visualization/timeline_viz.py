"""Visualization tools for patient treatment timelines.

This module provides functions to create and display ASCII-based timelines
of patient treatment histories, showing visits, injections, and treatment gaps.

The timeline visualization helps analyze treatment patterns and adherence.
"""
from datetime import datetime, timedelta
from typing import List, Dict

def create_timeline(history: List[Dict], start_date: datetime, end_date: datetime) -> str:
    """Create an ASCII timeline visualization of patient treatment history.

    Parameters
    ----------
    history : List[Dict]
        List of visit dictionaries containing:
        - date: datetime of visit
        - actions: list of actions performed (e.g. ['injection', 'assessment'])
    start_date : datetime
        Start date for the timeline
    end_date : datetime
        End date for the timeline

    Returns
    -------
    str
        ASCII timeline string with symbols representing treatment events:
        | = visit without injection
        x = visit with injection 
        . = week without visit
        o = treatment stopped
        [N] = week counter every 4 weeks

    Examples
    --------
    >>> history = [
    ...     {'date': datetime(2023,1,1), 'actions': ['injection']},
    ...     {'date': datetime(2023,1,15), 'actions': ['assessment']}
    ... ]
    >>> create_timeline(history, datetime(2023,1,1), datetime(2023,2,1))
    'x..|[4]'
    """
    timeline = ""
    current_date = start_date
    week_count = 0
    
    # Convert history to dict keyed by date for easier lookup
    # Round dates to nearest day to avoid time comparison issues
    visit_map = {}
    for visit in history:
        visit_date = visit['date'].replace(hour=0, minute=0, second=0, microsecond=0)
        visit_map[visit_date.date()] = visit
    
    while current_date <= end_date:
        current_day = current_date.date()
        if current_day in visit_map:
            visit = visit_map[current_day]
            if 'injection' in visit.get('actions', []):
                timeline += "x"
            else:
                timeline += "|"
        else:
            timeline += "."
            
        current_date += timedelta(weeks=1)
        week_count += 1
        
        # Add week counter every 4 weeks
        if week_count % 4 == 0:
            timeline += f"[{week_count}]"
            
    return timeline

def print_patient_timeline(patient_id: str, history: List[Dict], 
                         start_date: datetime, end_date: datetime):
    """Print a formatted timeline visualization for a patient's treatment history.

    Parameters
    ----------
    patient_id : str
        Unique identifier for the patient
    history : List[Dict]
        List of visit dictionaries (see create_timeline for format)
    start_date : datetime
        Start date for the timeline
    end_date : datetime
        End date for the timeline

    Notes
    -----
    The printed output includes:
    - Patient identifier header
    - Legend explaining the timeline symbols
    - The generated ASCII timeline
    - Horizontal rules for visual separation
    """
    timeline = create_timeline(history, start_date, end_date)
    
    print(f"\nTimeline for Patient {patient_id}:")
    print("=" * 80)
    print("Legend: x=injection, |=visit, .=no visit, o=stopped")
    print("-" * 80)
    print(timeline)
    print("-" * 80)
