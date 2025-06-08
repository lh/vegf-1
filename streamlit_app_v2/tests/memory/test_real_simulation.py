"""
Test with real simulation data to ensure Parquet handling works correctly.
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add imports
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from core.simulation_runner import SimulationRunner
from core.results import ResultsFactory
from core.results.parquet import ParquetResults


class TestRealSimulation:
    """Test with actual simulation data, not mocks."""
    
    @pytest.fixture
    def protocol_path(self):
        """Get path to test protocol."""
        return Path(__file__).parent.parent.parent / "protocols" / "eylea.yaml"
        
    def test_small_real_simulation(self, protocol_path):
        """Test small simulation with real data."""
        # Load protocol
        spec = ProtocolSpecification.from_yaml(protocol_path)
        
        # Run small simulation
        runner = SimulationRunner(spec)
        results = runner.run(
            engine_type="abs",
            n_patients=50,
            duration_years=1.0,
            seed=42,
            show_progress=False
        )
        
        # Should use Parquet storage (all simulations now use Parquet)
        assert results.metadata.storage_type == "parquet"
        
        # Verify we can access data
        assert results.get_patient_count() == 50
        assert results.get_total_injections() > 0
        
        # Check patient iteration works
        patient_count = 0
        for batch in results.iterate_patients(batch_size=10):
            patient_count += len(batch)
            # Verify patient data structure
            for patient in batch:
                assert 'patient_id' in patient
                assert 'visits' in patient
                assert len(patient['visits']) > 0
                
        assert patient_count == 50
        
    def test_large_real_simulation(self, protocol_path):
        """Test large simulation that triggers Parquet storage."""
        # Load protocol
        spec = ProtocolSpecification.from_yaml(protocol_path)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override storage directory
            ResultsFactory.DEFAULT_RESULTS_DIR = Path(tmpdir)
            
            # Run large simulation (15K patient-years)
            runner = SimulationRunner(spec)
            results = runner.run(
                engine_type="abs",
                n_patients=10000,
                duration_years=1.5,
                seed=42,
                show_progress=True  # Show progress for debugging
            )
            
            # Should use Parquet storage
            assert results.metadata.storage_type == "parquet"
            assert isinstance(results, ParquetResults)
            
            # Verify files were created
            sim_dir = Path(tmpdir) / results.metadata.sim_id
            assert sim_dir.exists()
            assert (sim_dir / 'patients.parquet').exists()
            assert (sim_dir / 'visits.parquet').exists()
            assert (sim_dir / 'metadata.parquet').exists()
            
            # Verify we can access data
            assert results.get_patient_count() == 10000
            assert results.get_total_injections() > 0
            
            # Check vision stats
            mean_vision, std_vision = results.get_final_vision_stats()
            assert 0 <= mean_vision <= 100
            assert std_vision >= 0
            
            # Test patient iteration
            patient_count = 0
            first_batch = True
            for batch in results.iterate_patients(batch_size=100):
                patient_count += len(batch)
                
                # Check first batch in detail
                if first_batch:
                    first_batch = False
                    for patient in batch[:5]:  # Check first 5 patients
                        assert 'patient_id' in patient
                        assert 'visits' in patient
                        assert isinstance(patient['visits'], list)
                        assert len(patient['visits']) > 0
                        
                        # Check visit structure
                        first_visit = patient['visits'][0]
                        assert 'time_days' in first_visit  # Changed from time_years
                        assert 'vision' in first_visit
                        assert 'injected' in first_visit
                        
                # Don't process all 10K patients in test
                if patient_count >= 1000:
                    break
                    
            assert patient_count >= 1000
            
            # Test specific patient access
            patient_data = results.get_patient('P0000')
            assert patient_data is not None
            assert patient_data['patient_id'] == 'P0000'
            
            # Test summary statistics
            stats = results.get_summary_statistics()
            assert stats['patient_count'] == 10000
            assert 'mean_visits_per_patient' in stats
            
    def test_memory_efficiency_real_data(self, protocol_path):
        """Test that Parquet uses less memory than threshold."""
        spec = ProtocolSpecification.from_yaml(protocol_path)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            ResultsFactory.DEFAULT_RESULTS_DIR = Path(tmpdir)
            
            # Run simulation that should use Parquet
            runner = SimulationRunner(spec)
            results = runner.run(
                engine_type="abs",
                n_patients=5000,
                duration_years=3.0,
                seed=42,
                show_progress=False
            )
            
            # Memory usage should be minimal
            memory_mb = results.get_memory_usage_mb()
            assert memory_mb <= 2.0  # Should be around 1MB
            
            # But we can still access all the data
            assert results.get_patient_count() == 5000
            
            # Test lazy loading doesn't increase memory
            initial_memory = memory_mb
            
            # Access some patients
            for i, batch in enumerate(results.iterate_patients(batch_size=100)):
                if i >= 5:  # Only process 5 batches
                    break
                    
            # Memory should still be low
            final_memory = results.get_memory_usage_mb()
            assert final_memory <= initial_memory + 0.5  # Allow small increase