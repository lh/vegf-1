"""
Tests for the new patient states streamgraph implementation.
"""

import pytest
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from streamlit_app.streamgraph_patient_states import (
    extract_patient_states, 
    aggregate_states_by_month,
    create_streamgraph,
    PATIENT_STATES
)


class TestStreamgraphPatientStates:
    """Test the new streamgraph implementation with correct state tracking"""
    
    @pytest.fixture
    def sample_patient_histories(self):
        """Create realistic patient histories with ABS discontinuation types"""
        return {
            # Patient who never discontinues
            "P001": [
                {"time": 0, "is_discontinuation_visit": False},
                {"time": 30, "is_discontinuation_visit": False},
                {"time": 180, "is_discontinuation_visit": False},
            ],
            
            # Patient with planned discontinuation and retreatment
            "P002": [
                {"time": 0, "is_discontinuation_visit": False},
                {"time": 90, "is_discontinuation_visit": True,
                 "discontinuation_reason": "stable_max_interval"},
                {"time": 180, "is_retreatment_visit": True},
                {"time": 360, "is_discontinuation_visit": True,
                 "discontinuation_reason": "premature"},
            ],
            
            # Patient with administrative discontinuation
            "P003": [
                {"time": 0, "is_discontinuation_visit": False},
                {"time": 60, "is_discontinuation_visit": True,
                 "discontinuation_reason": "random_administrative"},
            ],
            
            # Patient with course complete discontinuation
            "P004": [
                {"time": 0, "is_discontinuation_visit": False},
                {"time": 365, "is_discontinuation_visit": True,
                 "discontinuation_reason": "course_complete_but_not_renewed"},
            ],
            
            # Patient with premature discontinuation
            "P005": [
                {"time": 0, "is_discontinuation_visit": False},
                {"time": 120, "is_discontinuation_visit": True,
                 "discontinuation_reason": "premature"},
                {"time": 240, "is_retreatment_visit": True},
            ],
        }
    
    def test_extract_patient_states(self, sample_patient_histories):
        """Test that patient states are correctly extracted"""
        df = extract_patient_states(sample_patient_histories)
        
        # Check we have data for all patients
        assert len(df['patient_id'].unique()) == 5
        
        # Check P001 remains active throughout
        p1_states = df[df['patient_id'] == 'P001']['state'].unique()
        assert len(p1_states) == 1
        assert p1_states[0] == 'active'
        
        # Check P002 transitions correctly
        p2_states = df[df['patient_id'] == 'P002']['state'].tolist()
        assert p2_states[0] == 'active'
        assert p2_states[1] == 'discontinued_stable_max_interval'
        assert p2_states[2] == 'active_retreated_from_stable_max_interval'
        assert p2_states[3] == 'discontinued_premature'
        
        # Check P003 administrative discontinuation
        p3_states = df[df['patient_id'] == 'P003']['state'].tolist()
        assert p3_states[-1] == 'discontinued_random_administrative'
        
        # Check P004 course complete
        p4_states = df[df['patient_id'] == 'P004']['state'].tolist()
        assert p4_states[-1] == 'discontinued_course_complete_but_not_renewed'
        
        # Check P005 premature then retreated
        p5_states = df[df['patient_id'] == 'P005']['state'].tolist()
        assert p5_states[1] == 'discontinued_premature'
        assert p5_states[2] == 'active_retreated_from_premature'
    
    def test_aggregate_states_by_month(self, sample_patient_histories):
        """Test monthly aggregation of patient states"""
        patient_states_df = extract_patient_states(sample_patient_histories)
        monthly_counts = aggregate_states_by_month(patient_states_df, 12)
        
        # At month 0, all should be active
        month_0 = monthly_counts[monthly_counts['time_months'] == 0]
        active_count = month_0[month_0['state'] == 'active']['count'].sum()
        assert active_count == 5
        
        # At month 3, check specific states
        month_3 = monthly_counts[monthly_counts['time_months'] == 3]
        
        # P002 should be discontinued_stable_max_interval
        stable_disc = month_3[month_3['state'] == 'discontinued_stable_max_interval']['count'].sum()
        assert stable_disc >= 1
        
        # P003 should be discontinued_random_administrative
        admin_disc = month_3[month_3['state'] == 'discontinued_random_administrative']['count'].sum()
        assert admin_disc >= 1
        
        # Check total conservation
        total_month_3 = month_3['count'].sum()
        assert total_month_3 == 5
    
    def test_all_states_represented(self, sample_patient_histories):
        """Test that all expected states can be represented"""
        patient_states_df = extract_patient_states(sample_patient_histories)
        all_states = patient_states_df['state'].unique()
        
        # We should see these states in our test data
        expected_states = {
            'active',
            'discontinued_stable_max_interval',
            'discontinued_random_administrative',
            'discontinued_course_complete_but_not_renewed',
            'discontinued_premature',
            'active_retreated_from_stable_max_interval',
            'active_retreated_from_premature'
        }
        
        for state in expected_states:
            assert state in all_states, f"Missing expected state: {state}"
    
    def test_retreatment_state_tracking(self, sample_patient_histories):
        """Test that retreatment states correctly track previous discontinuation"""
        patient_states_df = extract_patient_states(sample_patient_histories)
        
        # P002: stable_max_interval -> retreated from stable
        p2_retreated = patient_states_df[
            (patient_states_df['patient_id'] == 'P002') & 
            (patient_states_df['state'].str.contains('retreated'))
        ]
        assert len(p2_retreated) > 0
        assert p2_retreated.iloc[0]['state'] == 'active_retreated_from_stable_max_interval'
        
        # P005: premature -> retreated from premature
        p5_retreated = patient_states_df[
            (patient_states_df['patient_id'] == 'P005') & 
            (patient_states_df['state'].str.contains('retreated'))
        ]
        assert len(p5_retreated) > 0
        assert p5_retreated.iloc[0]['state'] == 'active_retreated_from_premature'
    
    def test_datetime_handling(self):
        """Test handling of datetime-based visit times"""
        start_date = datetime(2023, 1, 1)
        
        patient_histories = {
            "P001": [
                {"time": start_date, "date": start_date, 
                 "is_discontinuation_visit": False},
                {"time": start_date + timedelta(days=90), 
                 "date": start_date + timedelta(days=90),
                 "is_discontinuation_visit": True,
                 "discontinuation_reason": "premature"},
            ]
        }
        
        df = extract_patient_states(patient_histories)
        # Should handle datetime objects without error
        assert len(df) == 2
        
        # Test aggregation with datetime
        monthly = aggregate_states_by_month(df, 12)
        assert len(monthly) > 0
    
    def test_create_streamgraph_integration(self, sample_patient_histories):
        """Test the full streamgraph creation"""
        results = {
            "patient_histories": sample_patient_histories,
            "duration_years": 2
        }
        
        fig = create_streamgraph(results)
        
        # Should create a figure without error
        assert fig is not None
        
        # Should have the correct title
        assert fig.axes[0].get_title() == 'Patient Treatment Status Over Time'
    
    def test_state_ordering(self):
        """Test that states are ordered correctly in visualization"""
        # All defined states should be in the correct order for stacking
        assert len(PATIENT_STATES) == 9
        
        # Active states should come first
        assert PATIENT_STATES[0] == "active"
        assert all(state.startswith("active_retreated") for state in PATIENT_STATES[1:5])
        
        # Discontinued states should come after
        assert all(state.startswith("discontinued") for state in PATIENT_STATES[5:9])