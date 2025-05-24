"""
Tests to verify patient state data at specific time points for streamgraph visualization.
"""

import pytest
from datetime import datetime, timedelta
import numpy as np
from streamlit_app.streamgraph_list_format import count_patient_states_from_visits


class TestStreamgraphPatientStates:
    """Test patient state tracking at specific time points"""
    
    @pytest.fixture
    def sample_simulation_results(self):
        """Create sample simulation results with known discontinuation patterns"""
        
        # Create patient histories with various states
        patient_histories = {
            # Patient who remains active throughout
            "P001": [
                {"time": timedelta(days=0), "vision": 60, "is_discontinuation_visit": False},
                {"time": timedelta(days=30), "vision": 65, "is_discontinuation_visit": False},
                {"time": timedelta(days=180), "vision": 68, "is_discontinuation_visit": False},
                {"time": timedelta(days=720), "vision": 70, "is_discontinuation_visit": False},
            ],
            
            # Patient who discontinues early (planned)
            "P002": [
                {"time": timedelta(days=0), "vision": 50, "is_discontinuation_visit": False},
                {"time": timedelta(days=30), "vision": 55, "is_discontinuation_visit": False},
                {"time": timedelta(days=60), "vision": 58, "is_discontinuation_visit": True,
                 "discontinuation_reason": "patient_choice", "discontinuation_type": "planned"},
            ],
            
            # Patient who discontinues administratively
            "P003": [
                {"time": timedelta(days=0), "vision": 45, "is_discontinuation_visit": False},
                {"time": timedelta(days=30), "vision": 48, "is_discontinuation_visit": False},
                {"time": timedelta(days=180), "vision": 50, "is_discontinuation_visit": True,
                 "discontinuation_reason": "administrative", "discontinuation_type": "administrative"},
            ],
            
            # Patient who discontinues and then retreats
            "P004": [
                {"time": timedelta(days=0), "vision": 55, "is_discontinuation_visit": False},
                {"time": timedelta(days=180), "vision": 60, "is_discontinuation_visit": True,
                 "discontinuation_reason": "premature", "discontinuation_type": "premature"},
                {"time": timedelta(days=270), "vision": 58, "is_discontinuation_visit": False,
                 "is_retreatment_visit": True},
                {"time": timedelta(days=365), "vision": 62, "is_discontinuation_visit": False},
            ],
            
            # Patient who discontinues premature
            "P005": [
                {"time": timedelta(days=0), "vision": 52, "is_discontinuation_visit": False},
                {"time": timedelta(days=30), "vision": 54, "is_discontinuation_visit": False},
                {"time": timedelta(days=365), "vision": 56, "is_discontinuation_visit": True,
                 "discontinuation_reason": "premature", "discontinuation_type": "premature"},
            ],
        }
        
        return {
            "patient_histories": patient_histories,
            "duration_years": 2
        }
    
    def test_patient_states_at_time_zero(self, sample_simulation_results):
        """Test that all patients are active at time 0"""
        df = count_patient_states_from_visits(sample_simulation_results)
        
        # At time 0, all 5 patients should be active
        month_0_data = df[df['time'] == 0]
        assert len(month_0_data) > 0, "No data for month 0"
        
        # Check that we have patient count data
        active_states = month_0_data[month_0_data['state'] == 'active']
        assert len(active_states) == 1, "Should have exactly one active state row"
        assert active_states.iloc[0]['count'] == 5, "All 5 patients should be active at month 0"
        
        # Check no discontinued patients at start
        discontinued_states = month_0_data[month_0_data['state'].str.contains('discontinued')]
        assert discontinued_states['count'].sum() == 0, "No patients should be discontinued at month 0"
    
    def test_patient_states_at_one_month(self, sample_simulation_results):
        """Test patient states at 1 month"""
        df = count_patient_states_from_visits(sample_simulation_results)
        
        month_1_data = df[df['time'] == 1]
        assert len(month_1_data) > 0, "No data for month 1"
        
        # At 1 month, all patients should still be active (no discontinuations yet)
        active_states = month_1_data[month_1_data['state'] == 'active']
        assert active_states.iloc[0]['count'] == 5, "All 5 patients should still be active at month 1"
        
        # Verify no discontinuations
        discontinued_states = month_1_data[month_1_data['state'].str.contains('discontinued')]
        assert discontinued_states['count'].sum() == 0, "No patients should be discontinued at month 1"
    
    def test_patient_states_at_six_months(self, sample_simulation_results):
        """Test patient states at 6 months"""
        df = count_patient_states_from_visits(sample_simulation_results)
        
        month_6_data = df[df['time'] == 6]
        assert len(month_6_data) > 0, "No data for month 6"
        
        # At 6 months:
        # - P001: active
        # - P002: discontinued (planned) at month 2
        # - P003: active (discontinues at month 6)
        # - P004: active (discontinues at month 6)
        # - P005: active
        
        active_count = month_6_data[month_6_data['state'] == 'active']['count'].sum()
        planned_disc_count = month_6_data[month_6_data['state'] == 'discontinued_planned']['count'].sum()
        admin_disc_count = month_6_data[month_6_data['state'] == 'discontinued_administrative']['count'].sum()
        premature_disc_count = month_6_data[month_6_data['state'] == 'discontinued_premature']['count'].sum()
        
        # Check expected counts
        assert active_count == 3, f"Expected 3 active patients at month 6, got {active_count}"
        assert planned_disc_count == 1, f"Expected 1 planned discontinuation, got {planned_disc_count}"
        assert admin_disc_count == 1, f"Expected 1 administrative discontinuation, got {admin_disc_count}"
        assert premature_disc_count == 0, f"Expected 0 premature discontinuations, got {premature_disc_count}"
        
        # Verify total population conservation
        total_patients = month_6_data['count'].sum()
        assert total_patients == 5, f"Total patient count should be 5, got {total_patients}"
    
    def test_patient_states_at_two_years(self, sample_simulation_results):
        """Test patient states at 2 years (24 months)"""
        df = count_patient_states_from_visits(sample_simulation_results)
        
        month_24_data = df[df['time'] == 24]
        assert len(month_24_data) > 0, "No data for month 24"
        
        # At 24 months:
        # - P001: active
        # - P002: discontinued (planned)
        # - P003: discontinued (administrative)
        # - P004: active_retreated (discontinued then retreated)
        # - P005: discontinued (premature)
        
        active_count = month_24_data[month_24_data['state'] == 'active']['count'].sum()
        active_retreated_count = month_24_data[month_24_data['state'] == 'active_retreated']['count'].sum()
        all_discontinued = month_24_data[month_24_data['state'].str.contains('discontinued')]['count'].sum()
        
        assert active_count == 1, f"Expected 1 active patient at month 24, got {active_count}"
        assert active_retreated_count == 1, f"Expected 1 retreated patient, got {active_retreated_count}"
        assert all_discontinued == 3, f"Expected 3 discontinued patients, got {all_discontinued}"
        
        # Check specific discontinuation types
        planned_disc = month_24_data[month_24_data['state'] == 'discontinued_planned']['count'].sum()
        admin_disc = month_24_data[month_24_data['state'] == 'discontinued_administrative']['count'].sum()
        premature_disc = month_24_data[month_24_data['state'] == 'discontinued_premature']['count'].sum()
        
        assert planned_disc == 1, f"Expected 1 planned discontinuation, got {planned_disc}"
        assert admin_disc == 1, f"Expected 1 administrative discontinuation, got {admin_disc}"
        assert premature_disc == 1, f"Expected 1 premature discontinuation, got {premature_disc}"
        
        # Verify population conservation
        total_patients = month_24_data['count'].sum()
        assert total_patients == 5, f"Total patient count should be 5, got {total_patients}"
    
    def test_retreatment_tracking(self, sample_simulation_results):
        """Test that retreatments are properly tracked"""
        df = count_patient_states_from_visits(sample_simulation_results)
        
        # Check at month 9 (after P004 retreats)
        month_9_data = df[df['time'] == 9]
        
        # P004 should be in active_retreated state
        active_retreated = month_9_data[month_9_data['state'] == 'active_retreated']['count'].sum()
        assert active_retreated >= 1, "Should have at least 1 retreated patient at month 9"
    
    def test_discontinuation_reasons_tracked(self, sample_simulation_results):
        """Test that different discontinuation reasons are properly categorized"""
        df = count_patient_states_from_visits(sample_simulation_results)
        
        # Get all unique states
        all_states = df['state'].unique()
        
        # Verify we have expected discontinuation states
        expected_disc_states = [
            'discontinued_planned',
            'discontinued_administrative', 
            'discontinued_premature'
        ]
        
        for state in expected_disc_states:
            assert state in all_states, f"Missing expected state: {state}"
    
    def test_data_structure_validation(self, sample_simulation_results):
        """Test that the data structure matches expected format"""
        df = count_patient_states_from_visits(sample_simulation_results)
        
        # Check DataFrame structure
        expected_columns = ['time', 'state', 'count']
        assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {df.columns}"
        
        # Check data types
        assert df['time'].dtype in [int, np.int64], "Time should be integer (months)"
        assert df['state'].dtype == object, "State should be string/object"
        assert df['count'].dtype in [int, np.int64], "Count should be integer"
        
        # Check time range
        assert df['time'].min() == 0, "Time should start at 0"
        assert df['time'].max() == 24, "Time should end at 24 months for 2-year simulation"