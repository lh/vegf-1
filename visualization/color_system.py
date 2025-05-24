"""
Centralized color system for the visualization components.

This module defines a consistent color palette for all visualizations in the application.
Import this module to ensure consistent colors across all charts and plots.

The color system follows Edward Tufte's visualization principles with a focus on:
1. Using color semantically rather than decoratively
2. Maintaining consistent meaning for colors across different visualizations
3. Using subtle, appropriate colors that don't overwhelm the data
4. Creating a unified visual language across the application

Usage:
    from visualization.color_system import COLORS, SEMANTIC_COLORS

    # Use semantic colors for consistent meaning
    plt.bar(x, heights, color=SEMANTIC_COLORS['patient_counts'])

    # Or use named colors directly
    plt.plot(x, y, color=COLORS['primary'])
"""

# Base color palette - the source of truth for all color values
COLORS = {
    'primary': '#4682B4',    # Steel Blue - for visual acuity data
    'primary_dark': '#2a4d6e', # Darker Steel Blue - for acuity trend lines
    'secondary': '#B22222',  # Firebrick - reserved for critical information and alerts
    'tertiary': '#228B22',   # Forest Green - for additional data series
    'patient_counts': '#8FAD91',  # Muted Sage Green - for patient/sample counts
    'patient_counts_dark': '#5e7260', # Darker Sage Green - for patient count trend lines
    'background': '#FFFFFF', # White background
    'grid': '#EEEEEE',       # Very light gray for grid lines
    'text': '#333333',       # Dark gray for titles and labels
    'text_secondary': '#666666',  # Medium gray for secondary text
    'border': '#CCCCCC',     # Light gray for necessary borders
    
    # Patient state colors for streamgraph visualization
    # GREENS - Anyone being treated
    'active': '#2E7D32',      # Dark green for active treatment
    'recommencing': '#66BB6A', # Medium green for transient retreatment state
    
    # AMBER - Untreated but correctly (good outcome)
    'untreated_remission': '#FFA726', # Amber/orange for stable remission
    
    # REDS - Stopped when they shouldn't be (need distinct shades)
    'not_booked': '#EF5350',   # Light red for administrative issues
    'not_renewed': '#E53935',  # Medium red for treatment not renewed
    'premature_discontinuation': '#C62828', # Dark red for premature stop
    'discontinued_without_reason': '#B71C1C', # Very dark red for unclear discontinuation
    
    # GRAYS - Poor outcomes and death
    'stopped_poor_outcome': '#757575', # Medium gray for poor visual outcome
    'death': '#424242' # Dark gray for death (future use)
}

# Standardized alpha values for consistent transparency across visualizations
ALPHAS = {
    'high': 0.8,        # High opacity for primary data elements (e.g., trend lines)
    'medium': 0.5,      # Medium opacity for standard chart elements (e.g., bars)
    'low': 0.2,         # Low opacity for background elements
    'very_low': 0.1,    # Very low opacity for subtle elements (e.g., reference bands)
    'patient_counts': 0.35  # Consistent opacity for all patient/sample count visualizations
}

# Semantic color assignments - maps data types to specific colors
SEMANTIC_COLORS = {
    'acuity_data': COLORS['primary'],       # Blue for visual acuity data
    'acuity_trend': COLORS['primary_dark'],  # Darker blue for acuity trend lines
    'patient_counts': COLORS['patient_counts'],  # Sage Green for patient/sample counts
    'patient_counts_trend': COLORS['patient_counts_dark'],  # Darker sage green for patient count trend lines
    'critical_info': COLORS['secondary'],   # Red for critical information and alerts
    'additional_series': COLORS['tertiary'], # Green for any additional data series
    
    # Patient state colors for streamgraph visualization
    'patient_state_active': COLORS['active'],
    'patient_state_recommencing': COLORS['recommencing'],
    'patient_state_untreated_remission': COLORS['untreated_remission'],
    'patient_state_not_booked': COLORS['not_booked'],
    'patient_state_not_renewed': COLORS['not_renewed'],
    'patient_state_premature_discontinuation': COLORS['premature_discontinuation'],
    'patient_state_stopped_poor_outcome': COLORS['stopped_poor_outcome'],
    'patient_state_discontinued_without_reason': COLORS['discontinued_without_reason']
}

# Color System Design Guide Documentation
"""
Color System Design Guide
------------------------
This visualization system establishes consistent standards for both colors and opacity levels
to maintain a unified visual language across all charts and plots.

COLOR ASSIGNMENTS
----------------
Colors are assigned to specific data types regardless of chart type:

- Steel Blue (#4682B4): Visual acuity data (primary metric)
  - Use for acuity bars, lines, and markers
  - Acuity trend lines use Darker Steel Blue (#2a4d6e)

- Muted Sage Green (#8FAD91): Patient and sample counts
  - Use for enrollment bars and sample size indicators
  - Patient count trend lines use Darker Sage Green (#5e7260)
  - Selected for colorblind safety and visual complementarity

- Firebrick Red (#B22222): Reserved for alerts and critical information
  - Use sparingly to highlight important trends or thresholds
  - High visual impact should be reserved for key insights

- Trend Lines: ALWAYS use the matching darker version of the source data color
  - Acuity trend lines: SEMANTIC_COLORS['acuity_trend'] - Darker Steel Blue (#2a4d6e)
  - Patient count trend lines: SEMANTIC_COLORS['patient_counts_trend'] - Darker Sage Green (#5e7260)
  - NEVER use red for trend lines unless the data itself uses red

PATIENT STATE COLORS
------------------
Semantic color scheme for patient states in streamgraph visualizations based on clinical logic:

- GREEN SPECTRUM: Patients Currently Receiving Treatment
  - Dark Green (#2E7D32): Active patients receiving regular injections
  - Medium Green (#66BB6A): Recommencing treatment (transient state during retreatment)
  
- AMBER (#FFA726): Untreated but Correctly
  - Patients in stable remission who no longer need treatment
  - This is a GOOD outcome - deliberate clinical decision
  
- RED SPECTRUM: Stopped When They Shouldn't Be (distinct shades for different reasons)
  - Light Red (#EF5350): Not booked (administrative failure)
  - Medium Red (#E53935): Not renewed (treatment course complete but should continue)
  - Dark Red (#C62828): Premature discontinuation (stopped too early)
  - Very Dark Red (#B71C1C): Discontinued without clear reason
  
- GRAY SPECTRUM: Poor Clinical Outcomes
  - Medium Gray (#757575): Stopped due to poor visual outcome
  - Dark Gray (#424242): Death (future use)

OPACITY (ALPHA) STANDARDS
------------------------
Standardized alpha values maintain consistent visual hierarchy:

- High (0.8): Primary data elements
  - Main trend lines
  - Important markers
  - Key data points the user should focus on

- Medium (0.5): Standard chart elements
  - Regular bars in bar charts
  - Normal plot elements
  - Secondary lines

- Patient Counts (0.35): All patient count visualizations
  - Patient enrollment charts
  - Sample size indicators
  - Patient count bars

- Low (0.2): Background elements
  - Reference areas
  - Secondary/supporting data

- Very Low (0.1): Subtle elements
  - Background bands
  - Reference regions
  - Light grid lines

This consistent design language ensures users immediately understand both what data
they're viewing and its relative importance across different visualizations.
"""