"""
Establish memory usage baselines for current implementation.

These measurements will be our reference for ensuring the new
architecture doesn't increase memory usage for small simulations.
"""

import pytest
import psutil
import gc
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent))


class TestMemoryBaseline:
    """Establish memory baselines for current system."""
    
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Force garbage collection before and after each test."""
        gc.collect()
        yield
        gc.collect()
    
    def get_memory_mb(self):
        """Get current process memory in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def test_import_memory_overhead(self):
        """Measure memory overhead of imports."""
        gc.collect()
        mem_before = self.get_memory_mb()
        
        # Import simulation modules
        from simulation_v2.core.simulation_runner import SimulationRunner
        from simulation_v2.protocols.protocol_spec import ProtocolSpecification
        
        gc.collect()
        mem_after = self.get_memory_mb()
        
        import_overhead = mem_after - mem_before
        print(f"\nImport overhead: {import_overhead:.1f} MB")
        
        # Record baseline
        assert import_overhead < 100, "Import overhead should be reasonable"
        
    def test_empty_simulation_memory(self):
        """Measure memory for minimal simulation."""
        from simulation_v2.core.simulation_runner import SimulationRunner
        from simulation_v2.protocols.protocol_spec import ProtocolSpecification
        
        gc.collect()
        mem_start = self.get_memory_mb()
        
        # Create minimal protocol
        protocol_path = Path(__file__).parent / "minimal_protocol.yaml"
        protocol_path.write_text("""
name: Minimal
version: 1.0.0
description: Minimal protocol for memory testing

disease_states:
  - name: active
disease_transitions:
  active:
    active: 1.0
treatment_effect_on_transitions:
  active:
    active: 1.0

min_interval_days: 28
max_interval_days: 28
extension_days: 0
shortening_days: 0

baseline_vision_mean: 70
baseline_vision_std: 0
baseline_vision_min: 70
baseline_vision_max: 70

max_injections_per_year: 13
loading_doses: 3
discontinuation_vision_threshold: 20
discontinuation_low_vision_prob: 0
discontinuation_rate_per_month: 0
""")
        
        spec = ProtocolSpecification.from_yaml(protocol_path)
        runner = SimulationRunner(spec)
        
        gc.collect()
        mem_loaded = self.get_memory_mb()
        
        # Run tiny simulation
        results = runner.run("abs", n_patients=1, duration_years=0.1, seed=42)
        
        gc.collect()
        mem_after = self.get_memory_mb()
        
        print(f"\nMinimal simulation memory:")
        print(f"  After import: {mem_start:.1f} MB")
        print(f"  After loading: {mem_loaded:.1f} MB")
        print(f"  After 1 patient: {mem_after:.1f} MB")
        print(f"  Total increase: {mem_after - mem_start:.1f} MB")
        
        # Cleanup
        protocol_path.unlink()
        
    def test_memory_scaling(self):
        """Test memory usage scaling with patient count."""
        from simulation_v2.core.simulation_runner import SimulationRunner
        from simulation_v2.protocols.protocol_spec import ProtocolSpecification
        
        # Use same minimal protocol
        protocol_path = Path(__file__).parent / "scaling_protocol.yaml"
        protocol_path.write_text("""
name: Scaling Test
version: 1.0.0
description: Protocol for memory scaling tests

disease_states:
  - name: active
disease_transitions:
  active:
    active: 1.0
treatment_effect_on_transitions:
  active:
    active: 1.0

min_interval_days: 42
max_interval_days: 42
extension_days: 0
shortening_days: 0

baseline_vision_mean: 70
baseline_vision_std: 5
baseline_vision_min: 60
baseline_vision_max: 80

max_injections_per_year: 9
loading_doses: 3
discontinuation_vision_threshold: 20
discontinuation_low_vision_prob: 0.1
discontinuation_rate_per_month: 0.01
""")
        
        spec = ProtocolSpecification.from_yaml(protocol_path)
        
        # Test scaling
        memory_usage = []
        patient_counts = [10, 50, 100, 500]
        
        for n_patients in patient_counts:
            gc.collect()
            mem_before = self.get_memory_mb()
            
            # Run simulation
            runner = SimulationRunner(spec)
            results = runner.run("abs", n_patients, 0.5, seed=42)
            
            gc.collect()
            mem_after = self.get_memory_mb()
            
            memory_increase = mem_after - mem_before
            bytes_per_patient = (memory_increase * 1024 * 1024) / n_patients
            
            memory_usage.append({
                'n_patients': n_patients,
                'memory_mb': memory_increase,
                'bytes_per_patient': bytes_per_patient,
                'total_visits': results.total_injections
            })
            
            # Cleanup
            del results
            del runner
            gc.collect()
        
        # Log results
        print("\nMemory scaling baseline:")
        for usage in memory_usage:
            print(f"  {usage['n_patients']:4d} patients: "
                  f"{usage['memory_mb']:6.1f} MB "
                  f"({usage['bytes_per_patient']:6.0f} bytes/patient, "
                  f"{usage['total_visits']} visits)")
        
        # Verify roughly linear scaling
        if len(memory_usage) >= 2:
            # Compare bytes per patient for different sizes
            small = memory_usage[0]['bytes_per_patient']
            large = memory_usage[-1]['bytes_per_patient']
            ratio = large / small
            
            print(f"\nScaling ratio (large/small): {ratio:.2f}")
            assert 0.5 <= ratio <= 2.0, "Memory should scale roughly linearly"
        
        # Cleanup
        protocol_path.unlink()
        
    def test_memory_persistence(self):
        """Test memory behavior with persistence."""
        from simulation_v2.core.simulation_runner import SimulationRunner
        from simulation_v2.protocols.protocol_spec import ProtocolSpecification
        import pickle
        
        protocol_path = Path(__file__).parent / "persist_protocol.yaml"
        protocol_path.write_text("""
name: Persistence Test
version: 1.0.0

disease_states:
  - name: active
disease_transitions:
  active:
    active: 1.0
treatment_effect_on_transitions:
  active:
    active: 1.0

min_interval_days: 42
max_interval_days: 42
extension_days: 0
shortening_days: 0

baseline_vision_mean: 70
baseline_vision_std: 5
baseline_vision_min: 60
baseline_vision_max: 80

max_injections_per_year: 9
loading_doses: 3
discontinuation_vision_threshold: 20
discontinuation_low_vision_prob: 0.1
discontinuation_rate_per_month: 0.01
""")
        
        spec = ProtocolSpecification.from_yaml(protocol_path)
        runner = SimulationRunner(spec)
        
        # Run simulation
        gc.collect()
        mem_before = self.get_memory_mb()
        
        results = runner.run("abs", 100, 1.0, seed=42)
        
        gc.collect()
        mem_with_results = self.get_memory_mb()
        
        # Pickle results (simulate session state storage)
        pickled = pickle.dumps(results)
        pickle_size_mb = len(pickled) / (1024 * 1024)
        
        # Unpickle (simulate page reload)
        restored = pickle.loads(pickled)
        
        gc.collect()
        mem_after_restore = self.get_memory_mb()
        
        print(f"\nPersistence memory usage:")
        print(f"  Before simulation: {mem_before:.1f} MB")
        print(f"  With results: {mem_with_results:.1f} MB")
        print(f"  Pickle size: {pickle_size_mb:.1f} MB")
        print(f"  After restore: {mem_after_restore:.1f} MB")
        
        # Verify restore doesn't double memory
        memory_ratio = (mem_after_restore - mem_before) / (mem_with_results - mem_before)
        assert memory_ratio < 2.5, "Restoring shouldn't more than double memory"
        
        # Cleanup
        protocol_path.unlink()
        
    @pytest.mark.slow
    def test_maximum_reasonable_size(self):
        """Test current maximum reasonable simulation size."""
        from simulation_v2.core.simulation_runner import SimulationRunner
        from simulation_v2.protocols.protocol_spec import ProtocolSpecification
        
        protocol_path = Path(__file__).parent / "max_protocol.yaml"
        protocol_path.write_text("""
name: Maximum Size Test
version: 1.0.0

disease_states:
  - name: active
disease_transitions:
  active:
    active: 1.0
treatment_effect_on_transitions:
  active:
    active: 1.0

min_interval_days: 42
max_interval_days: 84
extension_days: 14
shortening_days: 14

baseline_vision_mean: 70
baseline_vision_std: 10
baseline_vision_min: 40
baseline_vision_max: 90

max_injections_per_year: 9
loading_doses: 3
discontinuation_vision_threshold: 20
discontinuation_low_vision_prob: 0.2
discontinuation_rate_per_month: 0.02
""")
        
        spec = ProtocolSpecification.from_yaml(protocol_path)
        runner = SimulationRunner(spec)
        
        # Try progressively larger simulations
        max_working_size = 0
        
        for n_patients in [1000, 2000, 5000]:
            gc.collect()
            mem_before = self.get_memory_mb()
            
            try:
                print(f"\nTrying {n_patients} patients...")
                results = runner.run("abs", n_patients, 1.0, seed=42)
                
                gc.collect()
                mem_after = self.get_memory_mb()
                memory_used = mem_after - mem_before
                
                print(f"  Success! Memory used: {memory_used:.1f} MB")
                print(f"  Total injections: {results.total_injections}")
                
                max_working_size = n_patients
                
                # Cleanup
                del results
                gc.collect()
                
            except MemoryError:
                print(f"  Failed - out of memory")
                break
            except Exception as e:
                print(f"  Failed - {type(e).__name__}: {e}")
                break
        
        print(f"\nMaximum working size: {max_working_size} patients")
        
        # Cleanup
        protocol_path.unlink()
        
        # Record this as our baseline maximum
        assert max_working_size >= 1000, "Should handle at least 1000 patients currently"