"""
Visualization Templates Module

This module provides standardized visualization templates and configurations
that establish a consistent visual grammar across all application charts and graphs.

Each template defines the complete styling, layout, and parameter settings for
a specific visualization type. All application charts should be derived from
these templates to ensure consistency in:

1. Visual styling (colors, opacity, line weights, etc.)
2. Data representation (how each data type is visualized)
3. Layout patterns (axis placement, legend positioning, etc.)
4. Annotation approaches (labeling, highlighting, etc.)

Usage:
    from visualization.visualization_templates import TEMPLATES, apply_template

    # Apply a template to a figure:
    fig, ax = plt.subplots()
    apply_template('patient_time', fig, ax, data=data)

    # Or get template parameters:
    template_params = TEMPLATES['enrollment_chart']
    # Then use parameters in your custom visualization
"""

from typing import Dict, Any, Optional, Tuple, List, Union, Callable
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd

# Import our centralized styling systems
from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
from streamlit_app.utils.tufte_style import (
    set_tufte_style, style_axis, style_bar_chart, style_line,
    add_data_label, add_reference_line, add_text_annotation,
    TUFTE_COLORS
)

# ===============================================================
# Template Definitions
# ===============================================================

TEMPLATES = {
    # -------------------------------------------------------
    # Patient Time Visualization Template
    # -------------------------------------------------------
    'patient_time': {
        'description': 'Visual acuity by patient time with sample size indicators',
        'figure_params': {
            'figsize': (10, 6),
            'dpi': 100,
            'tight_layout_pad': 1.5
        },
        'data_representation': {
            'acuity_data': {
                'style': 'line_with_markers',
                'color': SEMANTIC_COLORS['acuity_data'],
                'linewidth': 0.8,
                'markersize': 3,
                'alpha': ALPHAS['low'],
            },
            'acuity_trend': {
                'style': 'line',
                'color': SEMANTIC_COLORS['acuity_trend'],
                'linewidth': 1.2,
                'alpha': ALPHAS['medium'],
            },
            'sample_size': {
                'style': 'bars',
                'color': SEMANTIC_COLORS['patient_counts'],
                'alpha': ALPHAS['patient_counts'],
                'width_ratio': 0.8,  # Percentage of bin width
            }
        },
        'axis_settings': {
            'main': {
                'ylim': (0, 85),  # Fixed range for visual acuity (ETDRS letters)
                'ylabel': 'Visual Acuity (ETDRS letters)',
                'hide_spines': ['top', 'right', 'left'],
                'grid': ['y'],
            },
            'secondary': {
                'ylabel': 'Sample Size',
                'visible_spines': [],
                'grid': False,
            }
        },
        'binning': {
            'default_width': 4,  # Default 4-week interval
            'show_bin_labels': True,
            'label_format': 'W{start}-{end}',
            'label_position': 'bottom',
        },
        'annotations': {
            'show_baseline_reference': True,
            'show_binning_explanation': True,
        }
    },

    # -------------------------------------------------------
    # Enrollment Chart Template
    # -------------------------------------------------------
    'enrollment_chart': {
        'description': 'Patient enrollment over time',
        'figure_params': {
            'figsize': (10, 5),
            'dpi': 100,
            'tight_layout_pad': 1.5
        },
        'data_representation': {
            'enrollment_bars': {
                'style': 'bars',
                'color': SEMANTIC_COLORS['patient_counts'],
                'alpha': ALPHAS['patient_counts'],
                'edgecolor': 'none',
            },
            'trend': {
                'style': 'line',
                'color': SEMANTIC_COLORS['patient_counts_trend'],
                'linewidth': 1.2,
                'alpha': ALPHAS['medium'],
                'show': True,  # Whether to display the trend line
            }
        },
        'axis_settings': {
            'main': {
                'ylabel': 'Number of Patients',
                'hide_spines': ['top', 'right', 'left'],
                'grid': ['y'],
                'xticklabel_rotation': 45,
                'xticklabel_ha': 'right',
            }
        },
        'annotations': {
            'show_total_patients': True,
        }
    },

    # -------------------------------------------------------
    # Visual Acuity Time Series Template
    # -------------------------------------------------------
    'acuity_time_series': {
        'description': 'Visual acuity time series with trend',
        'figure_params': {
            'figsize': (10, 5),
            'dpi': 100,
            'tight_layout_pad': 1.5
        },
        'data_representation': {
            'acuity_data': {
                'style': 'line_with_markers',
                'color': SEMANTIC_COLORS['acuity_data'],
                'linewidth': 1.0,
                'markersize': 4,
                'alpha': ALPHAS['medium'],
            },
            'trend': {
                'style': 'line',
                'color': SEMANTIC_COLORS['acuity_trend'],
                'linewidth': 1.2,
                'alpha': ALPHAS['medium'],
                'show': True,
            }
        },
        'axis_settings': {
            'main': {
                'ylim': (0, 85),  # Fixed range for visual acuity (ETDRS letters)
                'ylabel': 'Visual Acuity (ETDRS letters)',
                'hide_spines': ['top', 'right', 'left'],
                'grid': ['y'],
            }
        },
        'annotations': {
            'show_baseline_reference': True,
            'show_statistics': True,
        }
    },

    # -------------------------------------------------------
    # Discontinuation-Retreatment Chart Template
    # -------------------------------------------------------
    'discontinuation_retreatment': {
        'description': 'Combined chart showing discontinuation reasons and retreatment status',
        'figure_params': {
            'figsize': (10, 6),
            'dpi': 100,
            'tight_layout_pad': 1.5
        },
        'data_representation': {
            'total_bars': {
                'style': 'background_bars',
                'color': TUFTE_COLORS['grid'],
                'alpha': 0.3,
                'width_ratio': 2.5,  # Width multiplier
                'zorder': 1,  # Background
            },
            'retreated_bars': {
                'style': 'grouped_bars',
                'color': SEMANTIC_COLORS['acuity_data'],
                'alpha': ALPHAS['medium'],
                'width_ratio': 0.4,  # Width as fraction of x unit
                'position': -0.5,  # Offset from center (x - bar_width/2)
                'zorder': 2,  # Foreground
            },
            'not_retreated_bars': {
                'style': 'grouped_bars',
                'color': SEMANTIC_COLORS['patient_counts'],
                'alpha': ALPHAS['patient_counts'],
                'width_ratio': 0.4,  # Width as fraction of x unit
                'position': 0.5,  # Offset from center (x + bar_width/2)
                'zorder': 2,  # Foreground
            }
        },
        'axis_settings': {
            'main': {
                'ylabel': 'Number of patients',
                'hide_spines': ['top', 'right', 'left'],
                'grid': ['y'],
            }
        },
        'annotations': {
            'show_percentages': True,
            'show_counts': True,
            'show_explanation': True,
        },
        'legend': {
            'location': 'upper right',
            'frameon': False,
        }
    },

    # -------------------------------------------------------
    # Treatment Protocol Comparison Template
    # -------------------------------------------------------
    'protocol_comparison': {
        'description': 'Treatment protocol comparison chart',
        'figure_params': {
            'figsize': (12, 6),
            'dpi': 100,
            'tight_layout_pad': 1.5
        },
        'data_representation': {
            'protocol_a': {
                'style': 'line_with_markers',
                'color': SEMANTIC_COLORS['acuity_data'],
                'linewidth': 1.0,
                'markersize': 4,
                'alpha': ALPHAS['medium'],
                'label': 'Protocol A',
            },
            'protocol_b': {
                'style': 'line_with_markers',
                'color': SEMANTIC_COLORS['additional_series'],
                'linewidth': 1.0,
                'markersize': 4,
                'alpha': ALPHAS['medium'],
                'label': 'Protocol B',
            }
        },
        'axis_settings': {
            'main': {
                'ylim': (0, 85),  # Fixed range for visual acuity (ETDRS letters)
                'ylabel': 'Visual Acuity (ETDRS letters)',
                'hide_spines': ['top', 'right', 'left'],
                'grid': ['y'],
            }
        },
        'legend': {
            'location': 'best',
            'frameon': False,
            'fontsize': 9,
        },
        'annotations': {
            'show_significance': True,
            'significance_threshold': 0.05,
        }
    }
}


