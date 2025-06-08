"""Test Analysis Overview page compatibility with different result types."""

import pytest
import sys
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from core.simulation_runner import SimulationRunner


class TestAnalysisOverview:
    """Test Analysis Overview page with different storage backends."""
    
    @pytest.fixture
    def protocol_spec(self):
        """Load test protocol."""
        return ProtocolSpecification.from_yaml(Path("protocols/eylea.yaml"))
        
    def test_analysis_overview_with_parquet(self, protocol_spec):
        """Test that Analysis Overview works with Parquet storage."""
        # Run simulation that uses Parquet
        runner = SimulationRunner(protocol_spec)
        results = runner.run(
            engine_type="abs",
            n_patients=100,
            duration_years=1.0,
            seed=42,
            show_progress=False
        )
        
        # Test that we can get the data needed for analysis overview
        # without accessing patient_histories directly
        
        # Get summary statistics
        stats = results.get_summary_statistics()
        assert 'patient_count' in stats
        assert 'mean_final_vision' in stats
        assert 'std_final_vision' in stats
        
        # Get vision trajectories
        vision_df = results.get_vision_trajectory_df()
        assert not vision_df.empty
        assert 'patient_id' in vision_df.columns
        assert 'time_days' in vision_df.columns
        assert 'vision' in vision_df.columns
        
        # Calculate baseline and final visions from trajectory data
        baseline_visions = []
        final_visions = []
        
        for patient_id in vision_df['patient_id'].unique():
            patient_data = vision_df[vision_df['patient_id'] == patient_id]
            patient_data = patient_data.sort_values('time_days')
            
            if not patient_data.empty:
                baseline_visions.append(patient_data.iloc[0]['vision'])
                final_visions.append(patient_data.iloc[-1]['vision'])
                
        assert len(baseline_visions) > 0
        assert len(final_visions) > 0
        
        # Verify we can calculate vision changes
        vision_changes = [f - b for b, f in zip(baseline_visions, final_visions)]
        assert len(vision_changes) == len(baseline_visions)
        
    def test_analysis_overview_with_small_simulation(self, protocol_spec):
        """Test that Analysis Overview works with small simulations."""
        # Run small simulation
        runner = SimulationRunner(protocol_spec)
        results = runner.run(
            engine_type="abs",
            n_patients=50,
            duration_years=0.5,
            seed=42,
            show_progress=False
        )
        
        # Should use Parquet storage
        assert hasattr(results, 'data_path')
            
        # Test the same methods work
        stats = results.get_summary_statistics()
        assert stats['patient_count'] == 50
        
        vision_df = results.get_vision_trajectory_df()
        assert not vision_df.empty