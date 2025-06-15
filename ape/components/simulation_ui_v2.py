"""Enhanced simulation UI components with recruitment mode selection."""

import streamlit as st
from typing import Tuple, Dict, Any
import numpy as np

def render_recruitment_parameters() -> Dict[str, Any]:
    """
    Render recruitment parameters with smart dependency.
    
    Returns:
        Dictionary with recruitment parameters
    """
    # Use four columns for all recruitment parameters
    col1, col2, col3, col4 = st.columns(4)
    
    # Initialize tracking for which field was last edited
    if 'last_edited_field' not in st.session_state:
        st.session_state.last_edited_field = 'total'  # Default to total-driven
    
    # Get stored values or defaults
    stored_total = st.session_state.get('n_patients', 
                   st.session_state.get('preset_patients', 1000))
    stored_rate = st.session_state.get('recruitment_rate', 80.0)
    stored_duration = st.session_state.get('duration_years',
                      st.session_state.get('preset_duration', 2.0))
    
    # Handle preset values
    if 'preset_patients' in st.session_state:
        stored_total = st.session_state.preset_patients
        st.session_state.last_edited_field = 'total'
        # Store the preset value as the current value
        st.session_state.n_patients = stored_total
        del st.session_state.preset_patients
    
    if 'recruitment_rate' in st.session_state and 'rate_unit' in st.session_state:
        # Convert from weekly if needed
        if st.session_state.rate_unit == "per week":
            stored_rate = st.session_state.recruitment_rate * 4.345
        else:
            stored_rate = st.session_state.recruitment_rate
        st.session_state.last_edited_field = 'rate'
        # Store the preset value as the current value
        st.session_state.recruitment_rate = stored_rate
        if 'rate_unit' in st.session_state:
            del st.session_state.rate_unit
    
    # Always calculate both values for display
    calculated_rate = stored_total / (stored_duration * 12)
    calculated_total = int(stored_rate * stored_duration * 12)
    
    with col1:
        # Show total - track if it was edited
        if st.session_state.last_edited_field == 'total':
            display_total = stored_total
        else:
            display_total = calculated_total
            
        def on_total_change():
            st.session_state.last_edited_field = 'total'
            st.session_state.n_patients = st.session_state.total_input
            
        n_patients = st.number_input(
            "Total Patients",
            min_value=10,
            max_value=50000,
            value=display_total,
            step=1,
            help="Total number of patients to recruit",
            key="total_input",
            on_change=on_total_change
        )
            
    with col2:
        # Show rate - track if it was edited
        if st.session_state.last_edited_field == 'rate':
            display_rate = stored_rate
        else:
            display_rate = calculated_rate
            
        # Ensure display rate meets minimum constraint
        display_rate_clamped = max(1.0, round(display_rate, 1))
        
        def on_rate_change():
            st.session_state.last_edited_field = 'rate'
            st.session_state.recruitment_rate = st.session_state.rate_input
            
        recruitment_rate = st.number_input(
            "Monthly Rate",
            min_value=1.0,
            max_value=5000.0,
            value=display_rate_clamped,
            step=1.0,
            help="Patients to recruit per month (minimum of 1)",
            key="rate_input",
            on_change=on_rate_change
        )
            
    with col3:
        def on_duration_change():
            st.session_state.duration_years = st.session_state.duration_input
            
        duration_years = st.number_input(
            "Years",
            min_value=1,
            max_value=20,
            value=int(stored_duration),
            step=1,
            help="Simulation duration in years",
            key="duration_input",
            on_change=on_duration_change
        )
    
    with col4:
        # Create two sub-columns for seed input and randomize button
        seed_col1, seed_col2 = st.columns([5, 1])
        
        with seed_col1:
            seed = st.number_input(
                "Random Seed",
                min_value=0,
                max_value=999999,
                value=st.session_state.get('seed', 42),
                help="For reproducible results",
                key="seed_input"
            )
            st.session_state.seed = seed
        
        with seed_col2:
            # Add some vertical spacing to align with the input
            st.write("")  # Empty space
            if st.button("🎲", key="randomize_seed", help="Generate random seed"):
                import random
                st.session_state.seed = random.randint(0, 999999)
                st.rerun()
    
    # Build recruitment parameters based on which field is primary
    recruitment_params = {
        'duration_years': st.session_state.get('duration_years', stored_duration),
        'seed': st.session_state.get('seed', 42)
    }
    
    if st.session_state.last_edited_field == 'total':
        # Total is primary - Fixed Total mode
        recruitment_params['mode'] = 'Fixed Total'
        recruitment_params['n_patients'] = st.session_state.get('n_patients', stored_total)
        recruitment_params['engine_type'] = st.session_state.get('engine_type', 'abs')
    else:
        # Rate is primary - Constant Rate mode
        recruitment_params['mode'] = 'Constant Rate'
        recruitment_params['recruitment_rate'] = st.session_state.get('recruitment_rate', stored_rate)
        recruitment_params['rate_unit'] = 'per month'
        recruitment_params['expected_total'] = int(st.session_state.get('recruitment_rate', stored_rate) * recruitment_params['duration_years'] * 12)
        recruitment_params['rate_per_day'] = st.session_state.get('recruitment_rate', stored_rate) / 30.44
        recruitment_params['engine_type'] = st.session_state.get('engine_type', 'abs')
    
    # Clean up preset duration after using it
    if 'preset_duration' in st.session_state:
        # Make sure it's stored as the current duration
        st.session_state.duration_years = st.session_state.preset_duration
        del st.session_state.preset_duration
    if 'recruitment_mode' in st.session_state:
        del st.session_state.recruitment_mode
    
    return recruitment_params


