#!/usr/bin/env python3
"""
Treatment Pattern Visualizations - Based on treatment data alone.

This visualization uses ONLY information available in real-world treatment data:
- Visit dates/times
- Treatment intervals
- Gaps in treatment
- Injection given (yes/no)

NO disease state information is used, making it directly comparable to real-world data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time

# Set pandas option to avoid FutureWarning about downcasting
pd.set_option('future.no_silent_downcasting', True)

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.results.factory import ResultsFactory


# Color scheme for treatment-based states
TREATMENT_STATE_COLORS = {
    # Treatment intensity states (based on intervals alone)
    "Initial Treatment": "#e6f2ff",
    "Intensive (Monthly)": "#4a90e2",
    "Regular (6-8 weeks)": "#7fba00", 
    "Extended (12+ weeks)": "#5c8a00",
    "Maximum Extension (16 weeks)": "#2d5016",
    
    # Gap-based states (inferred from treatment patterns)
    "Treatment Gap (3-6 months)": "#ffd700",
    "Extended Gap (6-12 months)": "#ff9500",
    "Long Gap (12+ months)": "#ff6347",
    
    # Discontinuation (inferred from no further visits)
    "No Further Visits": "#999999",
    
    # Special patterns
    "Restarted After Gap": "#ff1493",
    "Irregular Pattern": "#dda0dd"
}


def get_available_simulations():
    """Get list of available simulation results."""
    results_dir = Path(__file__).parent.parent / "simulation_results"
    simulations = []
    
    if results_dir.exists():
        for sim_dir in sorted(results_dir.iterdir(), reverse=True):
            if sim_dir.is_dir() and sim_dir.name.startswith("sim_"):
                metadata_file = sim_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    duration_years = metadata.get('duration_years', 0)
                    duration_months = int(duration_years * 12) if duration_years else metadata.get('simulation_months', 0)
                    
                    simulations.append({
                        'id': sim_dir.name,
                        'date': metadata.get('timestamp', metadata.get('simulation_date', 'Unknown')),
                        'patients': metadata.get('n_patients', 0),
                        'duration': duration_months,
                        'path': sim_dir
                    })
    
    return simulations


def extract_treatment_patterns_vectorized(results):
    """
    Extract patient transitions based ONLY on treatment patterns.
    
    This uses only information available in real-world data:
    - Visit timing
    - Treatment intervals
    - Gaps in treatment
    
    Returns: (transitions_df, visits_df_with_intervals)
    """
    DAYS_PER_MONTH = 365.25 / 12
    
    if hasattr(results, 'get_visits_df'):
        st.info("Extracting treatment patterns from visit data...")
        start_time = time.time()
        
        # Get all visits as DataFrame
        visits_df = results.get_visits_df()
        
        # Sort by patient and time
        visits_df = visits_df.sort_values(['patient_id', 'time_days'])
        
        # Add visit number for each patient
        visits_df['visit_num'] = visits_df.groupby('patient_id').cumcount()
        
        # Calculate intervals
        visits_df['prev_time_days'] = visits_df.groupby('patient_id')['time_days'].shift(1)
        visits_df['interval_days'] = visits_df['time_days'] - visits_df['prev_time_days']
        
        # Determine treatment state based on intervals alone
        visits_df['treatment_state'] = determine_treatment_state_vectorized(visits_df)
        
        # Create previous state column
        visits_df['prev_treatment_state'] = visits_df.groupby('patient_id')['treatment_state'].shift(1)
        
        # First visit handling
        first_visits = visits_df['visit_num'] == 0
        visits_df.loc[first_visits, 'prev_treatment_state'] = 'Pre-Treatment'
        visits_df.loc[first_visits, 'prev_time_days'] = 0
        
        # Filter to only state changes
        state_changes = visits_df[visits_df['treatment_state'] != visits_df['prev_treatment_state']].copy()
        
        # Create transitions DataFrame
        transitions_df = pd.DataFrame({
            'patient_id': state_changes['patient_id'],
            'from_state': state_changes['prev_treatment_state'],
            'to_state': state_changes['treatment_state'],
            'from_time_days': state_changes['prev_time_days'],
            'to_time_days': state_changes['time_days'],
            'from_time': state_changes['prev_time_days'] / DAYS_PER_MONTH,
            'to_time': state_changes['time_days'] / DAYS_PER_MONTH,
            'duration_days': state_changes['time_days'] - state_changes['prev_time_days'],
            'duration': (state_changes['time_days'] - state_changes['prev_time_days']) / DAYS_PER_MONTH,
            'interval_days': state_changes['interval_days']
        })
        
        # Add final state transitions
        last_visits = visits_df.groupby('patient_id').last().reset_index()
        
        # Determine if patients have stopped treatment (no further visits)
        # In real data, we'd define this as no visit for > 6 months from simulation end
        sim_end_days = visits_df['time_days'].max()
        last_visits['time_since_last'] = sim_end_days - last_visits['time_days']
        
        # Create final transitions for patients who appear to have stopped
        stopped_mask = last_visits['time_since_last'] > 180  # 6+ months
        stopped_patients = last_visits[stopped_mask]
        
        if len(stopped_patients) > 0:
            final_transitions = pd.DataFrame({
                'patient_id': stopped_patients['patient_id'],
                'from_state': stopped_patients['treatment_state'],
                'to_state': 'No Further Visits',
                'from_time_days': stopped_patients['time_days'],
                'to_time_days': stopped_patients['time_days'],
                'from_time': stopped_patients['time_days'] / DAYS_PER_MONTH,
                'to_time': stopped_patients['time_days'] / DAYS_PER_MONTH,
                'duration_days': 0,
                'duration': 0,
                'interval_days': 0
            })
            
            transitions_df = pd.concat([transitions_df, final_transitions], ignore_index=True)
        
        elapsed = time.time() - start_time
        st.success(f"Extracted {len(transitions_df)} treatment pattern transitions in {elapsed:.1f} seconds")
        
        return transitions_df, visits_df
    else:
        st.error("This visualization requires visit data")
        return pd.DataFrame(), pd.DataFrame()


def determine_treatment_state_vectorized(visits_df):
    """
    Determine treatment state based ONLY on visit intervals.
    
    This mirrors what we can infer from real-world treatment data.
    """
    states = pd.Series('Initial Treatment', index=visits_df.index)
    
    # For visits after the first one, categorize by interval
    has_interval = visits_df['interval_days'].notna()
    
    # Intensive treatment (monthly - up to 5 weeks)
    intensive_mask = has_interval & (visits_df['interval_days'] <= 35)
    states[intensive_mask] = 'Intensive (Monthly)'
    
    # Regular treatment (6-8 weeks)
    regular_mask = has_interval & (visits_df['interval_days'] > 35) & (visits_df['interval_days'] <= 63)
    states[regular_mask] = 'Regular (6-8 weeks)'
    
    # Extended treatment (12-15 weeks)
    extended_mask = has_interval & (visits_df['interval_days'] > 63) & (visits_df['interval_days'] < 112)
    states[extended_mask] = 'Extended (12+ weeks)'
    
    # Maximum extension (16 weeks)
    max_mask = has_interval & (visits_df['interval_days'] >= 112) & (visits_df['interval_days'] <= 119)
    states[max_mask] = 'Maximum Extension (16 weeks)'
    
    # Treatment gaps
    gap_3_6_mask = has_interval & (visits_df['interval_days'] > 119) & (visits_df['interval_days'] <= 180)
    states[gap_3_6_mask] = 'Treatment Gap (3-6 months)'
    
    gap_6_12_mask = has_interval & (visits_df['interval_days'] > 180) & (visits_df['interval_days'] <= 365)
    states[gap_6_12_mask] = 'Extended Gap (6-12 months)'
    
    gap_12plus_mask = has_interval & (visits_df['interval_days'] > 365)
    states[gap_12plus_mask] = 'Long Gap (12+ months)'
    
    # Mark visits after long gaps as restarted - FULLY VECTORIZED
    # Identify visits that follow a long gap
    visits_df['had_long_gap'] = visits_df['interval_days'] > 180
    
    # Within each patient, mark visits that come after a long gap
    # Use shift to look at previous visit's gap status
    # Create a boolean column explicitly to avoid downcasting warnings
    visits_df['after_gap'] = visits_df.groupby('patient_id')['had_long_gap'].shift(1)
    visits_df['after_gap'] = visits_df['after_gap'].fillna(False)
    visits_df['after_gap'] = visits_df['after_gap'].astype('bool')
    
    # Create restart groups - increment when we see a new gap
    visits_df['gap_group'] = visits_df.groupby('patient_id')['had_long_gap'].cumsum()
    
    # Count visits within each gap group for each patient
    visits_df['visits_in_gap_group'] = visits_df.groupby(['patient_id', 'gap_group']).cumcount()
    
    # Mark as restarted if:
    # 1. We're after a gap (gap_group > 0)
    # 2. We're in the first 3 visits of the new group (visits_in_gap_group < 3) 
    # 3. The interval is reasonable (not another gap)
    restart_mask = (
        (visits_df['gap_group'] > 0) & 
        (visits_df['visits_in_gap_group'] < 3) & 
        (visits_df['interval_days'] <= 63) &
        has_interval
    )
    
    states[restart_mask] = 'Restarted After Gap'
    
    return states


def create_treatment_pattern_sankey(transitions_df):
    """Create Sankey diagram of treatment patterns."""
    # Aggregate transitions
    flow_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
    
    # Filter out small flows
    min_flow_size = max(1, len(transitions_df) * 0.001)
    flow_counts = flow_counts[flow_counts['count'] >= min_flow_size]
    
    # Create nodes
    nodes = []
    node_map = {}
    
    # Define preferred order for nodes
    state_order = [
        'Pre-Treatment',
        'Initial Treatment',
        'Intensive (Monthly)',
        'Regular (6-8 weeks)',
        'Extended (12+ weeks)',
        'Maximum Extension (16 weeks)',
        'Treatment Gap (3-6 months)',
        'Extended Gap (6-12 months)',
        'Long Gap (12+ months)',
        'Restarted After Gap',
        'Irregular Pattern',
        'No Further Visits'
    ]
    
    # Add nodes in preferred order if they exist
    for state in state_order:
        if state in flow_counts['from_state'].values or state in flow_counts['to_state'].values:
            node_map[state] = len(nodes)
            nodes.append({
                'label': state,
                'color': TREATMENT_STATE_COLORS.get(state, "#cccccc")
            })
    
    # Add any missing states
    for _, row in flow_counts.iterrows():
        for state in [row['from_state'], row['to_state']]:
            if state not in node_map:
                node_map[state] = len(nodes)
                nodes.append({
                    'label': state,
                    'color': TREATMENT_STATE_COLORS.get(state, "#cccccc")
                })
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=25,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=[n['label'] for n in nodes],
            color=[n['color'] for n in nodes]
        ),
        link=dict(
            source=[node_map[row['from_state']] for _, row in flow_counts.iterrows()],
            target=[node_map[row['to_state']] for _, row in flow_counts.iterrows()],
            value=[row['count'] for _, row in flow_counts.iterrows()],
            color="rgba(100, 100, 100, 0.2)"
        ),
        textfont=dict(size=10, color='black', family='Arial')
    )])
    
    fig.update_layout(
        title=dict(
            text="Treatment Pattern Transitions (Based on Visit Intervals Only)",
            font=dict(size=16)
        ),
        font=dict(size=12),
        height=800,
        margin=dict(l=20, r=20, t=60, b=20),
        annotations=[{
            'text': 'This visualization uses ONLY treatment timing data - no disease state information',
            'showarrow': False,
            'xref': 'paper', 'yref': 'paper',
            'x': 0.5, 'y': -0.05,
            'xanchor': 'center', 'yanchor': 'top',
            'font': {'size': 11, 'color': 'gray'}
        }]
    )
    
    return fig


def create_interval_distribution_chart(transitions_df):
    """Create distribution of treatment intervals."""
    # Get intervals from transitions
    interval_data = transitions_df[transitions_df['interval_days'] > 0]['interval_days']
    
    # Create histogram
    fig = go.Figure()
    
    # Define bins for common intervals
    bins = [0, 35, 63, 84, 112, 180, 365, 1000]
    labels = ['Monthly', '6-8 weeks', '9-11 weeks', '12-16 weeks', '3-6 months', '6-12 months', '12+ months']
    
    hist, bin_edges = np.histogram(interval_data, bins=bins)
    
    # Create bar chart
    fig.add_trace(go.Bar(
        x=labels,
        y=hist,
        marker_color=['#4a90e2', '#7fba00', '#5c8a00', '#2d5016', '#ffd700', '#ff9500', '#ff6347'],
        text=hist,
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Distribution of Treatment Intervals",
        xaxis_title="Interval Category",
        yaxis_title="Number of Visits",
        height=400,
        showlegend=False
    )
    
    return fig


def create_gap_analysis_chart_tufte(visits_df):
    """Analyze treatment gaps by patient."""
    # Get all unique patients
    all_patients = visits_df['patient_id'].unique()
    
    # Filter to only rows with valid intervals (exclude first visits)
    valid_intervals = visits_df[visits_df['interval_days'].notna()]
    
    # Calculate max gap per patient (only for those with intervals)
    if len(valid_intervals) > 0:
        patient_gaps = valid_intervals.groupby('patient_id')['interval_days'].agg(['max', 'mean', 'count']).reset_index()
        patient_gaps.columns = ['patient_id', 'max_gap_days', 'mean_interval_days', 'interval_count']
        
        # Debug: Show some statistics (commented out for clean display)
        # st.write(f"Debug: Found {len(patient_gaps)} patients with intervals")
        # st.write(f"Debug: Max gap range: {patient_gaps['max_gap_days'].min():.0f} - {patient_gaps['max_gap_days'].max():.0f} days")
        
        # Add patients with only one visit (no intervals) as having no gaps
        patients_with_intervals = set(patient_gaps['patient_id'])
        patients_without_intervals = set(all_patients) - patients_with_intervals
        
        if len(patients_without_intervals) > 0:
            no_interval_df = pd.DataFrame({
                'patient_id': list(patients_without_intervals),
                'max_gap_days': 0,  # No intervals means no gaps
                'mean_interval_days': 0,
                'interval_count': 0
            })
            patient_gaps = pd.concat([patient_gaps, no_interval_df], ignore_index=True)
            # st.write(f"Debug: Added {len(patients_without_intervals)} patients with single visits")
    else:
        # If no intervals at all, all patients have single visits
        patient_gaps = pd.DataFrame({
            'patient_id': all_patients,
            'max_gap_days': 0,
            'mean_interval_days': 0,
            'interval_count': 0
        })
    
    # Categorize patients by their maximum gap - using more granular thresholds
    # that match the actual data distribution
    gap_categories = pd.cut(
        patient_gaps['max_gap_days'],
        bins=[0, 42, 63, 84, 112, float('inf')],
        labels=[
            'Very frequent (≤6 weeks)', 
            'Frequent (6-9 weeks)', 
            'Regular (9-12 weeks)', 
            'Extended (12-16 weeks)',
            'Gaps (>16 weeks)'
        ],
        include_lowest=True  # Include 0 in the first bin
    )
    
    gap_summary = gap_categories.value_counts()
    
    # Sort categories for horizontal bar chart
    gap_summary = gap_summary.sort_values(ascending=True)
    
    # Create a clean horizontal bar chart (Tufte-style)
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(go.Bar(
        y=gap_summary.index,
        x=gap_summary.values,
        orientation='h',
        text=[f'{val:,} ({val/len(patient_gaps)*100:.1f}%)' for val in gap_summary.values],
        textposition='outside',
        marker_color=['#4a90e2' if '≤6 weeks' in str(idx) else
                     '#7fba00' if '6-9 weeks' in str(idx) else
                     '#5c8a00' if '9-12 weeks' in str(idx) else
                     '#ffd700' if '12-16 weeks' in str(idx) else
                     '#ff6347' for idx in gap_summary.index],
        showlegend=False
    ))
    
    # Tufte-style clean layout
    fig.update_layout(
        title=None,  # Title in text above instead
        xaxis=dict(
            title="Number of Patients",
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks='',
        ),
        yaxis=dict(
            title=None,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks='',
        ),
        height=300,
        margin=dict(l=150, r=100, t=20, b=40),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Add a subtle reference line at 25%, 50%, 75%
    for pct in [0.25, 0.5, 0.75]:
        fig.add_vline(
            x=len(patient_gaps) * pct,
            line_dash="dot",
            line_color="lightgray",
            opacity=0.5
        )
    
    return fig


def main():
    """Main Streamlit app."""
    st.set_page_config(page_title="Treatment Pattern Analysis", layout="wide")
    
    st.title("💉 Treatment Pattern Analysis")
    st.markdown("""
    ### Analyzing Patient Journeys Using Only Treatment Data
    
    This visualization uses **ONLY** information available in real-world treatment records:
    - Visit dates and intervals
    - Treatment gaps
    - Pattern changes over time
    
    **No disease state information is used**, making this directly comparable to real-world data analysis.
    """)
    
    # Add clear distinction box
    st.info("""
    🔍 **Key Difference from Other Visualizations**:
    - ✅ Uses only treatment timing data
    - ❌ Does NOT use disease activity states
    - ✅ Can be applied to real-world data
    - ✅ Shows patterns inferable from visit schedules alone
    """)
    
    # Sidebar
    with st.sidebar:
        st.header("Select Simulation")
        
        simulations = get_available_simulations()
        
        if not simulations:
            st.error("No simulation results found!")
            st.stop()
        
        sim_options = [f"{sim['id']} ({sim['patients']} patients, {sim['duration']}m)" 
                      for sim in simulations]
        selected_idx = st.selectbox(
            "Choose simulation",
            range(len(sim_options)),
            format_func=lambda x: sim_options[x]
        )
        
        selected_sim = simulations[selected_idx]
        
        st.subheader("Simulation Details")
        st.metric("Patients", f"{selected_sim['patients']:,}")
        st.metric("Duration", f"{selected_sim['duration']} months")
        
        # Load simulation data
        try:
            results = ResultsFactory.load_results(selected_sim['path'])
            
            # Extract transitions and visits with intervals
            transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
            
            if len(transitions_df) == 0:
                st.error("No transitions found")
                st.stop()
                
            st.success(f"Analyzed {len(transitions_df):,} treatment patterns")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Treatment Pattern Flow",
        "📈 Interval Distribution",
        "🔍 Gap Analysis",
        "📋 Pattern Statistics"
    ])
    
    with tab1:
        st.subheader("Patient Flow Through Treatment Patterns")
        st.markdown("""
        This Sankey diagram shows how patients transition between different treatment patterns
        based solely on the timing of their visits. Width indicates number of patients.
        """)
        
        fig1 = create_treatment_pattern_sankey(transitions_df)
        st.plotly_chart(fig1, use_container_width=True)
        
        # Add interpretation guide
        with st.expander("📖 How to interpret this diagram"):
            st.markdown("""
            **Treatment States** (inferred from visit intervals):
            - **Initial Treatment**: First visits in treatment sequence
            - **Intensive (Monthly)**: Visits ≤35 days apart
            - **Regular (6-8 weeks)**: Visits 36-63 days apart
            - **Extended (12+ weeks)**: Visits 64-111 days apart
            - **Maximum Extension (16 weeks)**: Visits 112-119 days apart
            
            **Gap States** (potential treatment interruptions):
            - **Treatment Gap (3-6 months)**: 120-180 days between visits
            - **Extended Gap (6-12 months)**: 181-365 days between visits
            - **Long Gap (12+ months)**: >365 days between visits
            
            **Special Patterns**:
            - **Restarted After Gap**: Regular treatment resuming after a gap >6 months
            - **No Further Visits**: No visits in last 6 months of observation period
            """)
    
    with tab2:
        st.subheader("Distribution of Treatment Intervals")
        st.markdown("How frequently are patients being treated?")
        
        fig2 = create_interval_distribution_chart(transitions_df)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            median_interval = transitions_df['interval_days'].median()
            st.metric("Median Interval", f"{median_interval:.0f} days")
        with col2:
            mean_interval = transitions_df['interval_days'].mean()
            st.metric("Mean Interval", f"{mean_interval:.0f} days")
        with col3:
            pct_extended = (transitions_df['interval_days'] >= 84).mean() * 100
            st.metric("% Extended (≥12 weeks)", f"{pct_extended:.1f}%")
    
    with tab3:
        st.subheader("Maximum Treatment Intervals by Patient")
        
        # Remove debug output for cleaner display
        fig3 = create_gap_analysis_chart_tufte(visits_df)
        st.plotly_chart(fig3, use_container_width=True)
        
        # Add context in Tufte style
        st.markdown("*Each patient's longest interval between visits*")
        
        # Additional gap statistics
        st.markdown("### Gap Patterns")
        
        # Find patients with multiple gaps
        gap_visits = visits_df[visits_df['interval_days'] > 180]
        patients_with_gaps = gap_visits['patient_id'].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Patients with any gap >6 months", len(patients_with_gaps))
            st.metric("Patients with multiple gaps", (patients_with_gaps > 1).sum())
        
        with col2:
            if len(gap_visits) > 0:
                st.metric("Average gap duration", f"{gap_visits['interval_days'].mean():.0f} days")
                st.metric("Longest gap", f"{gap_visits['interval_days'].max():.0f} days")
    
    with tab4:
        st.subheader("Treatment Pattern Statistics")
        
        # Most common transitions
        st.markdown("### Most Common Treatment Pattern Changes")
        top_transitions = transitions_df.groupby(['from_state', 'to_state']).size()\
            .reset_index(name='count').sort_values('count', ascending=False).head(15)
        
        # Format the display
        top_transitions['Transition'] = top_transitions['from_state'] + ' → ' + top_transitions['to_state']
        top_transitions['Percentage'] = (top_transitions['count'] / len(transitions_df) * 100).round(1)
        
        st.dataframe(
            top_transitions[['Transition', 'count', 'Percentage']].rename(columns={'count': 'Count', 'Percentage': '% of Total'}),
            use_container_width=True,
            hide_index=True
        )
        
        # Time in each pattern
        st.markdown("### Average Duration in Each Treatment Pattern")
        pattern_durations = transitions_df.groupby('from_state').agg({
            'duration': ['mean', 'median', 'std'],
            'patient_id': 'count'
        }).round(1)
        
        pattern_durations.columns = ['Mean (months)', 'Median (months)', 'Std Dev', 'N Transitions']
        pattern_durations = pattern_durations.sort_values('Mean (months)', ascending=False)
        
        st.dataframe(pattern_durations, use_container_width=True)


if __name__ == "__main__":
    main()