"""
Analysis Overview - Visualize simulation results.
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

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

st.set_page_config(page_title="Analysis Overview", page_icon="📊", layout="wide")

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

# Create tabs for different analyses
tab1, tab2, tab3, tab4 = st.tabs(["Vision Outcomes", "Treatment Patterns", "Patient Trajectories", "Audit Trail"])

with tab1:
    st.header("Vision Outcomes")
    
    # Prepare vision data
    baseline_visions = []
    final_visions = []
    vision_changes = []
    
    for patient in results.patient_histories.values():
        baseline_visions.append(patient.baseline_vision)
        final_visions.append(patient.current_vision)
        vision_changes.append(patient.current_vision - patient.baseline_vision)
    
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
    
    # Summary statistics
    st.subheader("Vision Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Mean Baseline Vision", f"{StyleConstants.format_vision(np.mean(baseline_visions))} letters")
        st.metric("Std Baseline Vision", f"{StyleConstants.format_statistic(np.std(baseline_visions))} letters")
        
    with col2:
        st.metric("Mean Final Vision", f"{StyleConstants.format_vision(np.mean(final_visions))} letters")
        st.metric("Std Final Vision", f"{StyleConstants.format_statistic(np.std(final_visions))} letters")
        
    with col3:
        st.metric("Mean Vision Change", f"{StyleConstants.format_vision(np.mean(vision_changes))} letters")
        st.metric("Patients Improved", f"{StyleConstants.format_count(sum(1 for v in vision_changes if v > 0))}/{StyleConstants.format_count(len(vision_changes))}")

with tab2:
    st.header("Treatment Patterns")
    
    # Injection counts
    injection_counts = [p.injection_count for p in results.patient_histories.values()]
    visit_counts = [len(p.visit_history) for p in results.patient_histories.values()]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Injection count distribution
        mean_injections = np.mean(injection_counts)
        
        chart = (ChartBuilder('Distribution of Injection Counts')
                .with_labels(xlabel='Number of Injections', ylabel='Number of Patients')
                .with_count_axis('x')
                .with_count_axis('y')
                .plot(lambda ax, colors: 
                      ax.hist(injection_counts, bins=20, color=colors['warning'], 
                             alpha=0.7, edgecolor=colors['neutral'], linewidth=1.5))
                .add_reference_line(mean_injections, 
                                   f'Mean: {StyleConstants.format_statistic(mean_injections)}', 
                                   'vertical', 'primary')
                .build())
        st.pyplot(chart.figure)
        
    with col2:
        # Injections vs Visits scatter plot
        def plot_scatter(ax, colors):
            # Scatter points
            ax.scatter(visit_counts, injection_counts, 
                      alpha=0.6, color=colors['primary'],
                      s=50 if current_mode == 'presentation' else 30,
                      edgecolor=colors['neutral'], linewidth=0.5)
            
            # Add trend line
            z = np.polyfit(visit_counts, injection_counts, 1)
            p = np.poly1d(z)
            ax.plot(sorted(visit_counts), p(sorted(visit_counts)), 
                   color=colors['secondary'], linestyle='--', 
                   linewidth=2.5 if current_mode == 'presentation' else 1.5,
                   label=f'Trend (ratio={z[0]:.2f})')
        
        chart = (ChartBuilder('Injections vs Visits')
                .with_labels(xlabel='Total Visits', ylabel='Total Injections')
                .with_count_axis('x')
                .with_count_axis('y')
                .plot(plot_scatter)
                .with_legend(loc='lower right')
                .build())
        st.pyplot(chart.figure)
    
    # Treatment intervals
    st.subheader("Treatment Intervals")
    
    # Calculate intervals for a sample of patients
    all_intervals = []
    for patient in list(results.patient_histories.values())[:50]:  # Sample 50 patients
        visits = patient.visit_history
        for i in range(1, len(visits)):
            interval = (visits[i]['date'] - visits[i-1]['date']).days
            all_intervals.append(interval)
    
    if all_intervals:
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

with tab3:
    st.header("Patient Trajectories")
    
    # Select sample patients to plot
    n_sample = min(20, len(results.patient_histories))
    sample_patients = list(results.patient_histories.items())[:n_sample]
    
    # Vision trajectories
    def plot_trajectories(ax, colors):
        # Use different alpha and linewidth based on mode
        alpha = 0.6 if current_mode == 'presentation' else 0.4
        lw = 2 if current_mode == 'presentation' else 1
        
        for i, (pid, patient) in enumerate(sample_patients):
            if patient.visit_history:
                dates = [v['date'] for v in patient.visit_history]
                visions = [v['vision'] for v in patient.visit_history]
                
                # Calculate days from start
                start_date = dates[0]
                days = [(d - start_date).days for d in dates]
                
                # Use a color cycle for better visibility in presentation mode
                if current_mode == 'presentation':
                    color = plt.cm.tab10(i % 10)
                else:
                    color = colors['primary']
                
                ax.plot(days, visions, alpha=alpha, linewidth=lw, color=color)
    
    # Calculate max duration for time axis
    max_days = max([max([(v['date'] - patient.visit_history[0]['date']).days 
                        for v in patient.visit_history] or [0]) 
                   for _, patient in sample_patients])
    
    chart = (ChartBuilder(f'Vision Trajectories (first {n_sample} patients)')
            .with_labels(xlabel='Days from First Visit', ylabel='Vision (ETDRS letters)')
            .with_time_axis('x', duration_days=max_days, preferred_unit='days')
            .with_vision_axis('y')
            .plot(plot_trajectories)
            .build())
    st.pyplot(chart.figure)
    
    # Disease state progression
    st.subheader("Disease State Progression")
    
    # Count states over time
    state_counts_over_time = {}
    
    for patient in results.patient_histories.values():
        for visit in patient.visit_history:
            month = int((visit['date'] - patient.visit_history[0]['date']).days / 30.44)
            if month not in state_counts_over_time:
                state_counts_over_time[month] = {'NAIVE': 0, 'STABLE': 0, 'ACTIVE': 0, 'HIGHLY_ACTIVE': 0}
            state_counts_over_time[month][visit['disease_state'].name] += 1
    
    # Create stacked area chart
    months = sorted(state_counts_over_time.keys())
    states = ['NAIVE', 'STABLE', 'ACTIVE', 'HIGHLY_ACTIVE']
    state_data = {state: [state_counts_over_time.get(m, {}).get(state, 0) for m in months] for state in states}
    
    def plot_state_progression(ax, colors):
        # Define state colors
        state_colors = {
            'NAIVE': '#3498DB',     # Bright blue
            'STABLE': '#27AE60',    # Clear green
            'ACTIVE': '#F39C12',    # Strong orange
            'HIGHLY_ACTIVE': '#E74C3C'  # Vivid red
        }
        
        # Adjust alpha based on mode
        alpha = 0.8 if current_mode == 'presentation' else 0.6
        
        ax.stackplot(months, 
                     state_data['NAIVE'], 
                     state_data['STABLE'], 
                     state_data['ACTIVE'], 
                     state_data['HIGHLY_ACTIVE'],
                     labels=states,
                     colors=[state_colors[s] for s in states],
                     alpha=alpha)
    
    # Calculate max duration for time axis
    max_months = max(months) if months else 12
    
    chart = (ChartBuilder('Disease State Distribution Over Time')
            .with_labels(xlabel='Months from Start', ylabel='Number of Patients')
            .with_time_axis('x', duration_days=max_months * 30.44, preferred_unit='months')
            .with_count_axis('y')
            .plot(plot_state_progression)
            .with_legend(loc='upper right', ncol=2)
            .build())
    st.pyplot(chart.figure)

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