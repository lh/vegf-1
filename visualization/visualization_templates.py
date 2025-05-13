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
    add_data_label, add_reference_line, add_text_annotation
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


# Add more specific visualization functions as needed