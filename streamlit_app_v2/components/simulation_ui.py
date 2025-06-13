"""
Simulation UI Components.

Reusable UI components for the Simulations page.
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Any, List, Tuple
from core.results.factory import ResultsFactory
from utils.carbon_button_helpers import ape_button
from utils.simulation_loader import load_simulation_results

try:
    import pendulum
    HAS_PENDULUM = True
except ImportError:
    HAS_PENDULUM = False


def format_timestamp(timestamp_str: str) -> str:
    """
    Format a timestamp string into a human-friendly format.
    
    Examples:
        "2025-06-07T23:20:49" -> "2 hours ago"
        "2025-06-07T23:20:49" -> "Yesterday at 11:20 PM"
        "2025-05-07T23:20:49" -> "May 7 at 11:20 PM"
    """
    if not timestamp_str or timestamp_str == 'Unknown':
        return 'Unknown'
    
    try:
        if HAS_PENDULUM:
            # Parse the timestamp - treat naive timestamps as local time
            dt = pendulum.parse(timestamp_str, tz='local')
            now = pendulum.now()
            
            # Use pendulum's human-friendly formatting
            diff_days = (now - dt).days
            
            if diff_days == 0:
                # Today - show relative time
                return dt.diff_for_humans()
            elif diff_days == 1:
                # Yesterday
                return f"Yesterday at {dt.format('h:mm A')}"
            elif diff_days < 7:
                # This week
                return dt.format('dddd [at] h:mm A')
            elif diff_days < 30:
                # This month
                return dt.format('MMM D [at] h:mm A')
            else:
                # Older
                return dt.format('MMM D, YYYY')
        else:
            # Fallback to basic formatting
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return timestamp_str[:19]  # Just return the date part if parsing fails


def render_preset_buttons():
    """Render simulation preset buttons (Small/Medium/Large/XL)"""
    preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)

    with preset_col1:
        if ape_button("Small", key="preset_small", full_width=True, 
                     help_text="100 patients, 1 year"):
            st.session_state.preset_patients = 100
            st.session_state.preset_duration = 1.0
            st.rerun()

    with preset_col2:
        if ape_button("Medium", key="preset_medium", full_width=True,
                     help_text="500 patients, 2 years"):
            st.session_state.preset_patients = 500
            st.session_state.preset_duration = 2.0
            st.rerun()

    with preset_col3:
        if ape_button("Large", key="preset_large", full_width=True,
                     help_text="2000 patients, 5 years"):
            st.session_state.preset_patients = 2000
            st.session_state.preset_duration = 5.0
            st.rerun()

    with preset_col4:
        if ape_button("Extra Large", key="preset_xl", full_width=True,
                     help_text="10000 patients, 10 years"):
            st.session_state.preset_patients = 10000
            st.session_state.preset_duration = 10.0
            st.rerun()


def render_parameter_inputs() -> Tuple[str, int, float, int]:
    """
    Render simulation parameter inputs.
    
    Returns:
        Tuple of (engine_type, n_patients, duration_years, seed)
    """
    col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1.5])

    with col1:
        # Use current simulation parameters if loaded, otherwise use simple values
        if ('simulation_results' in st.session_state and 
            st.session_state.simulation_results is not None and 
            'parameters' in st.session_state.simulation_results):
            engine_value = st.session_state.simulation_results['parameters']['engine']
            engine_index = 0 if engine_value == "abs" else 1
        else:
            engine_index = 0  # Start with ABS
        
        engine_type = st.selectbox(
            "Engine",
            ["abs", "des"],
            format_func=lambda x: {"abs": "Agent-Based", "des": "Discrete Event"}[x],
            index=engine_index
        )

    with col2:
        # Check for preset from buttons FIRST, then fall back to current simulation
        if 'preset_patients' in st.session_state:
            patients_value = st.session_state.preset_patients
        elif ('simulation_results' in st.session_state and 
              st.session_state.simulation_results is not None and 
              'parameters' in st.session_state.simulation_results):
            patients_value = st.session_state.simulation_results['parameters']['n_patients']
        else:
            patients_value = 100
        
        # Force update the widget by changing its key when preset is used
        widget_key = "n_patients_input"
        if 'preset_patients' in st.session_state:
            widget_key = f"n_patients_input_{st.session_state.preset_patients}"
        
        n_patients = st.number_input(
            "Patients",
            min_value=10,
            max_value=50000,
            value=patients_value,
            step=10,
            key=widget_key
        )

    with col3:
        # Check for preset from buttons FIRST, then fall back to current simulation
        if 'preset_duration' in st.session_state:
            duration_value = st.session_state.preset_duration
        elif ('simulation_results' in st.session_state and 
              st.session_state.simulation_results is not None and 
              'parameters' in st.session_state.simulation_results):
            duration_value = st.session_state.simulation_results['parameters']['duration_years']
        else:
            duration_value = 2.0
        
        # Force update the widget by changing its key when preset is used
        widget_key = "duration_years_input"
        if 'preset_duration' in st.session_state:
            widget_key = f"duration_years_input_{st.session_state.preset_duration}"
        
        duration_years = st.number_input(
            "Years",
            min_value=0.5,
            max_value=20.0,
            value=duration_value,
            step=0.5,
            format="%.1f",
            key=widget_key
        )

    with col4:
        # Use current simulation seed if loaded
        if ('simulation_results' in st.session_state and 
            st.session_state.simulation_results is not None and 
            'parameters' in st.session_state.simulation_results):
            seed_value = st.session_state.simulation_results['parameters']['seed']
        else:
            seed_value = 42
        
        seed = st.number_input(
            "Random Seed",
            min_value=0,
            max_value=999999,
            value=seed_value
        )

    return engine_type, n_patients, duration_years, seed


def render_runtime_estimate(n_patients: int, duration_years: float):
    """Display runtime estimate and total visits"""
    estimated_seconds = (n_patients * duration_years) / 1000
    if estimated_seconds < 1:
        runtime_text = "short"
    elif estimated_seconds < 60:
        runtime_text = f"~{estimated_seconds:.0f} seconds"
    else:
        runtime_text = f"~{estimated_seconds/60:.1f} minutes"

    visits_per_year = 365 / 42  # Rough estimate (6-week average)
    total_visits = int(n_patients * duration_years * visits_per_year)

    st.caption(f"Estimated runtime: {runtime_text} • Total visits: ~{total_visits:,}")


def render_control_buttons(has_results: bool) -> Tuple[bool, bool, bool, bool]:
    """
    Render the control panel buttons.
    
    Returns:
        Tuple of (run_clicked, view_analysis_clicked, protocol_clicked, manage_clicked)
    """
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        # Run Simulation button with play icon
        run_clicked = ape_button("Run Simulation", key="run_sim_main", 
                                full_width=True, is_primary_action=True, icon="play")

    with col2:
        # View Analysis - always show but disable if no results  
        view_analysis_clicked = ape_button("View Analysis", key="view_analysis_action", 
                     full_width=True, 
                     disabled=not has_results,
                     icon="chart")

    with col3:
        # Change Protocol
        protocol_clicked = ape_button("Protocol", key="change_protocol", 
                     full_width=True,
                     icon="document")

    with col4:
        # Manage button
        has_any_simulations = False
        if ResultsFactory.DEFAULT_RESULTS_DIR.exists():
            sim_dirs = list(ResultsFactory.DEFAULT_RESULTS_DIR.iterdir())
            has_any_simulations = any(d.is_dir() for d in sim_dirs)
        
        show_manage = has_any_simulations or st.session_state.get('current_sim_id')
        
        manage_clicked = False
        if show_manage:
            manage_clicked = ape_button("Manage", key="manage_btn", 
                         full_width=True,
                         icon="save")
    
    return run_clicked, view_analysis_clicked, protocol_clicked, manage_clicked


def render_recent_simulations():
    """Render the recent simulations section"""
    st.header("Recent")

    results_dir = ResultsFactory.DEFAULT_RESULTS_DIR
    if results_dir.exists():
        sim_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()], 
                         key=lambda x: x.name, reverse=True)[:10]  # Show last 10
        
        if sim_dirs:
            # Create a list of simulations with metadata
            simulations = []
            for sim_dir in sim_dirs:
                try:
                    # Load metadata
                    metadata_path = sim_dir / "metadata.json"
                    if metadata_path.exists():
                        with open(metadata_path) as f:
                            metadata = json.load(f)
                        
                        # Extract key info
                        sim_info = {
                            'id': sim_dir.name,
                            'timestamp': metadata.get('timestamp', 'Unknown'),
                            'patients': metadata.get('n_patients', 0),
                            'duration': metadata.get('duration_years', 0),
                            'protocol': metadata.get('protocol_name', 'Unknown'),
                            'is_imported': sim_dir.name.startswith('imported_'),
                            'memorable_name': metadata.get('memorable_name', '')
                        }
                        simulations.append(sim_info)
                except:
                    continue
            
            if simulations:
                # Display as cards - 5 per row
                for i in range(0, len(simulations), 5):
                    cols = st.columns(5)
                    for j, col in enumerate(cols):
                        if i + j < len(simulations):
                            sim = simulations[i + j]
                            with col:
                                render_simulation_card(sim)
            else:
                st.info("No recent simulations found. Run a simulation above to get started.")
        else:
            st.info("No recent simulations found. Run a simulation above to get started.")
    else:
        st.info("No simulations directory found. Run your first simulation above!")


def render_simulation_card(sim: Dict[str, Any]):
    """Render a single simulation card"""
    # Card styling
    is_selected = st.session_state.get('current_sim_id') == sim['id']
    is_imported = sim['is_imported'] or sim['id'] in st.session_state.get('imported_simulations', set())
    
    # Create card with conditional styling
    card_style = "border: 2px solid #0F62FE;" if is_selected else "border: 1px solid #ddd;"
    if is_imported:
        card_style += " background-color: #f0f7ff;"
    
    with st.container():
        # Display memorable name if available
        memorable_display = f'<p style="margin: 0; font-size: 0.95rem; color: #0F62FE; font-style: italic;">{sim["memorable_name"]}</p>' if sim.get("memorable_name") else ""
        
        st.markdown(f"""
        <div style="padding: 1rem; {card_style} border-radius: 8px; margin-bottom: 1rem;">
            <h5 style="margin: 0 0 0.5rem 0;">{sim['protocol']}</h5>
            {memorable_display}
            <p style="margin: 0; font-size: 0.9rem; color: #666;">
                {sim['patients']:,} patients • {sim['duration']} years
            </p>
            <p style="margin: 0; font-size: 0.8rem; color: #999;">
                {format_timestamp(sim['timestamp'])}
            </p>
            {f'<span style="background: #0F62FE; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">IMPORTED</span>' if is_imported else ''}
        </div>
        """, unsafe_allow_html=True)
        
        if ape_button(
            "Select" if not is_selected else "Selected ✓",
            key=f"select_{sim['id']}",
            full_width=True,
            is_primary_action=not is_selected
        ):
            # Use the unified loader to set both current_sim_id AND load results
            if load_simulation_results(sim['id']):
                st.rerun()
            else:
                st.error(f"Failed to load simulation {sim['id']}")


def clear_preset_values():
    """Clear preset values from session state after successful simulation"""
    if 'preset_patients' in st.session_state:
        del st.session_state.preset_patients
    if 'preset_duration' in st.session_state:
        del st.session_state.preset_duration