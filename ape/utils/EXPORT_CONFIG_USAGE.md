# Export Configuration Usage Guide

## Overview
The export configuration system provides a centralized way to manage export formats across all visualizations in the APE application.

## Basic Usage

### 1. Import the utilities
```python
from utils.export_config import get_export_config, render_export_settings
```

### 2. Add export settings to your page
```python
# In sidebar (recommended)
render_export_settings("sidebar")

# Or in main content area
render_export_settings("main")
```

### 3. Apply to any Plotly chart
```python
# Get configuration with defaults
config = get_export_config()

# Or specify custom dimensions
config = get_export_config(
    filename="my_custom_chart",
    width=1200,
    height=800
)

# Apply to chart
st.plotly_chart(fig, use_container_width=True, config=config)
```

## Format Options

Users can select from:
- **PNG**: Universal compatibility, good for presentations
- **SVG**: Vector format, perfect for publications
- **JPEG**: Compressed format, good for web
- **WebP**: Modern format with best compression

## Advanced Features

### Format-specific options
- PNG exports include a quality scale slider (1x-4x)
- SVG exports use web-safe fonts for compatibility

### Pre-configured exports for common charts
```python
from utils.export_config import (
    get_sankey_export_config,
    get_line_chart_export_config,
    get_heatmap_export_config
)

# Use pre-configured settings
config = get_sankey_export_config()
```

## Integration Examples

### Line Chart (Visual Acuity)
```python
fig = create_visual_acuity_chart(data)
config = get_line_chart_export_config()
st.plotly_chart(fig, config=config)
```

### Heatmap
```python
fig = create_treatment_heatmap(data)
config = get_heatmap_export_config()
st.plotly_chart(fig, config=config)
```

### Custom Chart
```python
fig = create_custom_visualization(data)
config = get_export_config(
    filename="custom_viz",
    width=1600,
    height=900
)
st.plotly_chart(fig, config=config)
```

## Benefits

1. **Consistency**: All charts use the same export interface
2. **User Control**: Users can choose their preferred format
3. **Quality**: Format-specific optimizations ensure best output
4. **Reusability**: Centralized configuration reduces code duplication
5. **Extensibility**: Easy to add new formats or options

## Session State

The system uses Streamlit session state to persist user preferences:
- `st.session_state.export_format`: Current format (default: 'png')
- `st.session_state.export_scale`: PNG quality scale (default: 2.0)

## Tips

- Place `render_export_settings()` early in your sidebar for consistency
- Use descriptive filenames for better user experience
- Consider the use case when setting default dimensions
- SVG is best for publications and vector editing
- PNG for presentations and quick sharing
- Higher PNG scale = better quality but larger files