# Streamgraph Visualization Plan

## Overview
Create a streamgraph showing patient flow through treatment states over time, using the existing semantic color system and treatment state definitions.

## 1. Data Requirements

### States to Track (Already Defined)
- **Initial Treatment** - First visits in treatment
- **Intensive (Monthly)** - ≤35 days between visits
- **Regular (6-8 weeks)** - 36-63 days between visits  
- **Extended (12+ weeks)** - 64-111 days between visits
- **Maximum Extension (16 weeks)** - 112-119 days between visits
- **Treatment Gap (3-6 months)** - 120-180 days between visits
- **Extended Gap (6-12 months)** - 181-365 days between visits
- **Long Gap (12+ months)** - >365 days between visits
- **Restarted After Gap** - Return to treatment after >6 month gap
- **No Further Visits** - Discontinued/lost to follow-up

### Color Mapping (Already Exists)
The semantic colors are defined in `utils/visualization_modes.py` and mapped to states in `components/treatment_patterns/pattern_analyzer.py`.

## 2. Data Processing Steps

### Step 2.1: Extract Visit Data
- Load visits from ParquetResults
- Calculate intervals between visits
- Assign treatment states using existing `determine_treatment_state_vectorized()` function

### Step 2.2: Create Time Series
- Define time points (monthly intervals)
- For each time point, count patients in each state
- Handle patient entry/exit from cohort

### Step 2.3: Handle Transitions
- Track when patients move between states
- Ensure continuity (patients can't disappear and reappear)
- Account for new patients entering over time

## 3. Visualization Design

### Step 3.1: Choose Technology
- **Plotly** for interactivity and smooth rendering
- Stacked area chart (streamgraph)
- Time on x-axis, patient counts on y-axis

### Step 3.2: Layout Principles
- States ordered logically:
  - Active treatment states (Initial → Intensive → Regular → Extended → Maximum)
  - Gap states (Treatment Gap → Extended Gap → Long Gap)
  - Special states (Restarted, No Further Visits)
- Use semantic colors from visualization mode
- Show actual patient counts (not percentages initially)

### Step 3.3: Interactivity
- Hover to see exact counts
- Click legend to show/hide states
- Time resolution selector (months/weeks)

## 4. Implementation Steps

### Phase 1: Data Extraction
1. Create function to get patient state at any time point
2. Test with sample data to verify state assignments
3. Validate against known patterns

### Phase 2: Time Series Generation
1. Create monthly time points
2. Count patients in each state at each time
3. Store in DataFrame for plotting

### Phase 3: Visualization
1. Create basic Plotly stacked area chart
2. Apply semantic colors
3. Add proper labels and formatting

### Phase 4: Integration
1. Replace existing streamgraph in Analysis page
2. Add any necessary controls
3. Ensure proper caching for performance

## 5. Key Considerations

### Data Integrity
- Use ONLY real data from simulation
- No synthetic curves or smoothing
- Show actual state transitions

### Performance
- Cache processed data by simulation ID
- Vectorize operations where possible
- Limit time resolution to reasonable intervals

### User Experience
- Clear legend showing all states
- Informative hover tooltips
- Smooth transitions between time points

## 6. Success Criteria
- Shows patient flow through treatment states over time
- Uses semantic color system
- Accurately reflects simulation data
- Performs well with 10,000+ patients
- Provides clear insights into treatment patterns

## 7. Next Steps
1. Review and approve this plan
2. Start with Phase 1: Data Extraction
3. Test each phase before moving to the next
4. Keep visualization simple and focused