"""
Simplified version of the simulation_runner.py file that uses only the enhanced discontinuation chart.
"""

# This is a temporary file to show the simplified implementation
# We'll update the main simulation_runner.py to remove the fallback.

def generate_discontinuation_plot(results):
    """
    Generate plots of discontinuation types.
    
    Parameters
    ----------
    results : dict
        Simulation results
    
    Returns
    -------
    list
        List containing the enhanced discontinuation chart
    """
    # Import the enhanced implementation
    from streamlit_app.discontinuation_chart import generate_enhanced_discontinuation_plot

    # Create the enhanced chart showing discontinuation by retreatment status
    enhanced_fig = generate_enhanced_discontinuation_plot(results)

    # Return the figure in a list to maintain compatibility with the display code
    return [enhanced_fig]