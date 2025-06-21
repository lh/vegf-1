#!/usr/bin/env python3
"""
Analyze the wAMD cost calculator Excel file with better handling of merged cells.
"""

import pandas as pd
import numpy as np

def analyze_treatment_assumptions():
    """Focus on the treatment assumptions sheet which likely contains protocol info."""
    
    file_path = "docs/literature/wAMD cost calculator v1.0 FINAL.xlsx"
    
    # Read the treatment assumptions sheet with different header options
    print("=== Analyzing Treatment Assumptions Sheet ===\n")
    
    # Try reading with different header rows
    for header_row in [0, 1, 2, 3, 4, 5]:
        try:
            df = pd.read_excel(file_path, sheet_name='4- Treatment assumptions', 
                             header=header_row)
            
            # Skip if all columns are unnamed
            if all('Unnamed' in str(col) for col in df.columns):
                continue
                
            print(f"\nReading with header at row {header_row}:")
            print(f"Columns: {list(df.columns)}")
            print(f"Shape: {df.shape}")
            
            # Look for non-null data
            non_null_mask = df.notna().any(axis=1)
            if non_null_mask.any():
                print("\nFirst few rows with data:")
                print(df[non_null_mask].head(10))
                
        except Exception as e:
            continue
    
    # Also try reading without header to see raw data
    print("\n\n=== Raw data (no header) ===")
    df_raw = pd.read_excel(file_path, sheet_name='4- Treatment assumptions', header=None)
    
    # Find rows with actual content
    for idx, row in df_raw.iterrows():
        if idx > 30:  # Limit search
            break
        
        # Check if row has meaningful content
        row_values = row.dropna().values
        if len(row_values) > 0:
            # Look for protocol-related terms
            row_str = ' '.join(str(v) for v in row_values).lower()
            if any(term in row_str for term in ['protocol', 'interval', 'week', 'month', 
                                               'injection', 'tae', 't&e', 'prn', 'treat']):
                print(f"\nRow {idx}: {list(row_values)}")
    
    # Try the workings sheet which might have formulas
    print("\n\n=== Analyzing Workings Sheet ===")
    try:
        df_work = pd.read_excel(file_path, sheet_name='workings >', header=None)
        
        # Look for protocol patterns
        for idx, row in df_work.iterrows():
            if idx > 50:
                break
            
            row_values = row.dropna().values
            if len(row_values) > 0:
                row_str = ' '.join(str(v) for v in row_values).lower()
                if any(term in row_str for term in ['protocol', 'interval', 'regimen', 
                                                   'treatment', 'schedule']):
                    print(f"\nRow {idx}: {list(row_values)[:5]}...")  # First 5 values
                    
    except Exception as e:
        print(f"Error reading workings sheet: {e}")
    
    # Check the wetAMD sheets
    for sheet_suffix in ['injections', 'scans', 'consultations', 'cost calculator']:
        sheet_name = f'wetAMD {sheet_suffix}'
        if sheet_suffix == 'cost calculator':
            sheet_name = 'wetAMD cost calculator'
            
        print(f"\n\n=== Analyzing {sheet_name} ===")
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=20)
            
            for idx, row in df.iterrows():
                row_values = row.dropna().values
                if len(row_values) > 0:
                    print(f"Row {idx}: {list(row_values)[:6]}...")  # First 6 values
                    
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    analyze_treatment_assumptions()