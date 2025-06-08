"""Test workload analyzer with real simulation data."""

import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from components.treatment_patterns.workload_analyzer import calculate_clinical_workload_attribution, format_workload_insight
from utils.simulation_loader import load_simulation_data

def test_with_real_simulation(sim_id):
    """Test workload analyzer with a real simulation."""
    print(f"Testing with real simulation: {sim_id}")
    print("=" * 60)
    
    try:
        # Load the simulation data
        sim_data = load_simulation_data(sim_id)
        if sim_data is None:
            print(f"❌ Failed to load simulation data for {sim_id}")
            return
            
        results = sim_data['results']
        
        # Get the visits data - this should have patient_id, interval_days, etc.
        print("Loading visits data...")
        visits_df = results.get_visits_df()
        
        print(f"Raw visits data shape: {visits_df.shape}")
        print(f"Columns: {list(visits_df.columns)}")
        print(f"Sample visit:")
        print(visits_df.head(1))
        print()
        
        # Check if we have the required columns for interval calculation
        required_cols = ['patient_id', 'time_days']
        missing_cols = [col for col in required_cols if col not in visits_df.columns]
        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            print("Available columns:", visits_df.columns.tolist())
            return
            
        print(f"Total unique patients: {visits_df['patient_id'].nunique()}")
        print(f"Total visits: {len(visits_df)}")
        print()
        
        # The workload analyzer will calculate intervals if needed
            
        # Run the workload analysis
        print("Running clinical workload analysis...")
        results_data = calculate_clinical_workload_attribution(visits_df)
        
        print(f"Total patients analyzed: {results_data['total_patients']}")
        print(f"Total visits analyzed: {results_data['total_visits']}")
        print()
        
        print("Visit Contributions by Category:")
        print(results_data['visit_contributions'])
        print()
        
        print("Summary Statistics:")
        for category, stats in results_data['summary_stats'].items():
            print(f"\n{category}:")
            print(f"  Patients: {stats['patient_count']} ({stats['patient_percentage']:.1f}%)")
            print(f"  Visits: {stats['visit_count']} ({stats['visit_percentage']:.1f}%)")
            print(f"  Visits/Patient: {stats['visits_per_patient']:.1f}")
            print(f"  Workload Efficiency: {stats['workload_efficiency']:.1f}x")
        
        print("\n" + "="*40)
        print("KEY INSIGHT:")
        print(format_workload_insight(results_data['summary_stats']))
        print("="*40)
        
        # Show which categories have the highest workload efficiency
        efficiency_ranking = sorted(
            results_data['summary_stats'].items(),
            key=lambda x: x[1]['workload_efficiency'],
            reverse=True
        )
        
        print("\nWorkload Efficiency Ranking:")
        for i, (category, stats) in enumerate(efficiency_ranking, 1):
            print(f"{i}. {category}: {stats['workload_efficiency']:.1f}x efficiency "
                  f"({stats['patient_percentage']:.1f}% patients → {stats['visit_percentage']:.1f}% visits)")
        
    except Exception as e:
        print(f"❌ Error analyzing simulation: {str(e)}")
        import traceback
        traceback.print_exc()

# Test with a recent simulation that has good data
recent_sims = [
    "sim_20250608_164413_10-00_delicate-art",
    "sim_20250608_164406_10-00_polished-paper", 
    "sim_20250608_164359_10-00_lingering-resonance",
    "sim_20250608_151459_10-00_purple-haze",
    "sim_20250608_151147_10-00_crimson-paper"
]

for sim_id in recent_sims:
    sim_path = Path(f"simulation_results/{sim_id}")
    if sim_path.exists() and (sim_path / "visits.parquet").exists():
        test_with_real_simulation(sim_id)
        break
else:
    print("❌ No suitable simulation found!")
    print("Available simulations:")
    for p in Path("simulation_results").glob("sim_*"):
        if p.is_dir() and (p / "visits.parquet").exists():
            print(f"  {p.name}")