# Files to preserve from fix/restore-app-and-streamgraph branch

## Core files:
- streamlit_app/app.py - Fixed page configuration placement
- streamlit_app/streamgraph_patient_states_fixed.py - Visualization fix for retreatment
- streamlit_app/retreatment_panel.py - Updated for proper retreatment visualization
- streamlit_app/simulation_runner.py - Compatibility updates

## New simulation framework:
- simulation/enhanced_des.py - Configuration-driven protocol parameters
- simulation/treat_and_extend_adapter.py - Adapter to integrate with enhanced DES
- enhanced_treat_and_extend_des.py - Integrated implementation
- simulation/staggered_enhanced_des.py - Staggered enrollment support
- staggered_treat_and_extend_enhanced_des.py - Staggered enrollment with T&E

## Validation scripts:
- validate_enhanced_des.py
- validate_treat_and_extend_adapter.py
- validate_enhanced_treat_and_extend_des.py
- validate_staggered_treat_and_extend_des.py
