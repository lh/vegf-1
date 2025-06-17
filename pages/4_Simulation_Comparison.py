"""
Simulation Comparison - Compare results from two saved simulations.
"""

import streamlit as st
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import json

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
from ape.utils.simulation_package import load_simulation_results

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
        'recent_pairs': []
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
            return {
                'path': sim_path,
                'name': sim_path.name,
                'protocol': metadata.get('protocol_name', 'Unknown'),
                'patients': metadata.get('n_patients', 0),
                'duration': metadata.get('duration_months', 0),
                'date': datetime.fromisoformat(metadata.get('timestamp', '')).strftime('%Y-%m-%d'),
                'model_type': metadata.get('model_type', 'standard')
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
    return f"{sim_info['protocol']} - {sim_info['patients']} patients, {sim_info['duration']} months ({sim_info['date']})"

def get_compatible_simulations(selected_sim, all_sims):
    """Filter simulations to only show compatible options."""
    if not selected_sim:
        return all_sims
    
    selected_duration = selected_sim['duration']
    compatible = []
    
    for sim in all_sims:
        duration_diff = abs(sim['duration'] - selected_duration)
        if duration_diff <= 1:  # 1 month tolerance
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
            if ape_button(f"{sim_a_name[:20]}... vs {sim_b_name[:20]}...", 
                         key=f"recent_{i}", 
                         button_type="ghost"):
                # Load this comparison
                for sim in simulation_infos:
                    if sim['name'] == sim_a_name:
                        st.session_state.comparison_state['sim_a'] = sim
                    if sim['name'] == sim_b_name:
                        st.session_state.comparison_state['sim_b'] = sim
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
        # Swap simulations
        sim_a = st.session_state.comparison_state['sim_a']
        sim_b = st.session_state.comparison_state['sim_b']
        st.session_state.comparison_state['sim_a'] = sim_b
        st.session_state.comparison_state['sim_b'] = sim_a
        st.rerun()

with col3:
    st.markdown("**Simulation B**")
    
    # Get compatible simulations
    sim_a = st.session_state.comparison_state['sim_a']
    if sim_a:
        compatible_sims = get_compatible_simulations(sim_a, simulation_infos)
        st.caption(f"Showing {len(compatible_sims)} compatible simulations")
    else:
        compatible_sims = simulation_infos
    
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
    st.warning(f"⚠️ No simulations found with duration matching {sim_a['duration']} months")
else:
    st.info("ℹ️ Simulations must have matching duration for valid comparison")

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

# Update recent pairs
update_recent_pairs(sim_a, sim_b)

# Section 2: Simulation Overview Cards
st.markdown("---")
st.markdown("### Simulation Overview")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**📄 Simulation A**")
    st.markdown(f"**Protocol:** {sim_a['protocol']}")
    st.markdown(f"**Patients:** {sim_a['patients']:,}")
    st.markdown(f"**Duration:** {sim_a['duration']} months")
    st.markdown(f"**Model:** {sim_a['model_type'].title()}")
    st.markdown(f"**Run Date:** {sim_a['date']}")

with col2:
    st.markdown(f"**📄 Simulation B**")
    st.markdown(f"**Protocol:** {sim_b['protocol']}")
    st.markdown(f"**Patients:** {sim_b['patients']:,}")
    st.markdown(f"**Duration:** {sim_b['duration']} months")
    st.markdown(f"**Model:** {sim_b['model_type'].title()}")
    st.markdown(f"**Run Date:** {sim_b['date']}")

# Load the actual simulation data
with st.spinner("Loading simulation data..."):
    try:
        results_a = load_simulation_results(sim_a['path'])
        results_b = load_simulation_results(sim_b['path'])
        
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
with col2:
    if ape_button("Copy", key="copy_metrics", icon="copy", button_type="ghost"):
        st.info("Copy functionality coming soon")
        
with col3:
    if ape_button("CSV", key="download_csv", icon="csv", button_type="ghost"):
        st.info("Download functionality coming soon")

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

# Section 4: Visualizations (placeholder)
st.markdown("---")
st.markdown("### Visualizations")

# View mode toggle
view_mode = st.radio(
    "View Mode",
    ["Side-by-Side", "Overlay", "Difference"],
    horizontal=True,
    key="view_mode_radio"
)

st.info(f"Visualization in {view_mode} mode will be implemented next...")

# Success message
st.success(f"Successfully loaded comparison: {sim_a['protocol']} vs {sim_b['protocol']}")