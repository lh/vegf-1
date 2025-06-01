"""Enhanced Treatment Patterns tab with Sankey visualizations."""

import streamlit as st
import numpy as np
import pandas as pd
from utils.style_constants import StyleConstants
from utils.chart_builder import ChartBuilder
from components.treatment_patterns import (
    extract_treatment_patterns_vectorized,
    create_enhanced_sankey_with_colored_streams,
    create_gradient_sankey,
    create_interval_distribution_chart,
    create_gap_analysis_chart_tufte,
    calculate_interval_statistics
)


def render_enhanced_treatment_patterns_tab(results, protocol, params, stats):
    """Render enhanced treatment patterns tab with Sankey diagrams."""
    st.header("Treatment Patterns")
    
    # Create sub-tabs for different views - Sankey first!
    subtab1, subtab2, subtab3, subtab4 = st.tabs([
        "🌊 Treatment Flow Analysis",
        "📈 Interval Distributions", 
        "🔍 Pattern Details",
        "📊 Summary Statistics"
    ])
    
    # Import enhanced analyzer if available
    try:
        from components.treatment_patterns.pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals
        from components.treatment_patterns.sankey_builder_enhanced import create_enhanced_sankey_with_terminals
        enhanced_available = True
    except ImportError:
        enhanced_available = False
    
    # Cache functions at module level to avoid redefinition
    @st.cache_data
    def get_cached_treatment_intervals(sim_id):
        """Cache treatment intervals calculation."""
        return results.get_treatment_intervals_df()
    
    @st.cache_data
    def get_cached_treatment_patterns(sim_id, include_terminals=False):
        """Extract and cache treatment patterns."""
        if include_terminals and enhanced_available:
            transitions_df, visits_df = extract_treatment_patterns_with_terminals(results)
        else:
            transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
        return transitions_df, visits_df
    
    with subtab1:
        # Sankey Flow Analysis (was subtab2)
        st.subheader("Patient Journey Visualisation")
        
        # Mobile device warning
        mobile_warning = """
        <script>
        function checkMobile() {
            const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent) || window.innerWidth < 768;
            if (isMobile) {
                const warning = document.getElementById('mobile-warning');
                if (warning) warning.style.display = 'block';
            }
        }
        checkMobile();
        window.addEventListener('resize', checkMobile);
        </script>
        <div id="mobile-warning" style="display: none; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 0.25rem; padding: 1rem; margin-bottom: 1rem;">
            <strong>📱 Mobile Device Detected</strong><br>
            Sankey diagrams are complex visualisations best viewed on larger screens. 
            For optimal viewing on mobile, consider rotating your device to landscape mode or viewing on a desktop/tablet.
        </div>
        """
        st.markdown(mobile_warning, unsafe_allow_html=True)
        
        
        
        # Get treatment patterns - always include terminals if available
        with st.spinner("Analyzing treatment patterns..."):
            transitions_df, visits_df = get_cached_treatment_patterns(
                results.metadata.sim_id, 
                include_terminals=enhanced_available
            )
        
        if len(transitions_df) > 0:
            # Always use enhanced version with terminal status colors if available
            if enhanced_available:
                fig = create_enhanced_sankey_with_terminals(transitions_df)
            else:
                # Fallback to basic version if enhanced not available
                fig = create_enhanced_sankey_with_colored_streams(transitions_df)
            
            # Import export configuration
            from utils.export_config import get_sankey_export_config
            config = get_sankey_export_config()
            st.plotly_chart(fig, use_container_width=True, config=config)
            
            
            # Add interpretation guide as an always-visible panel
            st.markdown("---")  # Add a visual separator
            
            # Create a nice info panel
            with st.container():
                st.markdown("### 📖 Understanding the Treatment Pattern Flow")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    **Treatment States** (from visit intervals):
                    - **Initial**: First visits in treatment sequence
                    - **Intensive**: Monthly visits (≤35 days apart)
                    - **Regular**: 6-8 week visits (36-63 days)
                    - **Extended**: 12+ week visits (64-111 days)
                    - **Maximum**: 16 week visits (112-119 days)
                    
                    **Special Patterns**:
                    - **Restarted**: Treatment resuming after gap >6 months
                    - **Discontinued**: No visits in last 6 months
                    """)
                
                with col2:
                    st.markdown("""
                    **Gap States** (treatment interruptions):
                    - **Gap (3-6m)**: 120-180 days between visits
                    - **Gap (6-12m)**: 181-365 days between visits
                    - **Gap (12m+)**: >365 days between visits
                    
                    **Visual Elements**:
                    - 🟢 **Green nodes**: Still in treatment at end
                    - 🔴 **Red node**: Discontinued treatment
                    - **Flow colors**: Based on source state
                    - **Flow thickness**: Number of patients
                    """)
                
                st.info("""
                This visualisation shows patient transitions between treatment patterns based solely on visit intervals.
                No disease state information is used, making this directly comparable to real-world data.
                """)
        else:
            st.info("""
            📊 **No treatment pattern transitions detected**
            
            This can happen when:
            - The simulation is very short (patients haven't had multiple visits yet)
            - There are too few patients to show meaningful patterns
            - All patients are still in their initial treatment phase
            
            **What you can do:**
            - Try running a longer simulation (2+ years recommended)
            - Increase the number of patients (100+ recommended)
            - Check the Summary Statistics tab to see basic treatment metrics
            
            *Note: Treatment patterns emerge over time as patients progress through different visit intervals.*
            """)
    
    with subtab2:
        st.subheader("Treatment Interval Analysis")
        
        if 'transitions_df' not in locals():
            with st.spinner("Loading treatment patterns..."):
                transitions_df, visits_df = get_cached_treatment_patterns(results.metadata.sim_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Distribution of Treatment Intervals")
            if len(transitions_df) > 0:
                interval_fig = create_interval_distribution_chart(transitions_df)
                # Apply export config
                from utils.export_config import get_export_config
                config = get_export_config(filename="treatment_intervals")
                st.plotly_chart(interval_fig, use_container_width=True, config=config)
            else:
                st.info("📊 No interval data available yet - patterns will appear as the simulation progresses")
        
        with col2:
            st.markdown("#### Patient Gap Analysis")
            if len(visits_df) > 0:
                gap_fig = create_gap_analysis_chart_tufte(visits_df)
                # Apply export config
                config = get_export_config(filename="gap_analysis")
                st.plotly_chart(gap_fig, use_container_width=True, config=config)
            else:
                st.info("📊 No visit data available yet - data will appear as patients have follow-up visits")
        
        # Calculate and show detailed statistics
        if len(visits_df) > 0:
            interval_stats = calculate_interval_statistics(visits_df)
            
            st.subheader("Detailed Interval Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Median Interval", f"{interval_stats['median']:.1f} days")
                st.metric("Min Interval", f"{interval_stats['min']:.1f} days")
            
            with col2:
                st.metric("Mean Interval", f"{interval_stats['mean']:.1f} days")
                st.metric("Max Interval", f"{interval_stats['max']:.1f} days")
            
            with col3:
                st.metric("Std Deviation", f"{interval_stats['std']:.1f} days")
                st.metric("Extended (>12 weeks)", f"{interval_stats['extended_pct']:.1f}%")
            
            with col4:
                st.metric("Treatment Gaps (>6 months)", f"{interval_stats['gap_pct']:.1f}%")
                total_visits = len(visits_df)
                st.metric("Total Visits Analyzed", f"{StyleConstants.format_count(total_visits)}")
    
    with subtab3:
        st.subheader("Treatment Pattern Details")
        
        if 'transitions_df' not in locals():
            with st.spinner("Loading treatment patterns..."):
                transitions_df, visits_df = get_cached_treatment_patterns(results.metadata.sim_id)
        
        if len(transitions_df) > 0:
            # Show top transition patterns
            st.markdown("#### Most Common Treatment Transitions")
            
            # Calculate transition frequencies
            transition_counts = transitions_df.groupby(['from_state', 'to_state']).size().reset_index(name='count')
            transition_counts = transition_counts.sort_values('count', ascending=False).head(15)
            
            # Add percentage
            total_transitions = len(transitions_df)
            transition_counts['percentage'] = (transition_counts['count'] / total_transitions * 100).round(1)
            
            # Format for display
            transition_counts['Transition'] = transition_counts['from_state'] + ' → ' + transition_counts['to_state']
            transition_counts['Count'] = transition_counts['count'].apply(StyleConstants.format_count)
            transition_counts['Percentage'] = transition_counts['percentage'].astype(str) + '%'
            
            # Display as table
            display_df = transition_counts[['Transition', 'Count', 'Percentage']]
            st.dataframe(display_df, hide_index=True, use_container_width=True)
            
            # Summary insights
            st.markdown("#### Key Insights")
            
            # Calculate some key metrics
            gap_transitions = transitions_df[transitions_df['to_state'].str.contains('Gap')].shape[0]
            restart_transitions = transitions_df[transitions_df['to_state'] == 'Restarted After Gap'].shape[0]
            discontinuation_transitions = transitions_df[transitions_df['to_state'] == 'No Further Visits'].shape[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                gap_rate = (gap_transitions / total_transitions * 100) if total_transitions > 0 else 0
                st.metric("Transitions to Gaps", f"{gap_rate:.1f}%")
            
            with col2:
                restart_rate = (restart_transitions / gap_transitions * 100) if gap_transitions > 0 else 0
                st.metric("Gap Recovery Rate", f"{restart_rate:.1f}%")
            
            with col3:
                disc_rate = (discontinuation_transitions / total_transitions * 100) if total_transitions > 0 else 0
                st.metric("No Further Visits", f"{disc_rate:.1f}%")
            
            # Patient journey length analysis
            st.markdown("#### Patient Journey Characteristics")
            
            # Count transitions per patient
            transitions_per_patient = transitions_df.groupby('patient_id').size()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Mean Transitions/Patient", f"{transitions_per_patient.mean():.1f}")
                st.metric("Max Transitions", f"{transitions_per_patient.max()}")
            
            with col2:
                st.metric("Patients with >5 Transitions", 
                         f"{(transitions_per_patient > 5).sum()} ({(transitions_per_patient > 5).sum() / len(transitions_per_patient) * 100:.1f}%)")
                st.metric("Patients with Gaps", 
                         f"{transitions_df[transitions_df['to_state'].str.contains('Gap')]['patient_id'].nunique()}")
        else:
            st.info("""
            📊 **No detailed pattern data available yet**
            
            Pattern details will appear once patients have had multiple visits and transitions between treatment states.
            Check back after running a longer simulation or with more patients.
            """)
    
    with subtab4:
        # Summary Statistics (was subtab1)
        st.subheader("Treatment Summary")
        
        # Always show full dataset statistics
        total_patients = stats['patient_count']
        total_injections = stats.get('total_injections', 0)
        mean_injections = total_injections / total_patients if total_patients > 0 else 0
        
        # Show key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Patients", f"{StyleConstants.format_count(total_patients)}")
        with col2:
            st.metric("Total Injections", f"{StyleConstants.format_count(int(total_injections))}")
        with col3:
            st.metric("Mean Injections/Patient", f"{StyleConstants.format_statistic(mean_injections)}")
        with col4:
            st.metric("Injection Rate", f"{(total_injections / (total_patients * params['duration_years'])):.1f}/year")
        
        # Get treatment intervals - cached!
        with st.spinner("Loading treatment intervals..."):
            treatment_df = get_cached_treatment_intervals(results.metadata.sim_id)
            
            if not treatment_df.empty:
                # For visualization, we might sample if it's huge
                if len(treatment_df) > 50000:
                    display_df = treatment_df.sample(n=50000, random_state=42)
                    show_sample_note = True
                else:
                    display_df = treatment_df
                    show_sample_note = False
                
                all_intervals = display_df['interval_days'].values
                
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
                
                # Show interval statistics - vectorized operations
                st.subheader("Interval Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Mean Interval", f"{np.mean(all_intervals):.1f} days")
                with col2:
                    st.metric("Median Interval", f"{np.median(all_intervals):.1f} days")
                with col3:
                    st.metric("Std Dev", f"{np.std(all_intervals):.1f} days")
                    
                if show_sample_note:
                    st.caption(f"*Histogram based on sample of 50,000 intervals from {len(treatment_df):,} total")