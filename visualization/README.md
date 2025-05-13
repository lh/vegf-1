# Visualization System

This directory contains the standardized visualization system for creating consistent, informative visualizations following Edward Tufte's principles.

## Key Components

- **`color_system.py`** - Defines the centralized color palette and semantic color assignments
- **`visualization_templates.py`** - Contains standard templates for all visualization types
- **`acuity_viz.py`** - Specialized visualizations for visual acuity data

## Visual Grammar

Our visualization system uses a consistent visual grammar where:

1. **Colors have semantic meaning**:
   - Blue tones (`#4682B4`) for visual acuity data
   - Sage green (`#8FAD91`) for patient counts and enrollment data
   - Red (`#B22222`) reserved for critical alerts and important information

2. **Opacity (alpha) levels convey importance**:
   - High opacity (0.8) for key data elements
   - Medium opacity (0.5) for standard elements
   - Patient count elements use 0.35 opacity
   - Low opacity (0.2) for background elements
   - Very low opacity (0.1) for subtle elements

3. **Line weights and marker sizes**:
   - Data points: Small (3px) markers with thin (0.8px) lines
   - Trend lines: Moderate (1.2px) line width
   - Important indicators: Heavier lines (1.5-2.0px)

4. **Consistent patterns**:
   - Trend lines are always a darker version of the source data color
   - Patient counts always use the sage green color family
   - Visual acuity data always uses the blue color family
   - Grid lines are minimal and subtle gray

## Usage

### Basic Usage

Use the template system to create standardized visualizations:

```python
from visualization.visualization_templates import create_patient_time_visualization

# Create a standard patient time visualization
fig, ax = create_patient_time_visualization(
    data,
    time_col='weeks_since_enrollment',
    acuity_col='etdrs_letters',
    sample_size_col='patients',
    title='Visual Acuity Progression'
)
```

### Advanced Customization

You can customize visualizations while maintaining the visual grammar:

```python
from visualization.visualization_templates import create_from_template
from visualization.color_system import SEMANTIC_COLORS, ALPHAS

# Create from template with customizations
fig, ax = create_from_template(
    'patient_time',
    data=data,
    figsize=(12, 7),  # Custom figure size
    data_representation={
        'acuity_data': {
            'markersize': 4,  # Slightly larger markers
        }
    }
)
```

### Working with Colors and Alphas

Always use the centralized color and alpha definitions:

```python
from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS

# Good: Using semantic colors
plt.plot(x, y, color=SEMANTIC_COLORS['acuity_data'], alpha=ALPHAS['medium'])

# Good: Using base colors when appropriate
plt.axhline(y=baseline, color=COLORS['text_secondary'], alpha=ALPHAS['low'])

# Bad: Hard-coding colors or alpha values
plt.plot(x, y, color='#4682B4', alpha=0.5)  # Don't do this!
```

## Templates

The following standard templates are available:

1. **`patient_time`** - Visual acuity by patient time with sample size indicators
2. **`enrollment_chart`** - Patient enrollment over time
3. **`acuity_time_series`** - Visual acuity time series with trend
4. **`protocol_comparison`** - Treatment protocol comparison chart

## Adding New Templates

When adding new visualization templates:

1. Add the template definition to `TEMPLATES` in `visualization_templates.py`
2. Create a convenience function that wraps the template
3. Ensure it follows the established visual grammar
4. Document the template in this README

## Principles

All visualizations should follow these principles:

1. **Maximize the data-ink ratio** - Remove unnecessary elements
2. **Avoid chart junk** - No decorative elements that don't represent data
3. **Use consistent visual language** - Same colors, patterns across charts
4. **Make comparisons clear** - Design for the main analytical task
5. **Show causality** - Reveal relationships between variables
6. **Document sources and scales** - Always include units and data provenance