"""
Task-based workload visualization component.

This module provides visualizations for:
- Task workload over time (injection, decision, imaging tasks)
- Capacity planning based on tasks
- Resource utilization metrics
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum

from simulation_v2.economics.enhanced_cost_tracker import EnhancedCostTracker


class TaskType(Enum):
    """Types of tasks in the clinic."""
    INJECTION_TASK = "injection_task"
    DECISION_TASK = "decision_task"
    IMAGING_TASK = "imaging_task"
    ADMIN_TASK = "admin_task"
    VIRTUAL_REVIEW_TASK = "virtual_review_task"


class WorkloadVisualizer:
    """Visualizer for task-based workload metrics."""
    
    # Task time estimates (minutes)
    TASK_DURATIONS = {
        TaskType.INJECTION_TASK: 20,
        TaskType.DECISION_TASK: 15,
        TaskType.IMAGING_TASK: 10,
        TaskType.ADMIN_TASK: 5,
        TaskType.VIRTUAL_REVIEW_TASK: 10
    }
    
    def __init__(self, cost_tracker: Optional[EnhancedCostTracker] = None):
        """
        Initialize workload visualizer.
        
        Args:
            cost_tracker: Enhanced cost tracker with workload data
        """
        self.cost_tracker = cost_tracker
        
    def render(self) -> None:
        """Render all workload visualizations."""
        if not self.cost_tracker:
            st.warning("No cost tracking data available. Run a simulation with cost tracking enabled.")
            return
            
        st.header("📋 Task-Based Workload Analysis")
        
        # Get workload data and convert to task-based metrics
        workload_df = self._convert_to_task_based_metrics()
        
        if workload_df.empty:
            st.info("No workload data to display.")
            return
            
        # Summary metrics
        self._render_summary_metrics(workload_df)
        
        # Timeline visualizations
        tab1, tab2, tab3, tab4 = st.tabs([
            "Task Timeline", 
            "Task Distribution", 
            "Resource Requirements",
            "Data Export"
        ])
        
        with tab1:
            self._render_task_timeline(workload_df)
            
        with tab2:
            self._render_task_distribution(workload_df)
            
        with tab3:
            self._render_resource_requirements(workload_df)
            
        with tab4:
            self._render_data_export(workload_df)
            
    def _convert_to_task_based_metrics(self) -> pd.DataFrame:
        """Convert visit-based metrics to task-based metrics."""
        workload_df = self.cost_tracker.get_workload_summary()
        
        if workload_df.empty:
            return pd.DataFrame()
            
        # Calculate tasks based on visit types
        task_data = []
        
        for _, row in workload_df.iterrows():
            month_data = {
                'month': row['month'],
                'injection_tasks': row['injections'],
                'decision_tasks': row['decision_visits'],
                'imaging_tasks': row['oct_scans'],
                'virtual_review_tasks': row['virtual_reviews'],
                # Admin tasks = all visits (each visit has admin component)
                'admin_tasks': row['total_visits']
            }
            
            # Calculate task hours
            for task_type in TaskType:
                task_key = task_type.value + 's'  # e.g., injection_tasks
                if task_key in month_data:
                    count = month_data[task_key]
                    hours = (count * self.TASK_DURATIONS[task_type]) / 60
                    month_data[f'{task_type.value}_hours'] = hours
                    
            task_data.append(month_data)
            
        return pd.DataFrame(task_data)
        
    def _render_summary_metrics(self, df: pd.DataFrame) -> None:
        """Render summary metrics for tasks."""
        st.subheader("📊 Task Summary")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_injections = df['injection_tasks'].sum()
            st.metric("Injection Tasks", f"{total_injections:,}")
            
        with col2:
            total_decisions = df['decision_tasks'].sum()
            st.metric("Decision Tasks", f"{total_decisions:,}")
            
        with col3:
            total_imaging = df['imaging_tasks'].sum()
            st.metric("Imaging Tasks", f"{total_imaging:,}")
            
        with col4:
            total_virtual = df['virtual_review_tasks'].sum()
            st.metric("Virtual Reviews", f"{total_virtual:,}")
            
        with col5:
            total_admin = df['admin_tasks'].sum()
            st.metric("Admin Tasks", f"{total_admin:,}")
            
        # Task hours summary
        st.subheader("⏱️ Total Time Requirements")
        
        col1, col2, col3 = st.columns(3)
        
        total_hours = {}
        for task_type in TaskType:
            hours_col = f'{task_type.value}_hours'
            if hours_col in df.columns:
                total_hours[task_type] = df[hours_col].sum()
                
        with col1:
            clinical_hours = (total_hours.get(TaskType.INJECTION_TASK, 0) + 
                            total_hours.get(TaskType.DECISION_TASK, 0))
            st.metric(
                "Clinical Task Hours",
                f"{clinical_hours:,.0f}",
                help="Combined injection and decision task hours"
            )
            
        with col2:
            support_hours = (total_hours.get(TaskType.IMAGING_TASK, 0) + 
                           total_hours.get(TaskType.ADMIN_TASK, 0))
            st.metric(
                "Support Task Hours",
                f"{support_hours:,.0f}",
                help="Combined imaging and admin task hours"
            )
            
        with col3:
            total_task_hours = sum(total_hours.values())
            st.metric(
                "Total Task Hours",
                f"{total_task_hours:,.0f}",
                help="All tasks combined"
            )
            
    def _render_task_timeline(self, df: pd.DataFrame) -> None:
        """Render task timeline chart."""
        st.subheader("Task Volume Over Time")
        
        # Create stacked area chart for tasks
        fig = go.Figure()
        
        # Define task colors
        task_colors = {
            'injection_tasks': '#FF6B6B',
            'decision_tasks': '#4ECDC4',
            'imaging_tasks': '#FFE66D',
            'virtual_review_tasks': '#95E1D3',
            'admin_tasks': '#C9C9C9'
        }
        
        # Add traces for each task type
        for task, color in task_colors.items():
            if task in df.columns:
                task_label = task.replace('_', ' ').title()
                fig.add_trace(go.Scatter(
                    x=df['month'],
                    y=df[task],
                    mode='lines',
                    name=task_label,
                    line=dict(width=2, color=color),
                    stackgroup='one',
                    hovertemplate=f'%{{y}} {task_label}<extra></extra>'
                ))
        
        # Update layout
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Tasks",
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Add grid
        fig.update_xaxis(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        fig.update_yaxis(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Peak task analysis
        with st.expander("Peak Task Periods"):
            peak_data = []
            for task in ['injection_tasks', 'decision_tasks', 'imaging_tasks']:
                if task in df.columns:
                    peak_value = df[task].max()
                    peak_month = df.loc[df[task].idxmax(), 'month'].strftime('%b %Y')
                    peak_data.append({
                        'Task Type': task.replace('_', ' ').title(),
                        'Peak Count': peak_value,
                        'Peak Month': peak_month
                    })
            
            if peak_data:
                st.dataframe(pd.DataFrame(peak_data), hide_index=True)
                
    def _render_task_distribution(self, df: pd.DataFrame) -> None:
        """Render task distribution analysis."""
        st.subheader("Task Distribution Analysis")
        
        # Calculate total tasks
        task_totals = {
            'Injection Tasks': df['injection_tasks'].sum(),
            'Decision Tasks': df['decision_tasks'].sum(),
            'Imaging Tasks': df['imaging_tasks'].sum(),
            'Virtual Reviews': df['virtual_review_tasks'].sum(),
            'Admin Tasks': df['admin_tasks'].sum()
        }
        
        # Calculate total hours by task
        hour_totals = {}
        for task_type in TaskType:
            hours_col = f'{task_type.value}_hours'
            if hours_col in df.columns:
                label = task_type.value.replace('_', ' ').title()
                hour_totals[label] = df[hours_col].sum()
        
        # Create subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Task Count Distribution", "Time Distribution (Hours)"),
            specs=[[{'type':'pie'}, {'type':'pie'}]]
        )
        
        # Task count pie chart
        fig.add_trace(
            go.Pie(
                labels=list(task_totals.keys()),
                values=list(task_totals.values()),
                hole=0.4,
                marker_colors=['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3', '#C9C9C9'],
                textposition='inside',
                textinfo='percent+label'
            ),
            row=1, col=1
        )
        
        # Time distribution pie chart
        fig.add_trace(
            go.Pie(
                labels=list(hour_totals.keys()),
                values=list(hour_totals.values()),
                hole=0.4,
                marker_colors=['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3', '#C9C9C9'],
                textposition='inside',
                textinfo='percent+label'
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=50, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Monthly patterns
        st.subheader("Monthly Task Patterns")
        
        # Create heatmap of tasks by month
        task_cols = ['injection_tasks', 'decision_tasks', 'imaging_tasks', 'virtual_review_tasks']
        heatmap_data = df[['month'] + task_cols].copy()
        heatmap_data['month_str'] = heatmap_data['month'].dt.strftime('%b %Y')
        
        # Transpose for heatmap
        heatmap_matrix = heatmap_data.set_index('month_str')[task_cols].T
        heatmap_matrix.index = [idx.replace('_', ' ').title() for idx in heatmap_matrix.index]
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_matrix.values,
            x=heatmap_matrix.columns,
            y=heatmap_matrix.index,
            colorscale='Blues',
            hovertemplate='%{y}<br>%{x}: %{z} tasks<extra></extra>'
        ))
        
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Task Type",
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def _render_resource_requirements(self, df: pd.DataFrame) -> None:
        """Render resource requirement analysis."""
        st.subheader("Resource Requirements")
        
        # Calculate FTE requirements based on task hours
        # Assuming 37.5 hours per week, ~150 hours per month
        hours_per_fte_month = 150
        
        df['total_task_hours'] = 0
        for task_type in TaskType:
            hours_col = f'{task_type.value}_hours'
            if hours_col in df.columns:
                df['total_task_hours'] += df[hours_col]
                
        df['fte_required'] = df['total_task_hours'] / hours_per_fte_month
        
        # Create FTE requirement chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['month'],
            y=df['fte_required'],
            name='FTE Required',
            marker_color='#4ECDC4',
            hovertemplate='%{y:.2f} FTE<extra></extra>'
        ))
        
        # Add reference lines for staffing levels
        for fte_level in [1, 2, 3, 4]:
            fig.add_hline(
                y=fte_level,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"{fte_level} FTE",
                annotation_position="right"
            )
        
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Full-Time Equivalents (FTE) Required",
            hovermode='x unified',
            margin=dict(l=0, r=0, t=30, b=0),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Add grid
        fig.update_xaxis(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        fig.update_yaxis(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Task-specific time requirements
        st.subheader("Task Time Requirements by Month")
        
        # Create stacked bar chart of hours by task type
        fig = go.Figure()
        
        task_colors = {
            TaskType.INJECTION_TASK: '#FF6B6B',
            TaskType.DECISION_TASK: '#4ECDC4',
            TaskType.IMAGING_TASK: '#FFE66D',
            TaskType.VIRTUAL_REVIEW_TASK: '#95E1D3',
            TaskType.ADMIN_TASK: '#C9C9C9'
        }
        
        for task_type, color in task_colors.items():
            hours_col = f'{task_type.value}_hours'
            if hours_col in df.columns:
                task_label = task_type.value.replace('_', ' ').title()
                fig.add_trace(go.Bar(
                    x=df['month'],
                    y=df[hours_col],
                    name=task_label,
                    marker_color=color,
                    hovertemplate=f'%{{y:.1f}} hours<br>{task_label}<extra></extra>'
                ))
        
        fig.update_layout(
            barmode='stack',
            xaxis_title="Month",
            yaxis_title="Hours Required",
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Add grid
        fig.update_xaxis(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        fig.update_yaxis(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        
        st.plotly_chart(fig, use_container_width=True)
        
    def _render_data_export(self, df: pd.DataFrame) -> None:
        """Render data export section."""
        st.subheader("📊 Data Export")
        
        st.write("Download the raw task data for further analysis:")
        
        # Prepare export data
        export_df = df.copy()
        export_df['month_str'] = export_df['month'].dt.strftime('%Y-%m')
        
        # Reorder columns for clarity
        column_order = ['month_str']
        task_cols = [col for col in df.columns if col.endswith('_tasks')]
        hour_cols = [col for col in df.columns if col.endswith('_hours')]
        other_cols = [col for col in df.columns if col not in task_cols + hour_cols + ['month', 'month_str']]
        
        column_order.extend(sorted(task_cols))
        column_order.extend(sorted(hour_cols))
        column_order.extend(sorted(other_cols))
        
        export_df = export_df[column_order]
        
        # Show preview
        st.write("Data preview:")
        st.dataframe(export_df.head(), hide_index=True)
        
        # Download button
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="Download Task Data as CSV",
            data=csv,
            file_name=f"task_workload_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Summary statistics
        with st.expander("Summary Statistics"):
            st.write("**Task Counts:**")
            task_summary = {}
            for col in task_cols:
                task_summary[col.replace('_', ' ').title()] = {
                    'Total': int(export_df[col].sum()),
                    'Monthly Average': round(export_df[col].mean(), 1),
                    'Peak': int(export_df[col].max()),
                    'Minimum': int(export_df[col].min())
                }
            
            summary_df = pd.DataFrame(task_summary).T
            st.dataframe(summary_df)
            
    def export_workload_data(self) -> pd.DataFrame:
        """Export task-based workload data for further analysis."""
        if not self.cost_tracker:
            return pd.DataFrame()
            
        return self._convert_to_task_based_metrics()