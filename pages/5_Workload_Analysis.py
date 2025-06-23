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

# Show simulation context - always visible with smaller font
st.markdown("### Simulation Details")
st.markdown("""
<style>
    div[data-testid="stMetricValue"] {
        font-size: 0.9rem;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Protocol", sim_data['protocol']['name'])
with col2:
    st.metric("Patients", f"{sim_data['parameters']['n_patients']:,}")
with col3:
    st.metric("Duration", f"{sim_data['parameters']['duration_years']} years")
with col4:
    st.metric("Engine", sim_data['parameters']['engine'].upper())
with col5:
    # Add seed information if available
    seed = sim_data['parameters'].get('seed', 'Random')
    st.metric("Seed", seed if seed != 'Random' else 'Random')

# Helper function to safely call methods on resource_tracker
def safe_call_method(resource_tracker, method_name, default=None):
    """Safely call a method on resource_tracker, handling SimpleNamespace wrapper."""
    if hasattr(resource_tracker, method_name):
        return getattr(resource_tracker, method_name)()
    elif hasattr(resource_tracker, '__dict__'):
        # Try to get from dict if method not directly available
        rt_dict = resource_tracker.__dict__
        if method_name == 'get_total_costs':
            return rt_dict.get('total_costs', default or {'total': 0, 'drug': 0})
        elif method_name == 'get_workload_summary':
            return rt_dict.get('workload_summary', default or {})
    return default

# Get workload summary
workload_summary = safe_call_method(resource_tracker, 'get_workload_summary', {})

# Initialize drug cost variables early (needed for cost calculations)
# Get current drug costs from resource tracker (handle SimpleNamespace)
if hasattr(resource_tracker, '__dict__'):
    # SimpleNamespace wrapper
    rt_dict = resource_tracker.__dict__
    current_drug_costs = rt_dict.get('costs', {}).get('drugs', {})
    visits = rt_dict.get('visits', [])
else:
    # Direct ResourceTracker object
    current_drug_costs = resource_tracker.costs.get('drugs', {})
    visits = resource_tracker.visits

default_drug_cost = 816  # Default Aflibercept cost

# Find the primary drug used (usually the first one in the list)
if current_drug_costs:
    primary_drug = list(current_drug_costs.keys())[0]
    default_drug_cost = current_drug_costs[primary_drug].get('unit_cost', 816)

# Calculate total injections
total_injections = sum(1 for visit in visits if visit.get('injection_given', False))

# Get original costs (never changes)
original_costs = safe_call_method(resource_tracker, 'get_total_costs')

# Create tabs for better organization
tab1, tab2 = st.tabs(["Workload Analysis", "Cost Analysis"])

# Tab 1: Workload Analysis
with tab1:
    # Activity Summary
    st.header("Activity Summary")
    
    total_patients = sim_data['parameters']['n_patients']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Patients", f"{total_patients:,}")
    with col2:
        st.metric("Total Visits", f"{workload_summary['total_visits']:,}")
    with col3:
        visits_per_patient = workload_summary['total_visits'] / total_patients
        st.metric("Visits per Patient", f"{visits_per_patient:.1f}")
    
    # Daily Workload Pattern
    st.header("Daily Workload Pattern")
    st.write("Actual daily resource usage without smoothing")
    
    # Get daily workload data (handle SimpleNamespace)
    if hasattr(resource_tracker, 'get_all_dates_with_visits'):
        all_dates = resource_tracker.get_all_dates_with_visits()
    elif hasattr(resource_tracker, '__dict__'):
        rt_dict = resource_tracker.__dict__
        # Try to get all dates from daily_usage keys
        daily_usage = rt_dict.get('daily_usage', {})
        all_dates = sorted(daily_usage.keys()) if daily_usage else []
    else:
        all_dates = []
    
    if all_dates:
        # Create daily workload dataframe
        daily_data = []
        for date in all_dates:
            # Get daily usage (handle SimpleNamespace)
            if hasattr(resource_tracker, '__dict__'):
                rt_dict = resource_tracker.__dict__
                daily_usage_dict = rt_dict.get('daily_usage', {})
                daily_usage = daily_usage_dict.get(date, {})
            else:
                daily_usage = resource_tracker.daily_usage[date]
            for role, count in daily_usage.items():
                daily_data.append({
                    'date': date,
                    'role': role,
                    'count': count,
                    'sessions_needed': resource_tracker.calculate_sessions_needed(date, role) if hasattr(resource_tracker, 'calculate_sessions_needed') else 0
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
            # Get role data (handle SimpleNamespace)
            if hasattr(resource_tracker, '__dict__'):
                rt_dict = resource_tracker.__dict__
                roles = rt_dict.get('roles', {})
                role_data = roles.get(selected_role, {})
            else:
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
    
    # Resource Utilization
    st.header("Resource Utilization")
    
    # Create utilization summary
    utilization_data = []
    # Get session parameters (handle SimpleNamespace)
    if hasattr(resource_tracker, '__dict__'):
        rt_dict = resource_tracker.__dict__
        session_params = rt_dict.get('session_parameters', {})
        sessions_per_day = session_params.get('sessions_per_day', 2)
    else:
        sessions_per_day = resource_tracker.session_parameters['sessions_per_day']
    
    # Get roles (handle SimpleNamespace)
    if hasattr(resource_tracker, '__dict__'):
        rt_dict = resource_tracker.__dict__
        roles = rt_dict.get('roles', {})
    else:
        roles = resource_tracker.roles
    
    for role, role_info in roles.items():
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
    
    # Bottleneck Analysis
    # Identify bottlenecks (handle SimpleNamespace)
    if hasattr(resource_tracker, 'identify_bottlenecks'):
        bottlenecks = resource_tracker.identify_bottlenecks()
    else:
        bottlenecks = []
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
    
    # Staffing Requirements
    st.header("Staffing Requirements")
    st.write("Based on peak demand and standard working patterns")
    
    staffing_data = []
    # Get roles (handle SimpleNamespace)
    if hasattr(resource_tracker, '__dict__'):
        rt_dict = resource_tracker.__dict__
        roles = rt_dict.get('roles', {})
    else:
        roles = resource_tracker.roles
    
    for role, role_info in roles.items():
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

# Tab 2: Cost Analysis
with tab2:
    # Drug Cost Adjustment at the top
    st.header("Drug Cost Adjustment")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        new_drug_cost = st.slider(
            "Intravitreal Drug Cost per Dose (£)",
            min_value=50,
            max_value=1500,
            value=default_drug_cost,
            step=10,
            help="Adjust drug cost to see impact on total costs"
        )
        
        # Show cost difference
        cost_difference = new_drug_cost - default_drug_cost
        if cost_difference != 0:
            pct_change = (cost_difference / default_drug_cost) * 100
            if cost_difference > 0:
                st.caption(f"+£{cost_difference} (+{pct_change:.1f}%) from baseline")
            else:
                st.caption(f"-£{abs(cost_difference)} ({pct_change:.1f}%) from baseline")
    
    with col2:
        st.metric("Original Drug Cost", f"£{default_drug_cost}")
    
    with col3:
        st.metric("New Drug Cost", f"£{new_drug_cost}")
    
    # Calculate adjustments based on slider value
    drug_cost_adjustment = (new_drug_cost - default_drug_cost) * total_injections
    adjusted_costs = original_costs.copy()
    if cost_difference != 0:
        adjusted_costs['drug'] = original_costs.get('drug', 0) + drug_cost_adjustment
        adjusted_costs['total'] = original_costs['total'] + drug_cost_adjustment
    
    # Show impact if there's a change
    if cost_difference != 0:
        st.info(f"Impact: £{cost_difference:+.0f} per injection × {total_injections:,} injections = £{drug_cost_adjustment:+,.0f} total")
    
    st.divider()
    
    # Two columns layout for cost breakdown and metrics
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        # Cost Breakdown Chart
        st.subheader("Cost Breakdown")
        
        # Use adjusted costs for breakdown if drug price changed
        costs = adjusted_costs if cost_difference != 0 else original_costs
        cost_categories = []
        cost_values = []
        original_values = []  # For showing deltas
        
        # Organize costs for display
        if 'drug' in costs:
            cost_categories.append('Drug Costs')
            cost_values.append(costs['drug'])
            original_values.append(original_costs.get('drug', 0))
        if 'injection_procedure' in costs:
            cost_categories.append('Injection Procedures')
            cost_values.append(costs['injection_procedure'])
            original_values.append(original_costs.get('injection_procedure', 0))
        if 'consultation' in costs:
            cost_categories.append('Decision Consultations')
            cost_values.append(costs['consultation'])
            original_values.append(original_costs.get('consultation', 0))
        if 'oct_scan' in costs:
            cost_categories.append('OCT Scans')
            cost_values.append(costs['oct_scan'])
            original_values.append(original_costs.get('oct_scan', 0))
        
        # Create cost breakdown chart
        if cost_categories:
            # If drug costs changed, show both original and adjusted
            if cost_difference != 0:
                fig = go.Figure()
                
                # Original costs (lighter color)
                fig.add_trace(go.Bar(
                    name='Original',
                    x=cost_categories,
                    y=original_values,
                    text=[f"£{v:,.0f}" for v in original_values],
                    textposition='auto',
                    marker_color=COLORS['primary'],
                    opacity=0.5
                ))
                
                # Adjusted costs
                fig.add_trace(go.Bar(
                    name='Adjusted',
                    x=cost_categories,
                    y=cost_values,
                    text=[f"£{v:,.0f}" for v in cost_values],
                    textposition='auto',
                    marker_color=COLORS['primary']
                ))
                
                fig.update_layout(barmode='group')
            else:
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
                showlegend=cost_difference != 0,
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
    
    with col_right:
        # Cost Metrics
        st.subheader("Cost Metrics")
        
        # Use adjusted costs if drug price has changed
        total_costs = adjusted_costs if cost_difference != 0 else original_costs
        
        # Basic metrics
        st.metric("Total Cost", f"£{total_costs['total']:,.0f}")
        if cost_difference != 0:
            color = "green" if drug_cost_adjustment < 0 else "red"
            st.markdown(f"<p style='color: {color}; margin-top: -15px;'>£{drug_cost_adjustment:+,.0f}</p>", unsafe_allow_html=True)
        
        cost_per_patient = total_costs['total'] / total_patients
        st.metric("Cost per Patient", f"£{cost_per_patient:,.0f}")
        if cost_difference != 0:
            original_cpp = original_costs['total'] / total_patients
            cpp_diff = cost_per_patient - original_cpp
            color = "green" if cpp_diff < 0 else "red"
            st.markdown(f"<p style='color: {color}; margin-top: -15px;'>£{cpp_diff:+,.0f}</p>", unsafe_allow_html=True)
        
        if workload_summary['total_visits'] > 0:
            cost_per_visit = total_costs['total'] / workload_summary['total_visits']
            st.metric("Cost per Visit", f"£{cost_per_visit:.0f}")
            if cost_difference != 0:
                original_cpv = original_costs['total'] / workload_summary['total_visits']
                cpv_diff = cost_per_visit - original_cpv
                color = "green" if cpv_diff < 0 else "red"
                st.markdown(f"<p style='color: {color}; margin-top: -15px;'>£{cpv_diff:+,.0f}</p>", unsafe_allow_html=True)
        else:
            st.metric("Cost per Visit", "N/A")
        
        # Cost-effectiveness metrics
        try:
            # Get patient outcomes data
            from ape.components.treatment_patterns.discontinued_utils import get_discontinued_patients
            
            # Count active patients (not discontinued)
            discontinued_info = get_discontinued_patients(sim_data['results'])
            active_patients = sum(1 for info in discontinued_info.values() if not info['discontinued'])
            
            if active_patients > 0:
                cost_per_active = total_costs['total'] / active_patients
                st.metric("Cost per Active Patient", f"£{cost_per_active:,.0f}")
                if cost_difference != 0:
                    original_cpa = original_costs['total'] / active_patients
                    cpa_diff = cost_per_active - original_cpa
                    color = "green" if cpa_diff < 0 else "red"
                    st.markdown(f"<p style='color: {color}; margin-top: -15px;'>£{cpa_diff:+,.0f}</p>", unsafe_allow_html=True)
            
            # Get vision outcomes - ONLY for active patients
            vision_df = sim_data['results'].get_vision_trajectory_df()
            patient_vision_stats = vision_df.groupby('patient_id')['vision'].agg(['first', 'last']).reset_index()
            
            # Merge with discontinuation info to only count active patients
            active_patient_ids = {pid for pid, info in discontinued_info.items() if not info['discontinued']}
            
            # Convert patient_id to string if needed to match the format
            patient_vision_stats['patient_id'] = patient_vision_stats['patient_id'].astype(str)
            active_patient_ids_str = {str(pid) for pid in active_patient_ids}
            
            active_vision_stats = patient_vision_stats[patient_vision_stats['patient_id'].isin(active_patient_ids_str)]
            
            # Count ACTIVE patients maintaining vision (within 10 letters of baseline)
            vision_maintained = sum(
                1 for _, row in active_vision_stats.iterrows() 
                if row['last'] >= row['first'] - 10
            )
            
            if vision_maintained > 0:
                cost_per_maintained = total_costs['total'] / vision_maintained
                st.metric("Cost per Vision Maintained", f"£{cost_per_maintained:,.0f}")
                if cost_difference != 0:
                    original_cpvm = original_costs['total'] / vision_maintained
                    cpvm_diff = cost_per_maintained - original_cpvm
                    color = "green" if cpvm_diff < 0 else "red"
                    st.markdown(f"<p style='color: {color}; margin-top: -15px;'>£{cpvm_diff:+,.0f}</p>", unsafe_allow_html=True)
                    
        except Exception as e:
            # If patient outcomes data is not available, just show the basic metrics
            pass

# Export functionality (outside tabs)
st.header("Export Data")

# Create an expander for export options
with st.expander("Export Options", expanded=False):
    st.write("Download workload and economic analysis data for further analysis or reporting.")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Workload Summary Export
        st.markdown("#### Workload Summary")
        st.write("Complete workload analysis including daily patterns, bottlenecks, and resource utilization.")
        
        # Create export data
        export_data = {
            'simulation_info': {
                'protocol': sim_data['protocol']['name'],
                'n_patients': sim_data['parameters']['n_patients'],
                'duration_years': sim_data['parameters']['duration_years'],
                'seed': sim_data['parameters'].get('seed', 'N/A')
            },
            'summary': workload_summary,
            'total_costs': safe_call_method(resource_tracker, 'get_total_costs'),
            'bottlenecks': [
                {
                    'date': b['date'].isoformat(),
                    'role': b['role'],
                    'sessions_needed': b['sessions_needed'],
                    'sessions_available': b['sessions_available'],
                    'overflow': b['overflow'],
                    'procedures_affected': b['procedures_affected']
                }
                for b in bottlenecks
            ] if 'bottlenecks' in locals() else [],
            'daily_usage': [
                {
                    'date': date.isoformat(),
                    'usage': dict(rt_dict.get('daily_usage', {}).get(date, {}) if hasattr(resource_tracker, '__dict__') else resource_tracker.daily_usage[date])
                }
                for date in all_dates
            ] if 'all_dates' in locals() else [],
            'export_timestamp': datetime.now().isoformat()
        }
        
        # Convert to JSON string
        json_str = json.dumps(export_data, indent=2)
        
        st.download_button(
            label="Download Workload Summary (JSON)",
            data=json_str,
            file_name=f"workload_summary_{sim_data['results'].metadata.sim_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="download_workload_json"
        )
    
    with col2:
        # Cost Details Export
        st.markdown("#### Visit Cost Details")
        st.write("Detailed cost breakdown for each visit including procedures and medications.")
        
        # Create cost details for each visit
        visit_details = []
        # Get visits for cost details (handle SimpleNamespace) - reuse from earlier
        for visit in visits:
            visit_details.append({
                'date': visit['date'].isoformat(),
                'patient_id': visit['patient_id'],
                'visit_type': visit['visit_type'],
                'injection_given': visit['injection_given'],
                'oct_performed': visit['oct_performed'],
                'total_cost': sum(visit['costs'].values()),
                **visit['costs']
            })
        
        # Convert to DataFrame and CSV
        visit_df = pd.DataFrame(visit_details)
        csv_str = visit_df.to_csv(index=False)
        
        st.download_button(
            label="Download Cost Details (CSV)",
            data=csv_str,
            file_name=f"visit_costs_{sim_data['results'].metadata.sim_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_costs_csv"
        )
    
    with col3:
        # Financial Parameters Export
        st.markdown("#### Financial Parameters")
        st.write("NHS resource configuration and cost parameters used in this analysis.")
        
        try:
            from ape.utils.financial_pdf_generator import generate_financial_parameters_pdf
            
            # Handle both direct ResourceTracker and wrapped versions
            if hasattr(resource_tracker, '__dict__'):
                # If it's a SimpleNamespace or similar, access attributes directly
                rt_dict = resource_tracker.__dict__
                resource_config = {
                    'resources': {
                        'roles': rt_dict.get('roles', {}),
                        'visit_requirements': rt_dict.get('visit_requirements', {}),
                        'session_parameters': rt_dict.get('session_parameters', {})
                    },
                    'costs': rt_dict.get('costs', {})
                }
                
                # Add capacity constraints if available
                if 'capacity_constraints' in rt_dict:
                    resource_config['capacity_constraints'] = rt_dict['capacity_constraints']
            else:
                # Direct ResourceTracker object
                resource_config = {
                    'resources': {
                        'roles': roles if 'roles' in locals() else resource_tracker.roles,
                        'visit_requirements': resource_tracker.visit_requirements,
                        'session_parameters': session_params if 'session_params' in locals() else resource_tracker.session_parameters
                    },
                    'costs': current_drug_costs if 'current_drug_costs' in locals() else resource_tracker.costs
                }
                
                # Add capacity constraints if available
                if hasattr(resource_tracker, 'capacity_constraints'):
                    resource_config['capacity_constraints'] = resource_tracker.capacity_constraints
            
            # Generate PDF
            pdf_bytes = generate_financial_parameters_pdf(resource_config=resource_config)
            
            st.download_button(
                label="Download Financial Parameters (PDF)",
                data=pdf_bytes,
                file_name=f"financial_parameters_{sim_data['results'].metadata.sim_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                key="download_financial_pdf"
            )
            
        except Exception as e:
            st.error(f"Failed to generate financial parameters PDF: {e}")
    
    with col4:
        # Workload Results PDF Export
        st.markdown("#### Workload Results")
        st.write("Comprehensive PDF report of simulation workload and cost outcomes.")
        
        try:
            from ape.utils.workload_results_pdf_generator import generate_workload_results_pdf
            
            # Prepare simulation info
            simulation_info = {
                'protocol': sim_data['protocol']['name'],
                'n_patients': sim_data['parameters']['n_patients'],
                'duration_years': sim_data['parameters']['duration_years'],
                'engine': sim_data['parameters'].get('engine', 'ABS'),
                'seed': sim_data['parameters'].get('seed', 'Random')
            }
            
            # Prepare patient outcomes data if available
            patient_outcomes_data = None
            try:
                # Try to get the same data calculated in the cost analysis section
                from ape.components.treatment_patterns.discontinued_utils import get_discontinued_patients
                
                discontinued_info = get_discontinued_patients(sim_data['results'])
                active_patients = sum(1 for info in discontinued_info.values() if not info['discontinued'])
                retention_rate = (active_patients / total_patients) * 100
                
                vision_df = sim_data['results'].get_vision_trajectory_df()
                patient_vision_stats = vision_df.groupby('patient_id')['vision'].agg(['first', 'last']).reset_index()
                
                # Only count vision maintenance for active patients
                active_patient_ids = {pid for pid, info in discontinued_info.items() if not info['discontinued']}
                active_vision_stats = patient_vision_stats[patient_vision_stats['patient_id'].isin(active_patient_ids)]
                
                vision_maintained = sum(
                    1 for _, row in active_vision_stats.iterrows() 
                    if row['last'] >= row['first'] - 10
                )
                vision_maintenance_rate = (vision_maintained / active_patients) * 100 if active_patients > 0 else 0
                
                patient_outcomes_data = {
                    'active_patients': active_patients,
                    'retention_rate': retention_rate,
                    'vision_maintained': vision_maintained,
                    'vision_maintenance_rate': vision_maintenance_rate,
                    'total_patients': total_patients
                }
            except:
                # If we can't get patient outcomes, just proceed without them
                pass
            
            # Prepare bottlenecks data with string dates
            bottlenecks_for_pdf = [
                {
                    'date': b['date'].strftime('%Y-%m-%d'),
                    'role': b['role'],
                    'sessions_needed': b['sessions_needed'],
                    'sessions_available': b['sessions_available'],
                    'overflow': b['overflow'],
                    'procedures_affected': b['procedures_affected']
                }
                for b in bottlenecks
            ] if 'bottlenecks' in locals() else None
            
            # Generate PDF
            pdf_bytes = generate_workload_results_pdf(
                simulation_info=simulation_info,
                workload_summary=workload_summary,
                total_costs=safe_call_method(resource_tracker, 'get_total_costs'),
                utilization_data=utilization_data if 'utilization_data' in locals() else [],
                staffing_data=staffing_data if 'staffing_data' in locals() else [],
                bottlenecks=bottlenecks_for_pdf,
                patient_outcomes=patient_outcomes_data
            )
            
            st.download_button(
                label="Download Workload Results (PDF)",
                data=pdf_bytes,
                file_name=f"workload_results_{sim_data['results'].metadata.sim_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                key="download_workload_pdf"
            )
            
        except Exception as e:
            st.error(f"Failed to generate workload results PDF: {e}")