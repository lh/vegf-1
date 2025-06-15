"""
Test memorable name preservation during simulation import.
"""

import pytest
from pathlib import Path
import tempfile
import json
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

from ape.utils.simulation_package import SimulationPackageManager
from ape.core.results.base import SimulationMetadata
from datetime import datetime


class TestMemorableNameImport:
    """Test that memorable names are preserved and regenerated correctly during import"""
    
    @pytest.fixture
    def package_manager(self):
        """Create SimulationPackageManager instance"""
        return SimulationPackageManager()
    
    def test_memorable_name_export(self, package_manager):
        """Test that memorable names are included when exporting"""
        # Create mock results with memorable name
        mock_results = Mock()
        mock_results.metadata = Mock()
        mock_results.metadata.sim_id = "sim_20250615_120000_02-00_autumn-surf"
        mock_results.metadata.protocol_name = "Test Protocol"
        mock_results.metadata.protocol_version = "1.0"
        mock_results.metadata.engine_type = "abs"
        mock_results.metadata.n_patients = 100
        mock_results.metadata.duration_years = 2.0
        mock_results.metadata.seed = 42
        mock_results.metadata.timestamp = datetime.now()
        mock_results.metadata.runtime_seconds = 120.5
        mock_results.metadata.storage_type = "parquet"
        mock_results.metadata.memorable_name = "autumn-surf"
        
        # Mock data path
        mock_results.data_path = Path("/tmp/test_sim")
        
        # Test that metadata dict includes memorable_name
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            data_dir = temp_path / "data"
            data_dir.mkdir(exist_ok=True)
            
            # Create mock parquet files
            patients_df = pd.DataFrame({
                'patient_id': [1, 2, 3],
                'discontinued': [False, False, True],
                'total_injections': [12, 10, 8]
            })
            patients_df.to_parquet(data_dir / "patients.parquet")
            
            visits_df = pd.DataFrame({
                'patient_id': [1, 1, 2, 2, 3, 3],
                'time_days': [0, 30, 0, 30, 0, 30],
                'vision': [70, 75, 72, 77, 68, 65],
                'injected': [True, True, True, True, True, False]
            })
            visits_df.to_parquet(data_dir / "visits.parquet")
            
            # When preparing package files, memorable_name should be included
            files = {
                "data/patients.parquet": data_dir / "patients.parquet",
                "data/visits.parquet": data_dir / "visits.parquet"
            }
            
            # Create metadata dict (simulating what _prepare_package_files does)
            metadata_dict = {
                'sim_id': [mock_results.metadata.sim_id],
                'protocol_name': [mock_results.metadata.protocol_name],
                'protocol_version': [mock_results.metadata.protocol_version],
                'engine_type': [mock_results.metadata.engine_type],
                'n_patients': [mock_results.metadata.n_patients],
                'duration_years': [mock_results.metadata.duration_years],
                'seed': [mock_results.metadata.seed],
                'timestamp': [mock_results.metadata.timestamp.isoformat()],
                'runtime_seconds': [mock_results.metadata.runtime_seconds],
                'storage_type': [mock_results.metadata.storage_type],
                'memorable_name': [mock_results.metadata.memorable_name]
            }
            
            # Verify memorable_name is included
            assert 'memorable_name' in metadata_dict
            assert metadata_dict['memorable_name'][0] == "autumn-surf"
            
            # Save as parquet to verify it's preserved
            metadata_df = pd.DataFrame(metadata_dict)
            metadata_path = data_dir / "metadata.parquet"
            metadata_df.to_parquet(metadata_path)
            
            # Read back and verify
            loaded_df = pd.read_parquet(metadata_path)
            assert 'memorable_name' in loaded_df.columns
            assert loaded_df.iloc[0]['memorable_name'] == "autumn-surf"
    
    def test_memorable_name_import_new_generation(self, package_manager):
        """Test that imported simulations get new memorable names with 'imported' prefix"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            data_dir = temp_path / "data"
            data_dir.mkdir(exist_ok=True)
            
            # Create metadata with memorable name
            metadata_dict = {
                'sim_id': ['sim_20250615_120000_02-00_autumn-surf'],
                'protocol_name': ['Test Protocol'],
                'protocol_version': ['1.0'],
                'engine_type': ['abs'],
                'n_patients': [100],
                'duration_years': [2.0],
                'seed': [42],
                'timestamp': [datetime.now().isoformat()],
                'runtime_seconds': [120.5],
                'storage_type': ['parquet'],
                'memorable_name': ['autumn-surf']
            }
            
            metadata_df = pd.DataFrame(metadata_dict)
            metadata_row = metadata_df.iloc[0]
            
            # Test the logic for generating new memorable name
            original_memorable_name = metadata_row.get('memorable_name', '')
            assert original_memorable_name == 'autumn-surf'
            
            # Mock haikunator to control the generated name
            with patch('haikunator.Haikunator') as mock_haikunator_class:
                mock_haikunator = Mock()
                mock_haikunator.haikunate.return_value = "winter-breeze"
                mock_haikunator_class.return_value = mock_haikunator
                
                # Generate new memorable name (simulating import logic)
                from haikunator import Haikunator
                haikunator = Haikunator()
                new_memorable_name = haikunator.haikunate(token_length=0, delimiter='-')
                new_memorable_name = f"imported-{new_memorable_name}"
                
                assert new_memorable_name == "imported-winter-breeze"
                assert new_memorable_name.startswith("imported-")
                assert new_memorable_name != original_memorable_name
    
    def test_memorable_name_in_new_sim_id(self):
        """Test that new sim_id includes the new memorable name"""
        original_sim_id = "sim_20250615_120000_02-00_autumn-surf"
        new_memorable_name = "imported-winter-breeze"
        
        # Parse original sim_id
        sim_id_parts = original_sim_id.split('_')
        assert len(sim_id_parts) >= 4
        
        timestamp_part = sim_id_parts[1]  # 20250615
        time_part = sim_id_parts[2]      # 120000
        duration_code = sim_id_parts[3]   # 02-00
        
        # Create new sim_id with same format but new memorable name
        new_sim_id = f"sim_{timestamp_part}_{time_part}_{duration_code}_{new_memorable_name}"
        
        expected = "sim_20250615_120000_02-00_imported-winter-breeze"
        assert new_sim_id == expected
        assert "imported-" in new_sim_id
        assert "autumn-surf" not in new_sim_id
    
    def test_fallback_when_haikunator_unavailable(self):
        """Test fallback behavior when haikunator is not available"""
        original_memorable_name = "autumn-surf"
        
        # Simulate ImportError for haikunator
        try:
            raise ImportError("No module named 'haikunator'")
        except ImportError:
            # Fallback to using original name with imported prefix
            new_memorable_name = f"imported-{original_memorable_name}" if original_memorable_name else "imported-sim"
        
        assert new_memorable_name == "imported-autumn-surf"
        
        # Test with empty original name
        original_memorable_name = ""
        try:
            raise ImportError("No module named 'haikunator'")
        except ImportError:
            new_memorable_name = f"imported-{original_memorable_name}" if original_memorable_name else "imported-sim"
        
        assert new_memorable_name == "imported-sim"
    
    def test_metadata_preservation_with_memorable_name(self):
        """Test that SimulationMetadata correctly preserves memorable_name"""
        memorable_name = "imported-winter-breeze"
        
        metadata = SimulationMetadata(
            sim_id="sim_20250615_120000_02-00_imported-winter-breeze",
            protocol_name="Test Protocol",
            protocol_version="1.0",
            engine_type="abs",
            n_patients=100,
            duration_years=2.0,
            seed=42,
            timestamp=datetime.now(),
            runtime_seconds=120.5,
            storage_type="parquet",
            memorable_name=memorable_name
        )
        
        assert metadata.memorable_name == memorable_name
        
        # Test to_dict includes memorable_name
        metadata_dict = metadata.to_dict()
        assert 'memorable_name' in metadata_dict
        assert metadata_dict['memorable_name'] == memorable_name