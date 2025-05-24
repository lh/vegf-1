# Visualization Templates and Prototypes

This document describes the standard visualization templates and prototypes used in our application.
These templates should be followed to ensure consistent styling and experience across the application.

## Tufte-Inspired Visualization Principles

All visualizations should follow Edward Tufte's principles of information design:

1. **Show the data** - Focus on the data, not the design
2. **Minimize non-data ink** - Remove all unnecessary elements
3. **Maximize data-ink ratio** - Make every pixel count
4. **Avoid chartjunk** - No decorative elements that don't contribute to understanding
5. **Use clear, direct labeling** - Avoid legends when direct labeling is possible
6. **Respect proportions** - Don't distort the data with design choices

## Prototype Visualizations

### 1. Nested Bar Chart with Category Totals

**Description:** A nested bar chart that shows subcategories within each category, with a light background 
bar representing the total for that category. This chart provides both the breakdown and the total in a 
single, clear visualization.

**Best for:** Comparing proportions across categories with meaningful subcategories, especially when the 
subcategories form natural pairs (e.g., "Yes/No", "Retreated/Not Retreated").

**Example:** "Discontinuation Reasons by Retreatment Status" chart in the retreatment panel.

**Implementation:** `visualization.utils.nested_bar_chart.create_nested_bar_chart()`

**Key styling features:**
- No border/frame around the legend
- Properly formatted legend titles (capitalized, spaces instead of underscores)
- Minimal grid lines and chart borders
- Direct data labels on bars
- Light gray background bars for totals
- Blue/sage-green color scheme for standard visualizations
- Subdued colors with moderate transparency

**Screenshot:** See the "updated_discontinuation_chart.png" in the repository.

```python
# Example usage
fig, ax = create_nested_bar_chart(
    data=df,
    category_col="reason",
    subcategory_col="retreatment_status",
    value_col="count",
    title="Discontinuation Reasons by Retreatment Status",
    figsize=(10, 6),
    colors=['#4682B4', '#8FAD91'],  # Steel Blue, Sage Green
    show_legend=True,
    show_grid=False,
    show_spines=False,
    data_labels=True,
    minimal_style=True
)
```

### 2. [Additional visualization templates will be documented here]

## Color System

All visualizations should use our standard color system:

- **Primary:** #4682B4 (Steel Blue) - Used for primary data series, important metrics
- **Secondary:** #B22222 (Firebrick) - Used for critical information, warnings
- **Patient Counts:** #8FAD91 (Sage Green) - Used for patient population metrics

Opacity levels:
- High: 0.8 - Used for primary elements
- Medium: 0.5 - Used for standard elements  
- Low: 0.2 - Used for background elements
- Very Low: 0.1 - Used for subtle background elements

The color system is defined in `visualization.color_system`.

## Guidelines for New Visualizations

When creating new visualizations:

1. Check this document first to see if an existing template fits your needs
2. Use the appropriate template and maintain consistent styling
3. If a new type of visualization is needed, develop it with Tufte principles in mind
4. Document any new visualization templates in this file
5. Include examples of proper usage
6. Add a screenshot of the visualization to help others understand its appearance

## References

- Tufte, E. R. (2001). The Visual Display of Quantitative Information (2nd ed.). Graphics Press.
- Few, S. (2009). Now You See It: Simple Visualization Techniques for Quantitative Analysis. Analytics Press.