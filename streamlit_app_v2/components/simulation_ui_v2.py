"""Enhanced simulation UI components with recruitment mode selection."""

import streamlit as st
from typing import Tuple, Dict, Any
import numpy as np

def render_recruitment_parameters() -> Dict[str, Any]:
    """
    Render recruitment mode selection and related parameters.
    
    Returns:
        Dictionary with recruitment parameters
    """
    st.subheader("Recruitment Settings")
    
    # Radio buttons for recruitment mode
    recruitment_mode = st.radio(
        "Recruitment Mode",
        ["Fixed Total", "Constant Rate"],
        index=0,
        horizontal=True,
        help="""
        **Fixed Total**: Specify the exact number of patients to recruit, distributed evenly over the simulation period.
        
        **Constant Rate**: Specify a recruitment rate that continues throughout the simulation.
        """
    )
    
    col1, col2, col3 = st.columns([2, 2, 3])
    
    recruitment_params = {
        'mode': recruitment_mode
    }
    
    if recruitment_mode == "Fixed Total":
        with col1:
            # Calculate default based on Constant Rate if switching back
            if 'expected_total' in st.session_state and st.session_state.get('previous_mode') == 'Constant Rate':
                default_patients = st.session_state.get('expected_total', 1000)
            else:
                default_patients = st.session_state.get('preset_patients', 1000)
                
            n_patients = st.number_input(
                "Total Patients",
                min_value=10,
                max_value=50000,
                value=default_patients,
                step=10,
                help="Total number of patients to recruit"
            )
            recruitment_params['n_patients'] = n_patients
            # Store for mode switching
            st.session_state.n_patients = n_patients
            
        with col2:
            duration_years = st.number_input(
                "Duration (Years)",
                min_value=0.5,
                max_value=20.0,
                value=st.session_state.get('preset_duration', 2.0),
                step=0.5,
                format="%.1f",
                help="Simulation duration in years"
            )
            recruitment_params['duration_years'] = duration_years
            
        with col3:
            # Calculate and display the rate
            rate_per_month = n_patients / (duration_years * 12)
            rate_per_week = n_patients / (duration_years * 52.14)
            
            st.info(f"""
            **Calculated rates:**
            - {rate_per_month:.1f} patients/month
            - {rate_per_week:.1f} patients/week
            
            Patients will be recruited throughout the entire {duration_years:.1f} year period.
            """)
            
    else:  # Constant Rate mode
        with col1:
            # For initial setup, we need to know the unit first to set proper limits
            # Check if there's a preset unit
            if 'rate_unit' in st.session_state:
                default_unit_index = 0 if st.session_state.rate_unit == "per week" else 1
                initial_rate_unit = st.session_state.rate_unit
            else:
                default_unit_index = 0
                initial_rate_unit = "per week"
            
            # Determine rate limits and defaults based on unit
            if initial_rate_unit == "per week":
                min_rate = 0.1
                max_rate = 1000.0
                step = 0.1
            else:  # per month
                min_rate = 1.0
                max_rate = 5000.0
                step = 1.0
            
            # Check for preset values first
            if 'recruitment_rate' in st.session_state and st.session_state.get('rate_unit') == initial_rate_unit:
                # Use preset value if it matches current unit
                default_rate = st.session_state.recruitment_rate
            elif 'n_patients' in st.session_state:
                # Convert from total patients to rate
                n_patients = st.session_state.get('n_patients', 1000)
                duration = st.session_state.get('preset_duration', 2.0)
                if initial_rate_unit == "per week":
                    calculated_rate = n_patients / (duration * 52.14)
                    default_rate = max(0.1, round(calculated_rate, 1))
                else:  # per month
                    calculated_rate = n_patients / (duration * 12)
                    default_rate = max(1.0, round(calculated_rate, 0))
            else:
                # Use sensible defaults
                default_rate = 20.0 if initial_rate_unit == "per week" else 80.0
                
            # Show the rate input first
            recruitment_rate = st.number_input(
                "Recruitment Rate",
                min_value=min_rate,
                max_value=max_rate,
                value=default_rate,
                step=step,
                help=f"Number of patients to recruit {initial_rate_unit}"
            )
            recruitment_params['recruitment_rate'] = recruitment_rate
            
            # Then show the unit selector below
            rate_unit = st.selectbox(
                "Rate Unit",
                ["per week", "per month"],
                index=default_unit_index,
                help="Choose whether to specify recruitment rate per week or per month"
            )
            recruitment_params['rate_unit'] = rate_unit
            
        with col2:
            # Duration in middle column, consistent with Fixed Total mode
            duration_years = st.number_input(
                "Duration (Years)",
                min_value=0.5,
                max_value=20.0,
                value=st.session_state.get('preset_duration', 2.0),
                step=0.5,
                format="%.1f",
                help="Simulation duration in years"
            )
            recruitment_params['duration_years'] = duration_years
            
        with col3:
            # Calculate expected total
            if rate_unit == "per week":
                expected_total = int(recruitment_rate * duration_years * 52.14)
                rate_per_day = recruitment_rate / 7.0
            else:  # per month
                expected_total = int(recruitment_rate * duration_years * 12)
                rate_per_day = recruitment_rate / 30.44
                
            recruitment_params['expected_total'] = expected_total
            recruitment_params['rate_per_day'] = rate_per_day
            
            # Store for mode switching
            st.session_state.expected_total = expected_total
            
            st.info(f"""
            **Expected total:** ~{expected_total:,} patients
            
            *Note: Actual count will vary due to random arrival times*
            
            Recruitment continues throughout the entire simulation period.
            """)
    
    # Track mode for intelligent switching
    st.session_state.previous_mode = recruitment_mode
    
    return recruitment_params


