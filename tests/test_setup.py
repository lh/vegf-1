"""
Quick test to verify pytest is set up correctly.
"""

import pytest
import sys
from pathlib import Path


def test_pytest_works():
    """Verify pytest is installed and working."""
    assert True
    

def test_imports_work():
    """Verify we can import project modules."""
    # Add paths
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "streamlit_app_v2"))
    
    # Try imports
    try:
        from simulation_v2.core.disease_model import DiseaseState
        assert DiseaseState.NAIVE is not None
    except ImportError as e:
        pytest.skip(f"Simulation modules not available: {e}")
        

def test_psutil_available():
    """Verify psutil is available for memory monitoring."""
    import psutil
    
    # Get current memory usage
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    assert memory_mb > 0
    assert memory_mb < 10000  # Sanity check