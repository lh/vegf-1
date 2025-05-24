"""
Fix the date handling in the streamgraph_patient_states.py file.
This creates a fixed implementation that correctly handles epoch timestamps.
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

def convert_timestamp_to_months(timestamp, start_date=None):
    """
    Convert timestamp to months from the start date.
    
    Args:
        timestamp: Timestamp in nanoseconds epoch format (as seen in the data)
        start_date: Optional start date as a reference point. If None, uses the
                    timestamp itself converted to datetime
    
    Returns:
        Relative months (int)
    """
    # Convert nanosecond timestamp to datetime
    if isinstance(timestamp, (int, float)) and timestamp > 1e18:  # Nanosecond timestamp
        dt = pd.to_datetime(timestamp, unit='ns')
    elif isinstance(timestamp, (int, float)):
        dt = pd.to_datetime(timestamp, unit='s')
    else:
        dt = pd.to_datetime(timestamp)
    
    # If no start date, use the timestamp itself
    if start_date is None:
        return 0
    
    # Calculate months between dates
    if isinstance(start_date, (int, float)):
        start_date = pd.to_datetime(start_date, unit='ns' if start_date > 1e18 else 's')
    elif not isinstance(start_date, (datetime, pd.Timestamp)):
        start_date = pd.to_datetime(start_date)
    
    # Calculate difference in days and convert to months
    days_diff = (dt - start_date).days
    months_diff = int(days_diff / 30)
    
    return months_diff

def fix_aggregation_function():
    """Create an enhanced version of aggregate_states_by_month that handles epoch timestamps"""
    
    original_content = """
    # First, ensure time_months column is numeric
    if 'time_months' not in patient_states_df.columns or patient_states_df['time_months'].dtype == 'object':
        # Check if we have datetime objects in visit_time
        if 'visit_time' in patient_states_df.columns:
            sample = patient_states_df['visit_time'].iloc[0]
            if isinstance(sample, (datetime, pd.Timestamp)):
                # Find earliest date as reference
                min_date = patient_states_df['visit_time'].min()
                # Convert to months from start
                patient_states_df['time_months'] = patient_states_df['visit_time'].apply(
                    lambda x: int((x - min_date).days / 30)
                )
            else:
                # Use visit_time directly if it's already numeric
                patient_states_df['time_months'] = pd.to_numeric(patient_states_df['visit_time'], errors='coerce').fillna(0).astype(int)
    """
    
    fixed_content = """
    # First, ensure time_months column is numeric and correctly reflects months
    if 'visit_time' in patient_states_df.columns:
        # Get sample timestamps to determine format
        sample = patient_states_df['visit_time'].iloc[0]
        print(f"Sample timestamp: {sample}, type: {type(sample)}")
        
        # Find earliest date as reference
        min_date = patient_states_df['visit_time'].min()
        print(f"Min date: {min_date}, type: {type(min_date)}")
        
        # Convert timestamps to months from start - handle different formats
        if isinstance(sample, (int, float)) and sample > 1e18:  # Nanosecond epoch timestamp
            print("Detected nanosecond epoch timestamps")
            min_date_dt = pd.to_datetime(min_date, unit='ns')
            patient_states_df['time_months'] = patient_states_df['visit_time'].apply(
                lambda x: convert_timestamp_to_months(x, min_date)
            )
        elif isinstance(sample, (int, float)):  # Second epoch timestamp
            print("Detected second epoch timestamps")
            min_date_dt = pd.to_datetime(min_date, unit='s')
            patient_states_df['time_months'] = patient_states_df['visit_time'].apply(
                lambda x: int((pd.to_datetime(x, unit='s') - min_date_dt).days / 30)
            )
        elif isinstance(sample, (datetime, pd.Timestamp)):  # Already datetime
            print("Detected datetime objects")
            patient_states_df['time_months'] = patient_states_df['visit_time'].apply(
                lambda x: int((x - min_date).days / 30)
            )
        else:  # String dates or other formats
            print(f"Converting unknown timestamp format: {sample}")
            # Try to parse as datetime string
            min_date_dt = pd.to_datetime(min_date)
            patient_states_df['time_months'] = patient_states_df['visit_time'].apply(
                lambda x: int((pd.to_datetime(x) - min_date_dt).days / 30)
            )
        
        # Print some validation of the conversion
        print(f"First few time_months values: {patient_states_df['time_months'].head().tolist()}")
    """
    
    return {
        "original": original_content.strip(),
        "fixed": fixed_content.strip()
    }

def fix_streamgraph_state_file():
    """Create a patch for the streamgraph_patient_states.py file"""
    
    # Get file path
    file_path = "streamlit_app/streamgraph_patient_states.py"
    if not os.path.exists(file_path):
        print(f"Error: Could not find {file_path}")
        return False
    
    # Read content
    with open(file_path, "r") as f:
        content = f.read()
    
    # Get fixed function
    fixes = fix_aggregation_function()
    
    # Replace the problematic section
    if fixes["original"] in content:
        new_content = content.replace(fixes["original"], fixes["fixed"])
        
        # Add import for convert_timestamp_to_months function
        import_line = "from datetime import datetime, timedelta"
        timestamp_function = """
def convert_timestamp_to_months(timestamp, start_date=None):
    \"\"\"
    Convert timestamp to months from the start date.
    
    Args:
        timestamp: Timestamp in nanoseconds epoch format (as seen in the data)
        start_date: Optional start date as a reference point. If None, uses the
                    timestamp itself converted to datetime
    
    Returns:
        Relative months (int)
    \"\"\"
    # Convert nanosecond timestamp to datetime
    if isinstance(timestamp, (int, float)) and timestamp > 1e18:  # Nanosecond timestamp
        dt = pd.to_datetime(timestamp, unit='ns')
    elif isinstance(timestamp, (int, float)):
        dt = pd.to_datetime(timestamp, unit='s')
    else:
        dt = pd.to_datetime(timestamp)
    
    # If no start date, use the timestamp itself
    if start_date is None:
        return 0
    
    # Calculate months between dates
    if isinstance(start_date, (int, float)):
        start_date = pd.to_datetime(start_date, unit='ns' if start_date > 1e18 else 's')
    elif not isinstance(start_date, (datetime, pd.Timestamp)):
        start_date = pd.to_datetime(start_date)
    
    # Calculate difference in days and convert to months
    days_diff = (dt - start_date).days
    months_diff = int(days_diff / 30)
    
    return months_diff
"""
        
        # Add function after imports
        new_content = new_content.replace(import_line, import_line + "\n\n" + timestamp_function)
        
        # Write fixed file
        fixed_path = "streamlit_app/streamgraph_patient_states_fixed.py"
        with open(fixed_path, "w") as f:
            f.write(new_content)
        
        print(f"Fixed file written to {fixed_path}")
        return True
    else:
        print("Could not find the section to fix")
        return False

if __name__ == "__main__":
    if fix_streamgraph_state_file():
        print("Success! Fixed the date handling in streamgraph_patient_states.py")
    else:
        print("Failed to fix the file")