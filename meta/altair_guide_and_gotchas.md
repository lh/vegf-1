# Altair Guide and Gotchas

## Overview
This guide documents our experience with Altair for data visualization in the APE application, including common pitfalls and solutions.

## Why Altair?
- **Performance**: 2-3x faster than Plotly for rendering
- **Declarative**: Clear separation of data and visual encoding
- **Interactive**: Built-in interactivity without callbacks
- **Vega-Lite**: Based on robust visualization grammar

## Common Gotchas and Solutions

### 1. Chart Combination Errors
**Problem**: `SchemaValidationError` when combining charts
```python
# This will fail:
combined = alt.hconcat(chart1, chart2).properties(width=150)
```

**Solution**: Set properties before combining
```python
# Do this instead:
chart2_with_props = chart2.properties(width=150)
combined = alt.hconcat(chart1, chart2_with_props)
```

### 2. Scale Resolution Issues
**Problem**: Error when combining charts with different scales
```python
# Fails when legend uses different y-axis than main chart
legend_combined = alt.hconcat(legend, legend_text)
```

**Solution**: Use `resolve_scale()`
```python
# Tell Altair to handle scales independently
legend_combined = alt.hconcat(legend, legend_text).resolve_scale(
    y='independent'
)
```

### 3. Color Mapping from Data
**Problem**: Colors not appearing when using data values
```python
# This won't use your actual colors:
color=alt.Color('CategoryColor:N', scale=None)
```

**Solution**: Create explicit scale mapping
```python
# Map categories to their colors explicitly
color_scale = alt.Scale(
    domain=df['Category'].unique().tolist(),
    range=df['Color'].unique().tolist()
)
color=alt.Color('Category:N', scale=color_scale)
```

### 4. Caching Issues in Streamlit
**Problem**: Old chart structure cached, causing errors after updates

**Solution**: Rename cached functions to force refresh
```python
# Change function name to clear cache
@st.cache_data(ttl=300)  # 5-minute TTL helps too
def get_charts_v2():  # v2, v3, etc. to force new cache
    return create_charts()
```

### 5. Property Chaining Order
**Problem**: Some properties must be set in specific order
```python
# May not work as expected
chart.configure_axis().properties().configure_view()
```

**Solution**: Generally safe order
```python
chart.properties(
    width=500,
    height=400
).configure_axis(
    ...
).configure_view(
    ...
).configure_title(
    ...
)
```

### 6. Mark Properties vs Encoding Properties
**Problem**: `TypeError` when putting mark properties in encode()
```python
# This will fail:
text = alt.Chart(df).mark_text().encode(
    x='x:Q',
    y='y:Q',
    text='label:N',
    dy=-10,  # ERROR: dy is not an encoding!
    fontSize=12  # ERROR: fontSize is not an encoding!
)
```

**Solution**: Mark properties go in mark_*() method
```python
# Put visual properties in the mark method:
text = alt.Chart(df).mark_text(
    dy=-10,      # Vertical offset
    dx=5,        # Horizontal offset  
    fontSize=12,
    font='Arial',
    fontWeight='normal',
    align='center',
    baseline='middle'
).encode(
    x='x:Q',
    y='y:Q', 
    text='label:N',
    color='category:N'  # Color CAN be an encoding
)
```

**Common mark properties**:
- Position adjustments: `dy`, `dx`, `angle`
- Font properties: `fontSize`, `font`, `fontWeight`, `fontStyle`
- Text properties: `align`, `baseline`, `limit`
- Shape properties: `size`, `strokeWidth`, `opacity` (when fixed)
- Mark-specific: `interpolate` (lines), `cornerRadius` (bars), etc.

## Best Practices

### 1. Data Preparation
Always prepare your data in long format:
```python
# Good - long format
records = []
for category, stats in data.items():
    for metric, value in [('Patients', stats['patients']), 
                         ('Visits', stats['visits'])]:
        records.append({
            'Category': category,
            'Metric': metric,
            'Value': value,
            'Color': category_colors[category]
        })
df = pd.DataFrame(records)
```

### 2. Semantic Colors
Use our color system, never hardcode:
```python
# Import color system
from ape.utils.visualization_modes import get_mode_colors
colors = get_mode_colors()

# Use system colors
neutral_color = colors.get('neutral', '#264653')
```

### 3. Chart Structure
Build charts in layers:
```python
# 1. Base encoding
base = alt.Chart(df).encode(x=..., y=..., color=...)

# 2. Marks
bars = base.mark_bar()
text = base.mark_text()

# 3. Combine layers
chart = bars + text

# 4. Configure
final = chart.properties(...).configure_axis(...)
```

### 4. Tooltips
Always include helpful tooltips:
```python
tooltip=[
    alt.Tooltip('Category:N', title='Category'),
    alt.Tooltip('Value:Q', title='Value', format='.1f'),
    alt.Tooltip('Percentage:Q', title='Percentage', format='.1%')
]
```

