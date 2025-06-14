"""
Analysis Overview - Visualize simulation results (Vectorized for speed).
"""

import streamlit as st
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import time
import hashlib

# Import visualization mode system - no fallbacks!
from ape.utils.visualization_modes import (
    init_visualization_mode, mode_aware_figure, 
    get_mode_colors, apply_visualization_mode
)
from ape.utils.tufte_zoom_style import (
    style_axis, add_reference_line, format_zoom_legend
)
from ape.utils.style_constants import StyleConstants
from ape.utils.chart_builder import ChartBuilder
from ape.utils.export_config import render_export_settings

st.set_page_config(
    page_title="Analysis", 
    page_icon="🦍", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add parent for utils import
from ape.utils.carbon_button_helpers import top_navigation_home_button, ape_button
from ape.utils.state_helpers import get_active_simulation
from ape.components.treatment_patterns.enhanced_tab import render_enhanced_treatment_patterns_tab

# Top navigation
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if top_navigation_home_button():
        st.switch_page("APE.py")
with col2:
    st.title("Analysis")

# Initialize visualization mode selector - required!
current_mode = init_visualization_mode()

# Add export settings to sidebar
render_export_settings("sidebar")

# Check if results are available using new state helper
results_data = get_active_simulation()
if not results_data:
    # Just show centered navigation button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if ape_button("Run a Simulation", key="nav_run_sim", 
                     icon="play", full_width=True, is_primary_action=True):
            st.switch_page("pages/2_Simulations.py")
    st.stop()

results = results_data['results']
protocol = results_data['protocol']
params = results_data['parameters']

# Results header (subtle) with memorable name if available
memorable_name = ""
if hasattr(results.metadata, 'memorable_name') and results.metadata.memorable_name:
    memorable_name = f" • {results.metadata.memorable_name}"
st.caption(f"**{protocol['name']}**{memorable_name} • {params['n_patients']} patients • {params['duration_years']} years")

# Get summary statistics once and cache
@st.cache_data
def get_cached_stats(sim_id):
    """Cache summary statistics to avoid recalculation."""
    return results.get_summary_statistics()

@st.cache_data
def calculate_vision_stats_vectorized(sim_id, sample_size=None):
    """Calculate vision statistics using vectorized operations."""
    # Get vision trajectory data
    vision_df = results.get_vision_trajectory_df(sample_size=sample_size)
    
    # Use groupby to get first and last vision for each patient - MUCH faster!
    patient_stats = vision_df.groupby('patient_id')['vision'].agg(['first', 'last']).reset_index()
    
    # Extract arrays
    baseline_visions = patient_stats['first'].values
    final_visions = patient_stats['last'].values
    vision_changes = final_visions - baseline_visions
    
    return baseline_visions, final_visions, vision_changes, len(patient_stats)

stats = get_cached_stats(results.metadata.sim_id)
is_large_dataset = stats['patient_count'] > 1000

# Create tabs for different analyses - Patient Journey first as it's the most visual
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "Patient Journey Visualisation", 
    "Vision Outcomes", 
    "Patient Trajectories", 
    "Patient States",
    "Treatment Intervals",
    "Clinical Workload Analysis",
    "Pattern Details",
    "Treatment Summary",
    "Audit Trail"
])