def render_enhanced_parameter_inputs() -> Tuple[str, Dict[str, Any], int]:
    """
    Render all simulation parameters including recruitment settings.
    
    Returns:
        Tuple of (engine_type, recruitment_params, seed)
    """
    # Get engine type from session state (set by the engine selector in quick start box)
    engine_type = st.session_state.get('engine_type', 'abs')
    
    # Recruitment parameters (now includes seed)
    recruitment_params = render_recruitment_parameters()
    
    # Add engine type to params for convenience
    recruitment_params['engine_type'] = engine_type
    
    # Extract seed for return value compatibility
    seed = recruitment_params['seed']
    
    return engine_type, recruitment_params, seed


def render_preset_buttons_v2():
    """Enhanced preset buttons that work with recruitment modes."""
    st.write("**Quick Presets:**")
    
    preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
    
    with preset_col1:
        if st.button("Small Trial", key="preset_small_v2", use_container_width=True,
                     help="100 patients over 2 years"):
            st.session_state.preset_patients = 100
            st.session_state.preset_duration = 2
            st.session_state.recruitment_mode = "Fixed Total"
            st.rerun()
    
    with preset_col2:
        if st.button("Medium Trial", key="preset_medium_v2", use_container_width=True,
                     help="500 patients over 3 years"):
            st.session_state.preset_patients = 500
            st.session_state.preset_duration = 3
            st.session_state.recruitment_mode = "Fixed Total"
            st.rerun()
    
    with preset_col3:
        if st.button("Large Trial", key="preset_large_v2", use_container_width=True,
                     help="2000 patients over 5 years"):
            st.session_state.preset_patients = 2000
            st.session_state.preset_duration = 5
            st.session_state.recruitment_mode = "Fixed Total"
            st.rerun()
    
    with preset_col4:
        if st.button("Real-World", key="preset_rw_v2", use_container_width=True,
                     help="20 patients/week ongoing"):
            st.session_state.recruitment_rate = 20.0
            st.session_state.rate_unit = "per week"
            st.session_state.preset_duration = 5.0
            st.session_state.recruitment_mode = "Constant Rate"
            st.rerun()


def calculate_runtime_estimate_v2(recruitment_params: Dict[str, Any]) -> str:
    """Calculate runtime estimate based on recruitment parameters."""
    if recruitment_params['mode'] == "Fixed Total":
        n_patients = recruitment_params['n_patients']
    else:
        n_patients = recruitment_params.get('expected_total', 1000)
    
    duration_years = recruitment_params['duration_years']
    
    # Rough estimate
    estimated_seconds = (n_patients * duration_years) / 1000
    
    if estimated_seconds < 1:
        return "< 1 second"
    elif estimated_seconds < 60:
        return f"~{estimated_seconds:.0f} seconds"
    else:
        return f"~{estimated_seconds/60:.1f} minutes"