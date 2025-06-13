# Sankey Diagram Customization Guide

## Overview

Plotly's Sankey diagrams offer extensive customization options. This guide documents all available controls and shows how to manipulate appearance both during initial rendering and interactively.

## 1. Node Customization

### Current Implementation
```python
node=dict(
    pad=40,              # Space between nodes
    thickness=20,        # Width of node rectangles
    line=dict(           # Node border
        color="black", 
        width=1
    ),
    label=[...],         # Node labels
    color=[...],         # Node colors
    hoverlabel=dict(     # Hover text styling
        font=dict(color='black')
    )
)
```

### Additional Node Options

```python
node=dict(
    # Positioning
    pad=40,              # Vertical space between nodes (pixels)
    thickness=20,        # Node rectangle width (pixels)
    
    # Node appearance
    color=[...],         # List of colors (hex, rgb, rgba)
    line=dict(
        color=[...],     # Can be list for individual borders
        width=[...],     # Can be list for individual widths
    ),
    
    # Labels
    label=[...],         # Text labels
    customdata=[...],    # Extra data for hover/click
    hovertemplate=[...], # Custom hover text per node
    hoverlabel=dict(
        bgcolor="white",
        bordercolor="black",
        font=dict(
            family="Arial",
            size=13,
            color="black"
        )
    ),
    
    # Positioning control
    x=[...],            # Normalized x positions (0-1)
    y=[...],            # Normalized y positions (0-1)
    # Note: x,y override automatic layout
)
```

## 2. Link (Flow) Customization

### Current Implementation
```python
link=dict(
    source=[...],        # Source node indices
    target=[...],        # Target node indices
    value=[...],         # Flow values
    color="rgba(100, 100, 100, 0.2)"  # Single color
)
```

### Additional Link Options

```python
link=dict(
    # Required
    source=[...],
    target=[...],
    value=[...],
    
    # Appearance
    color=[...],         # Can be list for individual colors
    line=dict(
        color=[...],     # Border color for flows
        width=0.5        # Border width
    ),
    
    # Hover customization
    customdata=[...],    # Extra data per link
    hovertemplate=[...], # Custom hover text per link
    hoverlabel=dict(
        bgcolor="white",
        bordercolor="black",
        font=dict(size=12)
    ),
    
    # Labels on flows (new in recent versions)
    label=[...],         # Text labels on flows
    
    # Curvature control
    # Note: Limited in Sankey compared to other diagrams
)
```

## 3. Layout Arrangements

### Available Arrangements

```python
go.Sankey(
    # Arrangement options
    arrangement='snap',      # Default: optimized layout
    # arrangement='perpendicular',  # Flows at right angles
    # arrangement='freeform',       # Manual positioning
    # arrangement='fixed',          # Use provided x,y coordinates
    
    # Orientation
    orientation='h',     # Horizontal (default)
    # orientation='v',   # Vertical
    
    # Text positioning
    textfont=dict(
        size=12,
        color='#333333',
        family='Arial'
    ),
    
    # Value formatting
    valueformat='.0f',   # Number format for values
    valuesuffix=' patients',  # Suffix for values
)
```

## 4. Interactive Features

### Built-in Interactivity

1. **Hover Effects**
   - Node highlighting
   - Flow path highlighting
   - Custom tooltips

2. **Click Events** (requires JavaScript callback)
   ```python
   fig.update_traces(
       node_clicktolink=dict(
           # Define click behavior
       )
   )
   ```

3. **Zoom and Pan**
   - Enabled by default in Plotly
   - Can be disabled if needed

### Dynamic Updates

```python
# Update colors dynamically
fig.update_traces(
    node_color=[new_colors],
    link_color=[new_link_colors]
)

# Update positions
fig.update_traces(
    node_x=[new_x_positions],
    node_y=[new_y_positions]
)
```

## 5. Advanced Styling Options

### Gradient and Pattern Support

```python
# Gradient colors for links
link_colors = []
for i, row in flow_counts.iterrows():
    # Create gradient effect
    opacity = min(0.8, max(0.2, row['count'] / total_flow * 20))
    color = f'rgba({r}, {g}, {b}, {opacity})'
    link_colors.append(color)
```

### Multi-level Sankey

```python
# Add intermediate calculation nodes
# Useful for showing transformations
intermediate_nodes = create_intermediate_states(data)
nodes.extend(intermediate_nodes)
```

## 6. Responsive Design

### Current Implementation
```python
st.plotly_chart(fig, use_container_width=True)
```

### Additional Responsive Options

```python
fig.update_layout(
    # Responsive sizing
    autosize=True,
    
    # Minimum dimensions
    minreducedwidth=250,
    minreducedheight=250,
    
    # Breakpoints for different screen sizes
    updatemenus=[{
        'buttons': [
            {'label': 'Desktop', 'method': 'relayout', 
             'args': [{'height': 800}]},
            {'label': 'Mobile', 'method': 'relayout', 
             'args': [{'height': 400}]}
        ]
    }]
)
```

## 7. Performance Optimization

### For Large Datasets

```python
# Filter small flows
min_flow_size = max(1, len(transitions_df) * 0.001)
flow_counts = flow_counts[flow_counts['count'] >= min_flow_size]

# Aggregate similar paths
flow_counts = aggregate_similar_flows(flow_counts)

# Limit node count
if len(unique_nodes) > 50:
    nodes = prioritize_important_nodes(nodes, max_nodes=50)
```

