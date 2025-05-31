"""Test that Analysis Overview page uses the correct API."""

import pytest
from pathlib import Path
import pandas as pd
import numpy as np

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.results.base import SimulationResults, SimulationMetadata
from core.results.parquet import ParquetResults


class TestAnalysisPageAPI:
    """Test that UI pages use the correct SimulationResults API."""
    
    def test_parquet_results_api(self, tmp_path):
        """Test that ParquetResults implements required methods for Analysis Overview."""
        # Create mock Parquet files
        patients_df = pd.DataFrame({
            'patient_id': [f'P{i:04d}' for i in range(100)],
            'baseline_vision': np.random.normal(70, 10, 100),
            'final_vision': np.random.normal(65, 12, 100),
            'total_injections': np.random.poisson(10, 100),
            'total_visits': np.random.poisson(12, 100),
            'discontinued': np.random.choice([True, False], 100, p=[0.2, 0.8]),
            'discontinuation_time': [None] * 100,
            'discontinuation_type': [None] * 100,
            'final_disease_state': ['STABLE'] * 100
        })
        patients_df.to_parquet(tmp_path / 'patients.parquet')
        
        # Create visits data
        visits = []
        for i in range(100):
            for j in range(10):
                visits.append({
                    'patient_id': f'P{i:04d}',
                    'time_days': j * 30,  # Changed to days
                    'vision': 70 - j * 0.5 + np.random.normal(0, 2),
                    'injected': j % 2 == 0,
                    'next_interval_days': 42,
                    'disease_state': 'STABLE'
                })
        visits_df = pd.DataFrame(visits)
        visits_df.to_parquet(tmp_path / 'visits.parquet')
        
        # Create metadata
        metadata_df = pd.DataFrame([{
            'total_patients': 100,
            'total_injections': 950,
            'mean_final_vision': 65.2,
            'std_final_vision': 11.8,
            'discontinuation_rate': 0.2
        }])
        metadata_df.to_parquet(tmp_path / 'metadata.parquet')
        
        # Create ParquetResults instance
        from datetime import datetime
        sim_metadata = SimulationMetadata(
            sim_id='test_sim',
            engine_type='abs',
            n_patients=100,
            duration_years=1.0,
            protocol_name='test',
            protocol_version='1.0',
            timestamp=datetime.now(),
            runtime_seconds=10.0,
            seed=42,
            storage_type='parquet'
        )
        
        results = ParquetResults(sim_metadata, tmp_path)
        
        # Test required methods
        # 1. get_vision_trajectory_df
        vision_df = results.get_vision_trajectory_df()
        assert not vision_df.empty
        assert 'patient_id' in vision_df.columns
        assert 'time_days' in vision_df.columns
        assert 'vision' in vision_df.columns
        
        # 2. get_summary_statistics
        stats = results.get_summary_statistics()
        assert 'patient_count' in stats
        assert 'mean_final_vision' in stats
        assert stats['patient_count'] == 100
        
        # 3. get_treatment_intervals_df
        intervals_df = results.get_treatment_intervals_df()
        assert 'patient_id' in intervals_df.columns
        assert 'interval_days' in intervals_df.columns
        
        # 4. Sampling works
        sample_df = results.get_vision_trajectory_df(sample_size=10)
        assert sample_df['patient_id'].nunique() <= 10
        
    def test_analysis_calculations(self):
        """Test that the calculations done in Analysis Overview are correct."""
        # Create test vision data
        vision_data = pd.DataFrame({
            'patient_id': ['P0000', 'P0000', 'P0000', 'P0001', 'P0001', 'P0001'],
            'time_months': [0, 6, 12, 0, 6, 12],
            'vision': [70, 68, 65, 75, 74, 73]
        })
        
        # Calculate baseline and final visions (as done in Analysis Overview)
        baseline_visions = []
        final_visions = []
        vision_changes = []
        
        for patient_id in vision_data['patient_id'].unique():
            patient_data = vision_data[vision_data['patient_id'] == patient_id]
            patient_data = patient_data.sort_values('time_months')
            
            if not patient_data.empty:
                baseline = patient_data.iloc[0]['vision']
                final = patient_data.iloc[-1]['vision']
                baseline_visions.append(baseline)
                final_visions.append(final)
                vision_changes.append(final - baseline)
        
        # Verify calculations
        assert baseline_visions == [70, 75]
        assert final_visions == [65, 73]
        assert vision_changes == [-5, -2]
        assert np.mean(vision_changes) == -3.5