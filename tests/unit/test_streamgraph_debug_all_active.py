"""
Debug tests to understand why all patients are showing as Active (Never Discontinued).
"""

import pytest
from datetime import datetime, timedelta
import numpy as np
from streamlit_app.streamgraph_list_format import count_patient_states_from_visits


class TestStreamgraphDebugAllActive:
    """Debug why visualization shows all patients as active"""
    
    @pytest.fixture
    def real_simulation_format(self):
        """Create data in the actual format from simulation results"""
        
        # Mimic the actual data structure from simulation
        patient_histories = {
            # Patient with various visit types
            "P001": [
                {
                    "date": datetime(2023, 1, 1),
                    "time": 0,
                    "vision": 60,
                    "is_discontinuation_visit": False,
                    "actions": ["vision_test", "injection"]
                },
                {
                    "date": datetime(2023, 2, 1), 
                    "time": 31,
                    "vision": 62,
                    "is_discontinuation_visit": False,
                    "actions": ["vision_test", "injection"]
                },
                {
                    "date": datetime(2023, 7, 1),
                    "time": 181,
                    "vision": 65,
                    "is_discontinuation_visit": True,
                    "discontinuation_reason": "patient_choice",
                    "actions": ["vision_test"]
                }
            ],
            
            # Patient with different field names
            "P002": [
                {
                    "date": datetime(2023, 1, 1),
                    "time": 0,
                    "vision_acuity": 55,  # Different field name
                    "discontinued": False,  # Different field name
                    "visit_type": "initial"
                },
                {
                    "date": datetime(2023, 3, 1),
                    "time": 59,
                    "vision_acuity": 58,
                    "discontinued": True,  # Different field name
                    "reason": "administrative",  # Different field name
                    "visit_type": "discontinuation"
                }
            ]
        }
        
        return {
            "patient_histories": patient_histories,
            "duration_years": 2
        }
    
    def test_discontinuation_field_names(self, real_simulation_format):
        """Test if the code is looking for the right discontinuation fields"""
        df = count_patient_states_from_visits(real_simulation_format)
        
        # Print what we actually get
        print("\nDataFrame contents:")
        print(df)
        
        # Check if any discontinuations are detected
        discontinued_states = df[df['state'].str.contains('discontinued')]
        print(f"\nDiscontinued states found: {len(discontinued_states)}")
        print(discontinued_states)
        
        # At month 6, P001 should be discontinued  
        month_6_data = df[df['time'] == 6]
        print(f"\nMonth 6 data:")
        print(month_6_data)
        
        # P001 discontinues at month 6, P002 at month 2
        assert len(discontinued_states) > 0, "Should find some discontinued states"
    
    def test_visit_structure_variations(self):
        """Test different possible visit structures"""
        
        # Variation 1: Using 'discontinued' boolean
        data1 = {
            "patient_histories": {
                "P001": [
                    {"time": 0, "vision": 60, "discontinued": False},
                    {"time": 30, "vision": 62, "discontinued": True, "discontinuation_type": "planned"}
                ]
            },
            "duration_years": 1
        }
        
        # Variation 2: Using 'state' field
        data2 = {
            "patient_histories": {
                "P001": [
                    {"time": 0, "vision": 60, "state": "active"},
                    {"time": 30, "vision": 62, "state": "discontinued", "discontinuation_reason": "planned"}
                ]
            },
            "duration_years": 1
        }
        
        # Variation 3: Using 'patient_state' field
        data3 = {
            "patient_histories": {
                "P001": [
                    {"time": 0, "vision": 60, "patient_state": "active"},
                    {"time": 30, "vision": 62, "patient_state": "discontinued_planned"}
                ]
            },
            "duration_years": 1
        }
        
        # Test each variation
        for i, data in enumerate([data1, data2, data3], 1):
            print(f"\nTesting variation {i}:")
            try:
                df = count_patient_states_from_visits(data)
                print(f"Variation {i} DataFrame:")
                print(df[df['state'].str.contains('discontinued')])
            except Exception as e:
                print(f"Variation {i} failed: {e}")
    
    def test_field_detection_logic(self, real_simulation_format):
        """Test the actual field detection logic"""
        patient_histories = real_simulation_format["patient_histories"]
        
        # Check what fields are actually present in the data
        all_fields = set()
        for patient_id, visits in patient_histories.items():
            for visit in visits:
                all_fields.update(visit.keys())
        
        print(f"\nAll fields found in patient data: {sorted(all_fields)}")
        
        # Check for discontinuation-related fields
        disc_fields = [f for f in all_fields if 'disc' in f.lower()]
        print(f"Discontinuation-related fields: {disc_fields}")
        
        # Check for state-related fields
        state_fields = [f for f in all_fields if 'state' in f.lower()]
        print(f"State-related fields: {state_fields}")
        
        # Check what the actual discontinuation visits look like
        for patient_id, visits in patient_histories.items():
            for i, visit in enumerate(visits):
                if any(key for key in visit.keys() if 'disc' in key.lower() and visit.get(key)):
                    print(f"\nDiscontinuation visit found for {patient_id}:")
                    print(f"Visit {i}: {visit}")
    
    def test_time_field_handling(self, real_simulation_format):
        """Test how time fields are being handled"""
        patient_histories = real_simulation_format["patient_histories"]
        
        # Check time field formats
        for patient_id, visits in patient_histories.items():
            print(f"\nPatient {patient_id} time fields:")
            for i, visit in enumerate(visits):
                time_val = visit.get("time", visit.get("date"))
                print(f"Visit {i}: time={time_val}, type={type(time_val)}")
                
                # Check if discontinuation info is present
                if visit.get("is_discontinuation_visit"):
                    print(f"  -> Discontinuation: {visit.get('discontinuation_reason')}")
    
    def test_retreatment_field_detection(self):
        """Test retreatment field detection"""
        data = {
            "patient_histories": {
                "P001": [
                    {"time": 0, "vision": 60, "is_discontinuation_visit": False},
                    {"time": 90, "vision": 58, "is_discontinuation_visit": True, 
                     "discontinuation_reason": "premature"},
                    {"time": 180, "vision": 59, "is_retreatment_visit": True},
                    {"time": 270, "vision": 61, "is_discontinuation_visit": False}
                ]
            },
            "duration_years": 1
        }
        
        df = count_patient_states_from_visits(data)
        
        # Check for retreatment states
        retreated_states = df[df['state'].str.contains('retreated')]
        print(f"\nRetreated states: {len(retreated_states)}")
        print(retreated_states)
        
        # At month 6 and beyond, should show as retreated
        month_6_data = df[df['time'] == 6]
        active_retreated = month_6_data[month_6_data['state'] == 'active_retreated']['count'].sum()
        
        assert active_retreated > 0, "Should have retreated patient at month 6"