## 8. Export Options

### Static Images
```python
# High-resolution export
fig.write_image("sankey.png", width=1920, height=1080, scale=2)

# Vector format
fig.write_image("sankey.svg")
```

### Interactive HTML
```python
# Standalone HTML
fig.write_html("sankey.html", include_plotlyjs='cdn')

# With custom config
config = {
    'toImageButtonOptions': {
        'format': 'svg',
        'filename': 'treatment_patterns',
        'height': 800,
        'width': 1200,
        'scale': 1
    }
}
fig.show(config=config)
```

## 9. Accessibility Features

```python
# Add ARIA labels
fig.update_layout(
    title=dict(
        text="Treatment Pattern Flow",
        font=dict(size=16),
        # Add screen reader description
        subtitle="Sankey diagram showing patient treatment transitions"
    )
)

# High contrast mode
if high_contrast_mode:
    fig.update_traces(
        node_line_width=2,
        link_line=dict(width=1, color="black")
    )
```

## 10. Animation Possibilities

While Sankey diagrams don't support native Plotly animations, you can:

1. **Transition between states**
   ```python
   # Create multiple figures
   frames = create_time_series_sankeys(data, time_points)
   
   # Use Streamlit columns or tabs
   for i, frame in enumerate(frames):
       st.plotly_chart(frame)
   ```

2. **Gradual reveal**
   ```python
   # Add flows progressively
   for i in range(len(flow_counts)):
       subset = flow_counts[:i+1]
       fig = create_sankey(subset)
       placeholder.plotly_chart(fig)
       time.sleep(0.5)
   ```

## Example: Fully Customized Sankey

```python
def create_custom_sankey(transitions_df):
    """Create a highly customized Sankey diagram."""
    
    # Custom color scheme
    node_colors = {
        'Initial': '#3498db',      # Bright blue
        'Active': '#2ecc71',       # Green
        'Gap': '#f39c12',          # Orange
        'Terminal': '#95a5a6'      # Gray
    }
    
    # Create figure with all options
    fig = go.Figure(data=[go.Sankey(
        # Layout
        arrangement='snap',
        orientation='h',
        
        # Nodes
        node=dict(
            pad=50,
            thickness=25,
            line=dict(
                color=[get_border_color(n) for n in nodes],
                width=[2 if is_important(n) else 1 for n in nodes]
            ),
            label=[format_label(n) for n in nodes],
            color=[node_colors.get(get_category(n), '#cccccc') for n in nodes],
            x=[calculate_x_position(n) for n in nodes],
            y=[calculate_y_position(n) for n in nodes],
            hovertemplate='%{label}<br>%{value} patients<br>%{customdata}<extra></extra>',
            customdata=[get_node_details(n) for n in nodes]
        ),
        
        # Links
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=[get_flow_color(s, t, v) for s, t, v in zip(sources, targets, values)],
            line=dict(color="rgba(0,0,0,0.1)", width=0.5),
            hovertemplate='%{source.label} → %{target.label}<br>%{value} patients (%{customdata})<extra></extra>',
            customdata=[f"{v/total*100:.1f}%" for v in values]
        ),
        
        # Text
        textfont=dict(
            size=14,
            color='#2c3e50',
            family='Helvetica, Arial, sans-serif'
        ),
        
        # Value display
        valueformat=',.0f',
        valuesuffix=' patients'
    )])
    
    # Enhanced layout
    fig.update_layout(
        title=dict(
            text="Patient Treatment Pathways",
            font=dict(size=20, color='#2c3e50', family='Helvetica'),
            x=0.5,
            xanchor='center'
        ),
        font=dict(size=12),
        height=900,
        margin=dict(l=20, r=200, t=60, b=40),
        paper_bgcolor='#f8f9fa',
        plot_bgcolor='#ffffff',
        
        # Add controls
        updatemenus=[{
            'type': 'buttons',
            'direction': 'left',
            'x': 0.1,
            'y': 1.15,
            'buttons': [
                dict(label='All Flows', method='restyle', 
                     args=[{'visible': [True] * len(values)}]),
                dict(label='Major Flows', method='restyle',
                     args=[{'visible': [v > threshold for v in values]}])
            ]
        }]
    )
    
    return fig
```

## Limitations

1. **Node Positioning**: While x,y coordinates can be specified, Sankey's algorithm may override for optimization
2. **Flow Curves**: Limited control over bezier curves compared to other network diagrams
3. **Animation**: No native animation support (unlike scatter/line plots)
4. **3D**: No 3D Sankey support in Plotly
5. **Circular Flows**: Not well-suited for circular/cyclic flows

## Best Practices

1. **Color Usage**
   - Use categorical colors for states
   - Use opacity for flow volume
   - Ensure sufficient contrast

2. **Label Management**
   - Keep labels concise
   - Use hover for details
   - Consider abbreviations for mobile

3. **Flow Filtering**
   - Hide flows < 1% of total
   - Provide filter controls
   - Group minor flows as "Other"

4. **Performance**
   - Limit to ~50 nodes
   - Pre-aggregate data
   - Use caching for large datasets