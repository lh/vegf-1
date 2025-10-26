"""
Simulation Comparison - Compare results from two saved simulations.
"""

import streamlit as st
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import json
import yaml
import matplotlib.pyplot as plt
from visualization.color_system import COLORS, ALPHAS

# Page configuration
st.set_page_config(
    page_title="Simulation Comparison",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import UI components
from ape.utils.startup_redirect import handle_page_startup
from ape.components.ui.workflow_indicator import workflow_progress_indicator
from ape.utils.carbon_button_helpers import ape_button, CarbonIcons
# Import simulation loading utilities
from ape.utils.simulation_loader import load_simulation_data
from ape.core.results.factory import ResultsFactory
# Import vision distribution visualization
from ape.utils.vision_distribution_viz import create_compact_vision_distribution_plot
# Import streamgraph and flow visualizations
from ape.visualizations.streamgraph_treatment_states import create_treatment_state_streamgraph
from ape.components.treatment_patterns.sankey_builder_enhanced import create_enhanced_sankey_with_terminals

# Check for startup redirect
handle_page_startup("comparison")

# Show workflow progress - add comparison step
workflow_progress_indicator("comparison")

# Initialize session state
if 'comparison_state' not in st.session_state:
    st.session_state.comparison_state = {
        'sim_a': None,
        'sim_b': None,
        'view_mode': 'side_by_side',
        'show_ci': True,
        'show_thresholds': True,
        'recent_pairs': [],
        'last_compared_pair': None  # Track last pair to avoid double updates
    }

# Title with Carbon icon (will show as text for now)
st.title("Compare Simulation Results")

# Get available simulations
RESULTS_DIR = Path(__file__).parent.parent / "simulation_results"
saved_simulations = sorted(
    [f for f in RESULTS_DIR.iterdir() if f.is_dir() and not f.name.startswith('.')],
    key=lambda x: x.stat().st_mtime,
    reverse=True
)

def get_simulation_info(sim_path):
    """Extract key information from simulation for display."""
    try:
        # Load metadata
        metadata_file = sim_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
            
            # Extract key info
            # Convert duration_years to months for display
            duration_years = metadata.get('duration_years', 0)
            duration_months = int(duration_years * 12)
            
            # Handle different protocol name fields
            protocol_name = metadata.get('protocol_name') or metadata.get('protocol', 'Unknown')
            
            # Extract memorable name from simulation folder name
            # Format is: sim_YYYYMMDD_HHMMSS_XX-YY_memorable-name
            sim_name = sim_path.name
            memorable_name = ""
            
            # Extract memorable name from current format
            if sim_name.startswith('sim_') and '_' in sim_name:
                parts = sim_name.split('_')
                if len(parts) >= 5:  # sim_date_time_duration_name
                    memorable_name = parts[-1]
            
            # Load protocol configuration if available
            protocol_config = None
            protocol_file = sim_path / "protocol.yaml"
            if protocol_file.exists():
                try:
                    with open(protocol_file) as f:
                        protocol_config = yaml.safe_load(f)
                except:
                    pass
            
            return {
                'path': sim_path,
                'name': sim_path.name,
                'memorable_name': memorable_name,
                'protocol': protocol_name,
                'protocol_config': protocol_config,
                'patients': metadata.get('n_patients', 0),
                'duration': duration_months,
                'date': datetime.fromisoformat(metadata.get('timestamp', '')).strftime('%Y-%m-%d'),
                'model_type': metadata.get('model_type', 'visit_based')
            }
    except Exception as e:
        st.warning(f"Could not read simulation {sim_path.name}: {str(e)}")
        return None

# Get info for all simulations
simulation_infos = []
for sim_path in saved_simulations:
    info = get_simulation_info(sim_path)
    if info:
        simulation_infos.append(info)

if not simulation_infos:
    st.error("No saved simulations found. Please run some simulations first.")
    st.stop()

# Helper functions
def format_simulation_name(sim_info):
    """Format simulation name for dropdown display."""
    model_type = sim_info.get('model_type', 'visit_based').replace('_', ' ').title()
    base_name = f"{sim_info['protocol']} - {sim_info['patients']} patients, {sim_info['duration']} months, {model_type} ({sim_info['date']})"
    
    # Add memorable name if available
    memorable_name = sim_info.get('memorable_name', '')
    if memorable_name:
        # Replace hyphens with spaces for better readability
        memorable_name = memorable_name.replace('-', ' ')
        return f"{base_name} • {memorable_name}"
    return base_name

def get_compatible_simulations(selected_sim, all_sims, exclude_sim=None):
    """Filter simulations to only show compatible options."""
    if not selected_sim:
        # If no sim selected, return all except the excluded one
        if exclude_sim:
            return [sim for sim in all_sims if sim['name'] != exclude_sim['name']]
        return all_sims
    
    selected_duration = selected_sim['duration']
    compatible = []
    
    for sim in all_sims:
        # Only show simulations with EXACTLY the same duration
        # AND exclude the same simulation
        if sim['duration'] == selected_duration and sim['name'] != selected_sim['name']:
            compatible.append(sim)
    
    return compatible

# Section 1: Simulation Selection
st.markdown("### Select Simulations to Compare")

# Recent comparisons (if any)
if st.session_state.comparison_state['recent_pairs']:
    st.markdown("**Recent Comparisons:**")
    cols = st.columns(len(st.session_state.comparison_state['recent_pairs']) + 1)
    
    for i, (sim_a_name, sim_b_name) in enumerate(st.session_state.comparison_state['recent_pairs']):
        with cols[i]:
            # Find the simulations to get their memorable names
            sim_a_info = next((sim for sim in simulation_infos if sim['name'] == sim_a_name), None)
            sim_b_info = next((sim for sim in simulation_infos if sim['name'] == sim_b_name), None)
            
            # Create button label with memorable names if available
            if sim_a_info and sim_b_info:
                a_label = sim_a_info.get('memorable_name', sim_a_name[:15]).replace('-', ' ')
                b_label = sim_b_info.get('memorable_name', sim_b_name[:15]).replace('-', ' ')
                button_label = f"{a_label} vs {b_label}"
            else:
                button_label = f"{sim_a_name[:20]}... vs {sim_b_name[:20]}..."
            
            if ape_button(button_label, 
                         key=f"recent_{i}", 
                         button_type="ghost"):
                # Load this comparison
                for sim in simulation_infos:
                    if sim['name'] == sim_a_name:
                        st.session_state.comparison_state['sim_a'] = sim
                    if sim['name'] == sim_b_name:
                        st.session_state.comparison_state['sim_b'] = sim
                # Set last compared pair to avoid double update
                st.session_state.comparison_state['last_compared_pair'] = (sim_a_name, sim_b_name)
                st.rerun()
    
    with cols[-1]:
        if ape_button("Clear", key="clear_recent", icon="close", button_type="ghost"):
            st.session_state.comparison_state['recent_pairs'] = []
            st.rerun()

# Main selection area
col1, col2, col3 = st.columns([5, 1, 5])

with col1:
    st.markdown("**Simulation A**")
    
    # Find current selection in list
    current_a_idx = 0
    if st.session_state.comparison_state['sim_a']:
        for i, sim in enumerate(simulation_infos):
            if sim['name'] == st.session_state.comparison_state['sim_a']['name']:
                current_a_idx = i
                break
    
    selected_a_idx = st.selectbox(
        "Select first simulation",
        range(len(simulation_infos)),
        format_func=lambda x: format_simulation_name(simulation_infos[x]),
        index=current_a_idx,
        key="sim_a_select",
        label_visibility="collapsed"
    )
    
    if selected_a_idx is not None:
        st.session_state.comparison_state['sim_a'] = simulation_infos[selected_a_idx]

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Spacing
    if ape_button("", key="swap_sims", icon="swap", help_text="Swap simulations"):
        # Only swap if both simulations are selected
        if (st.session_state.comparison_state.get('sim_a') and 
            st.session_state.comparison_state.get('sim_b')):
            # Store current values
            temp_a = st.session_state.comparison_state['sim_a'].copy()
            temp_b = st.session_state.comparison_state['sim_b'].copy()
            # Swap them
            st.session_state.comparison_state['sim_a'] = temp_b
            st.session_state.comparison_state['sim_b'] = temp_a
            # Update last compared pair to the swapped order
            st.session_state.comparison_state['last_compared_pair'] = (temp_b['name'], temp_a['name'])
            st.rerun()

with col3:
    # Create sub-columns for the heading and caption
    header_col, caption_col = st.columns([1, 2])
    with header_col:
        st.markdown("**Simulation B**")
    
    # Get compatible simulations (excluding the selected simulation A)
    sim_a = st.session_state.comparison_state['sim_a']
    compatible_sims = get_compatible_simulations(sim_a, simulation_infos)
    
    with caption_col:
        if sim_a:
            st.caption(f"Showing {len(compatible_sims)} compatible simulations")
        else:
            st.caption(f"Showing {len(compatible_sims)} simulations")
    
    # Find current selection in compatible list
    current_b_idx = 0
    if st.session_state.comparison_state['sim_b']:
        for i, sim in enumerate(compatible_sims):
            if sim['name'] == st.session_state.comparison_state['sim_b']['name']:
                current_b_idx = i
                break
    
    if compatible_sims:
        selected_b_idx = st.selectbox(
            "Select compatible simulation",
            range(len(compatible_sims)),
            format_func=lambda x: format_simulation_name(compatible_sims[x]),
            index=current_b_idx if current_b_idx < len(compatible_sims) else 0,
            key="sim_b_select",
            label_visibility="collapsed"
        )
        
        if selected_b_idx is not None:
            st.session_state.comparison_state['sim_b'] = compatible_sims[selected_b_idx]
    else:
        st.warning("No compatible simulations found")

# Duration validation message
if sim_a and not compatible_sims:
    st.warning(f"⚠️ No simulations found with exactly {sim_a['duration']} months duration. Comparisons require identical duration.")
else:
    st.info("ℹ️ Only simulations with identical duration can be compared")

# Check if we have both simulations selected
sim_a = st.session_state.comparison_state['sim_a']
sim_b = st.session_state.comparison_state['sim_b']

if not (sim_a and sim_b):
    st.info("Please select two simulations to compare")
    st.stop()

# Add to recent pairs
def update_recent_pairs(sim_a, sim_b):
    """Update the list of recent comparison pairs."""
    pair = (sim_a['name'], sim_b['name'])
    recent = st.session_state.comparison_state['recent_pairs']
    
    # Remove if already exists
    recent = [p for p in recent if p != pair]
    
    # Add to front
    recent.insert(0, pair)
    
    # Keep only last 3
    st.session_state.comparison_state['recent_pairs'] = recent[:3]

# Update recent pairs only if selection changed
current_pair = (sim_a['name'], sim_b['name'])
if st.session_state.comparison_state.get('last_compared_pair') != current_pair:
    update_recent_pairs(sim_a, sim_b)
    st.session_state.comparison_state['last_compared_pair'] = current_pair

# Section 2: Simulation Overview Cards
st.markdown("---")
st.markdown("### Simulation Overview")

# Create columns for overview with space for charts
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**Simulation A**")
    if sim_a.get('memorable_name'):
        st.markdown(f"**Name:** {sim_a['memorable_name'].replace('-', ' ')}")
    st.markdown(f"**Protocol:** {sim_a['protocol']}")
    st.markdown(f"**Patients:** {sim_a['patients']:,}")
    st.markdown(f"**Duration:** {sim_a['duration']} months")
    st.markdown(f"**Model Type:** {sim_a['model_type'].replace('_', ' ').title()}")
    st.markdown(f"**Run Date:** {sim_a['date']}")
    
    # Add baseline vision distribution if available
    if sim_a.get('protocol_config') and sim_a['protocol_config'] is not None:
        dist_config = None
        
        # Check for new format first
        if 'baseline_vision_distribution' in sim_a['protocol_config']:
            dist_config = sim_a['protocol_config']['baseline_vision_distribution']
        # Fall back to old format
        elif 'baseline_vision' in sim_a['protocol_config']:
            baseline = sim_a['protocol_config']['baseline_vision']
            if isinstance(baseline, dict):
                dist_config = {
                    'type': 'normal',
                    'mean': baseline.get('mean', 70),
                    'std': baseline.get('std', 10),
                    'min': baseline.get('min', 20),
                    'max': baseline.get('max', 90)
                }
        
        if dist_config:
            # Create inline layout for baseline vision
            vision_col1, vision_col2 = st.columns([1, 3])
            with vision_col1:
                st.markdown("**Baseline Vision:**")
            with vision_col2:
                try:
                    fig = create_compact_vision_distribution_plot(
                        dist_config,
                        figsize=(1.0, 0.25),
                        show_stats=False,
                        title=None
                    )
                    st.pyplot(fig, use_container_width=False)
                    plt.close(fig)
                except Exception as e:
                    st.caption("Could not display")

with col2:
    st.markdown(f"**Simulation B**")
    if sim_b.get('memorable_name'):
        st.markdown(f"**Name:** {sim_b['memorable_name'].replace('-', ' ')}")
    st.markdown(f"**Protocol:** {sim_b['protocol']}")
    st.markdown(f"**Patients:** {sim_b['patients']:,}")
    st.markdown(f"**Duration:** {sim_b['duration']} months")
    st.markdown(f"**Model Type:** {sim_b['model_type'].replace('_', ' ').title()}")
    st.markdown(f"**Run Date:** {sim_b['date']}")
    
    # Add baseline vision distribution if available
    if sim_b.get('protocol_config') and sim_b['protocol_config'] is not None:
        dist_config = None
        
        # Check for new format first
        if 'baseline_vision_distribution' in sim_b['protocol_config']:
            dist_config = sim_b['protocol_config']['baseline_vision_distribution']
        # Fall back to old format
        elif 'baseline_vision' in sim_b['protocol_config']:
            baseline = sim_b['protocol_config']['baseline_vision']
            if isinstance(baseline, dict):
                dist_config = {
                    'type': 'normal',
                    'mean': baseline.get('mean', 70),
                    'std': baseline.get('std', 10),
                    'min': baseline.get('min', 20),
                    'max': baseline.get('max', 90)
                }
        
        if dist_config:
            # Create inline layout for baseline vision
            vision_col1, vision_col2 = st.columns([1, 3])
            with vision_col1:
                st.markdown("**Baseline Vision:**")
            with vision_col2:
                try:
                    fig = create_compact_vision_distribution_plot(
                        dist_config,
                        figsize=(1.0, 0.25),
                        show_stats=False,
                        title=None
                    )
                    st.pyplot(fig, use_container_width=False)
                    plt.close(fig)
                except Exception as e:
                    st.caption("Could not display")

# Helper function to load simulation data from path
def load_simulation_from_path(sim_info):
    """Load simulation data from parquet files."""
    try:
        sim_path = sim_info['path']
        
        # Load parquet data
        patients_df = pd.read_parquet(sim_path / "patients.parquet")
        visits_df = pd.read_parquet(sim_path / "visits.parquet")
        
        # Load summary stats
        summary_stats = {}
        summary_path = sim_path / "summary_stats.json"
        if summary_path.exists():
            with open(summary_path) as f:
                summary_stats = json.load(f)
        
        # Convert to format expected by comparison functions
        patient_histories = {}
        
        # Group visits by patient
        for patient_id in patients_df['patient_id'].unique():
            patient_visits = visits_df[visits_df['patient_id'] == patient_id].sort_values('date')
            patient_data = patients_df[patients_df['patient_id'] == patient_id].iloc[0]
            
            visits = []
            if len(patient_visits) > 0:
                baseline_date = pd.to_datetime(patient_visits.iloc[0]['date'])
                
                for _, visit in patient_visits.iterrows():
                    visit_date = pd.to_datetime(visit['date'])
                    month = (visit_date - baseline_date).days / 30.44
                    
                    visits.append({
                        'month': month,
                        'vision': visit['vision'],  # Column is 'vision' not 'visual_acuity'
                        'injection_given': visit['injected'],  # Column is 'injected' not 'injection_given'
                        'date': str(visit_date)
                    })
            
            patient_histories[patient_id] = {
                'visits': visits,
                'baseline_vision': float(patient_data['baseline_vision']),
                'current_vision': float(patient_data['final_vision']),
                'is_discontinued': bool(patient_data['discontinued'])
            }
        
        # Get discontinuation summary
        disc_summary = {
            'by_reason': {},
            'total': int(patients_df['discontinued'].sum())
        }
        
        # Add reason breakdown if available
        if 'discontinuation_reason' in patients_df.columns:
            # Filter out None/NaN values
            disc_patients = patients_df[patients_df['discontinued'] == True]
            if len(disc_patients) > 0:
                reason_counts = disc_patients['discontinuation_reason'].value_counts()
                disc_summary['by_reason'] = reason_counts.to_dict()
        
        return {
            'patient_histories': patient_histories,
            'discontinuation_summary': disc_summary,
            'summary_stats': summary_stats
        }
        
    except Exception as e:
        st.error(f"Error loading simulation data: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# Load the actual simulation data
with st.spinner("Loading simulation data..."):
    try:
        results_a = load_simulation_from_path(sim_a)
        results_b = load_simulation_from_path(sim_b)
        
        if not results_a or not results_b:
            st.error("Failed to load simulation data")
            st.stop()
            
    except Exception as e:
        st.error(f"Error loading simulations: {str(e)}")
        st.stop()

# Helper function to calculate metrics
def calculate_comparison_metrics(results_a, results_b):
    """Calculate key comparison metrics from simulation results."""
    metrics = {}
    
    # Extract patient histories
    histories_a = results_a.get('patient_histories', {})
    histories_b = results_b.get('patient_histories', {})
    
    # Visual Acuity Metrics
    # Get visual acuity arrays for calculations
    def get_vision_at_timepoints(histories):
        """Extract vision values at key timepoints."""
        baseline_values = []
        year1_values = []
        year2_values = []
        final_values = []
        
        for patient_id, history in histories.items():
            visits = history.get('visits', [])
            if not visits:
                continue
                
            # Baseline
            baseline_values.append(visits[0]['vision'])
            
            # Find visits closest to 12, 24 months and final
            for visit in visits:
                month = visit['month']
                if 11 <= month <= 13 and len(year1_values) < len(baseline_values):
                    year1_values.append(visit['vision'])
                elif 23 <= month <= 25 and len(year2_values) < len(baseline_values):
                    year2_values.append(visit['vision'])
            
            # Final visit
            if visits:
                final_values.append(visits[-1]['vision'])
        
        return {
            'baseline': np.array(baseline_values),
            'year1': np.array(year1_values),
            'year2': np.array(year2_values),
            'final': np.array(final_values)
        }
    
    vision_a = get_vision_at_timepoints(histories_a)
    vision_b = get_vision_at_timepoints(histories_b)
    
    # Calculate means
    metrics['visual_acuity'] = {
        'baseline': (
            np.mean(vision_a['baseline']) if len(vision_a['baseline']) > 0 else 0,
            np.mean(vision_b['baseline']) if len(vision_b['baseline']) > 0 else 0
        ),
        'year1': (
            np.mean(vision_a['year1']) if len(vision_a['year1']) > 0 else 0,
            np.mean(vision_b['year1']) if len(vision_b['year1']) > 0 else 0
        ),
        'year2': (
            np.mean(vision_a['year2']) if len(vision_a['year2']) > 0 else 0,
            np.mean(vision_b['year2']) if len(vision_b['year2']) > 0 else 0
        ),
        'final': (
            np.mean(vision_a['final']) if len(vision_a['final']) > 0 else 0,
            np.mean(vision_b['final']) if len(vision_b['final']) > 0 else 0
        )
    }
    
    # Calculate change from baseline
    if len(vision_a['baseline']) > 0 and len(vision_a['final']) > 0:
        change_a = np.mean(vision_a['final'] - vision_a['baseline'][:len(vision_a['final'])])
    else:
        change_a = 0
        
    if len(vision_b['baseline']) > 0 and len(vision_b['final']) > 0:
        change_b = np.mean(vision_b['final'] - vision_b['baseline'][:len(vision_b['final'])])
    else:
        change_b = 0
        
    metrics['visual_acuity']['change'] = (change_a, change_b)
    
    # Calculate maintained vision (≤5 letter loss)
    if len(vision_a['baseline']) > 0 and len(vision_a['final']) > 0:
        maintained_a = np.sum((vision_a['baseline'][:len(vision_a['final'])] - vision_a['final']) <= 5) / len(vision_a['final']) * 100
    else:
        maintained_a = 0
        
    if len(vision_b['baseline']) > 0 and len(vision_b['final']) > 0:
        maintained_b = np.sum((vision_b['baseline'][:len(vision_b['final'])] - vision_b['final']) <= 5) / len(vision_b['final']) * 100
    else:
        maintained_b = 0
        
    metrics['visual_acuity']['maintained'] = (maintained_a, maintained_b)
    
    # Treatment Burden Metrics
    def get_treatment_burden(histories):
        """Calculate treatment burden metrics."""
        total_injections = []
        total_visits = []
        
        for patient_id, history in histories.items():
            visits = history.get('visits', [])
            injection_count = sum(1 for v in visits if v.get('injection_given', False))
            visit_count = len(visits)
            
            total_injections.append(injection_count)
            total_visits.append(visit_count)
        
        return {
            'injections': np.array(total_injections),
            'visits': np.array(total_visits)
        }
    
    burden_a = get_treatment_burden(histories_a)
    burden_b = get_treatment_burden(histories_b)
    
    metrics['treatment_burden'] = {
        'mean_injections': (
            np.mean(burden_a['injections']) if len(burden_a['injections']) > 0 else 0,
            np.mean(burden_b['injections']) if len(burden_b['injections']) > 0 else 0
        ),
        'mean_visits': (
            np.mean(burden_a['visits']) if len(burden_a['visits']) > 0 else 0,
            np.mean(burden_b['visits']) if len(burden_b['visits']) > 0 else 0
        )
    }
    
    # Calculate injection:visit ratio
    ratio_a = metrics['treatment_burden']['mean_injections'][0] / metrics['treatment_burden']['mean_visits'][0] if metrics['treatment_burden']['mean_visits'][0] > 0 else 0
    ratio_b = metrics['treatment_burden']['mean_injections'][1] / metrics['treatment_burden']['mean_visits'][1] if metrics['treatment_burden']['mean_visits'][1] > 0 else 0
    metrics['treatment_burden']['injection_ratio'] = (ratio_a, ratio_b)
    
    # Discontinuation Metrics
    disc_summary_a = results_a.get('discontinuation_summary', {})
    disc_summary_b = results_b.get('discontinuation_summary', {})
    
    total_disc_a = sum(disc_summary_a.get('by_reason', {}).values())
    total_disc_b = sum(disc_summary_b.get('by_reason', {}).values())
    
    n_patients_a = len(histories_a)
    n_patients_b = len(histories_b)
    
    metrics['discontinuations'] = {
        'total_pct': (
            (total_disc_a / n_patients_a * 100) if n_patients_a > 0 else 0,
            (total_disc_b / n_patients_b * 100) if n_patients_b > 0 else 0
        ),
        'poor_vision_pct': (
            (disc_summary_a.get('by_reason', {}).get('poor_vision', 0) / n_patients_a * 100) if n_patients_a > 0 else 0,
            (disc_summary_b.get('by_reason', {}).get('poor_vision', 0) / n_patients_b * 100) if n_patients_b > 0 else 0
        )
    }
    
    return metrics

# Calculate metrics
metrics = calculate_comparison_metrics(results_a, results_b)

# Extract histories for visualization
histories_a = results_a.get('patient_histories', {})
histories_b = results_b.get('patient_histories', {})

# Section 3: Key Insights
st.markdown("---")
st.markdown("### Key Insights")

# Generate key insights
insights = []

# Vision preservation insight
vision_diff = metrics['visual_acuity']['change'][1] - metrics['visual_acuity']['change'][0]
if abs(vision_diff) > 1:
    if vision_diff > 0:
        insights.append(f"• Simulation B preserves {vision_diff:.1f} more letters despite different baseline")
    else:
        insights.append(f"• Simulation A preserves {-vision_diff:.1f} more letters over the study period")

# Treatment burden trade-off
inj_diff = metrics['treatment_burden']['mean_injections'][1] - metrics['treatment_burden']['mean_injections'][0]
visit_diff = metrics['treatment_burden']['mean_visits'][1] - metrics['treatment_burden']['mean_visits'][0]
if abs(inj_diff) > 2 and abs(visit_diff) > 2:
    if (inj_diff > 0 and visit_diff < 0) or (inj_diff < 0 and visit_diff > 0):
        insights.append(f"• Trade-off: {abs(inj_diff):.1f} {'more' if inj_diff > 0 else 'fewer'} injections but {abs(visit_diff):.1f} {'fewer' if visit_diff < 0 else 'more'} visits")

# Discontinuation insight
disc_diff = metrics['discontinuations']['total_pct'][1] - metrics['discontinuations']['total_pct'][0]
if abs(disc_diff) > 5:
    insights.append(f"• {'Higher' if disc_diff > 0 else 'Lower'} discontinuation rate in Simulation B ({disc_diff:+.1f}%)")

# Vision maintenance
maintained_diff = metrics['visual_acuity']['maintained'][1] - metrics['visual_acuity']['maintained'][0]
if abs(maintained_diff) > 5:
    insights.append(f"• {'Better' if maintained_diff > 0 else 'Worse'} vision maintenance in Simulation B ({maintained_diff:+.1f}% patients with ≤5 letter loss)")

# Display insights box
if insights:
    with st.container():
        st.info("\n".join(insights[:4]))  # Show top 4 insights
else:
    st.info("• Simulations show similar outcomes across key metrics")

# Section 4: Key Metrics Comparison
st.markdown("---")
st.markdown("### Key Outcome Metrics")

# Export buttons
col1, col2, col3 = st.columns([6, 1, 1])

# Prepare export data
def prepare_export_data():
    """Prepare comparison data for export."""
    export_data = []
    
    # Add metadata
    export_data.append({
        'Section': 'Metadata',
        'Metric': 'Simulation A',
        'Value A': sim_a['protocol'],
        'Value B': sim_b['protocol'],
        'Difference': ''
    })
    export_data.append({
        'Section': 'Metadata',
        'Metric': 'Patients',
        'Value A': sim_a['patients'],
        'Value B': sim_b['patients'],
        'Difference': sim_b['patients'] - sim_a['patients']
    })
    export_data.append({
        'Section': 'Metadata',
        'Metric': 'Duration (months)',
        'Value A': sim_a['duration'],
        'Value B': sim_b['duration'],
        'Difference': sim_b['duration'] - sim_a['duration']
    })
    
    # Add visual acuity metrics
    export_data.append({
        'Section': 'Visual Acuity',
        'Metric': 'Baseline Mean',
        'Value A': f"{metrics['visual_acuity']['baseline'][0]:.1f}",
        'Value B': f"{metrics['visual_acuity']['baseline'][1]:.1f}",
        'Difference': f"{metrics['visual_acuity']['baseline'][1] - metrics['visual_acuity']['baseline'][0]:.1f}"
    })
    export_data.append({
        'Section': 'Visual Acuity',
        'Metric': 'Final Mean',
        'Value A': f"{metrics['visual_acuity']['final'][0]:.1f}",
        'Value B': f"{metrics['visual_acuity']['final'][1]:.1f}",
        'Difference': f"{metrics['visual_acuity']['final'][1] - metrics['visual_acuity']['final'][0]:.1f}"
    })
    export_data.append({
        'Section': 'Visual Acuity',
        'Metric': 'Mean Change from Baseline',
        'Value A': f"{metrics['visual_acuity']['change'][0]:.1f}",
        'Value B': f"{metrics['visual_acuity']['change'][1]:.1f}",
        'Difference': f"{metrics['visual_acuity']['change'][1] - metrics['visual_acuity']['change'][0]:.1f}"
    })
    export_data.append({
        'Section': 'Visual Acuity',
        'Metric': 'Maintained Vision (%)',
        'Value A': f"{metrics['visual_acuity']['maintained'][0]:.1f}",
        'Value B': f"{metrics['visual_acuity']['maintained'][1]:.1f}",
        'Difference': f"{metrics['visual_acuity']['maintained'][1] - metrics['visual_acuity']['maintained'][0]:.1f}"
    })
    
    # Add treatment burden metrics
    export_data.append({
        'Section': 'Treatment Burden',
        'Metric': 'Mean Injections/Patient',
        'Value A': f"{metrics['treatment_burden']['mean_injections'][0]:.1f}",
        'Value B': f"{metrics['treatment_burden']['mean_injections'][1]:.1f}",
        'Difference': f"{metrics['treatment_burden']['mean_injections'][1] - metrics['treatment_burden']['mean_injections'][0]:.1f}"
    })
    export_data.append({
        'Section': 'Treatment Burden',
        'Metric': 'Mean Visits/Patient',
        'Value A': f"{metrics['treatment_burden']['mean_visits'][0]:.1f}",
        'Value B': f"{metrics['treatment_burden']['mean_visits'][1]:.1f}",
        'Difference': f"{metrics['treatment_burden']['mean_visits'][1] - metrics['treatment_burden']['mean_visits'][0]:.1f}"
    })
    export_data.append({
        'Section': 'Treatment Burden',
        'Metric': 'Injection:Visit Ratio',
        'Value A': f"{metrics['treatment_burden']['injection_ratio'][0]:.2f}",
        'Value B': f"{metrics['treatment_burden']['injection_ratio'][1]:.2f}",
        'Difference': f"{metrics['treatment_burden']['injection_ratio'][1] - metrics['treatment_burden']['injection_ratio'][0]:.2f}"
    })
    
    # Add discontinuation metrics
    export_data.append({
        'Section': 'Discontinuations',
        'Metric': 'Total Discontinued (%)',
        'Value A': f"{metrics['discontinuations']['total_pct'][0]:.1f}",
        'Value B': f"{metrics['discontinuations']['total_pct'][1]:.1f}",
        'Difference': f"{metrics['discontinuations']['total_pct'][1] - metrics['discontinuations']['total_pct'][0]:.1f}"
    })
    export_data.append({
        'Section': 'Discontinuations',
        'Metric': 'Poor Vision (%)',
        'Value A': f"{metrics['discontinuations']['poor_vision_pct'][0]:.1f}",
        'Value B': f"{metrics['discontinuations']['poor_vision_pct'][1]:.1f}",
        'Difference': f"{metrics['discontinuations']['poor_vision_pct'][1] - metrics['discontinuations']['poor_vision_pct'][0]:.1f}"
    })
    
    return pd.DataFrame(export_data)

with col2:
    if ape_button("Copy", key="copy_metrics", icon="copy", button_type="ghost"):
        # Prepare data for clipboard
        export_df = prepare_export_data()
        
        # Format as tab-separated for easy pasting into Excel
        clipboard_text = export_df.to_csv(sep='\t', index=False)
        
        # Using Streamlit's experimental clipboard (might need fallback)
        try:
            # Create a text area with the data
            st.text_area("Copy this data:", clipboard_text, height=100, key="copy_area")
            st.info("Data prepared for copying. Select all text above and copy.")
        except:
            st.warning("Copy the data from the CSV download instead.")
        
with col3:
    # Prepare CSV download
    export_df = prepare_export_data()
    csv = export_df.to_csv(index=False)
    
    # Create download button
    st.download_button(
        label="CSV",
        data=csv,
        file_name=f"comparison_{sim_a['name']}_{sim_b['name']}.csv",
        mime="text/csv",
        key="download_csv_btn",
        help="Download comparison data as CSV"
    )

# Create metrics table
def format_metric_row(label, value_a, value_b, format_str="{:.1f}", show_arrow=True):
    """Format a metric row with difference calculation."""
    diff = value_b - value_a
    
    if show_arrow:
        if abs(diff) < 0.01:
            arrow = ""
        elif diff > 0:
            arrow = "↑"
        else:
            arrow = "↓"
    else:
        arrow = ""
    
    # Color coding for differences
    if label.startswith("Mean Change") or "Vision" in label:
        # For vision metrics, positive diff is good
        color = "green" if diff > 0 else "red" if diff < 0 else "black"
    elif "Discontinued" in label:
        # For discontinuation, negative diff is good
        color = "red" if diff > 0 else "green" if diff < 0 else "black"
    else:
        # Neutral metrics
        color = "black"
    
    return {
        'Metric': label,
        'Simulation A': format_str.format(value_a),
        'Simulation B': format_str.format(value_b),
        'Difference': f"<span style='color: {color}'>{diff:+.1f} {arrow}</span>"
    }

# Build metrics data
metrics_data = []

# Visual Acuity section
metrics_data.append({'Metric': '**Visual Acuity (ETDRS Letters)**', 'Simulation A': '', 'Simulation B': '', 'Difference': ''})
metrics_data.append(format_metric_row('Baseline Mean', 
                                    metrics['visual_acuity']['baseline'][0],
                                    metrics['visual_acuity']['baseline'][1]))
metrics_data.append(format_metric_row('Year 1 Mean', 
                                    metrics['visual_acuity']['year1'][0],
                                    metrics['visual_acuity']['year1'][1]))
metrics_data.append(format_metric_row('Year 2 Mean', 
                                    metrics['visual_acuity']['year2'][0],
                                    metrics['visual_acuity']['year2'][1]))
metrics_data.append(format_metric_row('Final Mean', 
                                    metrics['visual_acuity']['final'][0],
                                    metrics['visual_acuity']['final'][1]))
metrics_data.append(format_metric_row('Mean Change from Baseline', 
                                    metrics['visual_acuity']['change'][0],
                                    metrics['visual_acuity']['change'][1]))
metrics_data.append(format_metric_row('Maintained Vision (≤5 letter loss)', 
                                    metrics['visual_acuity']['maintained'][0],
                                    metrics['visual_acuity']['maintained'][1],
                                    format_str="{:.1f}%"))

# Treatment Burden section
metrics_data.append({'Metric': '', 'Simulation A': '', 'Simulation B': '', 'Difference': ''})  # Spacer
metrics_data.append({'Metric': '**Treatment Burden**', 'Simulation A': '', 'Simulation B': '', 'Difference': ''})
metrics_data.append(format_metric_row('Mean Injections/Patient', 
                                    metrics['treatment_burden']['mean_injections'][0],
                                    metrics['treatment_burden']['mean_injections'][1]))
metrics_data.append(format_metric_row('Mean Visits/Patient', 
                                    metrics['treatment_burden']['mean_visits'][0],
                                    metrics['treatment_burden']['mean_visits'][1]))
metrics_data.append(format_metric_row('Injection:Visit Ratio', 
                                    metrics['treatment_burden']['injection_ratio'][0],
                                    metrics['treatment_burden']['injection_ratio'][1],
                                    format_str="{:.2f}"))

# Discontinuation section
metrics_data.append({'Metric': '', 'Simulation A': '', 'Simulation B': '', 'Difference': ''})  # Spacer
metrics_data.append({'Metric': '**Discontinuations**', 'Simulation A': '', 'Simulation B': '', 'Difference': ''})
metrics_data.append(format_metric_row('Total Discontinued', 
                                    metrics['discontinuations']['total_pct'][0],
                                    metrics['discontinuations']['total_pct'][1],
                                    format_str="{:.1f}%"))
metrics_data.append(format_metric_row('Poor Vision (<20 letters)', 
                                    metrics['discontinuations']['poor_vision_pct'][0],
                                    metrics['discontinuations']['poor_vision_pct'][1],
                                    format_str="{:.1f}%"))

# Convert to DataFrame and display
df_metrics = pd.DataFrame(metrics_data)

# Display as HTML table with formatting
st.markdown(df_metrics.to_html(escape=False, index=False), unsafe_allow_html=True)

# Add legend
st.caption("**Legend:** ↑ Higher/More  ↓ Lower/Less | Green = Favorable | Red = Unfavorable")

# Section 5: Visualizations
st.markdown("---")
st.markdown("### Visualizations")

# Display full protocol information for context
st.markdown("**Comparing:**")
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    **Simulation A:** {sim_a['protocol']}
    - {sim_a['patients']} patients, {sim_a['duration']} months
    - Model: {sim_a.get('model_type', 'visit_based').replace('_', ' ').title()}
    - Date: {sim_a['date']}
    """)
with col2:
    st.markdown(f"""
    **Simulation B:** {sim_b['protocol']}
    - {sim_b['patients']} patients, {sim_b['duration']} months
    - Model: {sim_b.get('model_type', 'visit_based').replace('_', ' ').title()}
    - Date: {sim_b['date']}
    """)

# Import visualization components
import matplotlib.pyplot as plt

# View mode toggle with settings
col1, col2, col3 = st.columns([3, 2, 2])
with col1:
    view_mode = st.radio(
        "View Mode",
        ["Side-by-Side", "Overlay", "Difference"],
        horizontal=True,
        key="view_mode_radio"
    )
with col2:
    show_ci = st.checkbox("Show Confidence Intervals", value=True, key="show_ci")
with col3:
    show_thresholds = st.checkbox("Show Clinical Thresholds", value=True, key="show_thresholds")

# Visual Acuity Over Time
st.subheader("Visual Acuity Over Time")

# Prepare data for visualization
def prepare_vision_data(histories):
    """Prepare vision data for plotting."""
    # Collect all visits
    all_months = []
    all_visions = []
    
    for patient_id, history in histories.items():
        visits = history.get('visits', [])
        for visit in visits:
            all_months.append(visit['month'])
            all_visions.append(visit['vision'])
    
    # Create DataFrame
    df = pd.DataFrame({
        'Month': all_months,
        'Vision': all_visions
    })
    
    # Calculate statistics by month
    stats = df.groupby('Month')['Vision'].agg(['mean', 'std', 'count']).reset_index()
    stats['ci_lower'] = stats['mean'] - 1.96 * stats['std'] / np.sqrt(stats['count'])
    stats['ci_upper'] = stats['mean'] + 1.96 * stats['std'] / np.sqrt(stats['count'])
    
    return stats

def create_standardized_vision_plot(ax, vision_data, title, color='blue', show_ci=True, show_thresholds=True, max_month=None):
    """Create a standardized vision plot with Tufte-style minimalist formatting."""
    # Main line
    ax.plot(vision_data['Month'], vision_data['mean'], color=color, linewidth=2.5, label='Mean Vision')
    
    # Confidence intervals
    if show_ci:
        ax.fill_between(vision_data['Month'], 
                      vision_data['ci_lower'], 
                      vision_data['ci_upper'],
                      alpha=0.15, color=color, label='95% CI')
    
    # Clinical thresholds - subtle reference lines
    if show_thresholds:
        ax.axhline(y=70, color='#999999', linestyle='-', alpha=0.3, linewidth=0.8)
        ax.axhline(y=20, color='#999999', linestyle='-', alpha=0.3, linewidth=0.8)
        # Add subtle labels directly on the lines
        ax.text(max_month * 0.98, 71, '70', ha='right', va='bottom', fontsize=8, color='#666666')
        ax.text(max_month * 0.98, 21, '20', ha='right', va='bottom', fontsize=8, color='#666666')
    
    # Remove top and right spines (Tufte style)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Make remaining spines subtle
    ax.spines['left'].set_color('#333333')
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    
    # Subtle tick marks
    ax.tick_params(colors='#333333', width=0.8, length=4)
    
    # Labels with better typography
    ax.set_xlabel('Time (months)', fontsize=10, color='#333333')
    ax.set_ylabel('Vision (ETDRS Letters)', fontsize=10, color='#333333')
    if title:
        ax.set_title(title, fontsize=11, color='#333333', pad=10)
    
    # Fixed axis ranges
    ax.set_xlim(0, max_month)
    ax.set_ylim(0, 85)
    
    # Set x-axis ticks at yearly intervals (0, 12, 24, 36, 48, 60)
    # Calculate how many years we need based on max_month
    years_needed = int(np.ceil(max_month / 12))
    x_ticks = [i * 12 for i in range(years_needed + 1)]
    # Only include ticks up to max_month
    x_ticks = [tick for tick in x_ticks if tick <= max_month]
    ax.set_xticks(x_ticks)
    
    # Remove grid or make it very subtle
    ax.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc')
    
    # Minimize legend
    if show_ci:
        ax.legend(fontsize=8, frameon=False, loc='upper right')
    else:
        # Remove legend if only showing mean
        ax.legend().set_visible(False)

# Prepare data
vision_data_a = prepare_vision_data(histories_a)
vision_data_b = prepare_vision_data(histories_b)

# Calculate max month across both simulations for consistent x-axis
max_month_a = vision_data_a['Month'].max() if len(vision_data_a) > 0 else 60
max_month_b = vision_data_b['Month'].max() if len(vision_data_b) > 0 else 60
max_month = max(max_month_a, max_month_b)

# Create visualizations based on view mode
if view_mode == "Side-by-Side":
    # Create both figures first to ensure identical sizing
    fig_a, ax_a = plt.subplots(figsize=(7, 5), dpi=80, facecolor='white')
    fig_b, ax_b = plt.subplots(figsize=(7, 5), dpi=80, facecolor='white')
    
    # Set axis background to white
    ax_a.set_facecolor('white')
    ax_b.set_facecolor('white')
    
    # Create both plots with identical parameters
    create_standardized_vision_plot(
        ax_a,
        vision_data_a,
        '',  # No title
        color=COLORS['primary'],  # Consistent Simulation A color
        show_ci=show_ci,
        show_thresholds=show_thresholds,
        max_month=max_month
    )

    create_standardized_vision_plot(
        ax_b,
        vision_data_b,
        '',  # No title
        color=COLORS['secondary'],  # Consistent Simulation B color
        show_ci=show_ci,
        show_thresholds=show_thresholds,
        max_month=max_month
    )
    
    # Apply tight layout to both
    fig_a.tight_layout()
    fig_b.tight_layout()
    
    # Now display them in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.pyplot(fig_a)
    
    with col2:
        st.pyplot(fig_b)
    
    # Close both figures
    plt.close(fig_a)
    plt.close(fig_b)

elif view_mode == "Overlay":
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
    ax.set_facecolor('white')
    
    # Plot both simulations with consistent colors
    ax.plot(vision_data_a['Month'], vision_data_a['mean'], color=COLORS['primary'], linewidth=2.5, label=f'A: {sim_a["protocol"]}')
    ax.plot(vision_data_b['Month'], vision_data_b['mean'], color=COLORS['secondary'], linewidth=2.5, label=f'B: {sim_b["protocol"]}')

    # Confidence intervals
    if show_ci:
        ax.fill_between(vision_data_a['Month'],
                      vision_data_a['ci_lower'],
                      vision_data_a['ci_upper'],
                      alpha=0.15, color=COLORS['primary'])
        ax.fill_between(vision_data_b['Month'],
                      vision_data_b['ci_lower'],
                      vision_data_b['ci_upper'],
                      alpha=0.15, color=COLORS['secondary'])
    
    # Clinical thresholds - subtle
    if show_thresholds:
        ax.axhline(y=70, color='#999999', linestyle='-', alpha=0.3, linewidth=0.8)
        ax.axhline(y=20, color='#999999', linestyle='-', alpha=0.3, linewidth=0.8)
        ax.text(max_month * 0.98, 71, '70', ha='right', va='bottom', fontsize=8, color='#666666')
        ax.text(max_month * 0.98, 21, '20', ha='right', va='bottom', fontsize=8, color='#666666')
    
    # Tufte styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#333333')
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    ax.tick_params(colors='#333333', width=0.8, length=4)
    
    ax.set_xlabel('Time (months)', fontsize=10, color='#333333')
    ax.set_ylabel('Vision (ETDRS Letters)', fontsize=10, color='#333333')
    ax.set_xlim(0, max_month)
    ax.set_ylim(0, 85)
    ax.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc')
    ax.legend(fontsize=9, frameon=False, loc='upper right')
    
    st.pyplot(fig)
    plt.close(fig)

else:  # Difference mode
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
    ax.set_facecolor('white')
    
    # Interpolate to common time points for difference calculation
    common_months = np.sort(list(set(vision_data_a['Month'].tolist()) & set(vision_data_b['Month'].tolist())))
    
    # Get values at common months
    mean_a_common = []
    mean_b_common = []
    for month in common_months:
        mean_a_common.append(vision_data_a[vision_data_a['Month'] == month]['mean'].values[0])
        mean_b_common.append(vision_data_b[vision_data_b['Month'] == month]['mean'].values[0])
    
    # Calculate difference (B - A)
    difference = np.array(mean_b_common) - np.array(mean_a_common)
    
    # Plot difference with Tufte style
    ax.plot(common_months, difference, color='#7f7f7f', linewidth=2.5, label='B - A')
    ax.fill_between(common_months, 0, difference, 
                   where=(difference >= 0), 
                   color='#2ca02c', alpha=0.2, label='B Better')
    ax.fill_between(common_months, 0, difference, 
                   where=(difference < 0), 
                   color='#d62728', alpha=0.2, label='A Better')
    
    # Zero line - more prominent as it's a key reference
    ax.axhline(y=0, color='#333333', linestyle='-', alpha=0.8, linewidth=1)
    
    # Tufte styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#333333')
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    ax.tick_params(colors='#333333', width=0.8, length=4)
    
    ax.set_xlabel('Time (months)', fontsize=10, color='#333333')
    ax.set_ylabel('Vision Difference (ETDRS Letters)', fontsize=10, color='#333333')
    ax.set_xlim(0, max_month)
    ax.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc')
    ax.legend(fontsize=9, frameon=False, title='Difference (B - A)', title_fontsize=10)
    
    st.pyplot(fig)
    plt.close(fig)

# ==================================================================
# POPULATION-LEVEL OUTCOME COMPARISON (Addressing Survivorship Bias)
# ==================================================================

st.markdown("---")
st.subheader("Population-Level Outcome Comparison")

# Repeat protocol information for long page context
st.markdown("**Comparing:**")
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    **Simulation A:** {sim_a['protocol']}
    - {sim_a['patients']} patients, {sim_a['duration']} months
    """)
with col2:
    st.markdown(f"""
    **Simulation B:** {sim_b['protocol']}
    - {sim_b['patients']} patients, {sim_b['duration']} months
    """)

st.markdown("""
This analysis addresses **survivorship bias** by tracking all patients from baseline, regardless of discontinuation status.

**Why This Matters:**
- Standard comparisons may show better outcomes in protocols with higher discontinuation rates (because poor responders are removed)
- Intent-to-Treat (ITT) analysis tracks ALL patients to give a true population-level view
- Stratified analysis shows outcomes separately for active vs. discontinued patients

**Three-Panel View:**
1. **Left**: ITT vision trajectory (all baseline patients, using last-observation-carried-forward)
2. **Middle**: Patient retention over time (% active vs. discontinued)
3. **Right**: Final vision outcomes stratified by patient status
""")

try:
    from visualization.population_outcome_comparison import (
        create_population_outcome_comparison,
        export_population_comparison_data
    )

    # Create the population outcome comparison
    with st.spinner("Generating population-level comparison..."):
        fig_population = create_population_outcome_comparison(
            results_a,
            results_b,
            label_a=f"{sim_a['protocol'][:20]}",
            label_b=f"{sim_b['protocol'][:20]}",
            max_months=int(max_month)
        )

        # Display the figure - no use_container_width to maintain crisp rendering
        st.pyplot(fig_population)
        plt.close(fig_population)

        # Export data option
        with st.expander("📊 Export Population Comparison Data"):
            export_pop_df = export_population_comparison_data(
                results_a,
                results_b,
                label_a=sim_a['protocol'],
                label_b=sim_b['protocol'],
                max_months=int(max_month)
            )

            st.dataframe(export_pop_df)

            csv_pop = export_pop_df.to_csv(index=False)
            st.download_button(
                label="Download Population Comparison CSV",
                data=csv_pop,
                file_name=f"population_comparison_{sim_a['name']}_{sim_b['name']}.csv",
                mime="text/csv"
            )

except Exception as e:
    st.error(f"Could not create population-level comparison: {str(e)}")
    import traceback
    st.code(traceback.format_exc())

# ==================================================================
# FINANCIAL COMPARISON
# ==================================================================

st.markdown("---")
st.markdown("### Financial Analysis")

# Import cost tracking functionality
from simulation_v2.economics.cost_config import CostConfig
from simulation_v2.economics.resource_tracker import ResourceTracker
from ape.components.treatment_patterns.discontinued_utils import get_discontinued_patients
from pathlib import Path

# Get available cost configs
COST_CONFIG_DIR = Path("protocols/cost_configs")
available_configs = [f.stem for f in COST_CONFIG_DIR.glob("*.yaml") if f.is_file()]

# Financial configuration selection
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    config_a = st.selectbox(
        "Cost Configuration for Simulation A",
        options=available_configs,
        index=available_configs.index("nhs_standard_2025") if "nhs_standard_2025" in available_configs else 0,
        key="cost_config_a"
    )

with col2:
    config_b = st.selectbox(
        "Cost Configuration for Simulation B", 
        options=available_configs,
        index=available_configs.index("nhs_standard_2025") if "nhs_standard_2025" in available_configs else 0,
        key="cost_config_b"
    )

with col3:
    use_same_config = st.checkbox("Use same", value=True, key="same_cost_config")
    
if use_same_config:
    config_b = config_a

# Load cost configurations
try:
    cost_config_a = CostConfig.from_yaml(COST_CONFIG_DIR / f"{config_a}.yaml")
    cost_config_b = CostConfig.from_yaml(COST_CONFIG_DIR / f"{config_b}.yaml")
    
    # Get default drug costs
    default_drug_cost_a = cost_config_a.drug_costs.get('aflibercept_2mg', 457)
    if isinstance(default_drug_cost_a, dict):
        default_drug_cost_a = default_drug_cost_a.get('unit_cost', 457)
    
    default_drug_cost_b = cost_config_b.drug_costs.get('aflibercept_2mg', 457)
    if isinstance(default_drug_cost_b, dict):
        default_drug_cost_b = default_drug_cost_b.get('unit_cost', 457)
    
except Exception as e:
    st.error(f"Error loading cost configurations: {str(e)}")
    cost_config_a = None
    cost_config_b = None
    default_drug_cost_a = 457
    default_drug_cost_b = 457

# Drug cost adjustment section
if cost_config_a and cost_config_b:
    st.markdown("#### Drug Cost Adjustments")
    
    # Toggle for shared vs individual adjustments
    adjustment_mode = st.radio(
        "Adjustment Mode",
        ["Shared slider", "Individual sliders"],
        horizontal=True,
        key="cost_adjustment_mode"
    )
    
    if adjustment_mode == "Shared slider":
        # Single slider for both simulations
        new_drug_cost = st.slider(
            "Intravitreal Drug Cost per Dose (£)",
            min_value=50,
            max_value=1500,
            value=int(default_drug_cost_a),
            step=10,
            key="shared_drug_cost"
        )
        new_drug_cost_a = new_drug_cost
        new_drug_cost_b = new_drug_cost
    else:
        # Individual sliders
        col1, col2 = st.columns(2)
        with col1:
            new_drug_cost_a = st.slider(
                f"Drug Cost A ({sim_a['memorable_name']}) £",
                min_value=50,
                max_value=1500,
                value=int(default_drug_cost_a),
                step=10,
                key="drug_cost_a"
            )
        with col2:
            new_drug_cost_b = st.slider(
                f"Drug Cost B ({sim_b['memorable_name']}) £",
                min_value=50,
                max_value=1500,
                value=int(default_drug_cost_b),
                step=10,
                key="drug_cost_b"
            )
    
    # Calculate financial outcomes using simulation data directly
    def calculate_costs_with_tracker(sim_data, cost_config, new_drug_cost, default_drug_cost):
        """Calculate costs similar to workload analysis page."""
        try:
            # Load the simulation using ResultsFactory to get resource tracker
            from ape.core.results.factory import ResultsFactory
            results = ResultsFactory.load_results(sim_data['path'])
            
            # Check if simulation has resource tracking
            resource_tracker = None
            if hasattr(results, 'resource_tracker'):
                resource_tracker = results.resource_tracker
            elif hasattr(results, '_raw_results') and hasattr(results._raw_results, 'resource_tracker'):
                resource_tracker = results._raw_results.resource_tracker
            
            if resource_tracker:
                # Use existing resource tracker's data
                # Helper function from workload analysis
                def safe_call_method(resource_tracker, method_name, default=None):
                    """Safely call a method on resource_tracker, handling SimpleNamespace wrapper."""
                    if hasattr(resource_tracker, method_name):
                        return getattr(resource_tracker, method_name)()
                    elif hasattr(resource_tracker, '__dict__'):
                        rt_dict = resource_tracker.__dict__
                        if method_name == 'get_total_costs':
                            return rt_dict.get('total_costs', default or {'total': 0, 'drug': 0})
                        elif method_name == 'get_workload_summary':
                            return rt_dict.get('workload_summary', default or {})
                    return default
                
                # Get original costs and workload
                original_costs = safe_call_method(resource_tracker, 'get_total_costs', {'total': 0, 'drug': 0})
                workload_summary = safe_call_method(resource_tracker, 'get_workload_summary', {})
                
                # Count injections from visits
                if hasattr(resource_tracker, '__dict__'):
                    visits = resource_tracker.__dict__.get('visits', [])
                else:
                    visits = getattr(resource_tracker, 'visits', [])
                
                total_injections = sum(1 for v in visits if v.get('injection_given', False))
                
                # Calculate drug cost adjustment
                drug_cost_diff = new_drug_cost - default_drug_cost
                drug_cost_adjustment = drug_cost_diff * total_injections
                
                # Apply adjustment
                adjusted_costs = original_costs.copy()
                if 'drug' in adjusted_costs:
                    adjusted_costs['drug'] = adjusted_costs.get('drug', 0) + drug_cost_adjustment
                    adjusted_costs['total'] = adjusted_costs.get('total', 0) + drug_cost_adjustment
                
                return {
                    'costs': adjusted_costs,
                    'original_costs': original_costs,
                    'workload_summary': workload_summary,
                    'total_injections': total_injections,
                    'resource_tracker': resource_tracker,
                    'has_resource_tracking': True
                }
            else:
                # No resource tracking available
                return {
                    'costs': {'total': 0, 'drug': 0},
                    'original_costs': {'total': 0, 'drug': 0},
                    'workload_summary': {},
                    'total_injections': 0,
                    'resource_tracker': None,
                    'has_resource_tracking': False
                }
            
        except Exception as e:
            st.error(f"Error calculating costs: {str(e)}")
            return None
    
    # Calculate costs for both simulations
    costs_a = calculate_costs_with_tracker(sim_a, cost_config_a, new_drug_cost_a, default_drug_cost_a)
    costs_b = calculate_costs_with_tracker(sim_b, cost_config_b, new_drug_cost_b, default_drug_cost_b)
    
    # Check if both simulations have resource tracking
    if costs_a and costs_b:
        # Check resource tracking availability
        has_tracking_a = costs_a.get('has_resource_tracking', False)
        has_tracking_b = costs_b.get('has_resource_tracking', False)
        
        if not has_tracking_a or not has_tracking_b:
            # Display warning message
            warning_msgs = []
            if not has_tracking_a:
                warning_msgs.append(f"**{sim_a['memorable_name']}** was run without resource tracking")
            if not has_tracking_b:
                warning_msgs.append(f"**{sim_b['memorable_name']}** was run without resource tracking")
            
            st.warning("Financial data is not available for the following simulations:")
            for msg in warning_msgs:
                st.markdown(f"- {msg}")
            
            st.info("""
            To enable financial analysis:
            1. Go to the **Simulation** page
            2. Enable **Resource Tracking** before running the simulation
            3. Run new simulations with resource tracking enabled
            
            Note: Resource tracking is only available for time-based protocols.
            """)
        
        elif has_tracking_a and has_tracking_b:
            # Display key financial metrics
            st.markdown("#### Key Financial Metrics")
            
            # Calculate metrics first
            cost_per_patient_a = costs_a['costs']['total'] / len(histories_a)
            cost_per_patient_b = costs_b['costs']['total'] / len(histories_b)
            
            # Calculate cost per vision maintained
            try:
                # Load patient data for vision outcomes
                patients_df_a = pd.read_parquet(sim_a['path'] / "patients.parquet")
                patients_df_b = pd.read_parquet(sim_b['path'] / "patients.parquet")
                
                # Count patients maintaining vision (not discontinued and vision loss ≤ 10)
                active_a = patients_df_a[patients_df_a['discontinued'] == False]
                vision_maintained_a = len(active_a[active_a['final_vision'] >= active_a['baseline_vision'] - 10])
                
                active_b = patients_df_b[patients_df_b['discontinued'] == False]
                vision_maintained_b = len(active_b[active_b['final_vision'] >= active_b['baseline_vision'] - 10])
                
                if vision_maintained_a > 0:
                    cost_per_maintained_a = costs_a['costs']['total'] / vision_maintained_a
                else:
                    cost_per_maintained_a = float('inf')
                    
                if vision_maintained_b > 0:
                    cost_per_maintained_b = costs_b['costs']['total'] / vision_maintained_b
                else:
                    cost_per_maintained_b = float('inf')
            except Exception:
                cost_per_maintained_a = float('inf')
                cost_per_maintained_b = float('inf')
            
            # Create three rows of side-by-side metrics
            # Row 1: Total Cost
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    f"Total Cost - {sim_a['memorable_name']}",
                    f"£{costs_a['costs']['total']:,.0f}"
                )
            with col2:
                st.metric(
                    f"Total Cost - {sim_b['memorable_name']}",
                    f"£{costs_b['costs']['total']:,.0f}",
                    delta=f"£{costs_b['costs']['total'] - costs_a['costs']['total']:+,.0f}"
                )
            
            # Row 2: Cost per Patient
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    f"Cost per Patient - {sim_a['memorable_name']}",
                    f"£{cost_per_patient_a:,.0f}"
                )
            with col2:
                st.metric(
                    f"Cost per Patient - {sim_b['memorable_name']}",
                    f"£{cost_per_patient_b:,.0f}",
                    delta=f"£{cost_per_patient_b - cost_per_patient_a:+,.0f}"
                )
            
            # Row 3: Cost per Sight Preserved
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    f"Cost per Sight Preserved - {sim_a['memorable_name']}",
                    f"£{cost_per_maintained_a:,.0f}" if cost_per_maintained_a != float('inf') else "N/A"
                )
            with col2:
                st.metric(
                    f"Cost per Sight Preserved - {sim_b['memorable_name']}",
                    f"£{cost_per_maintained_b:,.0f}" if cost_per_maintained_b != float('inf') else "N/A",
                    delta=f"£{cost_per_maintained_b - cost_per_maintained_a:+,.0f}" if cost_per_maintained_a != float('inf') and cost_per_maintained_b != float('inf') else None
                )
        
            # Sessions per week comparison
            st.markdown("#### Weekly Staffing Requirements")
        
            # Create comparison table
            sessions_data = []
        
            # Get sessions data from both simulations
            for label, costs_data, sim_info in [("Simulation A", costs_a, sim_a), ("Simulation B", costs_b, sim_b)]:
                workload = costs_data['workload_summary']
                for role in ['nurse', 'technician', 'consultant']:
                    if role in workload['average_daily_demand']:
                        avg_daily = workload['average_daily_demand'][role]
                        # Assuming 5 working days per week and standard capacity
                        capacity_per_session = {'nurse': 10, 'technician': 15, 'consultant': 8}.get(role, 10)
                        weekly_sessions = (avg_daily * 5) / capacity_per_session
                        
                        sessions_data.append({
                            'Simulation': sim_info['memorable_name'],
                            'Role': role.capitalize(),
                            'Avg Daily Demand': f"{avg_daily:.1f}",
                            'Weekly Sessions': f"{weekly_sessions:.1f}"
                        })
        
            if sessions_data:
                sessions_df = pd.DataFrame(sessions_data)
                
                # Pivot for better comparison
                pivot_df = sessions_df.pivot(index='Role', columns='Simulation', values='Weekly Sessions')
                st.dataframe(pivot_df, use_container_width=True)
        
            # Cost breakdown comparison
            st.markdown("#### Cost Breakdown Comparison")
            
            # Create side-by-side cost breakdown using plotly bar charts
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # Prepare data for both simulations
            cost_categories = ['Drug', 'Injection', 'Consultation', 'OCT Scan']
            cost_keys = ['drug', 'injection_procedure', 'consultation', 'oct_scan']
            
            values_a = [costs_a['costs'].get(key, 0) for key in cost_keys]
            values_b = [costs_b['costs'].get(key, 0) for key in cost_keys]
            
            # Create subplots
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=(sim_a['memorable_name'], sim_b['memorable_name']),
                horizontal_spacing=0.15
            )
            
            # Add bar chart for simulation A
            fig.add_trace(
                go.Bar(
                    x=cost_categories,
                    y=values_a,
                    text=[f"£{v:,.0f}" for v in values_a],
                    textposition='auto',
                    marker_color=COLORS['primary'],
                    showlegend=False
                ),
                row=1, col=1
            )
            
            # Add bar chart for simulation B
            fig.add_trace(
                go.Bar(
                    x=cost_categories,
                    y=values_b,
                    text=[f"£{v:,.0f}" for v in values_b],
                    textposition='auto',
                    marker_color=COLORS['secondary'],
                    showlegend=False
                ),
                row=1, col=2
            )
            
            # Update layout with Tufte principles
            fig.update_layout(
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=40, r=40, t=60, b=40),
                height=400
            )
            
            # Update axes
            for i in range(1, 3):
                fig.update_xaxes(
                    showgrid=False,
                    zeroline=False,
                    showline=True,
                    linewidth=1,
                    linecolor='gray',
                    row=1, col=i
                )
                fig.update_yaxes(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor=f'rgba(128,128,128,{ALPHAS["low"]})',
                    zeroline=True,
                    zerolinewidth=1,
                    zerolinecolor='gray',
                    title="Cost (£)" if i == 1 else "",
                    row=1, col=i
                )
            
            st.plotly_chart(fig, use_container_width=True)

