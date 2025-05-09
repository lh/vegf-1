"""
Patient Explorer Module for APE: AMD Protocol Explorer

This module provides the Interactive Patient Explorer component for the APE dashboard,
allowing users to select individual patients and explore their complete treatment journey.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from streamlit_app.json_utils import convert_datetimes_in_dict

def display_patient_explorer(patient_histories: Dict[str, List[Dict]], simulation_stats: Optional[Dict] = None):
    """
    Display the Interactive Patient Explorer.
    
    Parameters
    ----------
    patient_histories : Dict[str, List[Dict]]
        Dictionary mapping patient IDs to their visit histories
    simulation_stats : Optional[Dict]
        Optional dictionary of simulation statistics for context
    """
    st.header("Interactive Patient Explorer")
    
    if not patient_histories:
        st.warning("No patient data available. Please run a simulation first.")
        return
        
    # Convert any serialized datetime strings back to datetime objects
    processed_histories = {}
    for patient_id, history in patient_histories.items():
        # Convert datetime strings in each visit
        processed_history = [convert_datetimes_in_dict(visit) for visit in history]
        processed_histories[patient_id] = processed_history
    
    # Use the processed histories instead of the original
    patient_histories = processed_histories
    
    # Show simulation context if available
    if simulation_stats:
        st.info(f"Exploring data from simulation with {len(patient_histories)} patients over "
                f"{simulation_stats.get('duration_years', '?')} years.")
    
    # Patient selection
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # Extract summary metrics for each patient
        patient_summaries = []
        for patient_id, history in patient_histories.items():
            # Skip patients with no history
            if not history:
                continue
                
            # Calculate summary metrics
            injections = sum(1 for visit in history if 'injection' in visit.get('actions', []))
            visits = len(history)
            
            # Get initial and final vision
            initial_vision = next((visit.get('vision', None) for visit in history), None)
            final_vision = next((visit.get('vision', None) for visit in reversed(history)), None)
            va_change = None
            if initial_vision is not None and final_vision is not None:
                va_change = final_vision - initial_vision
            
            # Get discontinuation status
            is_discontinued = False
            discontinuation_type = None
            for visit in history:
                if visit.get('phase') == 'monitoring':
                    is_discontinued = True
                    discontinuation_type = visit.get('cessation_type', 'Unknown')
                    break
            
            # Create summary
            patient_summaries.append({
                'patient_id': patient_id,
                'visits': visits,
                'injections': injections,
                'initial_va': initial_vision,
                'final_va': final_vision,
                'va_change': va_change,
                'is_discontinued': is_discontinued,
                'discontinuation_type': discontinuation_type
            })
        
        # Create summary DataFrame
        summary_df = pd.DataFrame(patient_summaries)
        
        # Add derived columns
        if not summary_df.empty:
            summary_df['injection_rate'] = summary_df['injections'] / summary_df['visits'].clip(lower=1)
            summary_df['va_status'] = summary_df['va_change'].apply(
                lambda x: 'Improved' if x is not None and x > 5 else 
                          'Worsened' if x is not None and x < -5 else 
                          'Stable' if x is not None else 'Unknown')
        
        # Create filters
        st.subheader("Patient Filters")
        
        # Only show filters if we have data
        if not summary_df.empty:
            # VA change filter
            va_change_filter = st.radio(
                "VA Change Filter",
                options=["All", "Improved", "Stable", "Worsened"],
                horizontal=True
            )
            
            # Discontinuation filter
            discontinued_filter = st.radio(
                "Discontinuation Filter",
                options=["All", "Discontinued", "Active"],
                horizontal=True
            )
            
            # Apply filters
            filtered_df = summary_df.copy()
            
            if va_change_filter != "All":
                filtered_df = filtered_df[filtered_df['va_status'] == va_change_filter]
                
            if discontinued_filter != "All":
                filtered_df = filtered_df[filtered_df['is_discontinued'] == (discontinued_filter == "Discontinued")]
            
            # Show filter results
            st.text(f"Showing {len(filtered_df)} of {len(summary_df)} patients")
            
            # Patient selection
            patient_options = filtered_df['patient_id'].tolist()
            
            if patient_options:
                selected_patient = st.selectbox(
                    "Select a patient to explore:",
                    options=patient_options
                )
            else:
                st.warning("No patients match the selected filters.")
                return
        else:
            st.warning("No patient summary data available.")
            return
    
    # Display selected patient data
    if selected_patient:
        patient_data = patient_histories[selected_patient]
        
        with col2:
            # Patient summary metrics
            st.subheader(f"Patient {selected_patient} Summary")
            
            # Get patient summary from filtered DataFrame
            patient_summary = filtered_df[filtered_df['patient_id'] == selected_patient].iloc[0]
            
            # Create metrics row
            metric_cols = st.columns(4)
            
            with metric_cols[0]:
                st.metric("Total Visits", f"{patient_summary['visits']}")
                
            with metric_cols[1]:
                st.metric("Injections", f"{patient_summary['injections']}")
                
            with metric_cols[2]:
                va_change = patient_summary['va_change']
                if va_change is not None:
                    st.metric("VA Change", f"{va_change:.1f} letters")
                else:
                    st.metric("VA Change", "Unknown")
                    
            with metric_cols[3]:
                if patient_summary['is_discontinued']:
                    st.metric("Status", "Discontinued")
                else:
                    st.metric("Status", "Active")
        
        # Create patient timeline visualization
        st.subheader("Treatment Timeline")
        
        # Process patient data for timeline
        timeline_data = process_patient_for_timeline(patient_data)
        
        # Create the timeline visualization
        fig = create_patient_timeline(timeline_data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Visit details table
        st.subheader("Visit Details")
        visit_df = create_visit_dataframe(patient_data)
        
        if not visit_df.empty:
            st.dataframe(visit_df, use_container_width=True)
        else:
            st.warning("No visit data available for this patient.")
        
        # Clinical outcomes analysis
        st.subheader("Clinical Outcomes")
        
        # Create two columns for outcomes
        outcome_cols = st.columns(2)
        
        with outcome_cols[0]:
            # VA trajectory visualization
            va_data = extract_va_data(patient_data)
            
            if va_data['weeks'] and va_data['va_values']:
                # Create Tufte-inspired VA trajectory visualization
                fig, ax = plt.subplots(figsize=(8, 4))
                
                # Plot main VA line with soft blue color
                ax.plot(va_data['weeks'], va_data['va_values'], '-', color='#3498db', linewidth=2.5, alpha=0.8)
                
                # Add subtle markers
                ax.scatter(va_data['weeks'], va_data['va_values'], s=40, color='#3498db', alpha=0.7, zorder=5)
                
                # Calculate initial and final VA for annotations
                initial_va = va_data['va_values'][0] if va_data['va_values'] else None
                final_va = va_data['va_values'][-1] if va_data['va_values'] else None
                
                # Add initial and final annotations if available
                if initial_va is not None:
                    ax.annotate(f"Initial: {initial_va:.1f}", 
                                xy=(va_data['weeks'][0], initial_va),
                                xytext=(5, 0), textcoords="offset points",
                                ha="left", va="center", fontsize=9, color='#555555')
                    
                if final_va is not None and len(va_data['weeks']) > 1:
                    ax.annotate(f"Final: {final_va:.1f}", 
                                xy=(va_data['weeks'][-1], final_va),
                                xytext=(-5, 0), textcoords="offset points",
                                ha="right", va="center", fontsize=9, color='#555555')
                
                # Calculate y-axis range with padding
                if va_data['va_values']:
                    min_va = min(va_data['va_values']) - 5
                    max_va = max(va_data['va_values']) + 5
                    ax.set_ylim(max(0, min_va), min(85, max_va))
                
                # Clean, minimalist styling - Tufte-inspired
                ax.spines['right'].set_visible(False)
                ax.spines['top'].set_visible(False)
                ax.spines['left'].set_linewidth(0.5)
                ax.spines['bottom'].set_linewidth(0.5)
                
                # Use lighter grid lines
                ax.grid(True, linestyle='--', alpha=0.3, color='#cccccc')
                
                # Force a clear zero line as a reference
                ax.axhline(y=initial_va, color='#cccccc', linestyle='-', linewidth=0.5, alpha=0.7)
                
                # Set axis labels with clear typography
                ax.set_xlabel('Weeks from First Visit', fontsize=10, color='#555555')
                ax.set_ylabel('Visual Acuity (ETDRS letters)', fontsize=10, color='#555555')
                
                # Add a title that explains the chart
                ax.set_title("Visual Acuity Over Time", fontsize=12, color='#333333', loc='left', pad=10)
                
                # Use light gray tick labels
                ax.tick_params(colors='#555555')
                
                st.pyplot(fig)
            else:
                st.warning("Insufficient VA data for visualization.")
        
        with outcome_cols[1]:
            # Treatment phases analysis
            phase_data = analyze_treatment_phases(patient_data)
            
            # Create a pie chart of time spent in each phase with Tufte-inspired design
            if phase_data['phase_days'] and len(phase_data['phase_days']) > 0:
                fig, ax = plt.subplots(figsize=(8, 4))
                
                # Define an elegant color palette
                colors = {
                    'loading': '#3498db',      # Blue
                    'maintenance': '#2ecc71',  # Green
                    'monitoring': '#9b59b6',   # Purple
                    'unknown': '#95a5a6'       # Gray
                }
                
                # Match colors to phase names
                phase_colors = [colors.get(phase.lower(), '#95a5a6') for phase in phase_data['phase_days'].keys()]
                
                # Create the pie chart with a slight wedge property for better visibility
                wedges, texts, autotexts = ax.pie(
                    phase_data['phase_days'].values(), 
                    labels=None,  # We'll add custom labels
                    autopct='%1.1f%%',
                    colors=phase_colors,
                    startangle=90,
                    wedgeprops=dict(width=0.6, edgecolor='white'),  # Donut chart style
                    pctdistance=0.85,  # Move percentage closer to edge
                    textprops=dict(color='white', fontsize=10)
                )
                
                # Add a circular hole in center for donut chart
                circle = plt.Circle((0,0), 0.3, fc='white')
                ax.add_artist(circle)
                
                # Create a clean legend instead of labels on the pie
                legend_labels = [f"{phase} ({days} days)" for phase, days in phase_data['phase_days'].items()]
                ax.legend(wedges, legend_labels, loc="center", bbox_to_anchor=(0.5, 0), frameon=False, ncol=2)
                
                # Set title with Tufte-inspired simplicity
                ax.set_title('Time Spent in Treatment Phases', fontsize=12, color='#333333', pad=10)
                
                # Equal aspect ratio ensures the pie chart is circular
                ax.set_aspect('equal')
                
                st.pyplot(fig)
            else:
                st.warning("Insufficient phase data for visualization.")
            
            # Display key outcomes
            initial_va = patient_summary.get('initial_va')
            final_va = patient_summary.get('final_va')
            
            if initial_va is not None and final_va is not None:
                # Categorize VA change
                if final_va - initial_va >= 15:
                    outcome = "Significant improvement (≥15 letters)"
                    color = "green"
                elif final_va - initial_va >= 5:
                    outcome = "Moderate improvement (5-14 letters)"
                    color = "lightgreen"
                elif final_va - initial_va >= -5:
                    outcome = "Stable (-5 to +5 letters)"
                    color = "gray"
                elif final_va - initial_va >= -15:
                    outcome = "Moderate decline (5-15 letters)"
                    color = "orange"
                else:
                    outcome = "Significant decline (>15 letters)"
                    color = "red"
                    
                st.markdown(f"**Clinical Outcome:** <span style='color:{color}'>{outcome}</span>", unsafe_allow_html=True)
        
        # Debug section
        with st.expander("Debug Information"):
            st.subheader("Raw Patient Data")
            st.json(patient_data[0] if patient_data else {})
            
            st.subheader("Data Types")
            if patient_data:
                sample_visit = patient_data[0]
                debug_info = {}
                for key, value in sample_visit.items():
                    debug_info[key] = f"{type(value).__name__}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}"
                st.write(debug_info)
                
            st.subheader("Date Formatting")
            if patient_data:
                dates = [visit.get('date') for visit in patient_data if 'date' in visit]
                if dates:
                    st.write(f"First date type: {type(dates[0]).__name__}")
                    if isinstance(dates[0], datetime):
                        st.write(f"First date: {dates[0].isoformat()}")
                    else:
                        st.write(f"First date: {dates[0]}")
            
            st.subheader("Actions Format")
            if patient_data:
                actions_examples = [visit.get('actions') for visit in patient_data if 'actions' in visit]
                if actions_examples:
                    st.write(f"Actions type: {type(actions_examples[0]).__name__}")
                    st.write(f"Actions sample: {actions_examples[0]}")
            
            st.subheader("Patient Summary")
            st.write(patient_summary.to_dict() if hasattr(patient_summary, 'to_dict') else patient_summary)


def process_patient_for_timeline(patient_data: List[Dict]) -> Dict:
    """
    Process patient data into a format suitable for timeline visualization.
    
    Parameters
    ----------
    patient_data : List[Dict]
        List of patient visit dictionaries
        
    Returns
    -------
    Dict
        Processed data for timeline visualization
    """
    if not patient_data:
        return {
            'dates': [],
            'va_values': [],
            'injections': [],
            'monitoring': [],
            'phases': [],
            'phase_transitions': []
        }
    
    # Extract data for timeline
    dates = []
    va_values = []
    injection_dates = []
    monitoring_dates = []
    phases = []
    phase_changes = []
    
    current_phase = None
    
    for i, visit in enumerate(patient_data):
        # Skip if no date
        if 'date' not in visit:
            continue
            
        visit_date = visit['date']
        dates.append(visit_date)
        
        # Track visual acuity
        if 'vision' in visit:
            va_values.append(visit['vision'])
        else:
            # Use last known value or None
            va_values.append(va_values[-1] if va_values else None)
            
        # Track injections
        if 'actions' in visit and 'injection' in visit['actions']:
            injection_dates.append(visit_date)
            
        # Track monitoring visits
        if visit.get('type') == 'monitoring_visit':
            monitoring_dates.append(visit_date)
            
        # Track phase changes
        phase = visit.get('phase')
        phases.append(phase)
        
        if phase != current_phase:
            phase_changes.append((visit_date, phase))
            current_phase = phase
    
    return {
        'dates': dates,
        'va_values': va_values,
        'injections': injection_dates,
        'monitoring': monitoring_dates,
        'phases': phases,
        'phase_transitions': phase_changes
    }


def create_patient_timeline(timeline_data: Dict) -> go.Figure:
    """
    Create an interactive timeline visualization for a patient.
    
    Parameters
    ----------
    timeline_data : Dict
        Processed timeline data from process_patient_for_timeline
        
    Returns
    -------
    go.Figure
        Plotly figure object with the timeline visualization
    """
    # Extract data
    dates = timeline_data['dates']
    va_values = timeline_data['va_values']
    injection_dates = timeline_data['injections']
    monitoring_dates = timeline_data['monitoring']
    phases = timeline_data['phases']
    phase_transitions = timeline_data['phase_transitions']
    
    # Create figure
    fig = go.Figure()
    
    # Add visual acuity line
    if dates and va_values:
        fig.add_trace(go.Scatter(
            x=dates,
            y=va_values,
            mode='lines+markers',
            name='Visual Acuity',
            line=dict(color='blue', width=2),
            marker=dict(size=8, color='blue'),
            hovertemplate='Date: %{x}<br>VA: %{y:.1f} letters<extra></extra>'
        ))
    
    # Add injection markers
    if injection_dates:
        # Find VA values for injection dates
        injection_va = []
        for inj_date in injection_dates:
            if inj_date in dates:
                idx = dates.index(inj_date)
                injection_va.append(va_values[idx])
            else:
                injection_va.append(None)
        
        try:
            fig.add_trace(go.Scatter(
                x=injection_dates,
                y=injection_va,
                mode='markers',
                name='Injection',
                marker=dict(
                    symbol='triangle-up',
                    size=12,
                    color='red',
                    line=dict(width=1, color='#8B0000')  # Using hex color code for darkred
                ),
                hovertemplate='Injection Date: %{x}<br>VA: %{y:.1f} letters<extra></extra>'
            ))
        except Exception as e:
            st.warning(f"Error adding injection markers: {e}")
            # Fallback to simpler marker
            fig.add_trace(go.Scatter(
                x=injection_dates,
                y=injection_va,
                mode='markers',
                name='Injection',
                marker=dict(symbol='triangle-up', size=12, color='red'),
                hovertemplate='Injection Date: %{x}<br>VA: %{y:.1f} letters<extra></extra>'
            ))
    
    # Add monitoring visit markers
    if monitoring_dates:
        # Find VA values for monitoring dates
        monitoring_va = []
        for mon_date in monitoring_dates:
            if mon_date in dates:
                idx = dates.index(mon_date)
                monitoring_va.append(va_values[idx])
            else:
                monitoring_va.append(None)
        
        try:
            fig.add_trace(go.Scatter(
                x=monitoring_dates,
                y=monitoring_va,
                mode='markers',
                name='Monitoring Visit',
                marker=dict(
                    symbol='square',
                    size=10,
                    color='green',
                    line=dict(width=1, color='#006400')  # Using hex color code for darkgreen
                ),
                hovertemplate='Monitoring Date: %{x}<br>VA: %{y:.1f} letters<extra></extra>'
            ))
        except Exception as e:
            st.warning(f"Error adding monitoring markers: {e}")
            # Fallback to simpler marker
            fig.add_trace(go.Scatter(
                x=monitoring_dates,
                y=monitoring_va,
                mode='markers',
                name='Monitoring Visit',
                marker=dict(symbol='square', size=10, color='green'),
                hovertemplate='Monitoring Date: %{x}<br>VA: %{y:.1f} letters<extra></extra>'
            ))
    
    # Add phase transition markers if we have at least two
    if len(phase_transitions) >= 2:
        phase_dates = [pt[0] for pt in phase_transitions]
        phase_names = [pt[1] for pt in phase_transitions]
        
        # Find VA values for phase transition dates
        phase_va = []
        for phase_date in phase_dates:
            if phase_date in dates:
                idx = dates.index(phase_date)
                phase_va.append(va_values[idx])
            else:
                phase_va.append(None)
        
        try:
            fig.add_trace(go.Scatter(
                x=phase_dates,
                y=phase_va,
                mode='markers+text',
                name='Phase Change',
                marker=dict(
                    symbol='diamond',
                    size=14,
                    color='purple',
                    line=dict(width=1, color='#4B0082')  # Using hex code for indigo/dark purple
                ),
                text=phase_names,
                textposition="top center",
                hovertemplate='Phase Change: %{x}<br>New Phase: %{text}<extra></extra>'
            ))
        except Exception as e:
            st.warning(f"Error adding phase transition markers: {e}")
            # Fallback to simpler marker
            fig.add_trace(go.Scatter(
                x=phase_dates,
                y=phase_va,
                mode='markers+text',
                name='Phase Change',
                marker=dict(symbol='diamond', size=14, color='purple'),
                text=phase_names,
                textposition="top center",
                hovertemplate='Phase Change: %{x}<br>New Phase: %{text}<extra></extra>'
            ))
    
    # Add shapes to indicate different phases
    if phase_transitions:
        colors = {
            'loading': 'rgba(255, 200, 200, 0.2)',
            'maintenance': 'rgba(200, 255, 200, 0.2)',
            'monitoring': 'rgba(200, 200, 255, 0.2)'
        }
        
        for i in range(len(phase_transitions)):
            phase = phase_transitions[i][1]
            start_date = phase_transitions[i][0]
            
            # End date is either the next phase transition or the last visit
            if i < len(phase_transitions) - 1:
                end_date = phase_transitions[i+1][0]
            elif dates:
                end_date = dates[-1]
            else:
                continue
            
            # Add colored background for this phase
            if phase in colors:
                fig.add_shape(
                    type="rect",
                    xref="x",
                    yref="paper",
                    x0=start_date,
                    y0=0,
                    x1=end_date,
                    y1=1,
                    fillcolor=colors.get(phase, 'rgba(200, 200, 200, 0.2)'),
                    opacity=0.5,
                    layer="below",
                    line_width=0,
                )
    
    # Update layout
    fig.update_layout(
        title="Patient Treatment Timeline",
        xaxis_title="Date",
        yaxis_title="Visual Acuity (ETDRS letters)",
        legend_title="Event Type",
        template="plotly_white",
        height=400,
        hovermode="closest",
        hoverlabel=dict(
            bgcolor="white",
            font_size=14
        )
    )
    
    # Set y-axis range to 0-85 (ETDRS letters)
    fig.update_yaxes(range=[0, 85])
    
    return fig


def create_visit_dataframe(patient_data: List[Dict]) -> pd.DataFrame:
    """
    Create a DataFrame with detailed visit information.
    
    Parameters
    ----------
    patient_data : List[Dict]
        List of patient visit dictionaries
        
    Returns
    -------
    pd.DataFrame
        DataFrame with visit details
    """
    if not patient_data:
        return pd.DataFrame()
    
    # Extract data for DataFrame
    visit_records = []
    
    for visit in patient_data:
        try:
            # Handle actions specially to ensure it's always a list before joining
            actions = visit.get('actions', [])
            if actions is None:
                actions = []
            elif isinstance(actions, str):
                # If actions is already a string, use it as is
                actions_str = actions
            elif isinstance(actions, list):
                # Convert list of actions to comma-separated string
                actions_str = ', '.join(str(a) for a in actions)
            else:
                # Convert any other type to string
                actions_str = str(actions)
            
            # Extract key information
            record = {
                'Date': visit.get('date', None),
                'Visit Type': visit.get('type', 'Unknown'),
                'Actions': actions_str,
                'Vision': visit.get('vision', None),
                'Disease State': visit.get('disease_state', 'Unknown'),
                'Phase': visit.get('phase', 'Unknown'),
                'Interval': visit.get('interval', None)
            }
            visit_records.append(record)
        except Exception as e:
            st.warning(f"Error processing visit data: {e}")
            # Add a minimal record to avoid breaking the DataFrame
            visit_records.append({
                'Date': None,
                'Visit Type': 'Error',
                'Actions': f'Error: {str(e)}',
                'Vision': None,
                'Disease State': 'Unknown',
                'Phase': 'Unknown',
                'Interval': None
            })
    
    # Create DataFrame
    df = pd.DataFrame(visit_records)
    
    # Format date column
    if 'Date' in df.columns and len(df) > 0:
        try:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        except Exception as e:
            st.warning(f"Error converting dates: {e}")
    
    return df


def extract_va_data(patient_data: List[Dict]) -> Dict:
    """
    Extract visual acuity data from patient history.
    
    Parameters
    ----------
    patient_data : List[Dict]
        List of patient visit dictionaries
        
    Returns
    -------
    Dict
        Dictionary with weeks and VA values
    """
    if not patient_data:
        return {'weeks': [], 'va_values': []}
    
    try:
        # Get first visit date
        first_date = patient_data[0].get('date')
        if not first_date:
            st.warning("First visit missing date")
            return {'weeks': [], 'va_values': []}
        
        # Extract weeks and VA values
        weeks = []
        va_values = []
        
        for visit in patient_data:
            try:
                if 'date' in visit and 'vision' in visit:
                    # Calculate weeks from first visit
                    visit_date = visit['date']
                    
                    # Ensure these are datetime objects
                    if not isinstance(visit_date, datetime) or not isinstance(first_date, datetime):
                        # Try to convert to datetime if they're strings
                        if isinstance(visit_date, str):
                            visit_date = datetime.fromisoformat(visit_date)
                        if isinstance(first_date, str):
                            first_date = datetime.fromisoformat(first_date)
                    
                    # Calculate time difference
                    week = (visit_date - first_date).days / 7
                    
                    # Add data point only if valid
                    if isinstance(visit['vision'], (int, float)):
                        weeks.append(week)
                        va_values.append(float(visit['vision']))
            except Exception as e:
                st.warning(f"Error processing visit for VA data: {e}")
        
        return {'weeks': weeks, 'va_values': va_values}
        
    except Exception as e:
        st.warning(f"Error extracting VA data: {e}")
        return {'weeks': [], 'va_values': []}


def analyze_treatment_phases(patient_data: List[Dict]) -> Dict:
    """
    Analyze time spent in different treatment phases.
    
    Parameters
    ----------
    patient_data : List[Dict]
        List of patient visit dictionaries
        
    Returns
    -------
    Dict
        Dictionary with phase analysis data
    """
    if not patient_data:
        return {'phase_days': {}}
    
    try:
        # Extract phase transitions
        phases = []
        dates = []
        
        for visit in patient_data:
            if 'date' in visit and 'phase' in visit and visit['phase'] is not None:
                try:
                    # Ensure date is a datetime object
                    visit_date = visit['date']
                    if not isinstance(visit_date, datetime):
                        if isinstance(visit_date, str):
                            visit_date = datetime.fromisoformat(visit_date)
                        else:
                            continue  # Skip if date is not valid
                    
                    phases.append(str(visit['phase']))  # Convert phase to string for safety
                    dates.append(visit_date)
                except Exception as e:
                    st.warning(f"Error processing date in phase analysis: {e}")
        
        if not phases or not dates:
            return {'phase_days': {}}
        
        # Calculate days in each phase
        phase_days = {}
        current_phase = None
        phase_start = None
        
        # Process phase by phase
        for i, (phase, date) in enumerate(zip(phases, dates)):
            try:
                # If phase has changed or we're at the end
                if phase != current_phase or i == len(phases) - 1:
                    # Record the previous phase duration if we had one
                    if current_phase is not None and phase_start is not None:
                        end_date = date if i < len(phases) - 1 else dates[-1]
                        days = (end_date - phase_start).days
                        if days < 0:  # Ensure no negative values
                            days = 0
                        
                        if current_phase in phase_days:
                            phase_days[current_phase] += days
                        else:
                            phase_days[current_phase] = days
                    
                    # Start the new phase
                    current_phase = phase
                    phase_start = date
            except Exception as e:
                st.warning(f"Error calculating phase duration: {e}")
        
        return {'phase_days': phase_days}
        
    except Exception as e:
        st.warning(f"Error analyzing treatment phases: {e}")
        return {'phase_days': {}}