# ===============================================================
# Template Application Functions
# ===============================================================

def apply_template(template_name: str, fig, ax, data=None, **kwargs):
    """
    Apply a visualization template to a figure and axes.
    
    Parameters
    ----------
    template_name : str
        Name of the template to apply
    fig : matplotlib.figure.Figure
        Figure to apply the template to
    ax : matplotlib.axes.Axes
        Axes to apply the template to
    data : pandas.DataFrame, optional
        Data to visualize, by default None
    **kwargs : 
        Additional parameters to override template defaults
        
    Returns
    -------
    Tuple
        (fig, ax) - The styled figure and axes
        
    Raises
    ------
    ValueError
        If template_name is not found in TEMPLATES
    """
    if template_name not in TEMPLATES:
        raise ValueError(f"Template '{template_name}' not found. Available templates: {list(TEMPLATES.keys())}")
    
    template = TEMPLATES[template_name]
    
    # Apply Tufte base style
    set_tufte_style()
    
    # Apply template-specific styling
    # ...
    
    return fig, ax


def create_from_template(template_name: str, data=None, **kwargs):
    """
    Create a new visualization from a template.
    
    Parameters
    ----------
    template_name : str
        Name of the template to use
    data : pandas.DataFrame, optional
        Data to visualize, by default None
    **kwargs : 
        Additional parameters to override template defaults
        
    Returns
    -------
    Tuple
        (fig, ax) - The figure and axes with the visualization
        
    Raises
    ------
    ValueError
        If template_name is not found in TEMPLATES
    """
    if template_name not in TEMPLATES:
        raise ValueError(f"Template '{template_name}' not found. Available templates: {list(TEMPLATES.keys())}")
    
    template = TEMPLATES[template_name]
    
    # Create figure with template parameters
    figsize = kwargs.get('figsize', template['figure_params']['figsize'])
    dpi = kwargs.get('dpi', template['figure_params']['dpi'])
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Apply the template
    apply_template(template_name, fig, ax, data, **kwargs)
    
    return fig, ax


