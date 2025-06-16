"""
Convert time-based simulation results to parquet format for visualization.
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np

sys.path.append(str(Path(__file__).parent))

from haikunator import Haikunator

haikunator = Haikunator()


def convert_simulation_to_parquet(sim_dir: str):
    """Convert JSON simulation to parquet format."""
    
    sim_path = Path("simulation_results") / sim_dir
    
    # Load the simulation data
    with open(sim_path / "simulation_data.json") as f:
        data = json.load(f)
    
    sim_info = data['simulation_info']
    patient_histories = data['patient_histories']
    
    print(f"Converting {sim_dir}...")
    print(f"  Patients: {sim_info['n_patients']}")
    print(f"  Duration: {sim_info['duration_years']} years")
    
    # Generate new simulation ID with correct format
    timestamp = datetime.fromisoformat(sim_info['timestamp'])
    duration_code = f"{int(sim_info['duration_years']):02d}-00"  # YY-MM format
    memorable_name = haikunator.haikunate(token_length=0, delimiter='-')
    sim_id = f"sim_{timestamp.strftime('%Y%m%d_%H%M%S')}_{duration_code}_{memorable_name}"
    
    # Create new directory
    new_dir = Path("simulation_results") / sim_id
    new_dir.mkdir(parents=True, exist_ok=True)
    
    # Create metadata.json
    metadata = {
        "sim_id": sim_id,
        "protocol_name": sim_info['protocol_name'],
        "protocol_version": sim_info['protocol_version'],
        "engine_type": sim_info['engine_type'],
        "n_patients": sim_info['n_patients'],
        "duration_years": sim_info['duration_years'],
        "seed": sim_info['seed'],
        "timestamp": sim_info['timestamp'],
        "runtime_seconds": 0.1,  # Placeholder
        "storage_type": "parquet",
        "memorable_name": memorable_name
    }
    
    with open(new_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Copy protocol file
    if sim_info.get('model_type') == 'time_based':
        # Copy time-based protocol
        import shutil
        shutil.copy(
            "protocols/v2_time_based/eylea_time_based.yaml",
            new_dir / "protocol.yaml"
        )
    else:
        # Copy standard protocol
        import shutil
        shutil.copy(
            "protocols/v2/eylea_treat_and_extend_v1.0.yaml", 
            new_dir / "protocol.yaml"
        )
    
    # Copy audit log
    if (sim_path / "audit_log.json").exists():
        import shutil
        shutil.copy(sim_path / "audit_log.json", new_dir / "audit_log.json")
    
    # Create patient data frames
    patients_data = []
    visits_data = []
    patient_index_data = []
    
    visit_id = 0
    for patient_id, patient_data in patient_histories.items():
        # Patient record
        patients_data.append({
            'patient_id': patient_id,
            'baseline_vision': patient_data['baseline_vision'],
            'final_vision': patient_data['current_vision'],
            'injection_count': patient_data['injection_count'],
            'is_discontinued': patient_data['is_discontinued'],
            'current_state': patient_data['current_state']
        })
        
        # Patient index
        first_visit_id = visit_id
        num_visits = len(patient_data['visit_history'])
        patient_index_data.append({
            'patient_id': patient_id,
            'first_visit_id': first_visit_id,
            'num_visits': num_visits
        })
        
        # Visit records
        for i, visit in enumerate(patient_data['visit_history']):
            # Calculate time_days from enrollment (first visit)
            visit_date = datetime.fromisoformat(visit['date'])
            if i == 0:
                enrollment_date = visit_date
                time_days = 0
            else:
                time_days = (visit_date - enrollment_date).days
            
            # Calculate next interval if not last visit
            next_interval_days = None
            if i < len(patient_data['visit_history']) - 1:
                next_visit_date = datetime.fromisoformat(patient_data['visit_history'][i + 1]['date'])
                next_interval_days = (next_visit_date - visit_date).days
            
            visits_data.append({
                'patient_id': patient_id,
                'date': visit_date,  # Store as datetime object for pandas
                'time_days': time_days,
                'vision': visit['vision'],
                'injected': visit.get('treatment_given', False),
                'next_interval_days': next_interval_days,
                'disease_state': f"DiseaseState.{visit['disease_state']}"
            })
            visit_id += 1
    
    # Create DataFrames
    patients_df = pd.DataFrame(patients_data)
    visits_df = pd.DataFrame(visits_data)
    patient_index_df = pd.DataFrame(patient_index_data)
    
    # Create metadata DataFrame
    metadata_df = pd.DataFrame([metadata])
    
    # Save as parquet
    patients_df.to_parquet(new_dir / "patients.parquet", index=False)
    visits_df.to_parquet(new_dir / "visits.parquet", index=False)
    patient_index_df.to_parquet(new_dir / "patient_index.parquet", index=False)
    metadata_df.to_parquet(new_dir / "metadata.parquet", index=False)
    
    # Calculate summary stats
    total_visits = len(visits_df)
    total_injections = visits_df['injected'].sum()
    
    # Get actual patient count (may be less than n_patients due to arrival schedule)
    actual_patient_count = len(patients_df)
    
    summary_stats = {
        "total_patients": actual_patient_count,
        "total_injections": int(total_injections),
        "mean_final_vision": float(patients_df['final_vision'].mean()),
        "std_final_vision": float(patients_df['final_vision'].std()),
        "discontinuation_rate": float(patients_df['is_discontinued'].mean()),
        "write_time_seconds": 0.1,
        "chunk_size": 5000.0,
        "total_visits": total_visits,
        "mean_visits_per_patient": total_visits / actual_patient_count,
        "patient_count": actual_patient_count
    }
    
    with open(new_dir / "summary_stats.json", 'w') as f:
        json.dump(summary_stats, f, indent=2)
    
    print(f"\n✅ Converted to: {sim_id}")
    print(f"   Protocol: {sim_info['protocol_name']}")
    print(f"   Model type: {sim_info.get('model_type', 'standard')}")
    print(f"   Mean final vision: {summary_stats['mean_final_vision']:.1f}")
    
    return sim_id


def main():
    """Convert time-based simulation to correct format."""
    
    print("🔄 Converting time-based simulation to correct parquet format...\n")
    
    # Convert time-based simulation (generate new memorable name)
    time_based_id = convert_simulation_to_parquet("20250616-130647-sim-200p-2y-time_based")
    
    print("\n🎉 Conversion complete!")
    print(f"\nYou can now visualize the time-based simulation:")
    print(f"  - Time-based: {time_based_id}")
    print(f"  - Standard: sim_20250616_125050_02-00_jolly-fog")
    print(f"\n📊 Run: streamlit run Home.py")


if __name__ == "__main__":
    main()