with tab1:
    # Patient Journey Visualisation (Sankey diagram)
    st.header("Patient Journey Visualisation")
    
    # Import enhanced analyzer if available
    try:
        from ape.components.treatment_patterns.pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals
        from ape.components.treatment_patterns.sankey_builder_enhanced import create_enhanced_sankey_with_terminals
        enhanced_available = True
    except ImportError:
        enhanced_available = False
    
    from ape.components.treatment_patterns import extract_treatment_patterns_vectorized, create_enhanced_sankey_with_colored_streams
    
    @st.cache_data
    def get_cached_treatment_patterns(sim_id, include_terminals=False):
        """Get treatment patterns with backward compatibility."""
        # First check if data was pre-calculated
        cache_key = f"treatment_patterns_{sim_id}"
        
        if cache_key in st.session_state:
            data = st.session_state[cache_key]
            # Handle enhanced terminals if requested and available
            if include_terminals and 'transitions_df_with_terminals' in data:
                return data['transitions_df_with_terminals'], data['visits_df_with_terminals']
            else:
                return data['transitions_df'], data['visits_df']
        
        # Fall back to on-demand calculation (current behavior)
        if include_terminals and enhanced_available:
            transitions_df, visits_df = extract_treatment_patterns_with_terminals(results)
        else:
            transitions_df, visits_df = extract_treatment_patterns_vectorized(results)
        
        return transitions_df, visits_df
    
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
        <strong>Mobile Device Detected</strong><br>
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
        from ape.utils.export_config import get_sankey_export_config
        config = get_sankey_export_config()
        st.plotly_chart(fig, use_container_width=True, config=config)
        
        # Add interpretation guide as an always-visible panel
        st.markdown("---")  # Add a visual separator
        
        # Create a nice info panel
        with st.container():
            st.markdown("### Understanding the Treatment Pattern Flow")
            
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
                - **Green nodes**: Still in treatment at end
                - **Red node**: Discontinued treatment
                - **Flow colors**: Based on source state
                - **Flow thickness**: Number of patients
                """)
            
            st.info("""
            This visualisation shows patient transitions between treatment patterns based solely on visit intervals.
            No disease state information is used, making this directly comparable to real-world data.
            """)
    else:
        st.info("""
        **No treatment pattern transitions detected**
        
        This can happen when:
        - The simulation is very short (patients haven't had multiple visits yet)
        - There are too few patients to show meaningful patterns
        - All patients are still in their initial treatment phase
        
        **What you can do:**
        - Try running a longer simulation (2+ years recommended)
        - Increase the number of patients (100+ recommended)
        - Check the Treatment Summary tab to see basic treatment metrics
        
        *Note: Treatment patterns emerge over time as patients progress through different visit intervals.*
        """)

with tab2:
    st.header("Vision Outcomes")
    
    # Use vectorized calculation - always use all data since it's fast!
    with st.spinner(f"Calculating vision statistics for {stats['patient_count']:,} patients..."):
        baseline_visions, final_visions, vision_changes, n_patients = calculate_vision_stats_vectorized(
            results.metadata.sim_id, sample_size=None  # None = use all data
        )
    
    st.info(f"Analyzing all {stats['patient_count']:,} patients")
    
    # Vision distribution plots
    col1, col2 = st.columns(2)
    
    with col1:
        # Vision distribution chart
        chart = (ChartBuilder('Vision Distribution: Baseline vs Final')
                .with_labels(xlabel='Vision (ETDRS letters)', ylabel='Number of Patients')
                .with_vision_axis('x')
                .with_count_axis('y')
                .plot(lambda ax, colors: [
                    ax.hist(baseline_visions, bins=20, alpha=0.6, label='Baseline', 
                           color=colors['primary'], edgecolor=colors['neutral'], linewidth=1.5),
                    ax.hist(final_visions, bins=20, alpha=0.6, label='Final', 
                           color=colors['secondary'], edgecolor=colors['neutral'], linewidth=1.5)
                ])
                .with_legend(loc='upper left')
                .build())
        st.pyplot(chart.figure)
        
    with col2:
        # Vision change chart
        mean_change = np.mean(vision_changes)
        formatted_mean = StyleConstants.format_vision(mean_change)
        
        chart = (ChartBuilder('Distribution of Vision Changes')
                .with_labels(xlabel='Vision Change (ETDRS letters)', ylabel='Number of Patients')
                .with_count_axis('y')
                .plot(lambda ax, colors: 
                      ax.hist(vision_changes, bins=20, color=colors['success'], 
                             alpha=0.7, edgecolor=colors['neutral'], linewidth=1.5))
                .add_reference_line(0, 'No change', 'vertical', 'secondary')
                .add_reference_line(mean_change, f'Mean: {formatted_mean}', 'vertical', 'primary')
                .build())
        st.pyplot(chart.figure)
    
    # Summary statistics - always use full dataset stats
    st.subheader("Vision Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Use vectorized stats
        st.metric("Mean Baseline Vision", f"{StyleConstants.format_vision(np.mean(baseline_visions))} letters")
        st.metric("Std Baseline Vision", f"{StyleConstants.format_statistic(np.std(baseline_visions))} letters")
        
    with col2:
        # Always use full dataset stats from summary
        st.metric("Mean Final Vision", f"{StyleConstants.format_vision(stats.get('mean_final_vision', np.mean(final_visions)))} letters")
        st.metric("Std Final Vision", f"{StyleConstants.format_statistic(stats.get('std_final_vision', np.std(final_visions)))} letters")
        
    with col3:
        # Use vectorized stats
        st.metric("Mean Vision Change", f"{StyleConstants.format_vision(mean_change)} letters")
        st.metric("Patients Improved", f"{StyleConstants.format_count(np.sum(vision_changes > 0))}/{StyleConstants.format_count(len(vision_changes))}")


with tab3:
    st.header("Patient Trajectories")
    
    # For trajectories, we always need to sample for readability
    default_n_sample = 20
    max_sample = min(100, stats['patient_count'])
    
    # Add a slider for number of trajectories to show
    n_sample = st.slider(
        "Number of patient trajectories to display:",
        min_value=5,
        max_value=max_sample,
        value=default_n_sample,
        step=5,
        help="Showing too many trajectories makes the plot unreadable"
    )
    
    with st.spinner(f"Loading {n_sample} patient trajectories..."):
        vision_df_sample = results.get_vision_trajectory_df(sample_size=n_sample)
    
    # Vision trajectories with better x-axis
    def plot_trajectories(ax, colors):
        # Use different alpha and linewidth based on mode
        alpha = 0.6 if current_mode == 'presentation' else 0.4
        lw = 2 if current_mode == 'presentation' else 1
        
        # Group by patient_id once
        grouped = vision_df_sample.groupby('patient_id')
        
        for i, (patient_id, patient_data) in enumerate(grouped):
            patient_data = patient_data.sort_values('time_days')
            
            # Convert days to months for display
            months = patient_data['time_days'].values / 30.0
            visions = patient_data['vision'].values
            
            # Use a color cycle for better visibility
            if n_sample <= 20:
                # Use distinct colors for small samples
                color = plt.cm.tab10(i % 10)
            else:
                # Use gradient for larger samples
                color = plt.cm.viridis(i / n_sample)
            
            ax.plot(months, visions, alpha=alpha, linewidth=lw, color=color)
    
    # Create custom chart that uses months directly
    fig, ax = mode_aware_figure(f'Vision Trajectories ({n_sample} patients)')
    colors = get_mode_colors()
    
    # Plot the trajectories
    plot_trajectories(ax, colors)
    
    # Style the plot (title already set by mode_aware_figure)
    ax.set_xlabel('Time (months)')
    ax.set_ylabel('Vision (ETDRS letters)')
    
    # Set vision scale
    ax.set_ylim(0, 100)
    ax.set_yticks(StyleConstants.get_vision_ticks())
    
    # Set time scale with proper month ticks
    max_months = vision_df_sample['time_days'].max() / 30.0
    
    # Create clean month ticks
    if max_months <= 12:
        # Monthly ticks for first year
        month_ticks = list(range(0, int(max_months) + 1, 1))
    elif max_months <= 24:
        # Every 2 months for up to 2 years
        month_ticks = list(range(0, int(max_months) + 1, 2))
    elif max_months <= 60:
        # Every 6 months for up to 5 years
        month_ticks = list(range(0, int(max_months) + 1, 6))
    else:
        # Yearly for longer simulations
        month_ticks = list(range(0, int(max_months) + 1, 12))
    
    ax.set_xticks(month_ticks)
    ax.set_xlim(0, max_months)
    
    # Apply styling
    style_axis(ax)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Add trajectory statistics - vectorized!
    st.subheader("Trajectory Summary")
    
    # Calculate trajectory changes using vectorized operations
    trajectory_changes = vision_df_sample.groupby('patient_id')['vision'].agg(['first', 'last'])
    trajectory_changes['change'] = trajectory_changes['last'] - trajectory_changes['first']
    
    trajectories_improving = (trajectory_changes['change'] > 5).sum()
    trajectories_stable = ((trajectory_changes['change'] >= -5) & (trajectory_changes['change'] <= 5)).sum()
    trajectories_worsening = (trajectory_changes['change'] < -5).sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Improving (>5 letters)", trajectories_improving)
    with col2:
        st.metric("Stable (±5 letters)", trajectories_stable)
    with col3:
        st.metric("Worsening (>5 letters loss)", trajectories_worsening)
    
    st.caption(f"*Showing {n_sample} of {stats['patient_count']:,} total patients")

with tab4:
    st.header("Patient Treatment Flow")
    st.markdown("Comprehensive view of patient cohort flow through different treatment states over time.")
    
    # Import cache helper
    from ape.components.treatment_patterns.time_series_cache import should_show_week_resolution
    
    # Use the new comprehensive streamgraph
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # Determine available resolutions based on data size
        n_patients = results.metadata.n_patients
        duration_years = results.metadata.duration_years
        
        if should_show_week_resolution(n_patients, duration_years):
            resolution_options = ["month", "week", "quarter"]
            resolution_help = "Choose time resolution"
        else:
            resolution_options = ["month", "quarter"]
            resolution_help = f"Week resolution disabled for performance (large dataset)"
        
        time_resolution = st.radio(
            "Time Resolution",
            resolution_options,
            index=0,
            key="time_res",
            help=resolution_help
        )
        
        normalize = st.checkbox(
            "Show as Percentage",
            value=False,
            help="Display as percentage of total patients"
        )
    
    # Create the comprehensive visualization
    with st.spinner("Analyzing patient treatment journeys..."):
        # Import the new comprehensive streamgraph
        from ape.visualizations.streamgraph_treatment_states import create_treatment_state_streamgraph
        
        # Cache based on simulation ID
        @st.cache_data
        def get_comprehensive_streamgraph(sim_id: str, time_res: str, norm: bool):
            return create_treatment_state_streamgraph(results, time_res, normalize=norm)
        
        fig = get_comprehensive_streamgraph(results.metadata.sim_id, time_resolution, normalize)
    
    # Display the Plotly figure
    with col1:
        # Apply export config
        from ape.utils.export_config import get_export_config
        config = get_export_config(filename="patient_treatment_flow")
        st.plotly_chart(fig, use_container_width=True, config=config)
    
    # Show detailed statistics
    with st.expander("Detailed Statistics"):
        from ape.visualizations.streamgraph_comprehensive import calculate_patient_cohort_flow
        states_df, summary_stats = calculate_patient_cohort_flow(results, time_resolution)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Patients", summary_stats['total_patients'])
        with col2:
            st.metric("Total Discontinuations", summary_stats['total_discontinuations'])
        with col3:
            st.metric("Total Retreatments", summary_stats['total_retreatments'])
        
        if summary_stats.get('discontinuation_breakdown'):
            st.write("**Discontinuation Breakdown:**")
            for disc_type, count in summary_stats['discontinuation_breakdown'].items():
                pct = (count / summary_stats['total_patients']) * 100
                st.write(f"- {disc_type}: {count} ({pct:.1f}%)")
    
    # Add note about patient conservation
    st.caption("*Patient counts are conserved throughout the simulation - total always equals initial population.")

with tab5:
    # Treatment Intervals tab (from subtab2 of Treatment Patterns)
    st.header("Treatment Intervals")
    
    st.markdown("""
    This analysis shows **treatment pattern transitions** - when patients move between different 
    treatment intensities (e.g., from monthly to bi-monthly visits). Each data point represents 
    a **change in treatment pattern**, not every individual visit.
    
    **Use this view to understand:**
    - How treatment patterns evolve over time
    - Treatment adherence and protocol compliance
    - When patients transition to less frequent visits
    """)
    
    # Import needed functions
    from ape.components.treatment_patterns import (
        create_interval_distribution_chart,
        create_gap_analysis_chart_tufte,
        calculate_interval_statistics
    )
    
    # Reuse cached treatment patterns if available
    if 'transitions_df' not in locals() or 'visits_df' not in locals():
        with st.spinner("Loading treatment patterns..."):
            transitions_df, visits_df = get_cached_treatment_patterns(results.metadata.sim_id)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribution of Treatment Intervals")
        if len(transitions_df) > 0:
            interval_fig = create_interval_distribution_chart(transitions_df)
            # Apply export config
            from ape.utils.export_config import get_export_config
            config = get_export_config(filename="treatment_intervals")
            st.plotly_chart(interval_fig, use_container_width=True, config=config)
        else:
            st.info("No interval data available yet - patterns will appear as the simulation progresses")
    
    with col2:
        st.subheader("Patient Gap Analysis")
        if len(visits_df) > 0:
            gap_fig = create_gap_analysis_chart_tufte(visits_df)
            # Apply export config
            config = get_export_config(filename="gap_analysis")
            st.plotly_chart(gap_fig, use_container_width=True, config=config)
        else:
            st.info("No visit data available yet - data will appear as patients have follow-up visits")
    
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
            if 'p25' in interval_stats:
                st.metric("25th Percentile", f"{interval_stats['p25']:.1f} days")
        
        with col4:
            if 'p75' in interval_stats:
                st.metric("75th Percentile", f"{interval_stats['p75']:.1f} days")
            total_visits = len(visits_df)
            st.metric("Total Visits Analyzed", f"{StyleConstants.format_count(total_visits)}")

with tab6:
    # Clinical Workload Analysis (new tab)
    st.header("Clinical Workload Attribution Analysis")
    
    st.markdown("""
    This analysis shows how different patient treatment intensity patterns contribute to clinical workload.
    Understanding this helps optimise resource allocation and identify high-impact patient segments.
    """)
    
    # Import workload analysis components
    from ape.components.treatment_patterns.workload_analyzer_optimized import calculate_clinical_workload_attribution, format_workload_insight
    from ape.components.treatment_patterns.workload_visualizations_optimized import (
        create_dual_bar_chart, create_bubble_chart, 
        create_impact_pyramid, get_workload_insight_summary
    )
    workload_available = True
    
    if workload_available:
        # Get visits data for workload analysis
        if 'visits_df' not in locals():
            with st.spinner("Loading visit data..."):
                # Try to get visits from results
                if hasattr(results, 'get_visits_df'):
                    visits_df = results.get_visits_df()
                else:
                    st.error("Visit data not available in simulation results")
                    visits_df = pd.DataFrame()
        
        if not visits_df.empty:
            # Run workload analysis with caching
            @st.cache_data(show_spinner="Analysing clinical workload attribution...")
            def get_cached_workload_data(visits_df_hash):
                """Cache the expensive workload calculation."""
                return calculate_clinical_workload_attribution(visits_df)
            
            # Create a hash of the visits data for cache key
            # Use only relevant columns to avoid cache misses from unrelated changes
            cache_cols = ['patient_id', 'time_days', 'interval_days'] if 'interval_days' in visits_df.columns else ['patient_id', 'time_days']
            visits_hash = hashlib.md5(
                pd.util.hash_pandas_object(visits_df[cache_cols], index=False).values.tobytes()
            ).hexdigest()[:8]
            
            workload_data = get_cached_workload_data(visits_hash)
            
            if workload_data['summary_stats']:
                # Show key insight at the top
                st.success(f"**Key Insight:** {format_workload_insight(workload_data['summary_stats'])}")
                
                # Visualization selection using Carbon buttons
                st.markdown("#### Choose Visualisation Approach")
                
                # Import Carbon button helpers
                from ape.utils.carbon_button_helpers import ape_button
                
                # Initialize session state for visualization selection if not exists
                if 'workload_viz_type' not in st.session_state:
                    st.session_state.workload_viz_type = 'bar'
                
                # Create button columns
                col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
                
                with col1:
                    if ape_button(
                        label="Bar",
                        key="workload_bar_btn",
                        button_type="primary" if st.session_state.workload_viz_type == 'bar' else "secondary",
                        full_width=True
                    ):
                        st.session_state.workload_viz_type = 'bar'
                
                with col2:
                    if ape_button(
                        label="Pyramid",
                        key="workload_pyramid_btn",
                        button_type="primary" if st.session_state.workload_viz_type == 'pyramid' else "secondary",
                        full_width=True
                    ):
                        st.session_state.workload_viz_type = 'pyramid'
                
                with col3:
                    if ape_button(
                        label="Bubble",
                        key="workload_bubble_btn",
                        button_type="primary" if st.session_state.workload_viz_type == 'bubble' else "secondary",
                        full_width=True
                    ):
                        st.session_state.workload_viz_type = 'bubble'
                
                # Get selected option
                viz_option = st.session_state.workload_viz_type
                
                # Pre-create all visualizations (cached)
                from ape.utils.export_config import get_export_config
                tufte_mode = True  # Use clean styling
                
                # Cache key includes both sim_id and workload data hash
                import json
                
                # Create a hash of the workload data for cache key
                workload_hash = hashlib.md5(
                    json.dumps(
                        {k: len(v) if isinstance(v, (list, dict, pd.DataFrame)) else v 
                         for k, v in workload_data.items()}, 
                        sort_keys=True
                    ).encode()
                ).hexdigest()[:8]
                
                @st.cache_data(show_spinner="Creating all visualizations...", ttl=300)
                def get_all_workload_visualizations_v6(_workload_data, _tufte_mode, cache_key):
                    """Create all workload visualizations once and cache them."""
                    figs = {}
                    figs['bar'] = create_dual_bar_chart(_workload_data, _tufte_mode)
                    figs['pyramid'] = create_impact_pyramid(_workload_data, _tufte_mode)
                    figs['bubble'] = create_bubble_chart(_workload_data, _tufte_mode)
                    return figs
                
                # Get all figures (cached after first creation)
                all_figs = get_all_workload_visualizations_v6(workload_data, tufte_mode, workload_hash)
                
                # Display selected visualization
                if viz_option == 'bar':
                    st.subheader("Clinical Workload Attribution: Patient Distribution vs Visit Volume")
                    config = get_export_config(filename="clinical_workload_bar")
                    st.plotly_chart(all_figs['bar'], use_container_width=True, config=config)
                    
                    st.markdown("""
                    **Understanding the Dual Bar Chart:**
                    - Light bars show percentage of patients in each category
                    - Dark bars show percentage of visits generated by each category
                    - Categories where dark bars exceed light bars have high workload intensity
                    """)
                
                elif viz_option == 'pyramid':
                    st.subheader("Clinical Impact Pyramid: From Patients to Workload")
                    config = get_export_config(filename="clinical_workload_pyramid")
                    st.plotly_chart(all_figs['pyramid'], use_container_width=True, config=config)
                    
                    st.markdown("""
                    **Understanding the Impact Pyramid:**
                    - Left funnel shows patient distribution across categories
                    - Right funnel shows visit volume generated by each category
                    - Compare funnel shapes to see workload concentration effects
                    """)
                
                elif viz_option == 'bubble':
                    st.subheader("Workload Impact")
                    
                    # Create columns for chart and explanation
                    col1, col2 = st.columns([3, 2])  # 60/40 split
                    
                    with col1:
                        config = get_export_config(filename="clinical_workload_bubble")
                        st.plotly_chart(all_figs['bubble'], use_container_width=True, config=config)
                    
                    with col2:
                        st.markdown("### Reading the Chart")
                        st.markdown("""
                        **Axes:**
                        - **X**: % of patients in category
                        - **Y**: % of visits generated
                        
                        **Visual elements:**
                        - **Bubble size**: Workload intensity (visits per patient)
                        - **Diagonal line**: Proportional workload (1:1 ratio)
                        
                        **Interpretation:**
                        - Points **above** the line: High-intensity patients requiring disproportionate clinical time
                        - Points **below** the line: Lower-intensity patients requiring fewer visits
                        - **Larger bubbles** = Higher workload intensity (more visits per patient)
                        """)
                        
                        # Add category legend if useful
                        with st.expander("Category colours"):
                            for category, definition in workload_data['category_definitions'].items():
                                if category in workload_data['summary_stats']:
                                    color = definition['color']
                                    st.markdown(
                                        f"<div style='display: flex; align-items: center;'>"
                                        f"<div style='width: 20px; height: 20px; background-color: {color}; "
                                        f"border-radius: 50%; margin-right: 10px;'></div>"
                                        f"<span>{category}</span></div>",
                                        unsafe_allow_html=True
                                    )
                
                # Show detailed summary insights
                st.markdown("---")
                st.markdown("#### Detailed Analysis")
                
                # Create summary insight
                insight_summary = get_workload_insight_summary(workload_data)
                st.markdown(insight_summary)
                
                # Show category breakdown in an expandable section
                with st.expander("View Detailed Category Breakdown"):
                    # Create a summary table
                    summary_data = []
                    for category, stats in workload_data['summary_stats'].items():
                        summary_data.append({
                            'Category': category,
                            'Patients': f"{stats['patient_count']} ({stats['patient_percentage']:.1f}%)",
                            'Visits': f"{stats['visit_count']} ({stats['visit_percentage']:.1f}%)",
                            'Visits/Patient': f"{stats['visits_per_patient']:.1f}",
                            'Workload Intensity': f"{stats['workload_intensity']:.1f}x"
                        })
                    
                    summary_df = pd.DataFrame(summary_data)
                    summary_df = summary_df.sort_values('Workload Intensity', 
                                                      key=lambda x: x.str.replace('x', '').astype(float), 
                                                      ascending=False)
                    
                    st.dataframe(summary_df, hide_index=True, use_container_width=True)
                    
                    # Category definitions reference
                    st.markdown("**Category Definitions:**")
                    definitions = workload_data['category_definitions']
                    for category, definition in definitions.items():
                        if category in workload_data['summary_stats']:
                            st.markdown(f"- **{category}**: {definition['description']}")
            
            else:
                st.info("No workload analysis available - insufficient visit data with intervals")
        
        else:
            st.info("No visit data available for workload analysis")

with tab7:
    # Pattern Details tab (from subtab3 of Treatment Patterns)
    st.header("Pattern Details")
    
    # Reuse cached treatment patterns if available
    if 'transitions_df' not in locals() or 'visits_df' not in locals():
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
        **No detailed pattern data available yet**
        
        Pattern details will appear once patients have had multiple visits and transitions between treatment states.
        Check back after running a longer simulation or with more patients.
        """)