# ===============================================================
# Specific Visualization Creation Functions
# ===============================================================

def create_patient_time_visualization(data, time_col='time_weeks', acuity_col='visual_acuity',
                                     sample_size_col='sample_size', title='Mean Visual Acuity by Patient Time',
                                     **kwargs):
    """
    Create a patient time visualization from the standard template.
    
    This is a high-level wrapper around the template system that provides a 
    simpler interface for this specific visualization type.
    
    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame with patient time data
    time_col : str, optional
        Column with time data, by default 'time_weeks'
    acuity_col : str, optional
        Column with visual acuity data, by default 'visual_acuity'
    sample_size_col : str, optional
        Column with sample size data, by default 'sample_size'
    title : str, optional
        Chart title, by default 'Mean Visual Acuity by Patient Time'
    **kwargs : 
        Additional parameters to override template defaults
        
    Returns
    -------
    Tuple
        (fig, ax) - The figure and axes with the visualization
    """
    # Get the patient time template
    template = TEMPLATES['patient_time'].copy()
    
    # Override template parameters with kwargs
    for key, value in kwargs.items():
        if key in template:
            template[key] = value
    
    # Create figure and apply template
    # ...
    
    # For now, this is a placeholder. In a real implementation, this would
    # create the visualization using the template parameters.
    from streamlit_app.utils.tufte_style import create_tufte_patient_time_visualization
    return create_tufte_patient_time_visualization(
        data, 
        time_col=time_col, 
        acuity_col=acuity_col,
        sample_size_col=sample_size_col, 
        title=title,
        **kwargs
    )


def create_enrollment_chart(data, title='Patient Enrollment Over Time', **kwargs):
    """
    Create an enrollment chart from the standard template.
    
    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame with enrollment data
    title : str, optional
        Chart title, by default 'Patient Enrollment Over Time'
    **kwargs : 
        Additional parameters to override template defaults
        
    Returns
    -------
    Tuple
        (fig, ax) - The figure and axes with the visualization
    """
    # Placeholder - would implement using the template
    from streamlit_app.utils.tufte_style import create_tufte_enrollment_chart
    return create_tufte_enrollment_chart(data, title=title, **kwargs)


