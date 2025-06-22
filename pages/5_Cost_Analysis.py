"""
Cost Analysis - Analyze economic outcomes from simulations with cost tracking.
"""

import streamlit as st
from pathlib import Path
import pandas as pd
import json

from ape.utils.state_helpers import get_active_simulation
from ape.utils.startup_redirect import handle_page_startup
from ape.components.cost_tracking.cost_analysis_dashboard import CostAnalysisDashboard
from ape.components.ui.workflow_indicator import workflow_progress_indicator

st.set_page_config(
    page_title="Cost Analysis",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Check for startup redirect
handle_page_startup("cost_analysis")

# Show workflow progress
workflow_progress_indicator("analysis")

# Get active simulation
sim_data = get_active_simulation()

if not sim_data:
    st.error("No active simulation found. Please run a simulation first.")
    st.stop()

# Check if simulation has cost tracking
has_cost_tracking = False
cost_tracker = None

# Check in simulation results metadata
if hasattr(sim_data.get('results'), 'metadata'):
    has_cost_tracking = sim_data['results'].metadata.get('has_cost_tracking', False)
    
# Check in simulation data
if 'cost_tracking' in sim_data and sim_data['cost_tracking']:
    has_cost_tracking = True

# Try to get cost tracker from results
if hasattr(sim_data.get('results'), 'cost_tracker'):
    cost_tracker = sim_data['results'].cost_tracker
elif hasattr(sim_data.get('results'), '_raw_results'):
    # Try to get from raw results
    raw_results = sim_data['results']._raw_results
    if hasattr(raw_results, 'cost_tracker'):
        cost_tracker = raw_results.cost_tracker

if not has_cost_tracking:
    st.warning("This simulation was run without cost tracking enabled.")
    st.info("To enable cost tracking, select 'Enable Cost Tracking' when running a new simulation.")
    
    # Show basic simulation info
    st.subheader("Simulation Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Protocol", sim_data['protocol']['name'])
    with col2:
        st.metric("Patients", f"{sim_data['parameters']['n_patients']:,}")
    with col3:
        st.metric("Duration", f"{sim_data['parameters']['duration_years']} years")
        
    st.stop()

# Display cost analysis dashboard
st.title("💰 Economic Analysis Results")

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
        
    # Show cost configuration if available
    if 'cost_tracking' in sim_data and sim_data['cost_tracking']:
        cost_config = sim_data['cost_tracking']
        st.write("**Cost Configuration:**")
        st.write(f"- Drug Type: {cost_config.get('drug_type', 'Unknown')}")
        st.write(f"- Drug Cost: £{cost_config.get('drug_cost', 0):,.0f}")

# Check if we have saved cost data files
results_path = sim_data['results'].data_path
cost_files = {
    'workload': results_path / "workload_summary.parquet",
    'breakdown': results_path / "cost_breakdown.json",
    'patient_costs': results_path / "patient_costs.csv"
}

# If we don't have the cost tracker object, try to reconstruct from files
if not cost_tracker and all(f.exists() for f in cost_files.values()):
    st.info("Loading cost data from saved files...")
    
    # Create a mock cost tracker with the data
    from types import SimpleNamespace
    
    # Load workload data
    workload_df = pd.read_parquet(cost_files['workload'])
    
    # Load cost breakdown
    with open(cost_files['breakdown'], 'r') as f:
        cost_breakdown = json.load(f)
        
    # Load patient costs
    patient_costs_df = pd.read_csv(cost_files['patient_costs'])
    
    # Create mock cost tracker
    mock_tracker = SimpleNamespace()
    mock_tracker.get_workload_summary = lambda: workload_df
    mock_tracker.get_cost_breakdown = lambda: cost_breakdown
    
    # Calculate cost effectiveness metrics from data
    total_patients = len(patient_costs_df)
    total_cost = patient_costs_df['total_cost'].sum()
    total_injections = patient_costs_df['total_injections'].sum()
    
    # Vision maintenance (assuming -5 letter threshold)
    if 'vision_change' in patient_costs_df.columns:
        patients_maintaining = (patient_costs_df['vision_change'] >= -5).sum()
        mean_vision_change = patient_costs_df['vision_change'].mean()
    else:
        patients_maintaining = 0
        mean_vision_change = 0
        
    ce_metrics = {
        'total_cost': total_cost,
        'total_patients': total_patients,
        'cost_per_patient': total_cost / max(1, total_patients),
        'total_injections': total_injections,
        'cost_per_injection': total_cost / max(1, total_injections),
        'patients_maintaining_vision': patients_maintaining,
        'cost_per_vision_maintained': total_cost / max(1, patients_maintaining),
        'mean_vision_change': mean_vision_change,
        'mean_injections_per_patient': total_injections / max(1, total_patients)
    }
    
    mock_tracker.calculate_cost_effectiveness = lambda: ce_metrics
    
    # Create patient records for analysis
    patient_records = {}
    for _, row in patient_costs_df.iterrows():
        record = SimpleNamespace()
        record.total_cost = row['total_cost']
        record.total_drug_cost = row.get('drug_cost', 0)
        record.total_procedure_cost = row.get('procedure_cost', 0)
        record.total_injections = row.get('total_injections', 0)
        record.total_decision_visits = row.get('total_decision_visits', 0)
        record.vision_change = row.get('vision_change')
        record.cost_per_injection = row.get('cost_per_injection', 0)
        patient_records[row['patient_id']] = record
        
    mock_tracker.patient_records = patient_records
    
    cost_tracker = mock_tracker

# Create and render dashboard
if cost_tracker:
    dashboard = CostAnalysisDashboard(cost_tracker)
    dashboard.render()
else:
    st.error("Could not load cost tracking data. The simulation may not have cost tracking enabled.")
    st.info("Please run a new simulation with 'Enable Cost Tracking' selected.")