with tab8:
    # Treatment Summary tab (from subtab4 of Treatment Patterns)
    st.header("Treatment Summary")
    
    st.markdown("""
    This analysis shows the **raw distribution of all visit intervals** - the actual time between 
    every consecutive pair of visits for all patients. This includes all visits, not just pattern 
    changes.
    
    **Use this view to understand:**
    - Actual clinic visit frequency and workload
    - True distribution of treatment intervals
    - Overall treatment burden across the patient population
    """)
    
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
    
    # Cache functions for treatment intervals
    @st.cache_data
    def get_cached_treatment_intervals(sim_id):
        """Cache treatment intervals calculation."""
        return results.get_treatment_intervals_df()
    
    # Get treatment intervals - cached!
    with st.spinner("Loading treatment intervals..."):
        intervals_df = get_cached_treatment_intervals(results.metadata.sim_id)
    
    if len(intervals_df) > 0:
        # Extract just the numeric intervals
        intervals = intervals_df['interval_days'].values
        
        # Interval distribution summary
        st.subheader("Treatment Interval Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Mean Interval", f"{StyleConstants.format_statistic(np.mean(intervals))} days")
        with col2:
            st.metric("Median Interval", f"{StyleConstants.format_statistic(np.median(intervals))} days")
        with col3:
            st.metric("Min Interval", f"{int(np.min(intervals))} days")
        with col4:
            st.metric("Max Interval", f"{int(np.max(intervals))} days")
        
        # Visualize interval distribution with Tufte-compliant chart
        from ape.components.treatment_patterns.interval_visualization import (
            create_interval_distribution_tufte, create_interval_summary_table
        )
        
        # Create the interval distribution chart
        interval_fig = create_interval_distribution_tufte(intervals)
        config = get_export_config(filename="treatment_intervals_distribution")
        st.plotly_chart(interval_fig, use_container_width=True, config=config)
        
        # Optionally show detailed statistics table
        with st.expander("View Detailed Statistics"):
            stats_fig = create_interval_summary_table(intervals_df)
            st.plotly_chart(stats_fig, use_container_width=True, config=config)
    else:
        st.info("No treatment intervals found - data will appear as patients have follow-up visits.")