# ==================================================================
# TREATMENT FLOW ANALYSIS
# ==================================================================

st.subheader("Treatment Flow Analysis")

# Create columns for side-by-side streamgraphs
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**{sim_a['memorable_name']}: {sim_a['protocol']}**")
    try:
        # Load simulation data using ResultsFactory
        results_a = ResultsFactory.load_results(sim_a['path'])
        if results_a:
            streamgraph_a = create_treatment_state_streamgraph(
                results_a, 
                time_resolution='month',
                normalize=False,
                height=400,
                show_title=False
            )
            st.plotly_chart(streamgraph_a, use_container_width=True)
        else:
            st.error(f"Could not load {sim_a['memorable_name']} data for streamgraph")
    except Exception as e:
        st.error(f"Error creating streamgraph for {sim_a['memorable_name']}: {str(e)}")

with col2:
    st.markdown(f"**{sim_b['memorable_name']}: {sim_b['protocol']}**")
    try:
        # Load simulation data using ResultsFactory
        results_b = ResultsFactory.load_results(sim_b['path'])
        if results_b:
            streamgraph_b = create_treatment_state_streamgraph(
                results_b,
                time_resolution='month', 
                normalize=False,
                height=400,
                show_title=False
            )
            st.plotly_chart(streamgraph_b, use_container_width=True)
        else:
            st.error(f"Could not load {sim_b['memorable_name']} data for streamgraph")
    except Exception as e:
        st.error(f"Error creating streamgraph for {sim_b['memorable_name']}: {str(e)}")

