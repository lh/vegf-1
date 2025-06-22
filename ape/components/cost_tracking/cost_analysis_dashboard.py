"""
Cost analysis dashboard for simulation results.

This module provides the main interface for:
- Cost effectiveness metrics
- Cost breakdown visualization
- Patient-level cost analysis
- Protocol cost comparison
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, Optional, Any, List
from datetime import datetime

from simulation_v2.economics.enhanced_cost_tracker import EnhancedCostTracker
from .cost_configuration_widget import CostConfigurationWidget
from .workload_visualizer import WorkloadVisualizer


class CostAnalysisDashboard:
    """Main dashboard for cost analysis visualization."""
    
    def __init__(self, cost_tracker: Optional[EnhancedCostTracker] = None):
        """
        Initialize cost analysis dashboard.
        
        Args:
            cost_tracker: Enhanced cost tracker with simulation results
        """
        self.cost_tracker = cost_tracker
        self.config_widget = CostConfigurationWidget()
        self.workload_viz = WorkloadVisualizer(cost_tracker)
        
    def render(self) -> None:
        """Render the complete cost analysis dashboard."""
        st.header("💰 Cost Analysis Dashboard")
        
        if not self.cost_tracker:
            st.warning("No cost tracking data available. Please run a simulation with cost tracking enabled.")
            return
            
        # Get cost effectiveness metrics
        ce_metrics = self.cost_tracker.calculate_cost_effectiveness()
        
        # Summary metrics at top
        self._render_summary_metrics(ce_metrics)
        
        # Main analysis tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Cost Breakdown",
            "Cost Timeline",
            "Patient Analysis",
            "Workload Analysis",
            "Data Export"
        ])
        
        with tab1:
            self._render_cost_breakdown()
            
        with tab2:
            self._render_cost_timeline()
            
        with tab3:
            self._render_patient_analysis(ce_metrics)
            
        with tab4:
            self.workload_viz.render()
            
        with tab5:
            self._render_data_export(ce_metrics)
            
    def _render_summary_metrics(self, metrics: Dict[str, Any]) -> None:
        """Render key summary metrics."""
        st.subheader("📊 Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Cost",
                f"£{metrics['total_cost']:,.0f}",
                help="Total cost across all patients"
            )
            
        with col2:
            st.metric(
                "Cost per Patient",
                f"£{metrics['cost_per_patient']:,.0f}",
                help="Average cost per patient"
            )
            
        with col3:
            st.metric(
                "Total Injections",
                f"{metrics['total_injections']:,}",
                help="Total number of injections given"
            )
            
        with col4:
            st.metric(
                "Cost per Injection",
                f"£{metrics['cost_per_injection']:,.0f}",
                help="Average cost per injection episode"
            )
            
        # Vision outcomes
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Patients Treated",
                f"{metrics['total_patients']:,}"
            )
            
        with col2:
            st.metric(
                "Vision Maintained",
                f"{metrics['patients_maintaining_vision']:,}",
                help="Patients losing ≤5 letters"
            )
            
        with col3:
            if metrics['cost_per_vision_maintained'] > 0:
                st.metric(
                    "Cost per Vision Saved",
                    f"£{metrics['cost_per_vision_maintained']:,.0f}",
                    help="Cost per patient maintaining vision"
                )
            else:
                st.metric("Cost per Vision Saved", "N/A")
                
        with col4:
            st.metric(
                "Mean VA Change",
                f"{metrics['mean_vision_change']:.1f} letters",
                help="Average change in visual acuity"
            )
            
    def _render_cost_breakdown(self) -> None:
        """Render cost breakdown analysis."""
        st.subheader("Cost Component Analysis")
        
        # Get breakdown data
        breakdown = self.cost_tracker.get_cost_breakdown()
        
        # Create pie chart
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Cost by Component", "Drug vs Procedure Costs"),
            specs=[[{'type':'pie'}, {'type':'pie'}]]
        )
        
        # Component breakdown
        components = []
        values = []
        colors = []
        
        component_colors = {
            'drug_costs': '#FF6B6B',
            'injection_costs': '#4ECDC4',
            'oct_costs': '#FFE66D',
            'consultation_costs': '#95E1D3',
            'other_costs': '#C9C9C9'
        }
        
        for component, cost in breakdown.items():
            if component != 'total_costs' and cost > 0:
                components.append(component.replace('_', ' ').title())
                values.append(cost)
                colors.append(component_colors.get(component, '#999999'))
                
        fig.add_trace(
            go.Pie(
                labels=components,
                values=values,
                hole=0.4,
                marker_colors=colors,
                textposition='inside',
                textinfo='percent+label'
            ),
            row=1, col=1
        )
        
        # Drug vs procedure split
        drug_total = breakdown['drug_costs']
        procedure_total = sum(v for k, v in breakdown.items() 
                            if k not in ['drug_costs', 'total_costs'])
        
        fig.add_trace(
            go.Pie(
                labels=['Drug Costs', 'Procedure Costs'],
                values=[drug_total, procedure_total],
                hole=0.4,
                marker_colors=['#FF6B6B', '#4ECDC4'],
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
        
        # Cost breakdown table
        with st.expander("Detailed Cost Breakdown"):
            breakdown_data = []
            for component, cost in breakdown.items():
                if component != 'total_costs':
                    breakdown_data.append({
                        'Component': component.replace('_', ' ').title(),
                        'Total Cost': f"£{cost:,.0f}",
                        'Percentage': f"{(cost/breakdown['total_costs']*100):.1f}%" if breakdown['total_costs'] > 0 else "0%"
                    })
                    
            st.dataframe(pd.DataFrame(breakdown_data), hide_index=True)
            
    def _render_cost_timeline(self) -> None:
        """Render cost accumulation over time."""
        st.subheader("Cost Timeline Analysis")
        
        # Get monthly workload data for timeline
        workload_df = self.cost_tracker.get_workload_summary()
        
        if workload_df.empty:
            st.info("No timeline data available.")
            return
            
        # Calculate monthly costs
        # This is a simplified calculation - in reality would use actual visit costs
        drug_cost_per_injection = self.cost_tracker.cost_config.get_drug_cost(self.cost_tracker.active_drug)
        visit_costs = {
            'injection': self.cost_tracker.cost_config.get_component_cost('injection_administration'),
            'oct': self.cost_tracker.cost_config.get_component_cost('oct_scan'),
            'consultation': self.cost_tracker.cost_config.get_component_cost('consultant_followup')
        }
        
        # Estimate monthly costs
        workload_df['drug_costs'] = workload_df['injections'] * drug_cost_per_injection
        workload_df['procedure_costs'] = (
            workload_df['injections'] * visit_costs['injection'] +
            workload_df['oct_scans'] * visit_costs['oct'] +
            workload_df['decision_visits'] * visit_costs['consultation']
        )
        workload_df['total_costs'] = workload_df['drug_costs'] + workload_df['procedure_costs']
        
        # Calculate cumulative costs
        workload_df['cumulative_drug'] = workload_df['drug_costs'].cumsum()
        workload_df['cumulative_procedure'] = workload_df['procedure_costs'].cumsum()
        workload_df['cumulative_total'] = workload_df['total_costs'].cumsum()
        
        # Create timeline chart
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Monthly Costs", "Cumulative Costs"),
            shared_xaxes=True,
            vertical_spacing=0.15,
            row_heights=[0.4, 0.6]
        )
        
        # Monthly costs
        fig.add_trace(
            go.Bar(
                x=workload_df['month'],
                y=workload_df['drug_costs'],
                name='Drug Costs',
                marker_color='#FF6B6B',
                hovertemplate='£%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=workload_df['month'],
                y=workload_df['procedure_costs'],
                name='Procedure Costs',
                marker_color='#4ECDC4',
                hovertemplate='£%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Cumulative costs
        fig.add_trace(
            go.Scatter(
                x=workload_df['month'],
                y=workload_df['cumulative_total'],
                mode='lines',
                name='Total',
                line=dict(color='#333333', width=3),
                hovertemplate='£%{y:,.0f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=workload_df['month'],
                y=workload_df['cumulative_drug'],
                mode='lines',
                name='Drug',
                line=dict(color='#FF6B6B', width=2, dash='dot'),
                hovertemplate='£%{y:,.0f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=workload_df['month'],
                y=workload_df['cumulative_procedure'],
                mode='lines',
                name='Procedure',
                line=dict(color='#4ECDC4', width=2, dash='dot'),
                hovertemplate='£%{y:,.0f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            barmode='stack',
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=0, r=0, t=50, b=0),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        fig.update_xaxes(title_text="Month", row=2, col=1)
        fig.update_yaxes(title_text="Monthly Cost (£)", row=1, col=1)
        fig.update_yaxes(title_text="Cumulative Cost (£)", row=2, col=1)
        
        # Add grid
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Annual cost projections
        self._render_annual_projections(workload_df)
        
    def _render_annual_projections(self, df: pd.DataFrame) -> None:
        """Render annual cost projections."""
        with st.expander("Annual Cost Projections"):
            # Group by year
            df['year'] = ((df.index) // 12) + 1
            annual_costs = df.groupby('year').agg({
                'drug_costs': 'sum',
                'procedure_costs': 'sum',
                'total_costs': 'sum',
                'injections': 'sum'
            }).reset_index()
            
            # Display annual summary
            for _, year_data in annual_costs.iterrows():
                year = int(year_data['year'])
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(f"Year {year} Total", f"£{year_data['total_costs']:,.0f}")
                with col2:
                    st.metric("Drug Costs", f"£{year_data['drug_costs']:,.0f}")
                with col3:
                    st.metric("Procedure Costs", f"£{year_data['procedure_costs']:,.0f}")
                with col4:
                    st.metric("Injections", f"{int(year_data['injections'])}")
                    
    def _render_patient_analysis(self, ce_metrics: Dict[str, Any]) -> None:
        """Render patient-level cost analysis."""
        st.subheader("Patient-Level Analysis")
        
        # Get patient data
        patient_data = []
        for patient_id, record in self.cost_tracker.patient_records.items():
            patient_data.append({
                'Patient ID': patient_id,
                'Total Cost': record.total_cost,
                'Drug Cost': record.total_drug_cost,
                'Procedure Cost': record.total_procedure_cost,
                'Injections': record.total_injections,
                'Decision Visits': record.total_decision_visits,
                'Vision Change': record.vision_change if record.vision_change else 0,
                'Cost per Injection': record.cost_per_injection
            })
            
        patient_df = pd.DataFrame(patient_data)
        
        # Distribution plots
        col1, col2 = st.columns(2)
        
        with col1:
            # Cost distribution
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=patient_df['Total Cost'],
                nbinsx=30,
                name='Patient Cost Distribution',
                marker_color='#4ECDC4',
                hovertemplate='Cost: £%{x}<br>Count: %{y}<extra></extra>'
            ))
            
            # Add mean line
            mean_cost = patient_df['Total Cost'].mean()
            fig.add_vline(
                x=mean_cost,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Mean: £{mean_cost:,.0f}"
            )
            
            fig.update_layout(
                title="Patient Cost Distribution",
                xaxis_title="Total Cost per Patient (£)",
                yaxis_title="Number of Patients",
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            # Injection count distribution
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=patient_df['Injections'],
                nbinsx=20,
                name='Injection Distribution',
                marker_color='#FF6B6B',
                hovertemplate='Injections: %{x}<br>Count: %{y}<extra></extra>'
            ))
            
            # Add mean line
            mean_injections = patient_df['Injections'].mean()
            fig.add_vline(
                x=mean_injections,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Mean: {mean_injections:.1f}"
            )
            
            fig.update_layout(
                title="Injection Count Distribution",
                xaxis_title="Total Injections per Patient",
                yaxis_title="Number of Patients",
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        # Cost vs outcome scatter
        st.subheader("Cost vs Vision Outcomes")
        
        fig = go.Figure()
        
        # Color by vision outcome
        patient_df['Outcome'] = patient_df['Vision Change'].apply(
            lambda x: 'Improved' if x > 0 else ('Maintained' if x >= -5 else 'Declined')
        )
        
        for outcome, color in [('Improved', '#4ECDC4'), ('Maintained', '#FFE66D'), ('Declined', '#FF6B6B')]:
            subset = patient_df[patient_df['Outcome'] == outcome]
            fig.add_trace(go.Scatter(
                x=subset['Total Cost'],
                y=subset['Vision Change'],
                mode='markers',
                name=outcome,
                marker=dict(
                    size=subset['Injections']*2,  # Size by injection count
                    color=color,
                    opacity=0.6,
                    line=dict(width=1, color='white')
                ),
                hovertemplate='Cost: £%{x:,.0f}<br>VA Change: %{y:.1f}<br>Injections: %{marker.size}<extra></extra>'
            ))
            
        fig.update_layout(
            xaxis_title="Total Cost per Patient (£)",
            yaxis_title="Vision Change (letters)",
            hovermode='closest',
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        # Add reference line at -5 letters
        fig.add_hline(
            y=-5,
            line_dash="dash",
            line_color="gray",
            annotation_text="Maintenance threshold"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        with st.expander("Patient Cost Statistics"):
            stats_df = patient_df[['Total Cost', 'Drug Cost', 'Procedure Cost', 'Injections', 'Vision Change']].describe()
            st.dataframe(stats_df.round(2))
            
    def _render_data_export(self, ce_metrics: Dict[str, Any]) -> None:
        """Render data export options."""
        st.subheader("📊 Export Cost Analysis Data")
        
        # Summary report
        st.write("### Summary Report")
        
        summary_data = {
            'Metric': [
                'Total Cost',
                'Total Patients',
                'Cost per Patient',
                'Total Injections',
                'Cost per Injection',
                'Patients Maintaining Vision',
                'Cost per Vision Maintained',
                'Mean Vision Change'
            ],
            'Value': [
                f"£{ce_metrics['total_cost']:,.0f}",
                f"{ce_metrics['total_patients']:,}",
                f"£{ce_metrics['cost_per_patient']:,.0f}",
                f"{ce_metrics['total_injections']:,}",
                f"£{ce_metrics['cost_per_injection']:,.0f}",
                f"{ce_metrics['patients_maintaining_vision']:,}",
                f"£{ce_metrics['cost_per_vision_maintained']:,.0f}" if ce_metrics['cost_per_vision_maintained'] > 0 else "N/A",
                f"{ce_metrics['mean_vision_change']:.1f} letters"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, hide_index=True)
        
        # Export buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export summary
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="Download Summary Report",
                data=csv,
                file_name=f"cost_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
        with col2:
            # Export patient data
            if hasattr(self.cost_tracker, 'export_patient_data'):
                st.download_button(
                    label="Download Patient Data",
                    data="Click to generate patient data export",
                    file_name=f"patient_costs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    help="Export detailed patient-level cost data"
                )
                
        with col3:
            # Export workload data
            workload_df = self.workload_viz.export_workload_data()
            if not workload_df.empty:
                csv = workload_df.to_csv(index=False)
                st.download_button(
                    label="Download Workload Data",
                    data=csv,
                    file_name=f"workload_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )