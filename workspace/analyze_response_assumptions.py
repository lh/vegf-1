#!/usr/bin/env python3
"""
Focus on the response rate assumptions found in the cost calculator.
"""

import pandas as pd

def analyze_response_assumptions():
    """Extract the response rate assumptions and their implications."""
    
    file_path = "docs/literature/wAMD cost calculator v1.0 FINAL.xlsx"
    
    print("=== Response Rate Assumptions ===\n")
    
    # From the treatment assumptions sheet
    print("From Treatment Assumptions Sheet:")
    print("- Optimal response/stable disease: 60%")
    print("- Suboptimal response/unstable disease: 40%")
    print("\nThis 60/40 split appears consistent across all drugs:")
    print("- Ranibizumab: 60% optimal")
    print("- Aflibercept 2mg: 60% optimal")
    print("- Faricimab: 60% optimal") 
    print("- Aflibercept 8mg: 60% optimal")
    
    # Check if there are different injection patterns by response
    print("\n\n=== Checking Injection Patterns by Response ===")
    
    # Read the cost summary sheet to see if different responses have different costs
    df = pd.read_excel(file_path, sheet_name='wetAMD cost summary', header=None, nrows=60)
    
    print("\nFrom Cost Summary Sheet:")
    
    # Look for patterns around row 45 where we saw response categories
    for idx in range(40, 55):
        try:
            row = df.iloc[idx]
            row_values = row.dropna().values
            if len(row_values) > 0:
                row_str = str(row_values[0]).lower() if len(row_values) > 0 else ""
                if any(term in row_str for term in ['optimal', 'sub-optimal', 'response', 'disease activity', 'case split']):
                    print(f"\nRow {idx}: {list(row_values)[:8]}...")
                    
                    # Check if there are cost differences
                    if 'cost year' in str(row_values) or any(isinstance(v, (int, float)) and v > 1000 for v in row_values[1:]):
                        print("  → Shows different costs by response type")
        except:
            continue
    
    # Try to understand the treatment patterns
    print("\n\n=== Treatment Pattern Implications ===")
    
    # Read the injections workings
    df_inj = pd.read_excel(file_path, sheet_name='wetAMD injections', header=None, nrows=30)
    
    print("\nFrom Injections Sheet:")
    print("- Shows 'no disease activity' uses treat-and-extend")
    print("- Shows 'disease activity' uses fixed intervals:")
    print("  - Ranibizumab: 4 weeks")
    print("  - Others: 8 weeks")
    
    print("\n\n=== INTERPRETATION ===")
    print("""
The cost calculator appears to model TWO response groups:

1. OPTIMAL RESPONSE (60% of patients):
   - "No disease activity" / "Stable disease"
   - Follows treat-and-extend protocol
   - Can extend intervals up to maximum
   - Lower injection frequency over time
   
2. SUBOPTIMAL RESPONSE (40% of patients):  
   - "Disease activity" / "Unstable disease"
   - Maintains fixed short intervals
   - Ranibizumab: q4 weeks
   - Others: q8 weeks
   - Higher injection frequency maintained

This is a simplified model compared to clinical reality where:
- Patients can move between states
- There's a spectrum of response, not just binary
- Some patients discontinue treatment
- Vision outcomes aren't explicitly modeled

The 60/40 split suggests that in the real world:
- Only 60% of patients achieve good disease control with T&E
- 40% require intensive fixed-interval treatment
- This explains why real-world injection counts are often higher than ideal T&E
""")


if __name__ == "__main__":
    analyze_response_assumptions()