with tab9:
    st.header("Audit Trail")
    st.markdown("Complete parameter tracking and simulation events.")
    
    # Get audit trail from active simulation data
    audit_log = results_data.get('audit_trail')
    if audit_log:
        
        # Display audit events
        for i, event in enumerate(audit_log):
            with st.expander(f"{event['event']} - {event['timestamp']}", expanded=(i==0)):
                # Format the event data nicely
                if event['event'] == 'protocol_loaded':
                    st.json(event['protocol'])
                elif event['event'] == 'simulation_start':
                    st.write(f"**Engine:** {event['engine_type']}")
                    st.write(f"**Patients:** {event['n_patients']}")
                    st.write(f"**Duration:** {event['duration_years']} years")
                    st.write(f"**Seed:** {event['seed']}")
                    st.write(f"**Protocol:** {event['protocol_name']} v{event['protocol_version']}")
                    st.code(f"Checksum: {event['protocol_checksum']}")
                elif event['event'] == 'simulation_complete':
                    st.write(f"**Total Injections:** {StyleConstants.format_count(event['total_injections'])}")
                    st.write(f"**Mean Final Vision:** {StyleConstants.format_vision(event['final_vision_mean'])}")
                    st.write(f"**Discontinuation Rate:** {StyleConstants.format_percentage(event['discontinuation_rate'])}")
                else:
                    st.json(event)
        
        # Download audit trail
        import json
        audit_json = json.dumps(audit_log, indent=2)
        st.download_button(
            label="📥 Download Full Audit Trail",
            data=audit_json,
            file_name=f"audit_trail_{params['engine']}_{params['n_patients']}p_{params['duration_years']}y.json",
            mime="application/json"
        )
    else:
        st.info("No audit trail available for this session.")
    
    # Export functionality removed - now in Simulations page