"""Combined Treatment Intervals & Gaps Tab - Comprehensive view of all interval data."""

import streamlit as st
import pandas as pd
import numpy as np
from ape.utils.style_constants import StyleConstants
from ape.utils.export_config import get_export_config
from .interval_visualization import create_interval_distribution_tufte, create_interval_summary_table
from . import (
    create_interval_distribution_chart,
    create_gap_analysis_chart_tufte,
    calculate_interval_statistics
)


def render_combined_intervals_tab(results, stats, params):
    """
    Render a comprehensive treatment intervals and gaps analysis tab.
    
    Combines:
    - Summary statistics
    - Raw interval distribution (all visits)
    - Pattern transition distribution 
    - Patient gap analysis
    
    Args:
        results: Simulation results object
        stats: Summary statistics dict
        params: Simulation parameters
    """
    st.header("Treatment Intervals & Gaps")
    
    st.markdown("""
    Comprehensive analysis of treatment intervals showing both the raw distribution of all visits 
    and pattern transitions. This combines clinical workload data with treatment adherence insights.
    """)
    
    # 1. Summary Statistics (from former tab 8)
    st.subheader("Summary Statistics")
    
    total_patients = stats['patient_count']
    total_injections = stats.get('total_injections', 0)
    mean_injections = total_injections / total_patients if total_patients > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Patients", f"{StyleConstants.format_count(total_patients)}")
    with col2:
        st.metric("Total Injections", f"{StyleConstants.format_count(int(total_injections))}")
    with col3:
        st.metric("Mean Injections/Patient", f"{StyleConstants.format_statistic(mean_injections)}")
    with col4:
        st.metric("Injection Rate", f"{(total_injections / (total_patients * params['duration_years'])):.1f}/year")
    
    # 2. Get all required data
    # Cache function for treatment intervals
    @st.cache_data
    def get_cached_treatment_intervals(sim_id):
        """Cache treatment intervals calculation."""
        return results.get_treatment_intervals_df()
    
    # Cache function for treatment patterns
    @st.cache_data
    def get_cached_treatment_patterns(sim_id):
        """Get treatment patterns with caching."""
        from .pattern_analyzer import extract_treatment_patterns_vectorized
        return extract_treatment_patterns_vectorized(results)
    
    # Load data
    with st.spinner("Loading interval data..."):
        intervals_df = get_cached_treatment_intervals(results.metadata.sim_id)
        transitions_df, visits_df = get_cached_treatment_patterns(results.metadata.sim_id)
    
    if len(intervals_df) > 0:
        intervals = intervals_df['interval_days'].values
        
        # Interval statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Mean Interval", f"{StyleConstants.format_statistic(np.mean(intervals))} days")
        with col2:
            st.metric("Median Interval", f"{StyleConstants.format_statistic(np.median(intervals))} days")
        with col3:
            st.metric("Min Interval", f"{int(np.min(intervals))} days")
        with col4:
            st.metric("Max Interval", f"{int(np.max(intervals))} days")
        
        st.markdown("---")
        
        # 3. Visualizations in two columns
        col1, col2 = st.columns(2)
        
        with col1:
            # Raw interval distribution (from former tab 8)
            st.subheader("All Visit Intervals")
            st.caption("Distribution of time between every consecutive pair of visits")
            
            interval_fig = create_interval_distribution_tufte(intervals)
            config = get_export_config(filename="all_visit_intervals")
            st.plotly_chart(interval_fig, use_container_width=True, config=config)
            
            # Detailed statistics in expander
            with st.expander("View Detailed Statistics"):
                stats_fig = create_interval_summary_table(intervals_df)
                st.plotly_chart(stats_fig, use_container_width=True, config=config)
        
        with col2:
            # Pattern transitions (from former tab 5)
            st.subheader("Pattern Transitions")
            st.caption("When patients change treatment intensity")
            
            if len(transitions_df) > 0:
                transition_fig = create_interval_distribution_chart(transitions_df)
                config = get_export_config(filename="pattern_transitions")
                st.plotly_chart(transition_fig, use_container_width=True, config=config)
            else:
                st.info("No pattern transitions yet - will appear as simulation progresses")
        
        st.markdown("---")
        
        # 4. Patient Gap Analysis (full width)
        st.subheader("Patient Gap Analysis")
        st.caption("Categorizes patients by their maximum treatment gap")
        
        if len(visits_df) > 0:
            gap_fig = create_gap_analysis_chart_tufte(visits_df)
            config = get_export_config(filename="gap_analysis")
            st.plotly_chart(gap_fig, use_container_width=True, config=config)
            
            # Calculate detailed statistics if transitions exist
            if len(transitions_df) > 0:
                interval_stats = calculate_interval_statistics(visits_df)
                
                with st.expander("View Interval Statistics by Pattern"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Std Deviation", f"{interval_stats['std']:.1f} days")
                        if 'p25' in interval_stats:
                            st.metric("25th Percentile", f"{interval_stats['p25']:.1f} days")
                    
                    with col2:
                        if 'p75' in interval_stats:
                            st.metric("75th Percentile", f"{interval_stats['p75']:.1f} days")
                        if 'iqr' in interval_stats:
                            st.metric("IQR", f"{interval_stats['iqr']:.1f} days")
                    
                    with col3:
                        total_visits = len(visits_df)
                        st.metric("Total Visits Analyzed", f"{StyleConstants.format_count(total_visits)}")
                    
                    with col4:
                        # Additional insight
                        regular_visits = sum(1 for i in intervals if 28 <= i <= 42)
                        st.metric("Regular Monthly", f"{regular_visits/len(intervals)*100:.0f}%")
        
        # 5. Key Insights
        st.markdown("---")
        st.subheader("Key Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **All Visit Intervals** shows:
            - Actual clinic workload distribution
            - Most common visit frequencies
            - True treatment burden
            """)
        
        with col2:
            st.markdown("""
            **Pattern Transitions** shows:
            - Protocol adherence trends
            - When patients extend/shorten intervals
            - Treatment optimization opportunities
            """)
        
    else:
        st.info("No treatment intervals found - data will appear as patients have follow-up visits.")