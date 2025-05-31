# Treatment Patterns Visualization Summary

## Date: May 31, 2025

### Overview
We developed a comprehensive treatment pattern analysis system that visualizes patient journeys using ONLY treatment timing data (no disease states). This makes it directly comparable to real-world clinical data where disease activity may not be tracked.

### Key Achievements

#### 1. **Sankey Diagram Visualization** (`treatment_patterns_visualization.py`)
- **Purpose**: Shows patient flow through different treatment patterns based solely on visit intervals
- **Key Features**:
  - Grayscale flow diagram showing transitions between treatment states
  - States defined by visit intervals (e.g., Monthly, Regular 6-8 weeks, Extended 12+ weeks)
  - Special handling for treatment gaps and restart patterns
  - Width of flows indicates number of patients

#### 2. **Enhanced Colored Sankey** (`treatment_patterns_enhanced_sankey.py`)
- **Purpose**: Same as above but with colored streams for better visual tracking
- **Two Color Schemes**:
  1. **Source-based coloring**: Flows inherit the color of their origin state
     - Helps track where patients are coming FROM
     - Opacity varies by flow volume
  2. **Semantic coloring**: Flows colored by transition type
     - 🔵 Blue = Moving to intensive treatment
     - 🟢 Green = Regular/extended treatment
     - 🟡 Yellow/Orange = Developing gaps
     - 🔴 Red = Long gaps
     - 💜 Pink = Restarting after gap
     - ⚫ Gray = Discontinuation

#### 3. **Treatment Interval Distribution**
- Histogram showing the distribution of all treatment intervals
- Key metrics: median, mean, and percentage of extended intervals
- Helps identify the most common treatment patterns

#### 4. **Pattern Statistics**
- Top 15 most common state transitions
- Percentage breakdowns of each transition type
- Insights into gap frequencies and restart rates

#### 5. **Gap Analysis (Tufte-style)**
- **Initial Issue**: Pie chart showed 100% "No gaps" contradicting Sankey diagram
- **Root Cause**: Original thresholds (120+ days for gaps) exceeded max data range (112 days)
- **Solution**: Adjusted categories to match actual data distribution:
  - Very frequent (≤6 weeks)
  - Frequent (6-9 weeks)
  - Regular (9-12 weeks)
  - Extended (12-16 weeks)
  - Gaps (>16 weeks)
- **Final Design**: Clean horizontal bar chart following Tufte principles
  - No chartjunk
  - Direct data labels
  - Subtle quartile reference lines

### Technical Improvements Made
1. Fixed pandas FutureWarning by setting `pd.set_option('future.no_silent_downcasting', True)`
2. Ensured `interval_days` column available throughout pipeline by returning enhanced dataframe
3. Handled edge cases (single-visit patients, no intervals)
4. Vectorized all operations for performance

### Key Insights from Implementation
- Treatment patterns can be effectively analyzed using timing data alone
- Most patients in the simulation maintain regular intervals (no long gaps)
- The visualization revealed the simulation's treat-and-extend protocol working as designed
- Color coding significantly improves flow tracking in Sankey diagrams

### Running the Visualizations
```bash
# Original Sankey (grayscale)
cd experiments
streamlit run treatment_patterns_visualization.py --server.port 8512

# Enhanced Sankey (colored flows)
streamlit run treatment_patterns_enhanced_sankey.py --server.port 8514
```

### Next Steps for Integration
When incorporating into main Streamlit v2 app, consider:
1. Which color scheme works best for your users (source vs semantic)
2. Whether to include all tabs or select specific visualizations
3. How to handle larger datasets (current filtering at 0.1% of transitions)
4. Integration with existing V2 discontinuation categories

### Files Created/Modified
- `experiments/treatment_patterns_visualization.py` - Main visualization with grayscale Sankey
- `experiments/treatment_patterns_enhanced_sankey.py` - Enhanced version with colored flows
- Both import from existing `TREATMENT_STATE_COLORS` dictionary for consistency

### Key Functions to Reuse
- `extract_treatment_patterns_vectorized()` - Extracts transitions from visit data
- `determine_treatment_state_vectorized()` - Categorizes visits by interval
- `create_treatment_pattern_sankey()` - Creates basic Sankey
- `create_enhanced_sankey_with_colored_streams()` - Source-colored Sankey
- `create_gradient_sankey()` - Semantically-colored Sankey
- `create_gap_analysis_chart_tufte()` - Clean horizontal bar chart

This work provides a solid foundation for understanding patient treatment patterns without requiring disease state information, making it valuable for real-world data analysis.