def render_enhanced_parameter_inputs() -> Tuple[str, Dict[str, Any], int]:
    """
    Render all simulation parameters including recruitment settings.
    
    Returns:
        Tuple of (engine_type, recruitment_params, seed)
    """
    # Engine selection
    col1, col2 = st.columns([1, 3])
    
    with col1:
        engine_type = st.selectbox(
            "Engine",
            ["abs", "des"],
            format_func=lambda x: {"abs": "Agent-Based", "des": "Discrete Event"}[x],
            index=0
        )
    
    with col2:
        seed = st.number_input(
            "Random Seed",
            min_value=0,
            max_value=999999,
            value=st.session_state.get('seed', 42),
            help="For reproducible results"
        )
    
    # Recruitment parameters
    recruitment_params = render_recruitment_parameters()
    
    # Add engine type to params for convenience
    recruitment_params['engine_type'] = engine_type
    recruitment_params['seed'] = seed
    
    return engine_type, recruitment_params, seed


def render_preset_buttons_v2():
    """Enhanced preset buttons that work with recruitment modes."""
    st.write("**Quick Presets:**")
    
    preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
    
    with preset_col1:
        if st.button("Small Trial", key="preset_small_v2", use_container_width=True,
                     help="100 patients over 2 years"):
            st.session_state.preset_patients = 100
            st.session_state.preset_duration = 2.0
            st.session_state.recruitment_mode = "Fixed Total"
            st.rerun()
    
    with preset_col2:
        if st.button("Medium Trial", key="preset_medium_v2", use_container_width=True,
                     help="500 patients over 3 years"):
            st.session_state.preset_patients = 500
            st.session_state.preset_duration = 3.0
            st.session_state.recruitment_mode = "Fixed Total"
            st.rerun()
    
    with preset_col3:
        if st.button("Large Trial", key="preset_large_v2", use_container_width=True,
                     help="2000 patients over 5 years"):
            st.session_state.preset_patients = 2000
            st.session_state.preset_duration = 5.0
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