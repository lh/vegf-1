#!/usr/bin/env python3
"""
Search for outcomes data and assumptions in the cost calculator.
"""

import pandas as pd
import numpy as np

def search_for_outcomes():
    """Look for vision outcomes, QALY assumptions, or effectiveness data."""
    
    file_path = "docs/literature/wAMD cost calculator v1.0 FINAL.xlsx"
    
    # Keywords related to outcomes
    outcome_keywords = ['vision', 'visual', 'acuity', 'bcva', 'etdrs', 'letters', 
                       'qaly', 'quality', 'life', 'utility', 'effectiveness', 
                       'efficacy', 'outcome', 'gain', 'loss', 'improvement',
                       'maintenance', 'decline', 'response', 'success', 'failure']
    
    # Read all sheets
    excel_file = pd.ExcelFile(file_path)
    
    print("=== Searching for Outcomes Data ===\n")
    
    for sheet_name in excel_file.sheet_names:
        # Skip sheets we already analyzed
        if sheet_name in ['1- Cover', '2- Contents']:
            continue
            
        try:
            # Read without header to see all data
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            # Search for outcome-related content
            found_outcomes = False
            
            for idx, row in df.iterrows():
                row_values = row.dropna().values
                if len(row_values) > 0:
                    row_str = ' '.join(str(v) for v in row_values).lower()
                    
                    # Check if any outcome keyword is present
                    if any(keyword in row_str for keyword in outcome_keywords):
                        if not found_outcomes:
                            print(f"\n=== Sheet: {sheet_name} ===")
                            found_outcomes = True
                        
                        # Print the row if it's not too long
                        if len(row_values) <= 10:
                            print(f"Row {idx}: {list(row_values)}")
                        else:
                            print(f"Row {idx}: {list(row_values[:10])}... [{len(row_values)} values]")
                        
                        # Check surrounding rows for context
                        if idx > 0:
                            prev_row = df.iloc[idx-1].dropna().values
                            if len(prev_row) > 0 and len(prev_row) <= 10:
                                print(f"  (prev): {list(prev_row)}")
                        
                        if idx < len(df) - 1:
                            next_row = df.iloc[idx+1].dropna().values
                            if len(next_row) > 0 and len(next_row) <= 10:
                                print(f"  (next): {list(next_row)}")
                
                # Stop after checking first 100 rows per sheet
                if idx > 100:
                    break
                    
        except Exception as e:
            print(f"Error reading sheet {sheet_name}: {e}")
    
    # Also check specifically for assumptions in key sheets
    print("\n\n=== Checking Unit Costs Sheet for Assumptions ===")
    try:
        df = pd.read_excel(file_path, sheet_name='3 - Unit costs', header=None, nrows=50)
        for idx, row in df.iterrows():
            row_values = row.dropna().values
            if len(row_values) > 0:
                row_str = ' '.join(str(v) for v in row_values).lower()
                if any(term in row_str for term in ['assumption', 'assume', 'based on', 'source', 'reference']):
                    print(f"Row {idx}: {list(row_values)[:8]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Check summary sheet which might have overall assumptions
    print("\n\n=== Checking Summary Sheet ===")
    try:
        df = pd.read_excel(file_path, sheet_name='7- Summary', header=None, nrows=50)
        for idx, row in df.iterrows():
            row_values = row.dropna().values
            if len(row_values) > 0 and len(row_values) < 15:
                print(f"Row {idx}: {list(row_values)}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    search_for_outcomes()