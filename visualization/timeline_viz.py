from datetime import datetime, timedelta
from typing import List, Dict

def create_timeline(history: List[Dict], start_date: datetime, end_date: datetime) -> str:
    """Create a simple ASCII timeline visualization of patient treatment history
    
    Symbols:
    | = visit without injection
    x = visit with injection
    . = week without visit
    o = treatment stopped
    """
    timeline = ""
    current_date = start_date
    week_count = 0
    
    # Convert history to dict keyed by date for easier lookup
    visit_map = {visit['date']: visit for visit in history}
    
    while current_date <= end_date:
        if current_date in visit_map:
            visit = visit_map[current_date]
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
    """Print a formatted timeline for a patient"""
    timeline = create_timeline(history, start_date, end_date)
    
    print(f"\nTimeline for Patient {patient_id}:")
    print("=" * 80)
    print("Legend: x=injection, |=visit, .=no visit, o=stopped")
    print("-" * 80)
    print(timeline)
    print("-" * 80)