## Performance Tips

1. **Enable data transformer** for large datasets:
```python
alt.data_transformers.enable('default', max_rows=None)
```

2. **Pre-aggregate data** before passing to Altair

3. **Use quantitative (Q) scales** when possible - they're faster

4. **Avoid unnecessary layers** - combine marks when possible

## Common Patterns

### Grouped Bar Chart
```python
chart = alt.Chart(df).mark_bar().encode(
    x='Category:N',
    y='Value:Q',
    xOffset='Metric:N',  # Groups bars
    color='Category:N',
    opacity=alt.condition(
        alt.datum.Metric == 'Type1',
        alt.value(0.5),
        alt.value(1.0)
    )
)
```

### Reference Line
```python
line_df = pd.DataFrame({'x': [0, max_val], 'y': [0, max_val]})
line = alt.Chart(line_df).mark_line(
    strokeDash=[5, 5],
    color='#264653'
).encode(x='x:Q', y='y:Q')
```

### Custom Legend
```python
# Create separate legend chart
legend_df = pd.DataFrame({
    'label': ['Type 1', 'Type 2'],
    'y': [0, 1]
})

legend = alt.Chart(legend_df).mark_rect(
    width=15, height=15
).encode(
    y=alt.Y('y:O', axis=None),
    color=alt.value(color),
    opacity=alt.condition(...)
)

# Combine with main chart
final = alt.hconcat(main_chart, legend)
```

## Debugging Tips

1. **Check data types**: Use `:Q` for quantitative, `:N` for nominal, `:O` for ordinal
2. **Print intermediate charts**: `chart.to_dict()` to see structure
3. **Simplify first**: Remove all config/properties to isolate issues
4. **Check Altair version**: Some features vary between versions
5. **Use specific error messages**: The first line often has the key info

## Migration from Plotly

| Plotly | Altair |
|--------|---------|
| `go.Figure()` | `alt.Chart(df)` |
| `add_trace()` | Layer with `+` |
| `update_layout()` | `.configure_*()` |
| `marker_color=` | `color=` encoding |
| `hovertemplate=` | `tooltip=` list |

## Font and Rendering Quality Issues

### Problem: Poor font rendering and invisible chart elements
Symptoms:
- Blurry or pixelated fonts
- Chart elements (like bubbles) not visible
- "Washed out" appearance like "bad bitmap behind ground glass"

### Root Causes:
1. **Browser rendering**: Altair charts are rendered as SVG by browsers, quality varies
2. **DPI limitations**: Default rendering may be at low resolution
3. **Font availability**: Specified fonts may not be available, causing poor fallbacks
4. **Mark type issues**: Some marks render better than others

### Solutions:

#### 1. Use `mark_point` instead of `mark_circle`
```python
# Better rendering:
chart = alt.Chart(df).mark_point(
    filled=True,
    opacity=0.8,
    stroke='black',
    strokeWidth=2,
    strokeOpacity=1.0
)

# Instead of:
chart = alt.Chart(df).mark_circle()
```

#### 2. Use font stacks with fallbacks
```python
font='Helvetica, Arial, sans-serif'  # Provides fallbacks
```

#### 3. Use reasonable size ranges
```python
# Good:
size=alt.Size('value:Q', scale=alt.Scale(range=[200, 3000]))

# Bad (too large):
size=alt.Size('value:Q', scale=alt.Scale(range=[1000, 20000]))
```

#### 4. Increase font sizes and use bold
```python
mark_text(
    fontSize=14,  # Larger than default
    fontWeight='bold',
    font='Helvetica, Arial, sans-serif'
)
```

#### 5. Thicker strokes and higher contrast
```python
# For lines:
strokeWidth=2,  # Instead of 1
color='#CCCCCC',  # Light but visible

# For text:
color='#333333'  # Dark gray instead of light
```

## Resources
- [Altair Documentation](https://altair-viz.github.io/)
- [Altair Gallery](https://altair-viz.github.io/gallery/index.html)
- [Vega-Lite Specification](https://vega.github.io/vega-lite/)
- [GitHub Issue: Blurry chart rendering](https://github.com/altair-viz/altair/issues/2114)

---
## Known Limitations

### High-Resolution Display Issues
Altair charts can appear blurry or pixelated on high-resolution (4K/Retina) displays. This is a fundamental issue with how Vega-Lite renders in browsers. For production web applications requiring crisp visuals on modern displays, consider using Plotly or other alternatives.

### When to Avoid Altair
- Production web applications viewed on high-res displays
- Applications where font rendering quality is critical
- Complex visualizations with many small elements
- When consistent cross-browser rendering is required

---
*Last updated: 2025-06-14 after discovering rendering issues on high-resolution displays*