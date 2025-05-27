"""
Analysis Overview - Visualize simulation results (Vectorized for speed).
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import visualization mode system - no fallbacks!
from utils.visualization_modes import (
    init_visualization_mode, mode_aware_figure, 
    get_mode_colors, apply_visualization_mode
)
from utils.tufte_zoom_style import (
    style_axis, add_reference_line, format_zoom_legend
)
from utils.style_constants import StyleConstants
from utils.chart_builder import ChartBuilder

st.set_page_config(
    page_title="Analysis Overview", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add parent for utils import
sys.path.append(str(Path(__file__).parent.parent))
from utils.button_styling import style_navigation_buttons

# Apply our button styling
style_navigation_buttons()

# Top navigation
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if st.button("🦍 Home", key="top_home"):
        st.switch_page("APE.py")
with col2:
    st.title("📊 Analysis Overview")
    st.markdown("Visualize and analyze simulation results.")

# Initialize visualization mode selector - required!
current_mode = init_visualization_mode()

# Check if results are available
if not st.session_state.get('simulation_results'):
    st.warning("⚠️ No simulation results available. Please run a simulation first.")
    st.stop()

results_data = st.session_state.simulation_results
results = results_data['results']
protocol = results_data['protocol']
params = results_data['parameters']

# Results header
st.success(f"✅ Analyzing: {protocol['name']} - {params['n_patients']} patients over {params['duration_years']} years")

# Get summary statistics once and cache
@st.cache_data
def get_cached_stats(sim_id):
    """Cache summary statistics to avoid recalculation."""
    return results.get_summary_statistics()

@st.cache_data
def calculate_vision_stats_vectorized(sim_id, sample_size=None):
    """Calculate vision statistics using vectorized operations."""
    # Get vision trajectory data
    vision_df = results.get_vision_trajectory_df(sample_size=sample_size)
    
    # Use groupby to get first and last vision for each patient - MUCH faster!
    patient_stats = vision_df.groupby('patient_id')['vision'].agg(['first', 'last']).reset_index()
    
    # Extract arrays
    baseline_visions = patient_stats['first'].values
    final_visions = patient_stats['last'].values
    vision_changes = final_visions - baseline_visions
    
    return baseline_visions, final_visions, vision_changes, len(patient_stats)

stats = get_cached_stats(results.metadata.sim_id)
is_large_dataset = stats['patient_count'] > 1000

# Create tabs for different analyses
tab1, tab2, tab3, tab4 = st.tabs(["Vision Outcomes", "Treatment Patterns", "Patient Trajectories", "Audit Trail"])

with tab1:
    st.header("Vision Outcomes")
    
    # Use vectorized calculation
    if is_large_dataset:
        st.info(f"📊 Analyzing all {stats['patient_count']:,} patients. Histograms show representative samples for performance.")
        
        with st.spinner(f"Calculating vision statistics for {stats['patient_count']:,} patients..."):
            # Use a moderate sample for histogram visualization
            sample_size = min(5000, stats['patient_count'])
            baseline_visions, final_visions, vision_changes, n_patients = calculate_vision_stats_vectorized(
                results.metadata.sim_id, sample_size=sample_size
            )
    else:
        # For small datasets, use all data
        baseline_visions, final_visions, vision_changes, n_patients = calculate_vision_stats_vectorized(
            results.metadata.sim_id
        )
    
    # Vision distribution plots
    col1, col2 = st.columns(2)
    
    with col1:
        # Vision distribution chart
        chart = (ChartBuilder('Vision Distribution: Baseline vs Final')
                .with_labels(xlabel='Vision (ETDRS letters)', ylabel='Number of Patients')
                .with_vision_axis('x')
                .with_count_axis('y')
                .plot(lambda ax, colors: [
                    ax.hist(baseline_visions, bins=20, alpha=0.6, label='Baseline', 
                           color=colors['primary'], edgecolor=colors['neutral'], linewidth=1.5),
                    ax.hist(final_visions, bins=20, alpha=0.6, label='Final', 
                           color=colors['secondary'], edgecolor=colors['neutral'], linewidth=1.5)
                ])
                .with_legend(loc='upper left')
                .build())
        st.pyplot(chart.figure)
        
    with col2:
        # Vision change chart
        mean_change = np.mean(vision_changes)
        formatted_mean = StyleConstants.format_vision(mean_change)
        
        chart = (ChartBuilder('Distribution of Vision Changes')
                .with_labels(xlabel='Vision Change (ETDRS letters)', ylabel='Number of Patients')
                .with_count_axis('y')
                .plot(lambda ax, colors: 
                      ax.hist(vision_changes, bins=20, color=colors['success'], 
                             alpha=0.7, edgecolor=colors['neutral'], linewidth=1.5))
                .add_reference_line(0, 'No change', 'vertical', 'secondary')
                .add_reference_line(mean_change, f'Mean: {formatted_mean}', 'vertical', 'primary')
                .build())
        st.pyplot(chart.figure)
    
    # Summary statistics - always use full dataset stats
    st.subheader("Vision Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Use vectorized stats
        st.metric("Mean Baseline Vision", f"{StyleConstants.format_vision(np.mean(baseline_visions))} letters")
        st.metric("Std Baseline Vision", f"{StyleConstants.format_statistic(np.std(baseline_visions))} letters")
        
    with col2:
        # Always use full dataset stats from summary
        st.metric("Mean Final Vision", f"{StyleConstants.format_vision(stats.get('mean_final_vision', np.mean(final_visions)))} letters")
        st.metric("Std Final Vision", f"{StyleConstants.format_statistic(stats.get('std_final_vision', np.std(final_visions)))} letters")
        
    with col3:
        # Use vectorized stats
        st.metric("Mean Vision Change", f"{StyleConstants.format_vision(mean_change)} letters")
        st.metric("Patients Improved", f"{StyleConstants.format_count(np.sum(vision_changes > 0))}/{StyleConstants.format_count(len(vision_changes))}")
    
    if is_large_dataset:
        st.caption(f"*Histograms based on representative sample of {n_patients:,} patients. Statistics reflect all {stats['patient_count']:,} patients.")

with tab2:
    st.header("Treatment Patterns")
    
    # Always show full dataset statistics
    total_patients = stats['patient_count']
    total_injections = stats.get('total_injections', 0)
    mean_injections = total_injections / total_patients if total_patients > 0 else 0
    
    # Show key metrics first
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Patients", f"{StyleConstants.format_count(total_patients)}")
    with col2:
        st.metric("Total Injections", f"{StyleConstants.format_count(int(total_injections))}")
    with col3:
        st.metric("Mean Injections/Patient", f"{StyleConstants.format_statistic(mean_injections)}")
    with col4:
        st.metric("Injection Rate", f"{(total_injections / (total_patients * params['duration_years'])):.1f}/year")
    
    # Get treatment intervals - this is usually fast even for large datasets
    with st.spinner("Loading treatment intervals..."):
        treatment_df = results.get_treatment_intervals_df()
        
        if not treatment_df.empty:
            # For visualization, we might sample if it's huge
            if len(treatment_df) > 50000:
                display_df = treatment_df.sample(n=50000, random_state=42)
                show_sample_note = True
            else:
                display_df = treatment_df
                show_sample_note = False
            
            all_intervals = display_df['interval_days'].values
            
            # Visit intervals chart
            spec = protocol['spec']
            
            chart = (ChartBuilder('Distribution of Visit Intervals')
                    .with_labels(xlabel='Interval Between Visits (days)', ylabel='Frequency')
                    .with_count_axis('y')
                    .plot(lambda ax, colors: 
                          ax.hist(all_intervals, bins=30, color=colors['warning'], 
                                 alpha=0.7, edgecolor=colors['neutral'], linewidth=1.5))
                    .add_reference_line(spec.min_interval_days, 
                                       f'Min: {spec.min_interval_days} days', 
                                       'vertical', 'secondary')
                    .add_reference_line(spec.max_interval_days, 
                                       f'Max: {spec.max_interval_days} days', 
                                       'vertical', 'secondary')
                    .build())
            st.pyplot(chart.figure)
            
            # Show interval statistics - vectorized operations
            st.subheader("Interval Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Mean Interval", f"{np.mean(all_intervals):.1f} days")
            with col2:
                st.metric("Median Interval", f"{np.median(all_intervals):.1f} days")
            with col3:
                st.metric("Std Dev", f"{np.std(all_intervals):.1f} days")
                
            if show_sample_note:
                st.caption(f"*Histogram based on sample of 50,000 intervals from {len(treatment_df):,} total")

with tab3:
    st.header("Patient Trajectories")
    
    # For trajectories, we always need to sample for readability
    default_n_sample = 20
    max_sample = min(100, stats['patient_count'])
    
    # Add a slider for number of trajectories to show
    n_sample = st.slider(
        "Number of patient trajectories to display:",
        min_value=5,
        max_value=max_sample,
        value=default_n_sample,
        step=5,
        help="Showing too many trajectories makes the plot unreadable"
    )
    
    with st.spinner(f"Loading {n_sample} patient trajectories..."):
        vision_df_sample = results.get_vision_trajectory_df(sample_size=n_sample)
    
    # Vision trajectories with better x-axis
    def plot_trajectories(ax, colors):
        # Use different alpha and linewidth based on mode
        alpha = 0.6 if current_mode == 'presentation' else 0.4
        lw = 2 if current_mode == 'presentation' else 1
        
        # Group by patient_id once
        grouped = vision_df_sample.groupby('patient_id')
        
        for i, (patient_id, patient_data) in enumerate(grouped):
            patient_data = patient_data.sort_values('time_months')
            
            months = patient_data['time_months'].values
            visions = patient_data['vision'].values
            
            # Use a color cycle for better visibility
            if n_sample <= 20:
                # Use distinct colors for small samples
                color = plt.cm.tab10(i % 10)
            else:
                # Use gradient for larger samples
                color = plt.cm.viridis(i / n_sample)
            
            ax.plot(months, visions, alpha=alpha, linewidth=lw, color=color)
    
    # Create custom chart that uses months directly
    fig, ax = mode_aware_figure(f'Vision Trajectories ({n_sample} patients)')
    colors = get_mode_colors()
    
    # Plot the trajectories
    plot_trajectories(ax, colors)
    
    # Style the plot (title already set by mode_aware_figure)
    ax.set_xlabel('Time (months)')
    ax.set_ylabel('Vision (ETDRS letters)')
    
    # Set vision scale
    ax.set_ylim(0, 100)
    ax.set_yticks(StyleConstants.get_vision_ticks())
    
    # Set time scale with proper month ticks
    max_months = vision_df_sample['time_months'].max()
    
    # Create clean month ticks
    if max_months <= 12:
        # Monthly ticks for first year
        month_ticks = list(range(0, int(max_months) + 1, 1))
    elif max_months <= 24:
        # Every 2 months for up to 2 years
        month_ticks = list(range(0, int(max_months) + 1, 2))
    elif max_months <= 60:
        # Every 6 months for up to 5 years
        month_ticks = list(range(0, int(max_months) + 1, 6))
    else:
        # Yearly for longer simulations
        month_ticks = list(range(0, int(max_months) + 1, 12))
    
    ax.set_xticks(month_ticks)
    ax.set_xlim(0, max_months)
    
    # Apply styling
    style_axis(ax)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Add trajectory statistics - vectorized!
    st.subheader("Trajectory Summary")
    
    # Calculate trajectory changes using vectorized operations
    trajectory_changes = vision_df_sample.groupby('patient_id')['vision'].agg(['first', 'last'])
    trajectory_changes['change'] = trajectory_changes['last'] - trajectory_changes['first']
    
    trajectories_improving = (trajectory_changes['change'] > 5).sum()
    trajectories_stable = ((trajectory_changes['change'] >= -5) & (trajectory_changes['change'] <= 5)).sum()
    trajectories_worsening = (trajectory_changes['change'] < -5).sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Improving (>5 letters)", trajectories_improving)
    with col2:
        st.metric("Stable (±5 letters)", trajectories_stable)
    with col3:
        st.metric("Worsening (>5 letters loss)", trajectories_worsening)
    
    st.caption(f"*Showing {n_sample} of {stats['patient_count']:,} total patients")

with tab4:
    st.header("Audit Trail")
    st.markdown("Complete parameter tracking and simulation events.")
    
    if st.session_state.get('audit_trail'):
        audit_log = st.session_state.audit_trail
        
        # Display audit events
        for i, event in enumerate(audit_log):
            with st.expander(f"{event['event']} - {event['timestamp']}", expanded=(i==0)):
                # Format the event data nicely
                if event['event'] == 'protocol_loaded':
                    st.json(event['protocol'])
                elif event['event'] == 'simulation_start':
                    st.write(f"**Engine:** {event['engine_type']}")
                    st.write(f"**Patients:** {event['n_patients']}")
                    st.write(f"**Duration:** {event['duration_years']} years")
                    st.write(f"**Seed:** {event['seed']}")
                    st.write(f"**Protocol:** {event['protocol_name']} v{event['protocol_version']}")
                    st.code(f"Checksum: {event['protocol_checksum']}")
                elif event['event'] == 'simulation_complete':
                    st.write(f"**Total Injections:** {StyleConstants.format_count(event['total_injections'])}")
                    st.write(f"**Mean Final Vision:** {StyleConstants.format_vision(event['final_vision_mean'])}")
                    st.write(f"**Discontinuation Rate:** {StyleConstants.format_percentage(event['discontinuation_rate'])}")
                else:
                    st.json(event)
        
        # Download audit trail
        import json
        audit_json = json.dumps(audit_log, indent=2)
        st.download_button(
            label="📥 Download Full Audit Trail",
            data=audit_json,
            file_name=f"audit_trail_{params['engine']}_{params['n_patients']}p_{params['duration_years']}y.json",
            mime="application/json"
        )
    else:
        st.info("No audit trail available for this session.")