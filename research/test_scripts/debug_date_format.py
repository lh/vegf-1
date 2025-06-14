#!/usr/bin/env python3
"""Debug date format issue"""
import pandas as pd

# Test the exact date format from the error
date_str = "2025-02-25 02:00:00"

print(f"Date string: {date_str}")
print(f"Type: {type(date_str)}")
print(f"Is string: {isinstance(date_str, str)}")

try:
    parsed = pd.to_datetime(date_str)
    print(f"Successfully parsed: {parsed}")
    print(f"Type after parsing: {type(parsed)}")
except Exception as e:
    print(f"Failed to parse: {e}")
    import traceback
    traceback.print_exc()

# Also test if the datetime format works
import datetime
try:
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    print(f"Successfully parsed with strptime: {dt}")
except Exception as e:
    print(f"Failed with strptime: {e}")