"""
Archived discontinuation visualization code from run_simulation.py
Removed on 2025-05-22 to make room for new streamgraph visualizations.

This code can be restored if needed for comparison or fallback purposes.
"""

# ==============================================================================
# ARCHIVED CODE FROM run_simulation.py display_simulation_results()
# Lines approximately 414-437
# ==============================================================================

def old_discontinuation_and_retreatment_analysis_section(results):
    """
    ARCHIVED: Old discontinuation and retreatment analysis section.
    
    This was the original visualization that showed:
    1. Patient Cohort Flow (streamgraph)
    2. Discontinuation Breakdown (bar chart)
    
    Replaced with new patient state streamgraph visualizations.
    """
    # Show discontinuation and retreatment analysis
    if "discontinuation_counts" in results:
        st.subheader("Discontinuation and Retreatment Analysis")
        figs = generate_discontinuation_plot(results)

        # Display the discontinuation charts
        if isinstance(figs, list) and len(figs) > 0:
            # Show the streamgraph first
            st.write("**Patient Cohort Flow**")
            with st.container():
                st.pyplot(figs[0])
                st.caption("Streamgraph showing patient lifecycle through treatment states")
                
            # Show the bar chart for detailed breakdown
            st.write("**Discontinuation Breakdown**")
            with st.container():
                st.pyplot(figs[1])
                st.caption("Discontinuation reasons by retreatment status")
        else:
            # Fallback in case figs is not a list (should never happen with updated code)
            st.pyplot(figs)

        # Show retreatment analysis
        display_retreatment_panel(results)

# ==============================================================================
# RELATED IMPORTS THAT MAY BECOME UNUSED:
# ==============================================================================

# From imports at top of run_simulation.py:
# from streamlit_app.simulation_runner import generate_discontinuation_plot

# ==============================================================================
# RELATED FUNCTIONS IN simulation_runner.py:
# ==============================================================================

# generate_discontinuation_plot() at line 2208
# generate_simple_discontinuation_plot() 
# Plus various streamgraph imports that may not be needed:
# - streamlit_app.realistic_streamgraph
# - streamlit_app.enhanced_streamgraph  
# - streamlit_app.discontinuation_chart

# ==============================================================================
# NOTES FOR RESTORATION:
# ==============================================================================

# To restore this functionality:
# 1. Add back the code above in display_simulation_results()
# 2. Ensure the imports for generate_discontinuation_plot are present
# 3. Make sure the streamgraph dependencies are available
# 4. Test that the visualization renders correctly

# The new approach uses:
# - create_patient_state_streamgraph.py (cumulative view)
# - create_current_state_streamgraph.py (current state view)
# These provide more clinically meaningful visualizations of patient states.

# ==============================================================================
# ARCHIVED CODE FROM retreatment_panel.py 
# Lines approximately 84-151 - "Discontinuation Reasons by Retreatment Status"
# ==============================================================================

def old_discontinuation_reasons_by_retreatment_status_section(results):
    """
    ARCHIVED: Old discontinuation reasons by retreatment status section.
    
    This section used hardcoded sample data and complex chart creation
    with multiple fallbacks. Replaced with new streamgraph visualizations.
    """
    # Create and display the discontinuation by retreatment status chart
    st.subheader("Discontinuation Reasons by Retreatment Status")
    
    # Use the sample data from the test that worked correctly
    # This uses realistic proportions that match the expected visualization
    chart_data = [
        {"reason": "Administrative", "retreatment_status": "Retreated", "count": 3}, 
        {"reason": "Administrative", "retreatment_status": "Not Retreated", "count": 11}, 
        {"reason": "Not Renewed", "retreatment_status": "Retreated", "count": 19}, 
        {"reason": "Not Renewed", "retreatment_status": "Not Retreated", "count": 108}, 
        {"reason": "Planned", "retreatment_status": "Retreated", "count": 73}, 
        {"reason": "Planned", "retreatment_status": "Not Retreated", "count": 49}, 
        {"reason": "Premature", "retreatment_status": "Retreated", "count": 299}, 
        {"reason": "Premature", "retreatment_status": "Not Retreated", "count": 246}
    ]
    
    # Create the chart
    chart_df = pd.DataFrame(chart_data)
    
    # Try to use the fixed streamgraph implementation first
    try:
        if 'visualize_retreatment_by_discontinuation_type' in globals() or 'visualize_retreatment_by_discontinuation_type' in locals():
            st.write("### Enhanced Retreatment Visualization")
            
            # Check if we have the raw data needed
            if 'raw_discontinuation_stats' in results and 'retreatments_by_type' in results['raw_discontinuation_stats']:
                # Create the enhanced visualization
                fig = visualize_retreatment_by_discontinuation_type(results)
                st.pyplot(fig)
                
                # Add a caption to explain the enhanced chart
                st.caption("This visualization shows retreatment patterns by discontinuation type using the fixed implementation.")
                
                # Skip the old chart if we've successfully shown the enhanced one
                st.write("### Standard Discontinuation Chart (Fallback)")
            else:
                # If we don't have raw data, fall back to standard chart
                st.write("### Standard Discontinuation Chart")
    except Exception as e:
        # Log the exception but continue to standard chart
        if 'DEBUG_MODE' in globals() and DEBUG_MODE:
            st.error(f"Could not create enhanced visualization: {e}")
            import traceback
            st.code(traceback.format_exc())
        
        st.write("### Standard Discontinuation Chart")
    
    try:
        # Create the chart using the imported function
        fig, ax = create_discontinuation_retreatment_chart(
            chart_df,
            title="Discontinuation Reasons by Retreatment Status",
            figsize=(10, 6),
            show_data_labels=True,
            minimal_style=True
        )
        
        # Display the chart
        st.pyplot(fig)
        
        # Add a caption to explain the chart
        st.caption("This chart shows the distribution of retreated vs. non-retreated patients for each discontinuation reason.")
    except Exception as e:
        st.error(f"Could not create visualization: {e}")
        import traceback
        st.code(traceback.format_exc())
        # Display the data in tabular format as fallback
        st.dataframe(chart_df)