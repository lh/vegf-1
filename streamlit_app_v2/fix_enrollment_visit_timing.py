#!/usr/bin/env python3
"""
Fix for enrollment visit timing issue.

Problem: First visits can appear to happen before enrollment because:
1. Patient enrolls at specific time (e.g., 2:30 PM)
2. Visit is scheduled for enrollment datetime
3. Visits are processed at start of day (midnight)
4. This makes visit appear to be before enrollment

Solution: Schedule first visit for start of next day after enrollment.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))


def show_fix_locations():
    """Show where to apply the fix."""
    
    print("FIX REQUIRED in simulation_v2/engines/abs_engine.py")
    print("=" * 60)
    print("\nCurrent code (line ~206):")
    print("```python")
    print("# Schedule initial visit on arrival day")
    print("visit_schedule[patient_id] = arrival_date")
    print("```")
    print("\nShould be changed to:")
    print("```python")
    print("# Schedule initial visit for start of day after enrollment")
    print("# This ensures visit happens after enrollment time")
    print("next_day = arrival_date.date() + timedelta(days=1)")
    print("visit_schedule[patient_id] = datetime.combine(next_day, datetime.min.time())")
    print("```")
    print("\nAlternative fix (same day, but at end):")
    print("```python")
    print("# Schedule initial visit for end of enrollment day")
    print("# This keeps visit on same day but ensures it's after enrollment")
    print("visit_schedule[patient_id] = datetime.combine(arrival_date.date(), datetime.max.time())")
    print("```")
    
    print("\n" + "=" * 60)
    print("Similar fix needed in des_engine.py as well")
    print("=" * 60)


if __name__ == "__main__":
    show_fix_locations()