#!/usr/bin/env python3
"""
Analyze the wAMD cost calculator Excel file to understand protocols.
This is a temporary analysis file - results will be summarized but not committed.
"""

import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_cost_calculator():
    """Extract and analyze protocol information from the cost calculator."""
    
    file_path = "docs/literature/wAMD cost calculator v1.0 FINAL.xlsx"
    
    try:
        # Read all sheets to understand structure
        excel_file = pd.ExcelFile(file_path)
        print("Available sheets:")
        for sheet in excel_file.sheet_names:
            print(f"  - {sheet}")
        print()
        
        # Look for protocol-related sheets
        protocol_sheets = [s for s in excel_file.sheet_names 
                          if any(keyword in s.lower() for keyword in 
                                ['protocol', 'treatment', 'regime', 'pathway', 'schedule'])]
        
        if protocol_sheets:
            print("Protocol-related sheets found:")
            for sheet in protocol_sheets:
                print(f"\n=== Sheet: {sheet} ===")
                df = pd.read_excel(file_path, sheet_name=sheet)
                print(f"Shape: {df.shape}")
                print(f"Columns: {list(df.columns)}")
                
                # Show first few rows if not too wide
                if df.shape[1] < 10:
                    print("\nFirst 5 rows:")
                    print(df.head())
        
        # Try to read specific sheets that might contain protocol info
        common_sheet_names = ['Summary', 'Model', 'Parameters', 'Inputs', 'Assumptions', 
                            'Protocols', 'Treatment', 'Costs', 'Results']
        
        for sheet_name in common_sheet_names:
            if sheet_name in excel_file.sheet_names:
                print(f"\n=== {sheet_name} Sheet ===")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Look for protocol-related content
                protocol_keywords = ['interval', 'weeks', 'months', 'injection', 'visit', 
                                   'monitoring', 'loading', 'maintenance', 'TAE', 'T&E', 
                                   'PRN', 'fixed', 'treat', 'extend']
                
                # Check column names
                relevant_cols = [col for col in df.columns 
                               if any(kw in str(col).lower() for kw in protocol_keywords)]
                
                if relevant_cols:
                    print(f"Protocol-related columns: {relevant_cols}")
                    for col in relevant_cols[:5]:  # Show first 5 relevant columns
                        print(f"\n{col}:")
                        print(df[col].dropna().head(10))
                
                # Check for protocol descriptions in cells
                for col in df.columns:
                    if df[col].dtype == 'object':  # Text columns
                        mask = df[col].astype(str).str.contains('|'.join(protocol_keywords), 
                                                               case=False, na=False)
                        if mask.any():
                            print(f"\nProtocol mentions in column '{col}':")
                            print(df[mask][col].head(5))
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        print("\nTrying alternative approach...")
        
        # Try reading just the first sheet
        try:
            df = pd.read_excel(file_path)
            print(f"\nFirst sheet shape: {df.shape}")
            print(f"Columns: {list(df.columns)[:10]}...")  # First 10 columns
            
        except Exception as e2:
            print(f"Alternative approach also failed: {e2}")


if __name__ == "__main__":
    analyze_cost_calculator()