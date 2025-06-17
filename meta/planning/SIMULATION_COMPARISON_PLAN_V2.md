# Simulation Comparison Feature - Refined Plan V2

## Overview
A dedicated comparison page that allows users to select two saved simulations and compare their outcomes side-by-side, with key metrics and visualizations to support clinical decision-making.

## Page Location & Navigation
- **File**: `pages/4_Simulation_Comparison.py` (follows existing numbering)
- **Navigation**: Add to workflow indicator after Simulations
- **Icon**: Use `compare` (CHART_BAR_OVERLAY) icon
- **Access**: Only shows saved simulations (no live runs)

## Validation Rules
1. **Duration Match**: Both simulations must have the same duration (±30 days tolerance)
2. **Patient Count**: Warning if different, but allow comparison with clear indicator
3. **Time Alignment**: Both must use same time units (months)
4. **Auto-filtering**: When Simulation A is selected, filter B to only show compatible options

## UI Design

### Section 1: Simulation Selection with Smart Filtering
```
[compare icon] Compare Simulation Results

Recent Comparisons: [Button: A vs B] [Button: C vs D] [Button: Clear]

Simulation A                    [swap icon]              Simulation B
[document icon] Select first... ▼                       [document icon] Select compatible... ▼
                                                        (Auto-filtered to matching duration)

[warning icon] Duration must match for valid comparison
```

### Section 2: Simulation Overview Cards
```
┌─────────────────────────────────┬─────────────────────────────────┐
│ [document] Simulation A         │ [document] Simulation B         │
├─────────────────────────────────┼─────────────────────────────────┤
│ Protocol: Eylea T&E             │ Protocol: Eylea Fixed Bimonthly │
│ Patients: 1,000                 │ Patients: 1,000                 │
│ Duration: 5 years               │ Duration: 5 years               │
│ Model: Standard                 │ Model: Time-based               │
│ Baseline: Normal (μ=70, σ=10)   │ Baseline: Beta (μ=58.4)        │
│ Run Date: 2024-01-15            │ Run Date: 2024-01-16           │
└─────────────────────────────────┴─────────────────────────────────┘
```

### Section 3: Key Insights Summary (New)
```
┌──────────────────────────────────────────────────────────────────┐
│ [analytics] Key Insights                                          │
├──────────────────────────────────────────────────────────────────┤
│ • Simulation B preserves 2.4 more letters despite lower baseline │
│ • Fixed dosing requires 5.5 more injections but 4.3 fewer visits│
│ • Higher discontinuation in B driven by poor vision threshold   │
│ • Consider: Trade-off between visit burden and vision outcomes  │
└──────────────────────────────────────────────────────────────────┘
```

### Section 4: Enhanced Metrics Comparison
```
┌──────────────────────────────────────────────────────────────────┐
│ [table] Key Outcome Metrics              [copy] [csv] [help]     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Visual Acuity (ETDRS Letters)        A          B      Difference│
│ ─────────────────────────────────────────────────────────────── │
│ Baseline Mean                      70.0       58.4      -11.6 ↓  │
│ Year 1 Mean                        68.5       57.2      -11.3 ↓  │
│ Year 2 Mean                        66.2       55.8      -10.4 ↓  │
│ Year 5 Mean (End)                  61.3       52.1       -9.2 ↓  │
│ Mean Change from Baseline          -8.7       -6.3      +2.4 ↑   │
│ Maintained Vision (≤5 loss)        45.2%      52.8%     +7.6% ↑  │
│                                                                   │
│ Treatment Burden                     A          B      Difference │
│ ─────────────────────────────────────────────────────────────── │
│ Mean Injections/Patient            32.5       38.0      +5.5 ↑   │
│ Mean Visits/Patient                42.3       38.0      -4.3 ↓   │
│ Injection:Visit Ratio              0.77       1.00     +0.23 ↑   │
│ Injection Burden Categories:                                      │
│   ≤20 injections                  15.2%      8.3%      -6.9% ↓   │
│   21-40 injections                68.5%      45.2%    -23.3% ↓   │
│   >40 injections                  16.3%      46.5%    +30.2% ↑   │
│                                                                   │
│ Discontinuations                     A          B      Difference │
│ ─────────────────────────────────────────────────────────────── │
│ Total Discontinued                 23.5%      31.2%     +7.7% ↑   │
│ - Poor Vision (<20)                 8.2%      15.3%     +7.1% ↑   │
│ - Treatment Burden                  5.1%       4.8%     -0.3% ↓   │
│ - Other                           10.2%      11.1%     +0.9% ↑   │
│ Median Time to Discontinuation     36 mo      28 mo     -8 mo ↓   │
│                                                                   │
│ Protocol Efficiency                  A          B      Difference │
│ ─────────────────────────────────────────────────────────────── │
│ Vision-Years Preserved/Patient     4.2        3.8      -0.4 ↓    │
│ Vision-Years/Injection             0.13       0.10     -0.03 ↓   │
└──────────────────────────────────────────────────────────────────┘

Legend: ↑ Higher/More  ↓ Lower/Less  Green = Favorable  Red = Unfavorable
```

### Section 5: Visualizations with Enhanced Controls

#### View Mode Toggle
```
View Mode: [side_by_side icon] Side-by-Side  [overlay icon] Overlay  [chart icon] Difference

[Settings: ] [checkbox] Show Confidence Intervals  [checkbox] Show Clinical Thresholds
```

#### Visual Acuity Over Time
- **Side-by-Side**: Two charts with same y-axis scale (0-85)
- **Overlay**: Single chart, A in blue, B in orange, with legend
- **Difference**: Shows A-B with zero line and confidence bands
- Clinical threshold lines at 70 (funding), 35 (driving), 20 (legal blindness)
- Show mean with 95% confidence intervals