# ==================================================================
# PATIENT JOURNEY FLOW
# ==================================================================

st.subheader("Patient Journey Flow")

# Debug functionality
def save_sankey_debug(fig, name, transitions_df, save_path="debug"):
    """Save Sankey diagram and data for debugging."""
    import os
    from pathlib import Path
    
    # Create debug directory
    debug_dir = Path(save_path)
    debug_dir.mkdir(exist_ok=True)
    
    # Save figure as HTML for interactive inspection
    fig.write_html(debug_dir / f"{name}_sankey.html")
    
    # Save data summary
    with open(debug_dir / f"{name}_data_summary.txt", "w") as f:
        f.write(f"=== Debug Info for {name} ===\n")
        f.write(f"Transitions DataFrame shape: {transitions_df.shape}\n\n")
        
        f.write("Unique states in data:\n")
        # Check which column contains states
        if 'state' in transitions_df.columns:
            unique_states = sorted(transitions_df['state'].unique())
            for state in unique_states:
                count = len(transitions_df[transitions_df['state'] == state])
                f.write(f"  - {state}: {count} transitions\n")
        elif 'from_state' in transitions_df.columns and 'to_state' in transitions_df.columns:
            f.write("  From states:\n")
            for state in sorted(transitions_df['from_state'].dropna().unique()):
                count = len(transitions_df[transitions_df['from_state'] == state])
                f.write(f"    - {state}: {count} transitions\n")
            f.write("  To states:\n")
            for state in sorted(transitions_df['to_state'].dropna().unique()):
                count = len(transitions_df[transitions_df['to_state'] == state])
                f.write(f"    - {state}: {count} transitions\n")
                
            # Identify terminal states by name pattern
            f.write("\nTerminal states (identified by name pattern):\n")
            terminal_states = [s for s in transitions_df['to_state'].unique() 
                             if 'Still in' in s or 'No Further Visits' in s]
            for state in sorted(terminal_states):
                count = len(transitions_df[transitions_df['to_state'] == state])
                f.write(f"  - {state}: {count} transitions\n")
        else:
            f.write("  No state columns found! Columns are: " + str(list(transitions_df.columns)) + "\n")
        
        f.write("\nTransition patterns (first 20):\n")
        for idx, row in transitions_df.head(20).iterrows():
            f.write(f"  {row.get('from_state', 'N/A')} -> {row.get('to_state', row.get('state', 'N/A'))}\n")
    
    # Save raw data as CSV for analysis
    transitions_df.to_csv(debug_dir / f"{name}_transitions.csv", index=False)
    
    return debug_dir / f"{name}_sankey.html", debug_dir / f"{name}_data_summary.txt"

