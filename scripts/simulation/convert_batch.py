"""
Convert multiple simulations to parquet format.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from convert_to_parquet_format import convert_simulation_to_parquet


def main():
    """Convert interesting simulations."""
    
    simulations = [
        # Small/fast
        "20250616-131154-sim-100p-1y-time_based",
        "20250616-131154-sim-100p-1y-standard",
        
        # Medium 
        "20250616-131154-sim-500p-2y-time_based",
        "20250616-131154-sim-500p-2y-standard",
        
        # Large/long
        "20250616-131154-sim-1000p-3y-time_based",
        "20250616-131154-sim-1000p-3y-standard",
    ]
    
    print("🔄 Converting simulations to parquet format...\n")
    
    converted = []
    for sim in simulations:
        try:
            new_id = convert_simulation_to_parquet(sim)
            converted.append((sim, new_id))
            print()
        except Exception as e:
            print(f"⚠️  Failed to convert {sim}: {e}\n")
    
    print("\n" + "="*60)
    print("📊 CONVERSION COMPLETE")
    print("="*60)
    
    for original, new_id in converted:
        print(f"\n{original}")
        print(f"  → {new_id}")
    
    print(f"\n\n✨ Converted {len(converted)} simulations")
    print("📊 Run: streamlit run Home.py")


if __name__ == "__main__":
    main()