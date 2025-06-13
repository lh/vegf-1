# Regression Test Plan for Memory Architecture Implementation

## Overview

This test plan ensures that implementing memory-aware architecture doesn't break existing functionality. Tests should be written BEFORE making changes to establish a baseline.

## Test Structure

```
tests/
├── regression/
│   ├── test_existing_simulation.py    # Current functionality
│   ├── test_existing_visualization.py # Current charts work
│   ├── test_existing_state.py        # Session state compatibility
│   └── test_existing_ui.py           # UI interactions work
├── memory/
│   ├── test_memory_limits.py         # Memory threshold behavior
│   ├── test_memory_monitoring.py     # Monitoring accuracy
│   └── test_memory_cleanup.py        # GC and cleanup
├── integration/
│   ├── test_small_simulation.py      # < 1000 patients
│   ├── test_large_simulation.py      # > 1000 patients
│   └── test_tier_switching.py        # Automatic tier selection
└── performance/
    ├── test_baseline_performance.py   # Current speed
    ├── test_memory_performance.py     # In-memory speed
    └── test_parquet_performance.py    # Disk-based speed
```

## Baseline Tests (Run These First!)

### 1. test_existing_simulation.py
```python
import pytest
from simulation_v2.core.simulation_runner import SimulationRunner
from simulation_v2.protocols.protocol_spec import ProtocolSpecification

class TestExistingSimulation:
    """Baseline tests for current simulation functionality."""
    
    def test_small_simulation_runs(self):
        """Verify 100 patient simulation completes."""
        spec = ProtocolSpecification.from_yaml("protocols/default.yaml")
        runner = SimulationRunner(spec)
        results = runner.run("abs", 100, 2.0, 42)
        
        assert results.patient_count == 100
        assert results.total_injections > 0
        assert 0 <= results.discontinuation_rate <= 1
        
    def test_simulation_reproducible(self):
        """Verify same seed produces same results."""
        spec = ProtocolSpecification.from_yaml("protocols/default.yaml")
        runner1 = SimulationRunner(spec)
        runner2 = SimulationRunner(spec)
        
        results1 = runner1.run("abs", 50, 1.0, 12345)
        results2 = runner2.run("abs", 50, 1.0, 12345)
        
        assert results1.total_injections == results2.total_injections
        assert results1.final_vision_mean == results2.final_vision_mean
        
    def test_both_engines_work(self):
        """Verify ABS and DES engines both function."""
        spec = ProtocolSpecification.from_yaml("protocols/default.yaml")
        runner = SimulationRunner(spec)
        
        abs_results = runner.run("abs", 50, 1.0, 42)
        des_results = runner.run("des", 50, 1.0, 42)
        
        assert abs_results.patient_count == 50
        assert des_results.patient_count == 50
        
    @pytest.mark.parametrize("n_patients", [10, 100, 500])
    @pytest.mark.parametrize("duration", [0.5, 1.0, 2.0])
    def test_various_sizes(self, n_patients, duration):
        """Test different simulation sizes work."""
        spec = ProtocolSpecification.from_yaml("protocols/default.yaml")
        runner = SimulationRunner(spec)
        results = runner.run("abs", n_patients, duration, 42)
        
        assert results.patient_count == n_patients
```

### 2. test_existing_visualization.py
```python
import pytest
import matplotlib.pyplot as plt
from streamlit_app_v2.utils.chart_builder import ChartBuilder

class TestExistingVisualization:
    """Baseline tests for current visualizations."""
    
    @pytest.fixture
    def sample_results(self):
        """Create sample results for testing."""
        # Mock or load actual results
        pass
        
    def test_va_chart_creates(self, sample_results):
        """Verify VA progression chart works."""
        chart = ChartBuilder.create_va_progression(sample_results)
        assert chart is not None
        plt.close('all')  # Cleanup
        
    def test_distribution_chart(self, sample_results):
        """Verify distribution plots work."""
        chart = ChartBuilder.create_distribution(sample_results)
        assert chart is not None
        plt.close('all')
        
    def test_no_memory_leaks(self, sample_results):
        """Verify charts don't leak memory."""
        import gc
        import weakref
        
        # Create chart
        chart = ChartBuilder.create_va_progression(sample_results)
        chart_ref = weakref.ref(chart)
        
        # Clean up
        del chart
        plt.close('all')
        gc.collect()
        
        # Verify cleaned up
        assert chart_ref() is None
```

### 3. test_existing_state.py
```python
import pytest
import streamlit as st
import pickle

class TestExistingState:
    """Baseline tests for session state handling."""
    
    def test_state_serializable(self):
        """Verify session state can be pickled."""
        # Mock session state
        state = {
            'simulation_results': {
                'patient_count': 100,
                'results': {}  # Simplified
            },
            'current_protocol': {
                'name': 'test',
                'version': '1.0'
            }
        }
        
        # Should serialize without error
        serialized = pickle.dumps(state)
        deserialized = pickle.loads(serialized)
        
        assert deserialized['simulation_results']['patient_count'] == 100
        
    def test_state_persistence(self):
        """Verify state persists across pages."""
        # This would need Streamlit testing framework
        pass
```