# Add debug controls
debug_mode = st.checkbox("Enable Debug Mode", key="sankey_debug_mode")

# No columns needed for dual-stream approach
# The diagram will span the full width

def create_dual_stream_sankey(transitions_df_a, transitions_df_b, name_a, name_b):
    """Create a single Sankey diagram with two separate streams for comparison."""
    import plotly.graph_objects as go
    import pandas as pd
    from ape.components.treatment_patterns.pattern_analyzer import get_treatment_state_colors
    
    # Get color scheme
    treatment_colors = get_treatment_state_colors()
    
    # Process transitions for both streams
    def process_transitions(df, prefix):
        """Process transitions and add prefix to states."""
        # Group and aggregate
        flow_counts = df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
        
        # Adjust terminal node counts to show unique patients
        from ape.components.treatment_patterns.sankey_patient_counts import adjust_terminal_node_counts
        flow_counts = adjust_terminal_node_counts(flow_counts, df)
        
        # Filter out Pre-Treatment and small flows
        flow_counts = flow_counts[
            (flow_counts['from_state'] != 'Pre-Treatment') & 
            (flow_counts['to_state'] != 'Pre-Treatment')
        ]
        
        # Keep significant flows and all terminal flows
        min_flow = max(1, len(df) * 0.001)
        is_terminal = flow_counts['to_state'].str.contains('Still in|No Further|Discontinued')
        flow_counts = flow_counts[(flow_counts['count'] >= min_flow) | is_terminal]
        
        # Add prefix to states
        flow_counts['from_state'] = prefix + flow_counts['from_state']
        flow_counts['to_state'] = prefix + flow_counts['to_state']
        
        return flow_counts
    
    # Process both streams
    flows_a = process_transitions(transitions_df_a, "A:")
    flows_b = process_transitions(transitions_df_b, "B:")
    
    # Combine flows
    all_flows = pd.concat([flows_a, flows_b], ignore_index=True)
    
    # Get all unique states
    states_a = set(flows_a['from_state']) | set(flows_a['to_state'])
    states_b = set(flows_b['from_state']) | set(flows_b['to_state'])
    all_states = sorted(states_a | states_b)
    
    # Collect terminal states for each stream to calculate dynamic positioning
    terminal_states_a = sorted([s for s in states_a if 'Still in' in s])
    terminal_states_b = sorted([s for s in states_b if 'Still in' in s])
    
    # Count how many "Still in" states exist for each stream
    num_still_in_a = len(terminal_states_a)
    num_still_in_b = len(terminal_states_b)
    
    # Create node mapping
    node_map = {state: i for i, state in enumerate(all_states)}
    
    # Define positions for nodes
    # Y positions: A stream 0.55-0.95, B stream 0.05-0.45
    x_positions = []
    y_positions = []
    node_colors = []
    node_labels = []
    
    # Calculate dynamic Y positions for "Still in" states
    still_in_y_positions_a = {}
    still_in_y_positions_b = {}
    
    # For A stream: distribute between 0.65 and 0.90
    if num_still_in_a > 0:
        if num_still_in_a == 1:
            # Center single state
            still_in_y_positions_a[terminal_states_a[0]] = 0.775
        else:
            # Distribute evenly
            y_start_a = 0.65
            y_end_a = 0.90
            y_step_a = (y_end_a - y_start_a) / (num_still_in_a - 1)
            for i, state in enumerate(terminal_states_a):
                still_in_y_positions_a[state] = y_start_a + i * y_step_a
    
    # For B stream: distribute between 0.15 and 0.40
    if num_still_in_b > 0:
        if num_still_in_b == 1:
            # Center single state
            still_in_y_positions_b[terminal_states_b[0]] = 0.275
        else:
            # Distribute evenly
            y_start_b = 0.15
            y_end_b = 0.40
            y_step_b = (y_end_b - y_start_b) / (num_still_in_b - 1)
            for i, state in enumerate(terminal_states_b):
                still_in_y_positions_b[state] = y_start_b + i * y_step_b
    
    for state in all_states:
        # Remove prefix for base state
        base_state = state[2:] if state.startswith(('A:', 'B:')) else state
        is_stream_a = state.startswith('A:')
        
        # X position based on treatment stage
        if 'Initial' in base_state and 'Still in' not in base_state:
            x = 0.0
        elif 'Intensive' in base_state and 'Still in' not in base_state:
            x = 0.2
        elif 'Regular' in base_state and 'Still in' not in base_state:
            x = 0.4
        elif 'Extended' in base_state and 'Maximum' not in base_state and 'Still in' not in base_state:
            x = 0.6
        elif 'Maximum' in base_state and 'Still in' not in base_state:
            x = 0.7
        elif 'Still in' in base_state or 'No Further' in base_state:
            x = 0.95
        else:
            x = 0.5
            
        # Y position based on stream and state type
        # Compress the vertical space usage more
        if is_stream_a:
            # A stream - upper half (0.55 to 0.95)
            if 'Initial' in base_state:
                y = 0.75
            elif 'Intensive' in base_state:
                y = 0.78
            elif 'Regular' in base_state:
                y = 0.75
            elif 'Extended' in base_state:
                y = 0.72
            elif 'Maximum' in base_state:
                y = 0.70
            elif 'No Further' in base_state:
                y = 0.60  # Put discontinued at bottom of A stream
            elif 'Still in' in base_state:
                # Use dynamically calculated position
                y = still_in_y_positions_a.get(state, 0.77)
            else:
                y = 0.75
        else:
            # B stream - lower half (0.05 to 0.45)
            if 'Initial' in base_state:
                y = 0.25
            elif 'Intensive' in base_state:
                y = 0.22
            elif 'Regular' in base_state:
                y = 0.25
            elif 'Extended' in base_state:
                y = 0.28
            elif 'Maximum' in base_state:
                y = 0.30
            elif 'No Further' in base_state:
                y = 0.10  # Put discontinued at bottom of B stream
            elif 'Still in' in base_state:
                # Use dynamically calculated position
                y = still_in_y_positions_b.get(state, 0.32)
            else:
                y = 0.25
        
        x_positions.append(x)
        y_positions.append(y)
        
        # Colors based on state type
        if 'Still in' in base_state:
            node_colors.append('#27ae60')  # Green for continuing
        elif 'No Further' in base_state or 'Discontinued' in base_state:
            node_colors.append('#999999')  # Gray for discontinued (matches streamgraph)
        else:
            node_colors.append(treatment_colors.get(base_state, '#cccccc'))
        
        # Empty labels
        node_labels.append("")
    
    # Create links
    sources = [node_map[row['from_state']] for _, row in all_flows.iterrows()]
    targets = [node_map[row['to_state']] for _, row in all_flows.iterrows()]
    values = [row['count'] for _, row in all_flows.iterrows()]
    
    # Link colors with transparency
    link_colors = []
    for _, row in all_flows.iterrows():
        base_state = row['from_state'][2:]  # Remove prefix
        color = treatment_colors.get(base_state, '#cccccc')
        # Convert hex to rgba with transparency
        if color.startswith('#'):
            hex_color = color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            link_colors.append(f'rgba({r}, {g}, {b}, 0.4)')
        else:
            link_colors.append(color)
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        arrangement='fixed',
        node=dict(
            pad=8,  # Reduced padding
            thickness=15,  # Thinner nodes
            line=dict(width=0),
            label=node_labels,
            color=node_colors,
            x=x_positions,
            y=y_positions,
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate='%{value} patients<extra></extra>'
        ),
        textfont=dict(size=1, color='rgba(0,0,0,0)')
    )])
    
    # Add separator line
    fig.add_shape(
        type="line",
        x0=0, x1=1,
        y0=0.5, y1=0.5,
        line=dict(color="gray", width=1, dash="dash"),
        xref="paper", yref="paper"
    )
    
    # Add labels for each stream
    fig.add_annotation(
        text=f"<b>{name_a}</b>",
        xref="paper", yref="paper",
        x=0.02, y=0.95,
        showarrow=False,
        font=dict(size=14, color="#333"),
        bgcolor="rgba(255,255,255,0.9)",
        borderpad=4
    )
    
    fig.add_annotation(
        text=f"<b>{name_b}</b>",
        xref="paper", yref="paper",
        x=0.02, y=0.05,
        showarrow=False,
        font=dict(size=14, color="#333"),
        bgcolor="rgba(255,255,255,0.9)",
        borderpad=4
    )
    
    # Update layout
    fig.update_layout(
        height=650,  # Reduced height with better node positioning
        margin=dict(l=20, r=150, t=50, b=60),  # More margin at top and bottom
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# First, load both datasets
transitions_df_a = None
transitions_df_b = None

# Load data for Simulation A
try:
    # Check if we already loaded results_a above
    if 'results_a' not in locals():
        results_a = ResultsFactory.load_results(sim_a['path'])
        
    if results_a:
        # Use the same approach as analysis page - check for enhanced version
        try:
            from ape.components.treatment_patterns.pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals
            enhanced_available = True
        except ImportError:
            enhanced_available = False
            
        # Get patterns with terminal states if available
        if enhanced_available:
            transitions_df_a, _ = extract_treatment_patterns_with_terminals(results_a)
        else:
            from ape.components.treatment_patterns.data_manager import get_treatment_pattern_data
            transitions_df_a, _ = get_treatment_pattern_data(results_a)
except Exception as e:
    st.error(f"Error loading Simulation A data: {str(e)}")

# Load data for Simulation B
try:
    # Check if we already loaded results_b above
    if 'results_b' not in locals():
        results_b = ResultsFactory.load_results(sim_b['path'])
        
    if results_b:
        # Use the same approach as analysis page - check for enhanced version
        try:
            from ape.components.treatment_patterns.pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals
            enhanced_available = True
        except ImportError:
            enhanced_available = False
            
        # Get patterns with terminal states if available
        if enhanced_available:
            transitions_df_b, _ = extract_treatment_patterns_with_terminals(results_b)
        else:
            from ape.components.treatment_patterns.data_manager import get_treatment_pattern_data
            transitions_df_b, _ = get_treatment_pattern_data(results_b)
except Exception as e:
    st.error(f"Error loading Simulation B data: {str(e)}")

# Create dual-stream Sankey with both simulations
if transitions_df_a is not None and transitions_df_b is not None:
    # Get memorable names from simulations
    name_a = sim_a.get('memorable_name', sim_a['name'])
    name_b = sim_b.get('memorable_name', sim_b['name'])
    
    # Debug info
    if debug_mode:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Simulation A: {name_a}**")
            st.info(f"Transitions shape: {transitions_df_a.shape}")
            st.write(f"Enhanced analyzer: {enhanced_available}")
            
            # Show terminal states by name pattern
            terminal_states_a = [s for s in transitions_df_a['to_state'].unique() 
                               if 'Still in' in s or 'No Further Visits' in s]
            if terminal_states_a:
                st.write("Terminal states found:")
                for state in sorted(terminal_states_a):
                    count = len(transitions_df_a[transitions_df_a['to_state'] == state])
                    st.write(f"  - {state}: {count} transitions")
        
        with col2:
            st.markdown(f"**Simulation B: {name_b}**")
            st.info(f"Transitions shape: {transitions_df_b.shape}")
            st.write(f"Enhanced analyzer: {enhanced_available}")
            
            # Show terminal states by name pattern
            terminal_states_b = [s for s in transitions_df_b['to_state'].unique() 
                               if 'Still in' in s or 'No Further Visits' in s]
            if terminal_states_b:
                st.write("Terminal states found:")
                for state in sorted(terminal_states_b):
                    count = len(transitions_df_b[transitions_df_b['to_state'] == state])
                    st.write(f"  - {state}: {count} transitions")
    
    # Create and display the dual-stream Sankey
    try:
        dual_sankey = create_dual_stream_sankey(transitions_df_a, transitions_df_b, name_a, name_b)
        st.plotly_chart(dual_sankey, use_container_width=True)
        
        # Save debug files if in debug mode
        if debug_mode:
            try:
                # Save the dual sankey
                html_path = Path("debug") / "dual_stream_sankey.html"
                html_path.parent.mkdir(exist_ok=True)
                dual_sankey.write_html(html_path)
                st.caption(f"Debug file saved to {html_path}")
            except Exception as e:
                st.error(f"Error saving debug file: {str(e)}")
                
    except Exception as e:
        st.error(f"Error creating dual-stream Sankey: {str(e)}")
        if debug_mode:
            st.exception(e)
else:
    st.error("Could not load data for both simulations")

# Debug download section
if debug_mode:
    st.markdown("---")
    st.subheader("Debug Downloads")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Check if debug files exist
        debug_dir = Path("debug")
        if debug_dir.exists():
            # Create a zip of debug files
            import zipfile
            import io
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file in debug_dir.iterdir():
                    if file.is_file():
                        zip_file.write(file, file.name)
            
            st.download_button(
                label="Download Debug Files",
                data=zip_buffer.getvalue(),
                file_name="sankey_debug.zip",
                mime="application/zip"
            )
    
    with col2:
        st.info("Debug files include:\n- HTML interactive diagrams\n- Data summaries\n- Raw CSV data")
    
    with col3:
        # Add comparison with analysis page
        st.markdown("**Compare with Analysis Page:**")
        st.caption("To compare, navigate to Analysis > Patient Journey tab and enable debug mode there too")

# Success message at the bottom
st.success(f"Comparison complete: {sim_a['protocol']} vs {sim_b['protocol']}")