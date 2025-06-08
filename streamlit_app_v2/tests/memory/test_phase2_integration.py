"""
Test Phase 2 integration - verify Parquet writing/reading and Streamlit integration.
"""

import pytest
import tempfile
from pathlib import Path
import sys
import time

# Add imports
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from core.storage import ParquetWriter, ParquetReader, SimulationRegistry
from core.results import ResultsFactory
from simulation_v2.engines.abs_engine import SimulationResults as V2Results
from tests.memory.test_results_architecture import create_mock_v2_results


class TestPhase2Integration:
    """Test Phase 2 Parquet integration."""
    
    def test_parquet_writer_with_progress(self):
        """Test ParquetWriter with progress tracking."""
        # Use the centralized mock function
        raw_results = create_mock_v2_results(100)
        
        progress_history = []
        
        def progress_callback(pct, msg):
            progress_history.append((pct, msg))
            
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ParquetWriter(Path(tmpdir))
            writer.write_simulation_results(raw_results, progress_callback)
            
            # Check files were created
            assert (Path(tmpdir) / 'patients.parquet').exists()
            assert (Path(tmpdir) / 'visits.parquet').exists()
            assert (Path(tmpdir) / 'metadata.parquet').exists()
            
            # Check progress was reported
            assert len(progress_history) > 0
            assert progress_history[0][0] == 0  # Started at 0%
            assert progress_history[-1][0] == 100  # Ended at 100%
            
    def test_parquet_reader_lazy_iteration(self):
        """Test ParquetReader lazy iteration."""
        # Use the centralized mock function
        raw_results = create_mock_v2_results(50)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write data
            writer = ParquetWriter(Path(tmpdir))
            writer.write_simulation_results(raw_results)
            
            # Read lazily
            reader = ParquetReader(Path(tmpdir))
            
            # Test metadata
            assert reader.patient_count == 50
            assert reader.metadata['total_patients'] == 50
            
            # Test iteration
            patient_count = 0
            for batch in reader.iterate_patients(batch_size=10):
                assert len(batch) <= 10
                patient_count += len(batch)
                
            assert patient_count == 50
            
    def test_simulation_registry(self):
        """Test simulation registry management."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SimulationRegistry(Path(tmpdir))
            
            # Register a simulation
            registry.register_simulation(
                'test_sim_001',
                {
                    'protocol_name': 'Test Protocol',
                    'n_patients': 100,
                    'duration_years': 2.0
                },
                size_mb=10.5
            )
            
            # List simulations
            sims = registry.list_simulations()
            assert len(sims) == 1
            assert sims[0]['sim_id'] == 'test_sim_001'
            
            # Get specific simulation
            info = registry.get_simulation_info('test_sim_001')
            assert info is not None
            assert info['access_count'] == 1
            
            # Delete simulation
            assert registry.delete_simulation('test_sim_001')
            assert len(registry.list_simulations()) == 0
            
    def test_large_simulation_uses_parquet(self):
        """Test that large simulations automatically use Parquet."""
        # Create a "large" simulation
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
                duration_years=5.0,  # 25K patient-years
                seed=42,
                runtime_seconds=10.0
            )
            
            # Should be Parquet
            from core.results.parquet import ParquetResults
            assert isinstance(results, ParquetResults)
            assert results.metadata.storage_type == "parquet"
            
            # Should have created files
            sim_dir = Path(tmpdir) / results.metadata.sim_id
            assert sim_dir.exists()
            assert (sim_dir / 'patients.parquet').exists()
            assert (sim_dir / 'visits.parquet').exists()
            
            # Test we can iterate patients
            patient_count = 0
            for batch in results.iterate_patients(batch_size=100):
                patient_count += len(batch)
            assert patient_count == 1000  # We created 1000 mock patients
            
    def test_parquet_reader_filters(self):
        """Test Parquet reader with filters."""
        raw_results = create_mock_v2_results(20)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write data
            writer = ParquetWriter(Path(tmpdir))
            writer.write_simulation_results(raw_results)
            
            # Read with filters
            reader = ParquetReader(Path(tmpdir))
            
            # Get specific patient
            patient = reader.get_patient_by_id('P0000')
            assert patient is not None
            assert patient['patient_id'] == 'P0000'
            
            # Get patient visits
            visits = reader.get_patient_visits('P0000')
            assert len(visits) == 12  # Our mock creates 12 visits
            
    def test_parquet_results_constant_memory(self):
        """Test that Parquet results maintain constant memory usage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ResultsFactory.DEFAULT_RESULTS_DIR = Path(tmpdir)
            
            # Create a large Parquet result
            raw_results = create_mock_v2_results(1000)
            parquet_results = ResultsFactory.create_results(
                raw_results=raw_results,
                protocol_name="Test",
                protocol_version="1.0",
                engine_type="abs",
                n_patients=1000,
                duration_years=5.0,
                seed=42,
                runtime_seconds=10.0
            )
            
            # Memory usage should be constant (~1MB) regardless of data size
            assert parquet_results.get_memory_usage_mb() <= 2.0
            
            # Verify we can still access data efficiently
            patient_count = 0
            for batch in parquet_results.iterate_patients(batch_size=100):
                patient_count += len(batch)
            assert patient_count == 1000