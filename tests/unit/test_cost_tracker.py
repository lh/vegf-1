"""
Test suite for CostTracker class - following TDD approach.

These tests are written BEFORE the implementation to drive the design.
"""

import pytest
import pandas as pd
import json
from pathlib import Path
from simulation.economics import CostConfig, CostAnalyzer, CostTracker, CostEvent


class TestCostTracker:
    """Test suite for CostTracker class"""
    
    @pytest.fixture
    def cost_config(self):
        """Load test cost configuration"""
        config_path = Path("tests/fixtures/economics/test_cost_config.yaml")
        return CostConfig.from_yaml(config_path)
    
    @pytest.fixture
    def analyzer(self, cost_config):
        """Create analyzer with test configuration"""
        return CostAnalyzer(cost_config)
    
    @pytest.fixture
    def tracker(self, analyzer):
        """Create tracker with analyzer"""
        return CostTracker(analyzer)
    
    @pytest.fixture
    def sample_simulation_results(self):
        """Load sample simulation results"""
        # Create simulation results with multiple patients
        return {
            'patient_histories': {
                'patient_001': {
                    'patient_id': 'patient_001',
                    'visits': [
                        {
                            'type': 'injection',
                            'time': 0,
                            'drug': 'test_drug',
                            'metadata': {
                                'visit_subtype': 'injection_loading',
                                'phase': 'loading'
                            }
                        },
                        {
                            'type': 'injection',
                            'time': 1,
                            'drug': 'test_drug',
                            'metadata': {
                                'visit_subtype': 'injection_loading',
                                'phase': 'loading'
                            }
                        }
                    ]
                },
                'patient_002': {
                    'patient_id': 'patient_002',
                    'visits': [
                        {
                            'type': 'injection',
                            'time': 0,
                            'drug': 'eylea_2mg',
                            'metadata': {
                                'visit_subtype': 'injection_virtual',
                                'phase': 'maintenance'
                            }
                        },
                        {
                            'type': 'monitoring',
                            'time': 2,
                            'metadata': {
                                'components_performed': ['oct_scan', 'virtual_review']
                            }
                        }
                    ]
                }
            }
        }
    
    def test_process_patient_history(self, tracker, sample_simulation_results):
        """Test 3.1: Process complete patient history"""
        # When I process simulation results
        tracker.process_simulation_results(sample_simulation_results)
        
        # Then cost events should be created for all visits
        assert len(tracker.cost_events) == 4  # 2 patients × 2 visits each
        
        # Verify events are properly attributed to patients
        patient_001_events = [e for e in tracker.cost_events if e.patient_id == 'patient_001']
        patient_002_events = [e for e in tracker.cost_events if e.patient_id == 'patient_002']
        
        assert len(patient_001_events) == 2
        assert len(patient_002_events) == 2
        
    def test_get_patient_costs(self, tracker, sample_simulation_results):
        """Test 3.2: Calculate patient summary statistics"""
        # Given processed simulation results
        tracker.process_simulation_results(sample_simulation_results)
        
        # When I request costs for patient_001
        patient_costs_df = tracker.get_patient_costs('patient_001')
        
        # Then I should get a DataFrame with the right structure
        assert isinstance(patient_costs_df, pd.DataFrame)
        assert len(patient_costs_df) == 2
        
        # Check columns exist
        expected_columns = ['time', 'event_type', 'category', 'amount', 
                          'drug_cost', 'visit_cost', 'phase']
        for col in expected_columns:
            assert col in patient_costs_df.columns
        
        # Check data is correct
        assert patient_costs_df['time'].tolist() == [0, 1]
        assert patient_costs_df['amount'].tolist() == [160.0, 160.0]  # Both loading visits
        assert patient_costs_df['phase'].tolist() == ['loading', 'loading']
        
    def test_summary_statistics(self, tracker, sample_simulation_results):
        """Test 3.3: Generate population summary"""
        # Given processed simulation results
        tracker.process_simulation_results(sample_simulation_results)
        
        # When I request summary statistics
        summary = tracker.get_summary_statistics()
        
        # Then I should get comprehensive statistics
        assert summary['total_patients'] == 2
        assert summary['total_cost'] == 1250.0  # 160 + 160 + 890 + 40
        assert summary['avg_cost_per_patient'] == 625.0  # 1250 / 2
        
        # Check cost breakdowns
        assert 'cost_by_type' in summary
        assert summary['cost_by_type']['visit'] == 1250.0
        
        assert 'cost_by_category' in summary
        assert summary['cost_by_category']['injection_loading'] == 320.0  # 2 × 160
        assert summary['cost_by_category']['injection_virtual'] == 890.0
        assert summary['cost_by_category']['monitoring'] == 40.0
        
    def test_export_to_parquet(self, tracker, sample_simulation_results, tmp_path):
        """Test 3.4: Export to Parquet format"""
        # Given processed cost data
        tracker.process_simulation_results(sample_simulation_results)
        
        # When I export to Parquet
        output_dir = tmp_path / "test_output"
        output_dir.mkdir()
        tracker.export_to_parquet(output_dir)
        
        # Then I should get two parquet files
        assert (output_dir / 'cost_events.parquet').exists()
        assert (output_dir / 'cost_summary.parquet').exists()
        
        # Verify cost_events content
        events_df = pd.read_parquet(output_dir / 'cost_events.parquet')
        assert len(events_df) == 4
        assert 'patient_id' in events_df.columns
        assert 'time' in events_df.columns
        assert 'amount' in events_df.columns
        
        # Verify cost_summary content
        summary_df = pd.read_parquet(output_dir / 'cost_summary.parquet')
        assert len(summary_df) == 2  # One row per patient
        assert 'patient_id' in summary_df.columns
        assert 'total_cost' in summary_df.columns
        assert 'avg_cost_per_event' in summary_df.columns
        assert 'num_events' in summary_df.columns
        
        # Check summary calculations
        patient_001_rows = summary_df[summary_df['patient_id'] == 'patient_001']
        assert len(patient_001_rows) == 1
        patient_001_summary = patient_001_rows.iloc[0]
        assert patient_001_summary['total_cost'] == 320.0  # 2 × 160
        assert patient_001_summary['num_events'] == 2
        assert patient_001_summary['avg_cost_per_event'] == 160.0
        
    def test_empty_simulation_results(self, tracker):
        """Test handling empty simulation results"""
        # Given empty results
        empty_results = {'patient_histories': {}}
        
        # When I process them
        tracker.process_simulation_results(empty_results)
        
        # Then no errors should occur
        assert len(tracker.cost_events) == 0
        
        # And summary should handle empty data gracefully
        summary = tracker.get_summary_statistics()
        assert summary == {}
        
    def test_get_patient_costs_nonexistent(self, tracker, sample_simulation_results):
        """Test requesting costs for non-existent patient"""
        # Given processed results
        tracker.process_simulation_results(sample_simulation_results)
        
        # When I request costs for non-existent patient
        costs_df = tracker.get_patient_costs('nonexistent_patient')
        
        # Then I should get empty DataFrame
        assert isinstance(costs_df, pd.DataFrame)
        assert len(costs_df) == 0
        
    def test_component_cost_columns_in_export(self, tracker, tmp_path):
        """Test that component costs are exported as separate columns"""
        # Given a simulation with component costs
        results = {
            'patient_histories': {
                'patient_001': {
                    'patient_id': 'patient_001',
                    'visits': [
                        {
                            'type': 'monitoring',
                            'time': 0,
                            'metadata': {
                                'components_performed': ['oct_scan', 'virtual_review']
                            }
                        }
                    ]
                }
            }
        }
        
        # When I process and export
        tracker.process_simulation_results(results)
        output_dir = tmp_path / "test_output"
        output_dir.mkdir()
        tracker.export_to_parquet(output_dir)
        
        # Then component costs should be in separate columns
        events_df = pd.read_parquet(output_dir / 'cost_events.parquet')
        assert 'component_oct_scan' in events_df.columns
        assert 'component_virtual_review' in events_df.columns
        assert events_df.iloc[0]['component_oct_scan'] == 25.0
        assert events_df.iloc[0]['component_virtual_review'] == 15.0