# Discontinuation Retreatment Chart
def create_discontinuation_retreatment_chart(data, fig=None, ax=None,
                                            title="Discontinuation Reasons and Retreatment",
                                            figsize=(10, 6)):
    """
    Create a Tufte-inspired visualization showing discontinuation reasons with retreatment overlays.

    This chart combines discontinuation reasons and retreatment status into a unified visualization
    using an "unstacked" approach:
    - Grey rectangle shows total discontinued patients for each reason
    - Blue bars show retreated patients for each discontinuation type
    - Sage green bars show non-retreated patients for each discontinuation type

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame with columns:
        - 'reason': Discontinuation reason (Administrative, Planned, etc.)
        - 'retreated': Boolean or numeric (1/0) indicating retreatment
        - 'count': Number of patients
    fig : matplotlib.figure.Figure, optional
        Existing figure to use, by default None
    ax : matplotlib.axes.Axes, optional
        Existing axis to use, by default None
    title : str, optional
        Chart title, by default "Discontinuation Reasons and Retreatment"
    figsize : tuple, optional
        Figure size (width, height) in inches, by default (10, 6)

    Returns
    -------
    tuple
        (fig, ax) - Figure and axes objects
    """
    # Apply Tufte style
    set_tufte_style()

    # Create figure and axes if not provided
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=100)

    # Prepare data
    # Calculate total for each reason
    totals = data.groupby('reason')['count'].sum().reset_index()

    # Calculate counts for retreated and not retreated
    retreated = data[data['retreated'] == True].groupby('reason')['count'].sum().reset_index()
    not_retreated = data[data['retreated'] == False].groupby('reason')['count'].sum().reset_index()

    # Set up plotting parameters
    reasons = totals['reason'].tolist()
    x = np.arange(len(reasons))
    bar_width = 0.4

    # Plot grey background rectangles for total counts
    ax.bar(x, totals['count'], width=bar_width*2.5,
           color=TUFTE_COLORS['grid'], alpha=0.3, zorder=1,
           label='Total Discontinued')

    # Plot retreated bars (blue)
    retreated_counts = [retreated[retreated['reason'] == r]['count'].values[0]
                        if r in retreated['reason'].values else 0
                        for r in reasons]

    ax.bar(x - bar_width/2, retreated_counts, width=bar_width,
          color=SEMANTIC_COLORS['acuity_data'], alpha=ALPHAS['medium'], zorder=2,
          label='Retreated')

    # Plot not retreated bars (sage green)
    not_retreated_counts = [not_retreated[not_retreated['reason'] == r]['count'].values[0]
                           if r in not_retreated['reason'].values else 0
                           for r in reasons]

    ax.bar(x + bar_width/2, not_retreated_counts, width=bar_width,
          color=SEMANTIC_COLORS['patient_counts'], alpha=ALPHAS['patient_counts'], zorder=2,
          label='Not Retreated')

    # Add percentage labels on each bar
    for i, (r_count, nr_count) in enumerate(zip(retreated_counts, not_retreated_counts)):
        total = r_count + nr_count
        if total > 0:
            # Retreated percentage
            r_pct = r_count / total * 100
            ax.annotate(f'{r_pct:.1f}%',
                      xy=(x[i] - bar_width/2, r_count/2),
                      ha='center', va='center',
                      color='white' if r_pct > 15 else TUFTE_COLORS['text'])

            # Not retreated percentage
            nr_pct = nr_count / total * 100
            ax.annotate(f'{nr_pct:.1f}%',
                      xy=(x[i] + bar_width/2, nr_count/2),
                      ha='center', va='center',
                      color='white' if nr_pct > 15 else TUFTE_COLORS['text'])

    # Add styling
    style_axis(ax)

    # Add total counts above each bar
    for i, total in enumerate(totals['count']):
        ax.annotate(f'n={total}',
                   xy=(x[i], total),
                   xytext=(0, 5),
                   textcoords='offset points',
                   ha='center', va='bottom',
                   color=TUFTE_COLORS['text_secondary'],
                   fontsize=9)

    # Add labels and formatting
    ax.set_title(title, fontsize=14, color=TUFTE_COLORS['text'])
    ax.set_ylabel('Number of patients', fontsize=10, color=TUFTE_COLORS['text_secondary'])
    ax.set_xticks(x)
    ax.set_xticklabels(reasons)

    # Add a legend
    ax.legend(frameon=False, loc='upper right')

    # Add description
    fig.text(0.02, 0.02,
            "Bar height represents patient count. Grey rectangles show total patients for each discontinuation reason.\nBlue bars show patients who retreated; sage green bars show patients who did not retreat after discontinuation.",
            fontsize=8, color=TUFTE_COLORS['text_secondary'])

    fig.tight_layout(pad=1.5)
    return fig, ax

# Add more specific visualization functions as needed