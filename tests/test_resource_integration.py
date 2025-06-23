"""
Integration tests for resource tracking with time-based simulations.

Verifies that resource tracking integrates correctly without breaking simulations.
"""

import pytest
from pathlib import Path
from datetime import date

from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from simulation_v2.core.time_based_simulation_runner import TimeBasedSimulationRunner
from simulation_v2.core.time_based_simulation_runner_with_resources import TimeBasedSimulationRunnerWithResources
from simulation_v2.economics.resource_tracker import load_resource_config


class TestResourceIntegration:
    """Test resource tracking integration with simulations."""
    
    @pytest.fixture
    def tnt_protocol_path(self):
        """Path to T&T protocol."""
        return Path("protocols/v2_time_based/aflibercept_treat_and_treat_time_based.yaml")
    
    @pytest.fixture
    def resource_config_path(self):
        """Path to resource configuration."""
        return Path("protocols/resources/nhs_standard_resources.yaml")
    
    def test_simulation_with_resources_runs(self, tnt_protocol_path, resource_config_path):
        """Test that simulation runs with resource tracking enabled."""
        if not tnt_protocol_path.exists():
            pytest.skip(f"Protocol file not found: {tnt_protocol_path}")
        if not resource_config_path.exists():
            pytest.skip(f"Resource config not found: {resource_config_path}")
        
        # Load protocol
        spec = TimeBasedProtocolSpecification.from_yaml(tnt_protocol_path)
        
        # Create runner with resources
        runner = TimeBasedSimulationRunnerWithResources(
            spec, 
            resource_config_path=str(resource_config_path)
        )
        
        # Run small simulation
        results = runner.run(
            engine_type='abs',
            n_patients=10,
            duration_years=1,
            seed=42
        )
        
        # Basic checks
        assert results is not None
        assert results.patient_count >= 9  # Allow for slight variation
        assert results.total_injections > 0
        
        # Resource tracking checks
        assert hasattr(results, 'resource_usage')
        assert hasattr(results, 'total_costs')
        assert hasattr(results, 'workload_summary')
        assert hasattr(results, 'average_cost_per_patient_year')
        
        # Verify resource data collected
        assert len(results.resource_usage) > 0
        assert results.total_costs.get('total', 0) > 0
        assert results.workload_summary['total_visits'] > 0
    
    def test_results_match_without_resources(self, tnt_protocol_path):
        """Test that core results are identical with/without resource tracking."""
        if not tnt_protocol_path.exists():
            pytest.skip(f"Protocol file not found: {tnt_protocol_path}")
        
        spec = TimeBasedProtocolSpecification.from_yaml(tnt_protocol_path)
        
        # Run without resources
        runner_base = TimeBasedSimulationRunner(spec)
        results_base = runner_base.run('abs', n_patients=50, duration_years=2, seed=123)
        
        # Run with resources
        runner_resources = TimeBasedSimulationRunnerWithResources(spec)
        results_resources = runner_resources.run('abs', n_patients=50, duration_years=2, seed=123)
        
        # Core metrics must match
        assert results_base.total_injections == results_resources.total_injections
        assert results_base.final_vision_mean == results_resources.final_vision_mean
        assert results_base.discontinuation_rate == results_resources.discontinuation_rate
        assert results_base.patient_count == results_resources.patient_count
    
    def test_resource_data_reasonable(self, tnt_protocol_path, resource_config_path):
        """Test that resource data is reasonable and consistent."""
        if not tnt_protocol_path.exists():
            pytest.skip(f"Protocol file not found: {tnt_protocol_path}")
        if not resource_config_path.exists():
            pytest.skip(f"Resource config not found: {resource_config_path}")
        
        spec = TimeBasedProtocolSpecification.from_yaml(tnt_protocol_path)
        config = load_resource_config(str(resource_config_path))
        
        runner = TimeBasedSimulationRunnerWithResources(spec, resource_config=config)
        results = runner.run('abs', n_patients=100, duration_years=1, seed=456)
        
        # Check workload data
        workload = results.workload_summary
        
        # Should have injections
        assert workload['visits_by_type'].get('injection_only', 0) > 0
        
        # Check peak demand is reasonable
        assert workload['peak_daily_demand']['injector'] > 0
        assert workload['peak_daily_demand']['injector'] <= 20  # Reasonable daily peak
        
        # Check costs
        costs = results.total_costs
        assert costs['drug'] > 0  # Should have drug costs
        assert costs['injection_procedure'] > 0  # Should have procedure costs
        
        # Average cost per patient should be reasonable
        # Expecting ~7 injections in year 1 × (816 drug + 134 procedure) = ~6650
        assert 5000 < results.average_cost_per_patient_year < 10000
    
    def test_weekday_only_visits(self, tnt_protocol_path, resource_config_path):
        """Test that visits only occur on weekdays."""
        if not tnt_protocol_path.exists():
            pytest.skip(f"Protocol file not found: {tnt_protocol_path}")
        if not resource_config_path.exists():
            pytest.skip(f"Resource config not found: {resource_config_path}")
        
        spec = TimeBasedProtocolSpecification.from_yaml(tnt_protocol_path)
        runner = TimeBasedSimulationRunnerWithResources(
            spec,
            resource_config_path=str(resource_config_path)
        )
        
        results = runner.run('abs', n_patients=200, duration_years=0.5, seed=789)
        
        # Check all dates are weekdays
        for date_obj in results.resource_usage.keys():
            assert date_obj.weekday() < 5, f"Visit on weekend: {date_obj}"
    
    def test_visit_classification_correct(self, tnt_protocol_path, resource_config_path):
        """Test that visits are classified correctly."""
        if not tnt_protocol_path.exists():
            pytest.skip(f"Protocol file not found: {tnt_protocol_path}")
        if not resource_config_path.exists():
            pytest.skip(f"Resource config not found: {resource_config_path}")
        
        spec = TimeBasedProtocolSpecification.from_yaml(tnt_protocol_path)
        runner = TimeBasedSimulationRunnerWithResources(
            spec,
            resource_config_path=str(resource_config_path)
        )
        
        results = runner.run('abs', n_patients=20, duration_years=1.5, seed=999)
        
        # Check visit records
        if hasattr(results, 'visit_records'):
            # First 3 visits per patient should be injection_only
            patient_visits = {}
            for visit in results.visit_records:
                pid = visit['patient_id']
                if pid not in patient_visits:
                    patient_visits[pid] = []
                patient_visits[pid].append(visit)
            
            for pid, visits in patient_visits.items():
                if len(visits) >= 3:
                    # First 3 should be injection_only
                    for i in range(3):
                        assert visits[i]['visit_type'] == 'injection_only', \
                            f"Patient {pid} visit {i+1} not injection_only"
    
    def test_bottleneck_detection(self, tnt_protocol_path, resource_config_path):
        """Test that bottlenecks are detected when capacity exceeded."""
        if not tnt_protocol_path.exists():
            pytest.skip(f"Protocol file not found: {tnt_protocol_path}")
        if not resource_config_path.exists():
            pytest.skip(f"Resource config not found: {resource_config_path}")
        
        spec = TimeBasedProtocolSpecification.from_yaml(tnt_protocol_path)
        
        # Modify config to have very low capacity
        config = load_resource_config(str(resource_config_path))
        config['resources']['roles']['injector']['capacity_per_session'] = 2  # Very low
        
        runner = TimeBasedSimulationRunnerWithResources(spec, resource_config=config)
        results = runner.run('abs', n_patients=500, duration_years=0.25, seed=111)
        
        # Should detect bottlenecks
        assert len(results.bottlenecks) > 0
        
        # Check bottleneck structure
        bottleneck = results.bottlenecks[0]
        assert 'date' in bottleneck
        assert 'role' in bottleneck
        assert bottleneck['role'] == 'injector'  # Should be injector with low capacity
        assert bottleneck['sessions_needed'] > bottleneck['sessions_available']