#### Injection Frequency Distribution
- Histogram showing distribution of total injections per patient
- Side-by-side view with matching x-axis scales
- Overlay shows both distributions with transparency
- Add summary statistics (mean, median, IQR)

#### Discontinuation Timeline
- Cumulative discontinuation curves by reason
- Works well as overlay with different line styles
- Add risk table below showing numbers at risk

#### New: Waterfall Chart for Vision Outcomes
```
Starting → Loading Phase → Maintenance → Discontinuation → Final
  70.0   →     +2.5     →    -8.2     →      -3.0      → 61.3
```

## Technical Implementation

### Data Loading with Smart Filtering
```python
def get_compatible_simulations(selected_sim, all_sims):
    """Filter simulations to only show compatible options."""
    if not selected_sim:
        return all_sims
    
    selected_duration = selected_sim['metadata']['duration_months']
    compatible = []
    
    for sim in all_sims:
        duration = sim['metadata']['duration_months']
        if abs(duration - selected_duration) <= 1:  # 1 month tolerance
            compatible.append(sim)
    
    return compatible

# In UI:
sim_a = st.selectbox(
    "Simulation A",
    options=all_simulations,
    format_func=lambda x: f"{x['name']} ({x['date']})",
    key="sim_a_select"
)

compatible_sims = get_compatible_simulations(sim_a, all_simulations)
sim_b = st.selectbox(
    "Simulation B", 
    options=compatible_sims,
    format_func=lambda x: f"{x['name']} ({x['date']})",
    key="sim_b_select"
)
```

### Enhanced Metric Calculations
```python
def calculate_comparison_metrics(sim_a, sim_b):
    """Calculate comprehensive comparison metrics."""
    metrics = {
        'visual_acuity': {
            'baseline': (mean_a, mean_b, diff, direction_indicator),
            'maintained_vision': calculate_maintained_vision_pct(),
            # ... other metrics
        },
        'injection_burden': {
            'categories': calculate_injection_burden_distribution(),
            # ... other metrics
        },
        'efficiency': {
            'vision_years_per_patient': calculate_vision_years(),
            'vision_years_per_injection': calculate_efficiency(),
        }
    }
    
    # Add clinical significance flags
    for metric in metrics:
        add_clinical_significance_flags(metric)
    
    return metrics
```

### Key Insights Generation
```python
def generate_key_insights(metrics):
    """Generate automated insights from comparison metrics."""
    insights = []
    
    # Vision preservation insight
    if metrics['visual_acuity']['mean_change'][2] > 2:
        insights.append(f"Simulation {better_sim} preserves {diff:.1f} more letters")
    
    # Treatment burden trade-off
    if (metrics['treatment_burden']['injections'][2] > 0 and 
        metrics['treatment_burden']['visits'][2] < 0):
        insights.append("Trade-off: More injections but fewer visits")
    
    # Add clinical recommendations
    insights.extend(generate_clinical_recommendations(metrics))
    
    return insights[:4]  # Top 4 insights
```

## Button Implementation with Carbon Icons
```python
from ape.utils.carbon_button_helpers import ape_button

# Swap button
if ape_button("", key="swap_sims", icon="swap", help_text="Swap simulations"):
    st.session_state.sim_a, st.session_state.sim_b = st.session_state.sim_b, st.session_state.sim_a
    st.rerun()

# Export buttons
col1, col2 = st.columns(2)
with col1:
    if ape_button("Copy Table", key="copy_metrics", icon="copy"):
        copy_metrics_to_clipboard()
with col2:
    if ape_button("Download CSV", key="download_csv", icon="csv"):
        download_comparison_data()

# View mode toggle
view_mode = st.radio(
    "View Mode",
    ["Side-by-Side", "Overlay", "Difference"],
    horizontal=True,
    key="view_mode"
)
```

## State Management
```python
# Remember selections and preferences
if 'comparison_state' not in st.session_state:
    st.session_state.comparison_state = {
        'sim_a': None,
        'sim_b': None,
        'view_mode': 'side_by_side',
        'show_ci': True,
        'show_thresholds': True,
        'recent_pairs': []  # Track last 3 comparisons
    }

# Update recent pairs when comparison is made
def update_recent_pairs(sim_a, sim_b):
    pair = (sim_a['id'], sim_b['id'])
    recent = st.session_state.comparison_state['recent_pairs']
    if pair in recent:
        recent.remove(pair)
    recent.insert(0, pair)
    st.session_state.comparison_state['recent_pairs'] = recent[:3]
```

## Success Criteria
1. ✅ Smart filtering makes compatible simulation selection effortless
2. ✅ Key insights provide immediate value without deep analysis
3. ✅ Metrics table is comprehensive yet scannable
4. ✅ Clinical significance is highlighted throughout
5. ✅ Export functionality available from day 1
6. ✅ Carbon icons replace all emoji characters
7. ✅ Responsive design works on tablets/mobile

## Implementation Priority
1. **Phase 1 (MVP)**:
   - Simulation selection with smart filtering
   - Key metrics table with clinical indicators
   - Visual acuity comparison (all 3 modes)
   - Basic export (copy/CSV)
   
2. **Phase 2 (Enhancement)**:
   - Key insights panel
   - Injection distribution visualization
   - Discontinuation timeline
   - Recent comparisons feature
   
3. **Phase 3 (Advanced)**:
   - Waterfall chart
   - Statistical significance testing
   - PDF report generation
   - Batch comparison mode

This refined plan leverages the full Carbon icon set and focuses on making comparisons both powerful and intuitive, with smart features that guide users to meaningful insights.