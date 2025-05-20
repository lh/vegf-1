"""
Test with actual simulation data format to understand the structure.
"""

import pytest
from datetime import datetime, timedelta
import numpy as np
from streamlit_app.streamgraph_list_format import count_patient_states_from_visits


class TestStreamgraphRealDataFormat:
    """Test with actual simulation data structures"""
    
    def test_print_actual_data_structure(self):
        """Create minimal test to print actual data structure"""
        
        # Create test data that mimics real simulation output
        test_data = {
            "patient_histories": {
                "P001": [
                    {
                        "time": 0,
                        "date": datetime(2023, 1, 1),
                        "vision": 60,
                        "is_discontinuation_visit": False,
                        "actions": ["vision_test"]
                    },
                    {
                        "time": 30,
                        "date": datetime(2023, 2, 1),
                        "vision": 62,
                        "is_discontinuation_visit": True,
                        "discontinuation_reason": "planned",
                        "discontinuation_type": "patient_choice",
                        "actions": ["vision_test"]
                    }
                ]
            },
            "duration_years": 1
        }
        
        print("\nTest data structure:")
        print(f"Keys in results: {test_data.keys()}")
        print(f"Patient IDs: {list(test_data['patient_histories'].keys())}")
        print(f"First patient visits: {test_data['patient_histories']['P001']}")
        
        # Run the counting function
        df = count_patient_states_from_visits(test_data)
        print("\nResulting DataFrame:")
        print(df)
        
        # Check specific months
        month_0 = df[df['time'] == 0]
        month_1 = df[df['time'] == 1]
        
        print(f"\nMonth 0 states:")
        print(month_0)
        
        print(f"\nMonth 1 states:")
        print(month_1)
        
        # Assertions
        assert len(df) > 0, "Should produce some data"
        assert 'discontinued_planned' in df['state'].values, "Should detect planned discontinuation"
    
    def test_key_field_names(self):
        """Test the key field names that might vary"""
        
        field_variations = [
            # Variation 1: Standard format
            {
                "is_discontinuation_visit": True,
                "discontinuation_reason": "planned",
                "discontinuation_type": "patient_choice"
            },
            
            # Variation 2: Alternative naming
            {
                "discontinued": True,
                "reason": "planned",
                "type": "patient_choice"
            },
            
            # Variation 3: State-based
            {
                "patient_state": "discontinued",
                "state_reason": "planned",
                "state_type": "patient_choice"
            },
            
            # Variation 4: Action-based
            {
                "actions": ["discontinue"],
                "discontinuation_data": {
                    "reason": "planned",
                    "type": "patient_choice"
                }
            }
        ]
        
        for i, fields in enumerate(field_variations):
            print(f"\nField variation {i+1}:")
            print(fields)
            
            # Check which discontinuation indicators might be present
            disc_indicators = [
                fields.get("is_discontinuation_visit"),
                fields.get("discontinued"),
                fields.get("patient_state") == "discontinued",
                "discontinue" in fields.get("actions", [])
            ]
            
            print(f"Discontinuation indicators: {disc_indicators}")
            print(f"Any True: {any(disc_indicators)}")
    
    def test_check_streamgraph_logic(self):
        """Test the actual logic in the streamgraph counting function"""
        
        # Create test with explicit discontinuation
        test_data = {
            "patient_histories": {
                "P001": [
                    {"time": 0, "is_discontinuation_visit": False},
                    {"time": 30, "is_discontinuation_visit": True, 
                     "discontinuation_reason": "patient_choice",
                     "discontinuation_type": "planned"}
                ],
                "P002": [
                    {"time": 0, "is_discontinuation_visit": False},
                    {"time": 60, "is_discontinuation_visit": True,
                     "discontinuation_reason": "administrative", 
                     "discontinuation_type": "administrative"}
                ]
            },
            "duration_years": 1
        }
        
        df = count_patient_states_from_visits(test_data)
        
        # Group by time and state for analysis
        summary = df.groupby(['time', 'state'])['count'].sum().reset_index()
        print("\nSummary by time and state:")
        print(summary)
        
        # Check specific assertions
        month_0_active = df[(df['time'] == 0) & (df['state'] == 'active')]['count'].sum()
        month_1_disc = df[(df['time'] == 1) & (df['state'].str.contains('discontinued'))]['count'].sum()
        month_2_disc = df[(df['time'] == 2) & (df['state'].str.contains('discontinued'))]['count'].sum()
        
        assert month_0_active == 2, f"Should have 2 active at month 0, got {month_0_active}"
        assert month_1_disc >= 1, f"Should have at least 1 discontinued at month 1, got {month_1_disc}"
        assert month_2_disc >= 2, f"Should have at least 2 discontinued at month 2, got {month_2_disc}"