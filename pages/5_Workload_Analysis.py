"""
Workload and Economic Analysis - Analyze resource usage and costs from simulations.

This page provides detailed analysis of:
- Daily workload patterns
- Resource utilization
- Cost breakdown
- Staffing requirements
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path

from ape.utils.state_helpers import get_active_simulation
from ape.utils.startup_redirect import handle_page_startup
from ape.utils.carbon_button_helpers import ape_button
from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
from ape.components.ui.workflow_indicator import workflow_progress_indicator

st.set_page_config(
    page_title="Workload & Economic Analysis",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Check for startup redirect
handle_page_startup("workload_analysis")

# Show workflow progress with carbon buttons navigation
has_results = st.session_state.get('current_sim_id') is not None
workflow_progress_indicator("workload", has_results=has_results)

# Get active simulation
sim_data = get_active_simulation()

if not sim_data:
    st.error("No active simulation found. Please run a simulation first.")
    st.stop()

# Check if simulation has resource tracking
has_resource_tracking = False
resource_tracker = None

# Try to get resource tracker from results
if sim_data.get('results') and hasattr(sim_data['results'], 'resource_tracker'):
    resource_tracker = sim_data['results'].resource_tracker
    has_resource_tracking = resource_tracker is not None
elif sim_data.get('results') and hasattr(sim_data['results'], '_raw_results'):
    raw_results = sim_data['results']._raw_results
    if hasattr(raw_results, 'resource_tracker'):
        resource_tracker = raw_results.resource_tracker
        has_resource_tracking = resource_tracker is not None

if not has_resource_tracking or resource_tracker is None:
    st.warning("This simulation was run without resource tracking.")
    st.info("To enable resource tracking:")
    st.markdown("""
    1. Go to the **Simulation** page
    2. Check the **Enable Resource Tracking** checkbox
    3. Run a new simulation
    
    Note: Resource tracking is only available for time-based protocols.
    """)
    
    # Show basic simulation info
    st.subheader("Simulation Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Protocol", sim_data['protocol']['name'])
    with col2:
        st.metric("Patients", f"{sim_data['parameters']['n_patients']:,}")
    with col3:
        st.metric("Duration", f"{sim_data['parameters']['duration_years']} years")
    
    # Check if this is a time-based protocol
    if sim_data.get('protocol', {}).get('type') != 'time_based':
        st.warning("Resource tracking is only available for time-based protocols.")
    
    st.stop()

# Main title
st.title("Workload & Economic Analysis")

# Show simulation context
with st.expander("Simulation Details", expanded=False):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Protocol", sim_data['protocol']['name'])
    with col2:
        st.metric("Patients", f"{sim_data['parameters']['n_patients']:,}")
    with col3:
        st.metric("Duration", f"{sim_data['parameters']['duration_years']} years")
    with col4:
        st.metric("Engine", sim_data['parameters']['engine'].upper())

# Get workload summary
workload_summary = resource_tracker.get_workload_summary()

# Overview metrics
st.header("Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Visits", f"{workload_summary['total_visits']:,}")
    
with col2:
    total_costs = resource_tracker.get_total_costs()
    st.metric("Total Cost", f"£{total_costs['total']:,.0f}")
    
with col3:
    cost_per_patient = total_costs['total'] / sim_data['parameters']['n_patients']
    st.metric("Cost per Patient", f"£{cost_per_patient:,.0f}")
    
with col4:
    if workload_summary['total_visits'] > 0:
        cost_per_visit = total_costs['total'] / workload_summary['total_visits']
        st.metric("Cost per Visit", f"£{cost_per_visit:.0f}")
    else:
        st.metric("Cost per Visit", "N/A")

# Section 1: Daily Workload Pattern
st.header("Daily Workload Pattern")
st.write("Actual daily resource usage without smoothing")

# Get daily workload data
all_dates = resource_tracker.get_all_dates_with_visits()
if all_dates:
    # Create daily workload dataframe
    daily_data = []
    for date in all_dates:
        daily_usage = resource_tracker.daily_usage[date]
        for role, count in daily_usage.items():
            daily_data.append({
                'date': date,
                'role': role,
                'count': count,
                'sessions_needed': resource_tracker.calculate_sessions_needed(date, role)
            })
    
    daily_df = pd.DataFrame(daily_data)
    
    # Create role selector
    roles = sorted(daily_df['role'].unique())
    selected_role = st.selectbox("Select Role", ["All Roles"] + roles)
    
    # Filter data
    if selected_role == "All Roles":
        # Aggregate across all roles
        plot_df = daily_df.groupby('date').agg({
            'count': 'sum',
            'sessions_needed': 'sum'
        }).reset_index()
        y_label = "Total Procedures"
    else:
        plot_df = daily_df[daily_df['role'] == selected_role]
        y_label = f"{selected_role} Procedures"
    
    # Create workload chart
    fig = go.Figure()
    
    # Add daily count bars
    fig.add_trace(go.Bar(
        x=plot_df['date'],
        y=plot_df['count'],
        name='Daily Count',
        marker_color=COLORS['primary'],  # Use primary color for workload data
        opacity=0.8
    ))
    
    # Tufte-style layout
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=40, r=20, t=30, b=40),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor='gray',
            title="Date"
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor=f'rgba(128,128,128,{ALPHAS["low"]})',
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='gray',
            title=y_label
        ),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show peak demand info
    if selected_role != "All Roles":
        role_data = resource_tracker.roles[selected_role]
        capacity_per_session = role_data['capacity_per_session']
        peak_demand = workload_summary['peak_daily_demand'][selected_role]
        peak_sessions = peak_demand / capacity_per_session
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Peak Daily Demand", f"{peak_demand} procedures")
        with col2:
            st.metric("Sessions Needed", f"{peak_sessions:.1f}")
        with col3:
            avg_demand = workload_summary['average_daily_demand'][selected_role]
            st.metric("Average Daily Demand", f"{avg_demand:.1f} procedures")

# Section 2: Cost Breakdown
st.header("Cost Breakdown")

costs = resource_tracker.get_total_costs()
cost_categories = []
cost_values = []

# Organize costs for display
if 'drug' in costs:
    cost_categories.append('Drug Costs')
    cost_values.append(costs['drug'])
if 'injection_procedure' in costs:
    cost_categories.append('Injection Procedures')
    cost_values.append(costs['injection_procedure'])
if 'consultation' in costs:
    cost_categories.append('Decision Consultations')
    cost_values.append(costs['consultation'])
if 'oct_scan' in costs:
    cost_categories.append('OCT Scans')
    cost_values.append(costs['oct_scan'])

# Create cost breakdown chart
if cost_categories:
    fig = go.Figure(data=[
        go.Bar(
            x=cost_categories,
            y=cost_values,
            text=[f"£{v:,.0f}" for v in cost_values],
            textposition='auto',
            marker_color=COLORS['primary']
        )
    ])
    
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=40, r=20, t=30, b=40),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor='gray'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor=f'rgba(128,128,128,{ALPHAS["low"]})',
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='gray',
            title="Cost (£)"
        ),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Section 3: Resource Utilization
st.header("Resource Utilization")

# Create utilization summary
utilization_data = []
sessions_per_day = resource_tracker.session_parameters['sessions_per_day']

for role, role_info in resource_tracker.roles.items():
    capacity_per_session = role_info['capacity_per_session']
    peak_demand = workload_summary['peak_daily_demand'].get(role, 0)
    avg_demand = workload_summary['average_daily_demand'].get(role, 0)
    total_sessions = workload_summary['total_sessions_needed'].get(role, 0)
    
    peak_sessions_needed = peak_demand / capacity_per_session if capacity_per_session > 0 else 0
    avg_sessions_needed = avg_demand / capacity_per_session if capacity_per_session > 0 else 0
    
    # Calculate utilization based on average demand
    max_daily_capacity = capacity_per_session * sessions_per_day
    utilization = (avg_demand / max_daily_capacity * 100) if max_daily_capacity > 0 else 0
    
    utilization_data.append({
        'Role': role,
        'Peak Daily Demand': peak_demand,
        'Average Daily Demand': f"{avg_demand:.1f}",
        'Peak Sessions Needed': f"{peak_sessions_needed:.1f}",
        'Average Sessions/Day': f"{avg_sessions_needed:.1f}",
        'Utilization %': f"{utilization:.0f}%",
        'Total Sessions': total_sessions
    })

utilization_df = pd.DataFrame(utilization_data)
st.dataframe(utilization_df, use_container_width=True, hide_index=True)

# Section 4: Bottleneck Analysis
bottlenecks = resource_tracker.identify_bottlenecks()
if bottlenecks:
    st.header("Bottleneck Analysis")
    st.warning(f"Found {len(bottlenecks)} days where capacity was exceeded")
    
    # Group bottlenecks by role
    bottleneck_summary = defaultdict(list)
    for b in bottlenecks:
        bottleneck_summary[b['role']].append(b)
    
    for role, role_bottlenecks in bottleneck_summary.items():
        st.subheader(f"{role} Bottlenecks")
        st.write(f"Days with capacity issues: {len(role_bottlenecks)}")
        
        # Show worst cases
        worst_cases = sorted(role_bottlenecks, key=lambda x: x['overflow'], reverse=True)[:5]
        for case in worst_cases:
            st.write(f"- {case['date'].strftime('%Y-%m-%d')}: Needed {case['sessions_needed']:.1f} sessions, had {case['sessions_available']}")

# Section 5: Staffing Requirements
st.header("Staffing Requirements")
st.write("Based on peak demand and standard working patterns")

staffing_data = []
for role, role_info in resource_tracker.roles.items():
    capacity_per_session = role_info['capacity_per_session']
    peak_demand = workload_summary['peak_daily_demand'].get(role, 0)
    avg_demand = workload_summary['average_daily_demand'].get(role, 0)
    
    peak_sessions = peak_demand / capacity_per_session if capacity_per_session > 0 else 0
    avg_sessions = avg_demand / capacity_per_session if capacity_per_session > 0 else 0
    
    # Assume 1 staff member can do 2 sessions per day
    staff_needed_peak = int(peak_sessions / 2) + (1 if peak_sessions % 2 > 0 else 0)
    staff_needed_avg = avg_sessions / 2
    
    staffing_data.append({
        'Role': role,
        'Average Sessions/Day': f"{avg_sessions:.1f}",
        'Peak Sessions': f"{peak_sessions:.1f}",
        'Staff Needed (Average)': f"{staff_needed_avg:.1f}",
        'Staff Needed (Peak)': staff_needed_peak
    })

staffing_df = pd.DataFrame(staffing_data)
st.dataframe(staffing_df, use_container_width=True, hide_index=True)

# Export functionality
st.header("Export Data")
col1, col2 = st.columns(2)

with col1:
    if ape_button("Export Workload Summary", key="export_workload", button_type="secondary"):
        # Create export data
        export_data = {
            'summary': workload_summary,
            'total_costs': resource_tracker.get_total_costs(),
            'bottlenecks': [
                {
                    'date': b['date'].isoformat(),
                    'role': b['role'],
                    'sessions_needed': b['sessions_needed'],
                    'overflow': b['overflow']
                }
                for b in bottlenecks
            ],
            'daily_usage': [
                {
                    'date': date.isoformat(),
                    'usage': dict(resource_tracker.daily_usage[date])
                }
                for date in all_dates
            ]
        }
        
        # Save to file
        export_path = sim_data['results'].data_path / "workload_analysis.json"
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        st.success(f"Exported to {export_path}")

with col2:
    if ape_button("Export Cost Details", key="export_costs", button_type="secondary"):
        # Create cost details for each visit
        visit_details = []
        for visit in resource_tracker.visits:
            visit_details.append({
                'date': visit['date'].isoformat(),
                'patient_id': visit['patient_id'],
                'visit_type': visit['visit_type'],
                'injection_given': visit['injection_given'],
                'oct_performed': visit['oct_performed'],
                'total_cost': sum(visit['costs'].values()),
                **visit['costs']
            })
        
        # Save to CSV
        visit_df = pd.DataFrame(visit_details)
        export_path = sim_data['results'].data_path / "visit_costs.csv"
        visit_df.to_csv(export_path, index=False)
        
        st.success(f"Exported to {export_path}")