## Memory Safety Tests

### 4. test_memory_limits.py
```python
import pytest
import psutil
import os

class TestMemoryLimits:
    """Test memory threshold behavior."""
    
    def test_memory_monitoring(self):
        """Verify memory monitoring works."""
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        assert memory_mb > 0
        assert memory_mb < 1024  # Should be under 1GB
        
    def test_threshold_detection(self):
        """Test threshold detection logic."""
        from core.monitoring.memory import MemoryMonitor
        
        monitor = MemoryMonitor(warning_mb=500, critical_mb=700)
        
        # Mock different memory levels
        assert monitor.check_status(400) == "ok"
        assert monitor.check_status(550) == "warning"  
        assert monitor.check_status(750) == "critical"
```

## Integration Tests

### 5. test_tier_switching.py
```python
import pytest
from core.results.factory import ResultsFactory

class TestTierSwitching:
    """Test automatic tier selection."""
    
    def test_small_uses_memory(self):
        """Small simulations use in-memory storage."""
        results = ResultsFactory.create(n_patients=500)
        assert results.__class__.__name__ == "InMemoryResults"
        
    def test_large_uses_parquet(self):
        """Large simulations use Parquet storage."""
        results = ResultsFactory.create(n_patients=5000)
        assert results.__class__.__name__ == "ParquetResults"
        
    def test_threshold_edge_cases(self):
        """Test behavior at threshold boundaries."""
        results_999 = ResultsFactory.create(n_patients=999)
        results_1000 = ResultsFactory.create(n_patients=1000)
        results_1001 = ResultsFactory.create(n_patients=1001)
        
        assert results_999.__class__.__name__ == "InMemoryResults"
        assert results_1000.__class__.__name__ == "InMemoryResults"
        assert results_1001.__class__.__name__ == "ParquetResults"
```

## Performance Benchmarks

### 6. test_baseline_performance.py
```python
import pytest
import time

class TestBaselinePerformance:
    """Establish performance baselines."""
    
    @pytest.mark.benchmark
    def test_simulation_speed(self, benchmark):
        """Benchmark simulation speed."""
        def run_simulation():
            spec = ProtocolSpecification.from_yaml("protocols/default.yaml")
            runner = SimulationRunner(spec)
            return runner.run("abs", 100, 1.0, 42)
            
        result = benchmark(run_simulation)
        assert result.patient_count == 100
        
    def test_memory_usage_growth(self):
        """Test memory growth with patient count."""
        import gc
        
        memory_usage = []
        patient_counts = [100, 500, 1000, 2000]
        
        for n in patient_counts:
            gc.collect()
            
            # Measure before
            process = psutil.Process()
            mem_before = process.memory_info().rss
            
            # Run simulation
            spec = ProtocolSpecification.from_yaml("protocols/default.yaml")
            runner = SimulationRunner(spec)
            results = runner.run("abs", n, 0.5, 42)
            
            # Measure after
            mem_after = process.memory_info().rss
            memory_usage.append({
                'patients': n,
                'memory_mb': (mem_after - mem_before) / 1024 / 1024
            })
            
            # Cleanup
            del results
            del runner
            gc.collect()
        
        # Verify roughly linear growth
        # Log results for baseline
        print("Memory usage baseline:")
        for usage in memory_usage:
            print(f"  {usage['patients']} patients: {usage['memory_mb']:.1f} MB")
```

## Continuous Integration Tests

### pytest.ini
```ini
[pytest]
markers =
    regression: Tests that ensure existing functionality works
    memory: Tests related to memory management
    integration: Integration tests across components
    benchmark: Performance benchmark tests
    slow: Tests that take > 10 seconds
    
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Run regression tests first
addopts = -m "regression" --strict-markers
```

### GitHub Actions Workflow
```yaml
name: Regression Tests

on:
  pull_request:
    branches: [ main, dev/* ]
  push:
    branches: [ main ]

jobs:
  regression-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-benchmark
        
    - name: Run regression tests
      run: |
        pytest -m regression -v --cov=streamlit_app_v2
        
    - name: Run memory tests
      run: |
        pytest -m memory -v
        
    - name: Check memory leaks
      run: |
        pytest -m memory --memray
        
    - name: Performance regression check
      run: |
        pytest -m benchmark --benchmark-compare
```

## Test Execution Strategy

### Before Any Changes
1. Run all regression tests, save output
2. Run performance benchmarks, save baselines
3. Commit test results as "golden" reference

### During Development
1. Run regression tests after each change
2. Run relevant integration tests
3. Check memory usage doesn't exceed baseline

### Before Merging
1. Full regression suite must pass
2. Performance within 10% of baseline
3. Memory usage within 20% of baseline
4. No memory leaks detected

### After Deployment
1. Run tests on Streamlit Cloud
2. Verify memory limits respected
3. Load test with concurrent users

## Success Criteria

- ✅ All existing functionality works unchanged
- ✅ Performance degradation < 10% for small simulations
- ✅ Memory usage predictable and bounded
- ✅ Large simulations (>10K patients) now possible
- ✅ Clear error messages when limits exceeded
- ✅ No memory leaks in any code path