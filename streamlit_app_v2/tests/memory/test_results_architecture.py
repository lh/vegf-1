"""
Test the new memory-aware results architecture.
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add imports
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from core.results import SimulationResults, InMemoryResults, ParquetResults, ResultsFactory
from core.results.base import SimulationMetadata
from simulation_v2.engines.abs_engine import SimulationResults as V2Results
from datetime import datetime


class MockDiseaseState:
    """Mock disease state."""
    def __init__(self, value):
        self.value = value


class MockVisit:
    """Mock visit."""
    def __init__(self, time_years, vision, injected, next_interval_days):
        self.time_years = time_years
        self.vision = vision
        self.injected = injected
        self.next_interval_days = next_interval_days


class MockPatient:
    """Mock patient for testing."""
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.disease_state = MockDiseaseState('stable')
        self.vision = 70.0
        self.injection_count = 10
        self.discontinued = False
        self.visits = [
            MockVisit(
                time_years=i/12,
                vision=70 - i,
                injected=True,
                next_interval_days=42
            )
            for i in range(12)
        ]


def create_mock_v2_results(n_patients: int = 10):
    """Create mock V2 results for testing."""
    patient_histories = {
        f"patient_{i}": MockPatient(f"patient_{i}")
        for i in range(n_patients)
    }
    
    return V2Results(
        total_injections=n_patients * 10,
        patient_histories=patient_histories,
        final_vision_mean=65.0,
        final_vision_std=5.0,
        discontinuation_rate=0.1
    )


class TestResultsArchitecture:
    """Test the memory-aware results architecture."""
    
    def test_in_memory_results(self):
        """Test InMemoryResults implementation."""
        # Create metadata
        metadata = SimulationMetadata(
            sim_id="test_001",
            protocol_name="Test Protocol",
            protocol_version="1.0",
            engine_type="abs",
            n_patients=10,
            duration_years=1.0,
            seed=42,
            timestamp=datetime.now(),
            runtime_seconds=1.5,
            storage_type="memory"
        )
        
        # Create mock results
        raw_results = create_mock_v2_results(10)
        
        # Create InMemoryResults
        results = InMemoryResults(metadata, raw_results)
        
        # Test basic methods
        assert results.get_patient_count() == 10
        assert results.get_total_injections() == 100
        assert results.get_discontinuation_rate() == 0.1
        
        # Test final vision stats
        mean, std = results.get_final_vision_stats()
        assert mean == 65.0
        assert std == 5.0
        
        # Test patient iteration
        all_patients = []
        for batch in results.iterate_patients(batch_size=3):
            all_patients.extend(batch)
        assert len(all_patients) == 10
        
        # Test specific patient access
        patient = results.get_patient("patient_0")
        assert patient is not None
        assert patient['patient_id'] == "patient_0"
        assert len(patient['visits']) == 12
        
    def test_results_factory_small_simulation(self):
        """Test factory creates InMemoryResults for small simulations."""
        raw_results = create_mock_v2_results(100)
        
        results = ResultsFactory.create_results(
            raw_results=raw_results,
            protocol_name="Test",
            protocol_version="1.0",
            engine_type="abs",
            n_patients=100,
            duration_years=1.0,
            seed=42,
            runtime_seconds=1.0,
            force_parquet=False
        )
        
        # Should be InMemoryResults for small simulation
        assert isinstance(results, InMemoryResults)
        assert results.metadata.storage_type == "memory"
        
    def test_results_factory_large_simulation(self):
        """Test factory creates ParquetResults for large simulations."""
        raw_results = create_mock_v2_results(1000)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override default directory
            ResultsFactory.DEFAULT_RESULTS_DIR = Path(tmpdir)
            
            results = ResultsFactory.create_results(
                raw_results=raw_results,
                protocol_name="Test",
                protocol_version="1.0",
                engine_type="abs",
                n_patients=5000,
                duration_years=5.0,  # 25,000 patient-years
                seed=42,
                runtime_seconds=10.0,
                force_parquet=False
            )
            
            # Should be ParquetResults for large simulation
            assert isinstance(results, ParquetResults)
            assert results.metadata.storage_type == "parquet"
            
    def test_force_parquet(self):
        """Test forcing Parquet storage."""
        raw_results = create_mock_v2_results(10)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            ResultsFactory.DEFAULT_RESULTS_DIR = Path(tmpdir)
            
            results = ResultsFactory.create_results(
                raw_results=raw_results,
                protocol_name="Test",
                protocol_version="1.0",
                engine_type="abs",
                n_patients=10,
                duration_years=1.0,
                seed=42,
                runtime_seconds=1.0,
                force_parquet=True  # Force Parquet
            )
            
            # Should be ParquetResults even for small simulation
            assert isinstance(results, ParquetResults)
            
    def test_memory_estimates(self):
        """Test memory usage estimation."""
        estimates = ResultsFactory.estimate_memory_usage(1000, 5.0)
        
        assert 'estimated_mb' in estimates
        assert 'patient_years' in estimates
        assert 'recommended_storage' in estimates
        assert estimates['patient_years'] == 5000
        
        # Large simulation should recommend Parquet
        large_estimates = ResultsFactory.estimate_memory_usage(10000, 5.0)
        assert large_estimates['recommended_storage'] == 'parquet'
        
    def test_save_and_load(self):
        """Test saving and loading results."""
        metadata = SimulationMetadata(
            sim_id="test_save",
            protocol_name="Test Protocol",
            protocol_version="1.0",
            engine_type="abs",
            n_patients=10,
            duration_years=1.0,
            seed=42,
            timestamp=datetime.now(),
            runtime_seconds=1.5,
            storage_type="memory"
        )
        
        raw_results = create_mock_v2_results(10)
        results = InMemoryResults(metadata, raw_results)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test_results"
            
            # Save
            results.save(save_path)
            
            # Load
            loaded = ResultsFactory.load_results(save_path)
            
            # Verify
            assert isinstance(loaded, InMemoryResults)
            assert loaded.get_patient_count() == 10
            assert loaded.metadata.sim_id == "test_save"