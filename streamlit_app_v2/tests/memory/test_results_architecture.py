"""
Test Parquet-based results architecture.
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add imports
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from core.results import SimulationResults, ParquetResults, ResultsFactory
from core.results.base import SimulationMetadata
from datetime import datetime, timedelta


def create_mock_v2_results(n_patients=100):
    """Create mock V2 simulation results for testing."""
    # Create patient histories
    patient_histories = {}
    
    for i in range(n_patients):
        patient_id = f"P{i:04d}"
        
        # Add enrollment date - simulate staggered enrollment
        enrollment_date = datetime(2024, 1, 1) + timedelta(days=i * 3)  # Every 3 days
        
        # Create visits (monthly for 1 year)
        visits = []
        visit_history = []
        for month in range(12):
            visit_date = enrollment_date + timedelta(days=(month + 1) * 30)  # First visit 30 days after enrollment
            visits.append({
                'time': month * 30,  # days
                'injected': True,
                'vision': 70 - month * 0.5  # Gradual decline
            })
            visit_history.append({
                'date': visit_date,
                'treatment_given': True,
                'vision': 70 - month * 0.5,
                'disease_state': 'STABLE'
            })
        
        # Create a mock patient object instead of dict
        class MockPatient:
            def __init__(self, pid, visits_list, visit_hist, enroll_date):
                self.patient_id = pid
                self.visits = visits_list
                self.visit_history = visit_hist
                self.baseline_vision = 70
                self.final_vision = 64
                self.current_vision = 64
                self.enrollment_date = enroll_date
                self.is_discontinued = False
                self.discontinuation_date = None
                self.discontinuation_type = None
                self.discontinuation_reason = None
                self.pre_discontinuation_vision = None
                self.injection_count = len([v for v in visit_hist if v['treatment_given']])
                self.retreatment_count = 0
                self.current_state = 'STABLE'
                
        patient_histories[patient_id] = MockPatient(patient_id, visits, visit_history, enrollment_date)
    
    # Create mock V2Results object
    class MockV2Results:
        def __init__(self, histories):
            self.patient_histories = histories
            self.total_injections = sum(len(p.visits) for p in histories.values())
            self.final_vision_mean = 64
            self.final_vision_std = 5
            self.discontinuation_rate = 0.1
            
    return MockV2Results(patient_histories)


class TestResultsArchitecture:
    """Test the Parquet-only results architecture."""
    
    def test_parquet_results_always_used(self):
        """Test that all simulations use Parquet storage."""
        # Create results
        with tempfile.TemporaryDirectory() as tmpdir:
            ResultsFactory.DEFAULT_RESULTS_DIR = Path(tmpdir)
            
            results = ResultsFactory.create_results(
                raw_results=create_mock_v2_results(100),
                protocol_name="Test Protocol",
                protocol_version="1.0",
                engine_type="abs",
                n_patients=100,
                duration_years=1.0,
                seed=42,
                runtime_seconds=1.23
            )
            
            # Should always be ParquetResults
            assert isinstance(results, ParquetResults)
            assert results.metadata.storage_type == 'parquet'
            
            # Check files were created
            assert results.data_path.exists()
            assert (results.data_path / 'patients.parquet').exists()
            assert (results.data_path / 'visits.parquet').exists()
            
    def test_parquet_efficient_memory(self):
        """Test that Parquet uses minimal memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ResultsFactory.DEFAULT_RESULTS_DIR = Path(tmpdir)
            
            # Create large simulation
            results = ResultsFactory.create_results(
                raw_results=create_mock_v2_results(1000),
                protocol_name="Test Protocol",
                protocol_version="1.0",
                engine_type="abs",
                n_patients=1000,
                duration_years=1.0,
                seed=42,
                runtime_seconds=5.0
            )
            
            # Memory usage should be minimal
            memory_mb = results.get_memory_usage_mb()
            assert memory_mb < 5.0  # Should be ~1-2MB
            
    def test_results_interface_consistency(self):
        """Test that all results follow the same interface."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ResultsFactory.DEFAULT_RESULTS_DIR = Path(tmpdir)
            
            results = ResultsFactory.create_results(
                raw_results=create_mock_v2_results(50),
                protocol_name="Test Protocol",
                protocol_version="1.0",
                engine_type="des",
                n_patients=50,
                duration_years=2.0,
                seed=123,
                runtime_seconds=2.5
            )
            
            # Test all required methods exist and work
            assert results.get_patient_count() == 50
            assert results.get_total_injections() > 0
            
            mean_vision, std_vision = results.get_final_vision_stats()
            assert 0 <= mean_vision <= 100
            assert std_vision >= 0
            
            # Test iteration
            patient_count = 0
            for batch in results.iterate_patients(batch_size=10):
                patient_count += len(batch)
                if patient_count >= 20:  # Just test first 20
                    break
                    
            assert patient_count >= 20
            
            # Test summary statistics
            stats = results.get_summary_statistics()
            assert stats['patient_count'] == 50
            assert 'mean_final_vision' in stats
            
    def test_load_saved_results(self):
        """Test loading previously saved results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ResultsFactory.DEFAULT_RESULTS_DIR = Path(tmpdir)
            
            # Create and save results
            original = ResultsFactory.create_results(
                raw_results=create_mock_v2_results(30),
                protocol_name="Test Protocol",
                protocol_version="1.0",
                engine_type="abs",
                n_patients=30,
                duration_years=1.5,
                seed=999,
                runtime_seconds=0.5
            )
            
            sim_id = original.metadata.sim_id
            
            # Load from disk
            loaded = ResultsFactory.load_results(Path(tmpdir) / sim_id)
            
            # Verify metadata matches
            assert loaded.metadata.sim_id == sim_id
            assert loaded.metadata.n_patients == 30
            assert loaded.metadata.duration_years == 1.5
            
            # Verify data matches
            assert loaded.get_patient_count() == original.get_patient_count()
            assert loaded.get_total_injections() == original.get_total_injections()