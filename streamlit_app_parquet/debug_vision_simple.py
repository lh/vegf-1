"""
Simple debug script to check vision data in the simulation pipeline
"""
import sys
import os
sys.path.append(os.getcwd())

print("=== Testing Vision Data Recording ===\n")

# Test 1: Check if a simple patient visit records vision
print("1. Creating sample patient visit record...")
sample_visit = {
    'time': 0,
    'patient_id': 'test_001',
    'phase': 'loading',
    'vision': 70.5,  # This is what should be recorded
    'baseline_vision': 70.0,
    'actions': ['injection']
}
print(f"   Sample visit has 'vision' field: {'vision' in sample_visit}")
print(f"   Vision value: {sample_visit.get('vision')}")

# Test 2: Import and check actual simulation
print("\n2. Testing actual simulation patient...")
try:
    from treat_and_extend_abs import Patient
    
    # Create a patient
    from datetime import datetime
    patient = Patient("test_001", initial_vision=70.0, start_date=datetime.now())
    
    print(f"   Patient current_vision: {patient.current_vision}")
    print(f"   Patient baseline_vision: {patient.baseline_vision}")
    
    # Simulate a visit
    print("\n3. Simulating a visit...")
    # Just check what a visit record would look like
    visit_record = {
        'date': datetime.now(),
        'time': 0,
        'patient_id': patient.patient_id,
        'phase': patient.current_phase,
        'baseline_vision': patient.baseline_vision,
        'vision': patient.current_vision,  # This is the key line
        'actions': ['injection']
    }
    
    print(f"   Visit record keys: {list(visit_record.keys())}")
    print(f"   Vision in record: {visit_record.get('vision')}")
    
except Exception as e:
    print(f"   Error testing Patient: {e}")

# Test 3: Check the minimal simulation runner
print("\n4. Testing minimal simulation run...")
try:
    # Use the YAML config approach that simulation_runner uses
    with open('test_minimal_config.yaml', 'w') as f:
        f.write("""
protocol: "treat_and_extend"
simulation_type: "ABS"
num_patients: 2
duration_days: 30
random_seed: 42
verbose: true
start_date: "2024-01-01"
parameters:
  population_size: 2
  simulation_duration_years: 0.1
  discontinuation:
    enabled: true
    criteria:
      stable_max_interval:
        consecutive_visits: 3
        probability: 0.2
      random_administrative:
        annual_probability: 0.05
""")
    
    from simulation.config import SimulationConfig
    config = SimulationConfig.from_yaml('test_minimal_config.yaml')
    
    from treat_and_extend_abs_fixed import TreatAndExtendABS
    sim = TreatAndExtendABS(config)
    
    # Run a very short simulation
    patient_histories = sim.run()
    
    print(f"   Simulation completed with {len(patient_histories)} patients")
    
    # Check first patient's first visit
    for patient_id, history in patient_histories.items():
        if history:
            first_visit = history[0]
            print(f"\n   Patient {patient_id} first visit:")
            print(f"     Keys: {list(first_visit.keys())}")
            if 'vision' in first_visit:
                print(f"     ✓ Vision field exists: {first_visit['vision']}")
            else:
                print(f"     ✗ Vision field MISSING!")
            break
    
    # Clean up
    os.remove('test_minimal_config.yaml')
    
except Exception as e:
    print(f"   Error in minimal simulation: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check Parquet save
print("\n5. Testing Parquet save...")
try:
    if 'patient_histories' in locals() and patient_histories:
        from streamlit_app_parquet.simulation_runner import save_results_as_parquet
        
        params = {
            "simulation_type": "ABS",
            "population_size": 2,
            "duration_years": 0.1,
            "planned_discontinue_prob": 0.2,
            "administrative_discontinue_prob": 0.05,
            "premature_discontinue_factor": 2.0
        }
        
        base_path = save_results_as_parquet(
            patient_histories,
            sim.stats if hasattr(sim, 'stats') else {},
            config,
            params
        )
        
        print(f"   Saved to: {base_path}")
        
        # Load and check
        import pandas as pd
        visits_df = pd.read_parquet(f"{base_path}_visits.parquet")
        
        print(f"   Visits DataFrame shape: {visits_df.shape}")
        print(f"   Columns: {list(visits_df.columns)}")
        
        if 'vision' in visits_df.columns:
            print(f"   ✓ Vision column exists")
            print(f"     Non-null values: {visits_df['vision'].notna().sum()}")
            print(f"     Sample values: {visits_df['vision'].dropna().head().tolist()}")
        else:
            print(f"   ✗ Vision column MISSING from DataFrame!")
            
except Exception as e:
    print(f"   Error testing Parquet: {e}")
    import traceback
    traceback.print_exc()