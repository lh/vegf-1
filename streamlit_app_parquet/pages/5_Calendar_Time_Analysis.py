"""Calendar-Time Analysis - Analyze clinic activity from calendar-time perspective."""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

import sys
from pathlib import Path
# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from staggered_data_processor import (
    transform_to_calendar_view,
    calculate_resource_requirements,
    aggregate_patient_outcomes_by_enrollment_cohort
)
from staggered_visualizations import (
    create_clinic_activity_timeline,
    create_resource_utilization_chart,
    create_enrollment_flow_diagram,
    create_cohort_outcomes_comparison,
    create_phase_distribution_heatmap
)
from utils.paths import get_parquet_results_dir, debug_paths

logger = logging.getLogger(__name__)

# Streamlit page configuration
st.set_page_config(
    page_title="Calendar-Time Analysis",
    page_icon="📅",
    layout="wide"
)

# Define display function BEFORE main page logic
def display_calendar_results(calendar_data: Dict):
    """Display results from calendar-time analysis."""
    st.header("Calendar-Time Analysis Results")
    
    # Extract data
    calendar_visits = calendar_data['calendar_visits']
    clinic_metrics = calendar_data['clinic_metrics']
    resources = calendar_data['resources']
    cohort_outcomes = calendar_data['cohort_outcomes']
    settings = calendar_data['settings']
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_visits = clinic_metrics['total_visits'].sum()
        st.metric("Total Visits", f"{total_visits:,}")
    with col2:
        peak_monthly = clinic_metrics['total_visits'].max()
        st.metric("Peak Monthly Visits", f"{peak_monthly:,}")
    with col3:
        avg_monthly = clinic_metrics['total_visits'].mean()
        st.metric("Average Monthly Visits", f"{avg_monthly:.0f}")
    with col4:
        total_patients = calendar_visits['patient_id'].nunique()
        st.metric("Total Patients", f"{total_patients:,}")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Clinic Activity", 
        "👥 Resource Requirements",
        "📈 Patient Outcomes",
        "🔄 Patient Flow",
        "🗺️ Phase Distribution"
    ])
    
    with tab1:
        st.subheader("Clinic Activity Over Time")
        
        # Clinic activity timeline
        activity_fig = create_clinic_activity_timeline(clinic_metrics)
        st.plotly_chart(activity_fig, use_container_width=True)
        
        # Monthly details expander
        with st.expander("View Monthly Details"):
            display_df = clinic_metrics[[
                'month', 'total_visits', 'unique_patients', 
                'injection_visits', 'monitoring_visits', 'new_patients'
            ]].copy()
            display_df['month'] = pd.to_datetime(display_df['month']).dt.strftime('%Y-%m')
            st.dataframe(display_df, use_container_width=True)
    
    with tab2:
        if resources is not None:
            st.subheader("Resource Requirements Analysis")
            
            # Resource utilization chart
            resource_fig = create_resource_utilization_chart(
                resources,
                target_clinicians=settings['target_clinicians']
            )
            st.plotly_chart(resource_fig, use_container_width=True)
            
            # Staffing recommendations
            st.markdown("### Staffing Analysis")
            
            peak_fte = resources['fte_clinicians_needed'].max()
            avg_fte = resources['fte_clinicians_needed'].mean()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Peak FTE Required", f"{peak_fte:.1f}")
                st.metric("Average FTE Required", f"{avg_fte:.1f}")
            
            with col2:
                if settings['target_clinicians']:
                    utilization = (avg_fte / settings['target_clinicians'] * 100)
                    st.metric("Average Utilization", f"{utilization:.1f}%")
                    
                    if peak_fte > settings['target_clinicians']:
                        shortage = peak_fte - settings['target_clinicians']
                        st.warning(f"⚠️ Peak demand exceeds capacity by {shortage:.1f} FTE")
            
            # Resource planning table
            with st.expander("View Quarterly Resource Requirements"):
                quarterly_resources = resources.set_index('month').resample('QE').agg({
                    'total_visits': 'sum',
                    'fte_clinicians_needed': 'mean',
                    'total_hours': 'sum'
                }).round(1)
                st.dataframe(quarterly_resources, use_container_width=True)
        else:
            st.info("Enable 'Resource Requirements Analysis' in the sidebar to view this section.")
    
    with tab3:
        st.subheader("Patient Outcomes by Enrollment Cohort")
        
        # Cohort outcomes comparison
        if len(cohort_outcomes) > 0:
            outcomes_fig = create_cohort_outcomes_comparison(cohort_outcomes)
            st.plotly_chart(outcomes_fig, use_container_width=True)
            
            # Cohort details table
            with st.expander("View Cohort Details"):
                display_cohorts = cohort_outcomes.copy()
                display_cohorts.index = display_cohorts.index.astype(str)
                display_cohorts = display_cohorts.round(2)
                st.dataframe(display_cohorts, use_container_width=True)
        else:
            st.warning("Not enough data to display cohort outcomes.")
    
    with tab4:
        st.subheader("Patient Flow Analysis")
        
        # This would show patient flow through the system
        # For now, show enrollment distribution
        st.markdown("### Enrollment Timeline")
        
        enrollment_data = calendar_visits.groupby('enrollment_date')['patient_id'].nunique()
        enrollment_df = pd.DataFrame({
            'date': enrollment_data.index,
            'new_patients': enrollment_data.values
        })
        
        import plotly.express as px
        enrollment_fig = px.bar(
            enrollment_df, 
            x='date', 
            y='new_patients',
            title='Patient Enrollment Over Time'
        )
        st.plotly_chart(enrollment_fig, use_container_width=True)
        
        # Patient status summary
        st.markdown("### Patient Status Summary")
        
        # Calculate current patient status
        latest_visits = calendar_visits.sort_values('calendar_date').groupby('patient_id').last()
        
        # Check which discontinuation column exists
        if 'has_been_discontinued' in latest_visits.columns:
            active_mask = ~latest_visits['has_been_discontinued']
            discontinued_mask = latest_visits['has_been_discontinued']
        elif 'is_discontinuation' in latest_visits.columns:
            # For this column, we need to check if the patient ever discontinued
            patient_disc_status = calendar_visits.groupby('patient_id')['is_discontinuation'].any()
            active_mask = ~patient_disc_status
            discontinued_mask = patient_disc_status
        else:
            # No discontinuation data available
            active_mask = pd.Series([True] * len(latest_visits), index=latest_visits.index)
            discontinued_mask = pd.Series([False] * len(latest_visits), index=latest_visits.index)
        
        status_counts = {
            'Active': active_mask.sum(),
            'Discontinued': discontinued_mask.sum()
        }
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Active Patients", status_counts['Active'])
        with col2:
            st.metric("Discontinued Patients", status_counts['Discontinued'])
    
    with tab5:
        st.subheader("Treatment Phase Distribution")
        
        if 'phase' in calendar_visits.columns:
            # Phase distribution heatmap
            phase_fig = create_phase_distribution_heatmap(calendar_visits)
            st.plotly_chart(phase_fig, use_container_width=True)
            
            # Current phase distribution
            st.markdown("### Current Phase Distribution")
            
            current_phases = calendar_visits.sort_values('calendar_date').groupby('patient_id')['phase'].last()
            phase_counts = current_phases.value_counts()
            
            import plotly.express as px
            phase_pie = px.pie(
                values=phase_counts.values,
                names=phase_counts.index,
                title="Current Patient Distribution by Phase"
            )
            st.plotly_chart(phase_pie, use_container_width=True)
        else:
            st.info("Phase information not available in this simulation.")
    
    # Export options
    st.markdown("---")
    st.subheader("Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = clinic_metrics.to_csv(index=False)
        st.download_button(
            label="📥 Download Clinic Metrics (CSV)",
            data=csv,
            file_name=f"clinic_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        if resources is not None:
            csv = resources.to_csv(index=False)
            st.download_button(
                label="📥 Download Resource Analysis (CSV)",
                data=csv,
                file_name=f"resource_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col3:
        csv = cohort_outcomes.to_csv()
        st.download_button(
            label="📥 Download Cohort Outcomes (CSV)",
            data=csv,
            file_name=f"cohort_outcomes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


# Main page content
st.title("📅 Calendar-Time Analysis")

st.markdown("""
This page analyzes existing simulation data from a calendar-time perspective, 
showing clinic activity, resource requirements, and patient flow over real time.
""")

# Get parquet directory using path utilities
parquet_dir = get_parquet_results_dir()

# Debug mode - show path information
if st.checkbox("Show debug information", value=False):
    debug_paths()

# Check for available Parquet files
parquet_files = list(parquet_dir.glob("*_metadata.parquet"))
if not parquet_files:
    st.error("No Parquet simulation results found.")
    st.info("Please run a simulation first from the 'Run Simulation' page.")
    debug_paths()  # Always show debug info if no files found
else:
    # Sidebar configuration
    with st.sidebar:
        st.header("Calendar View Settings")
        
        # Get simulation names
        simulation_names = [f.stem.replace("_metadata", "") for f in parquet_files]
        
        # Check if we should auto-select a simulation
        default_index = 0
        if "selected_simulation_for_calendar" in st.session_state:
            # User selected a specific simulation from Run Simulation page
            selected_name = st.session_state["selected_simulation_for_calendar"]
            if selected_name in simulation_names:
                default_index = simulation_names.index(selected_name)
            del st.session_state["selected_simulation_for_calendar"]  # Clear after use
        elif "latest_simulation_name" in st.session_state:
            # Auto-select the latest simulation if available
            latest_name = st.session_state["latest_simulation_name"]
            if latest_name in simulation_names:
                default_index = simulation_names.index(latest_name)
        
        # Select simulation to analyze
        selected_sim = st.selectbox(
            "Select Simulation",
            options=simulation_names,
            index=default_index,
            help="Choose which simulation to analyze"
        )
        
        # Enrollment settings
        st.subheader("Enrollment Configuration")
        
        enrollment_pattern = st.selectbox(
            "Enrollment Pattern",
            options=["uniform", "front_loaded", "gradual"],
            format_func=lambda x: {
                "uniform": "Uniform (steady rate)",
                "front_loaded": "Front-loaded (more early)",
                "gradual": "Gradual (bell curve)"
            }[x],
            help="How patients are enrolled over time"
        )
        
        # Get simulation duration from selected simulation's metadata
        max_enrollment = 120  # Default maximum
        if selected_sim:
            try:
                # Read metadata to get simulation duration
                metadata_path = parquet_dir / f"{selected_sim}_metadata.parquet"
                if metadata_path.exists():
                    temp_metadata = pd.read_parquet(metadata_path)
                    if 'duration_years' in temp_metadata.columns:
                        sim_duration_years = temp_metadata['duration_years'].iloc[0]
                        # Allow enrollment throughout entire simulation period
                        max_enrollment = int(sim_duration_years * 12)
            except Exception:
                pass  # Use default if any error
        
        enrollment_months = st.number_input(
            "Enrollment Period (months)",
            min_value=1,
            max_value=max_enrollment,
            value=12,
            help=f"Period over which patients are enrolled. Can extend throughout entire simulation ({max_enrollment} months) to model steady-state clinic operations."
        )
        
        # Analysis options
        st.subheader("Analysis Options")
        
        show_resource_analysis = st.checkbox(
            "Resource Requirements Analysis",
            value=True,
            help="Calculate staffing and capacity requirements"
        )
        
        target_clinicians = None
        visits_per_clinician = 20
        
        if show_resource_analysis:
            target_clinicians = st.number_input(
                "Target FTE Clinicians",
                min_value=0.5,
                max_value=20.0,
                value=5.0,
                step=0.5,
                help="Target number of full-time equivalent clinicians"
            )
            
            visits_per_clinician = st.number_input(
                "Visits per Clinician per Day",
                min_value=10,
                max_value=40,
                value=20,
                help="Average number of visits a clinician can handle per day"
            )
        
        cohort_months = st.selectbox(
            "Cohort Grouping",
            options=[3, 6, 12],
            format_func=lambda x: f"{x} months",
            help="Group patients into cohorts by enrollment period"
        )
        
        # Transform button
        transform_button = st.button(
            "Transform to Calendar View",
            type="primary",
            use_container_width=True
        )
    
    # Main content area
    if transform_button or hasattr(st.session_state, 'calendar_data'):
        try:
            # Create a progress container
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Load Parquet data
                status_text.text("Loading simulation data...")
                progress_bar.progress(10)
                visits_df = pd.read_parquet(parquet_dir / f"{selected_sim}_visits.parquet")
                metadata_df = pd.read_parquet(parquet_dir / f"{selected_sim}_metadata.parquet")
                
                # Show data size
                status_text.text(f"Processing {len(visits_df):,} visits from {visits_df['patient_id'].nunique():,} patients...")
                progress_bar.progress(20)
                
                # Transform to calendar view
                status_text.text("Transforming to calendar-time view...")
                progress_bar.progress(30)
                calendar_visits_df, clinic_metrics_df = transform_to_calendar_view(
                    visits_df,
                    metadata_df,
                    enrollment_pattern=enrollment_pattern,
                    enrollment_months=enrollment_months
                )
                
                # Calculate additional metrics if requested
                if show_resource_analysis:
                    status_text.text("Calculating resource requirements...")
                    progress_bar.progress(60)
                    resources_df = calculate_resource_requirements(
                        clinic_metrics_df,
                        visits_per_clinician_per_day=visits_per_clinician
                    )
                else:
                    resources_df = None
                    progress_bar.progress(60)
                
                # Calculate cohort outcomes
                status_text.text("Aggregating cohort outcomes...")
                progress_bar.progress(80)
                cohort_outcomes_df = aggregate_patient_outcomes_by_enrollment_cohort(
                    calendar_visits_df,
                    metadata_df,
                    cohort_months=cohort_months
                )
                
                # Store in session state
                status_text.text("Finalizing...")
                progress_bar.progress(90)
                st.session_state.calendar_data = {
                    'calendar_visits': calendar_visits_df,
                    'clinic_metrics': clinic_metrics_df,
                    'resources': resources_df,
                    'cohort_outcomes': cohort_outcomes_df,
                    'settings': {
                        'enrollment_pattern': enrollment_pattern,
                        'enrollment_months': enrollment_months,
                        'target_clinicians': target_clinicians if show_resource_analysis else None
                    }
                }
                
                # Clear progress indicators
                progress_bar.progress(100)
                status_text.text("✅ Transformation complete!")
                time.sleep(0.5)  # Brief pause to show completion
                progress_container.empty()  # Clear the progress display
                
        except Exception as e:
            st.error(f"Error transforming data: {str(e)}")
            logger.exception("Calendar transformation error")
    
    # Display results if available
    if hasattr(st.session_state, 'calendar_data'):
        display_calendar_results(st.session_state.calendar_data)