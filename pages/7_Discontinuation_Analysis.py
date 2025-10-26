"""
Discontinuation Analysis - Experimental visualizations for comparing discontinuation patterns.

This page shows multiple visualization approaches for comparing discontinuation patterns
between two simulations. Used to explore and decide on the best visualization approach.
"""

import streamlit as st
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import json
from visualization.color_system import COLORS, ALPHAS

# Page configuration
st.set_page_config(
    page_title="Discontinuation Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import utilities
from ape.utils.startup_redirect import handle_page_startup
from ape.components.ui.workflow_indicator import workflow_progress_indicator
from ape.core.results.factory import ResultsFactory

# Check for startup redirect
handle_page_startup("discontinuation_analysis")

# Show workflow progress
workflow_progress_indicator("discontinuation_analysis")

st.title("🔍 Discontinuation Analysis - Experimental Visualizations")
st.markdown("""
This page shows **multiple visualization approaches** for comparing discontinuation patterns between simulations.
The goal is to explore different ways to visualize discontinuation data and decide which works best.
""")

# Get available simulations
RESULTS_DIR = ResultsFactory.DEFAULT_RESULTS_DIR
saved_simulations = sorted(
    [f for f in RESULTS_DIR.iterdir() if f.is_dir() and not f.name.startswith('.')],
    key=lambda x: x.stat().st_mtime,
    reverse=True
)

if len(saved_simulations) < 2:
    st.error("Need at least 2 saved simulations for comparison. Please run some simulations first.")
    st.stop()

def get_simulation_info(sim_path):
    """Extract key information from simulation."""
    try:
        metadata_file = sim_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)

            duration_years = metadata.get('duration_years', 0)
            duration_months = int(duration_years * 12)
            protocol_name = metadata.get('protocol_name') or metadata.get('protocol', 'Unknown')

            return {
                'path': sim_path,
                'name': sim_path.name,
                'protocol': protocol_name,
                'patients': metadata.get('n_patients', 0),
                'duration': duration_months,
                'date': datetime.fromisoformat(metadata.get('timestamp', '')).strftime('%Y-%m-%d'),
                'model_type': metadata.get('model_type', 'visit_based')
            }
    except Exception as e:
        st.warning(f"Could not read simulation {sim_path.name}: {str(e)}")
        return None

# Get info for all simulations
simulation_infos = [info for info in (get_simulation_info(s) for s in saved_simulations) if info]

if not simulation_infos:
    st.error("No valid simulations found.")
    st.stop()

# Simulation selection
st.markdown("### Select Simulations to Compare")
col1, col2 = st.columns(2)

with col1:
    sim_a_idx = st.selectbox(
        "Simulation A",
        range(len(simulation_infos)),
        format_func=lambda i: f"{simulation_infos[i]['protocol']} - {simulation_infos[i]['patients']}p, {simulation_infos[i]['duration']}m ({simulation_infos[i]['date']})",
        key="sim_a_select"
    )
    sim_a = simulation_infos[sim_a_idx]

with col2:
    # Filter out simulation A from B options
    sim_b_options = [i for i in range(len(simulation_infos)) if i != sim_a_idx]
    if not sim_b_options:
        st.error("Need at least 2 different simulations")
        st.stop()

    sim_b_idx = st.selectbox(
        "Simulation B",
        sim_b_options,
        format_func=lambda i: f"{simulation_infos[i]['protocol']} - {simulation_infos[i]['patients']}p, {simulation_infos[i]['duration']}m ({simulation_infos[i]['date']})",
        key="sim_b_select"
    )
    sim_b = simulation_infos[sim_b_idx]

# Load discontinuation data
@st.cache_data
def load_discontinuation_data(sim_path):
    """Load and analyze discontinuation data from a simulation."""
    try:
        results = ResultsFactory.load_results(sim_path)
        patients_df = results.get_patients_df()

        # Get total patients
        total_patients = len(patients_df)

        # Get discontinued patients
        discontinued_df = patients_df[patients_df['discontinued'] == True].copy()
        total_discontinued = len(discontinued_df)

        # Count by reason
        reason_counts = {}
        if 'discontinuation_reason' in discontinued_df.columns:
            reason_counts = discontinued_df['discontinuation_reason'].value_counts().to_dict()

        # If no reason column or all NaN, mark as unknown
        if not reason_counts:
            if total_discontinued > 0:
                reason_counts = {'unknown': total_discontinued}

        return {
            'total_patients': total_patients,
            'total_discontinued': total_discontinued,
            'discontinuation_rate': total_discontinued / total_patients if total_patients > 0 else 0,
            'reason_counts': reason_counts,
            'discontinued_df': discontinued_df,
            'patients_df': patients_df
        }
    except Exception as e:
        st.error(f"Error loading discontinuation data: {str(e)}")
        return None

# Load data
with st.spinner("Loading discontinuation data..."):
    data_a = load_discontinuation_data(sim_a['path'])
    data_b = load_discontinuation_data(sim_b['path'])

if not data_a or not data_b:
    st.error("Failed to load discontinuation data")
    st.stop()

# Display summary
st.markdown("---")
st.markdown("### Summary")
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    **Simulation A:** {sim_a['protocol']}
    - Total patients: {data_a['total_patients']}
    - Discontinued: {data_a['total_discontinued']} ({data_a['discontinuation_rate']:.1%})
    - Reasons: {len(data_a['reason_counts'])} categories
    """)

with col2:
    st.markdown(f"""
    **Simulation B:** {sim_b['protocol']}
    - Total patients: {data_b['total_patients']}
    - Discontinued: {data_b['total_discontinued']} ({data_b['discontinuation_rate']:.1%})
    - Reasons: {len(data_b['reason_counts'])} categories
    """)

# Prepare data for visualization
# Get all unique reasons across both simulations
all_reasons = sorted(set(list(data_a['reason_counts'].keys()) + list(data_b['reason_counts'].keys())))

# Define reason categories and colors
# Based on actual simulation data
REASON_COLORS = {
    # Clinical/bad outcomes - reds and oranges
    'death': '#d62728',  # Red - patient death
    'mortality': '#d62728',  # Red - patient death (alternative name)
    'deterioration': '#ff7f0e',  # Orange - vision deterioration
    'poor_response': '#ff7f0e',  # Orange - poor clinical response (alternative)
    'poor_vision': '#ff9896',  # Light red - poor vision threshold
    'treatment_decision_no_improvement': '#ffbb78',  # Light orange - no improvement

    # Administrative/system - yellows and cyans
    'administrative': '#bcbd22',  # Yellow-green - administrative
    'system_discontinuation': '#bcbd22',  # Yellow-green - system admin (alternative)
    'attrition': '#17becf',  # Cyan - patient attrition/lost to follow-up
    'reauthorization_failure': '#17becf',  # Cyan - bureaucratic (alternative)

    # Patient choice - purple
    'premature': '#9467bd',  # Purple - patient withdrew

    # Good outcomes - greens
    'treatment_decision_stable': '#2ca02c',  # Green - stable, treatment complete
    'stable_max_interval': '#2ca02c',  # Green - protocol completion (alternative)

    # Unknown
    'unknown': '#7f7f7f'  # Gray - unknown
}

REASON_LABELS = {
    'death': 'Patient Death',
    'mortality': 'Patient Death',
    'deterioration': 'Vision Deterioration',
    'poor_response': 'Poor Clinical Response',
    'poor_vision': 'Vision Below Threshold',
    'treatment_decision_no_improvement': 'No Improvement',
    'treatment_decision_stable': 'Stable/Treatment Complete',
    'stable_max_interval': 'Protocol Completion',
    'administrative': 'Administrative',
    'system_discontinuation': 'Administrative Loss',
    'attrition': 'Lost to Follow-up',
    'reauthorization_failure': 'Funding Not Renewed',
    'premature': 'Patient Withdrew',
    'unknown': 'Unknown Reason'
}

# Calculate max discontinuations for scaling
max_discontinued = max(data_a['total_discontinued'], data_b['total_discontinued'])

st.markdown("---")
st.markdown("## Experimental Visualizations")
st.markdown("Explore different ways to visualize the discontinuation comparison:")

# ==============================================================================
# VISUALIZATION 1: Side-by-Side Stacked Bars (Scaled to Max)
# ==============================================================================
st.markdown("### Visualization 1: Side-by-Side Stacked Bars (Scaled to Max)")
st.markdown("""
**Concept:** Both bars scaled so the simulation with more discontinuations reaches 100%.
Shows both absolute volume difference and breakdown by reason.
""")

fig1, ax1 = plt.subplots(figsize=(10, 6), facecolor='white')
ax1.set_facecolor('white')

# Prepare data
width = 0.6
x_positions = [0, 1.5]

# Build stacked bars
bottom_a = 0
bottom_b = 0

for reason in all_reasons:
    count_a = data_a['reason_counts'].get(reason, 0)
    count_b = data_b['reason_counts'].get(reason, 0)

    color = REASON_COLORS.get(reason, '#7f7f7f')
    label = REASON_LABELS.get(reason, reason)

    # Only add to legend once
    label_kwarg = {'label': label} if reason == all_reasons[0] or (count_a > 0 or count_b > 0) else {}

    if count_a > 0:
        ax1.bar(x_positions[0], count_a, width, bottom=bottom_a, color=color,
               edgecolor='white', linewidth=1, **label_kwarg)
        # Add count label if significant
        if count_a > max_discontinued * 0.05:  # Only label if >5% of max
            ax1.text(x_positions[0], bottom_a + count_a/2, str(count_a),
                    ha='center', va='center', fontsize=9, color='white', fontweight='bold')
        bottom_a += count_a

    if count_b > 0:
        ax1.bar(x_positions[1], count_b, width, bottom=bottom_b, color=color,
               edgecolor='white', linewidth=1)
        if count_b > max_discontinued * 0.05:
            ax1.text(x_positions[1], bottom_b + count_b/2, str(count_b),
                    ha='center', va='center', fontsize=9, color='white', fontweight='bold')
        bottom_b += count_b

# Tufte styling
ax1.set_xlim(-0.5, 2.5)
ax1.set_ylim(0, max_discontinued * 1.1)
ax1.set_xticks(x_positions)
ax1.set_xticklabels([f'Simulation A\n({data_a["total_discontinued"]} discontinued)',
                      f'Simulation B\n({data_b["total_discontinued"]} discontinued)'])
ax1.set_ylabel('Number of Discontinued Patients', fontsize=11, color='#333333')
ax1.set_title('Discontinuation Comparison: Absolute Numbers', fontsize=12, color='#333333', pad=15)

# Tufte spines
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_color('#333333')
ax1.spines['bottom'].set_color('#333333')
ax1.spines['left'].set_linewidth(0.8)
ax1.spines['bottom'].set_linewidth(0.8)
ax1.tick_params(colors='#333333', width=0.8, length=4)
ax1.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc', axis='y')

# Legend
ax1.legend(loc='upper right', frameon=False, fontsize=9)

plt.tight_layout()
st.pyplot(fig1)
plt.close(fig1)

# ==============================================================================
# VISUALIZATION 2: Grouped Bars by Reason
# ==============================================================================
st.markdown("---")
st.markdown("### Visualization 2: Grouped Bars by Discontinuation Reason")
st.markdown("""
**Concept:** Group by reason, show both simulations side-by-side for each reason.
Makes it easier to compare specific reasons directly.
""")

fig2, ax2 = plt.subplots(figsize=(12, 6), facecolor='white')
ax2.set_facecolor('white')

# Prepare data
x = np.arange(len(all_reasons))
width = 0.35

counts_a = [data_a['reason_counts'].get(r, 0) for r in all_reasons]
counts_b = [data_b['reason_counts'].get(r, 0) for r in all_reasons]

# Plot bars
bars1 = ax2.bar(x - width/2, counts_a, width, label='Simulation A',
               color=COLORS['primary'], alpha=0.8, edgecolor='none')
bars2 = ax2.bar(x + width/2, counts_b, width, label='Simulation B',
               color=COLORS['secondary'], alpha=0.8, edgecolor='none')

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=8, color='#666666')

# Styling
ax2.set_xlabel('Discontinuation Reason', fontsize=11, color='#333333')
ax2.set_ylabel('Number of Patients', fontsize=11, color='#333333')
ax2.set_title('Discontinuation Comparison: By Reason', fontsize=12, color='#333333', pad=15)
ax2.set_xticks(x)
ax2.set_xticklabels([REASON_LABELS.get(r, r) for r in all_reasons], rotation=45, ha='right')

# Tufte spines
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['left'].set_color('#333333')
ax2.spines['bottom'].set_color('#333333')
ax2.spines['left'].set_linewidth(0.8)
ax2.spines['bottom'].set_linewidth(0.8)
ax2.tick_params(colors='#333333', width=0.8, length=4)
ax2.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc', axis='y')

ax2.legend(frameon=False, fontsize=10)

plt.tight_layout()
st.pyplot(fig2)
plt.close(fig2)

# ==============================================================================
# VISUALIZATION 3: Separated Good vs Bad Outcomes
# ==============================================================================
st.markdown("---")
st.markdown("### Visualization 3: Good vs Bad Outcomes")
st.markdown("""
**Concept:** Separate "successful completion" from adverse discontinuations.
Highlights that `stable_max_interval` is actually a positive outcome.
""")

# Categorize reasons
good_reasons = ['stable_max_interval', 'treatment_decision_stable']
bad_reasons = [r for r in all_reasons if r not in good_reasons]

def count_by_category(reason_counts, category_list):
    return sum(reason_counts.get(r, 0) for r in category_list)

good_a = count_by_category(data_a['reason_counts'], good_reasons)
bad_a = count_by_category(data_a['reason_counts'], bad_reasons)
good_b = count_by_category(data_b['reason_counts'], good_reasons)
bad_b = count_by_category(data_b['reason_counts'], bad_reasons)

fig3, (ax3a, ax3b) = plt.subplots(1, 2, figsize=(14, 6), facecolor='white')
ax3a.set_facecolor('white')
ax3b.set_facecolor('white')

# Left panel: Bad outcomes
width = 0.6
x_pos = [0, 1.5]

bottom_a = 0
bottom_b = 0

for reason in bad_reasons:
    count_a = data_a['reason_counts'].get(reason, 0)
    count_b = data_b['reason_counts'].get(reason, 0)

    if count_a == 0 and count_b == 0:
        continue

    color = REASON_COLORS.get(reason, '#7f7f7f')
    label = REASON_LABELS.get(reason, reason)

    ax3a.bar(x_pos[0], count_a, width, bottom=bottom_a, color=color,
            edgecolor='white', linewidth=1, label=label)
    ax3a.bar(x_pos[1], count_b, width, bottom=bottom_b, color=color,
            edgecolor='white', linewidth=1)

    if count_a > 0:
        bottom_a += count_a
    if count_b > 0:
        bottom_b += count_b

ax3a.set_xlim(-0.5, 2.5)
ax3a.set_xticks(x_pos)
ax3a.set_xticklabels(['Simulation A', 'Simulation B'])
ax3a.set_ylabel('Number of Patients', fontsize=11, color='#333333')
ax3a.set_title('Adverse Discontinuations', fontsize=12, color='#333333', pad=15)
ax3a.legend(loc='upper right', frameon=False, fontsize=8)

# Tufte styling
ax3a.spines['top'].set_visible(False)
ax3a.spines['right'].set_visible(False)
ax3a.spines['left'].set_color('#333333')
ax3a.spines['bottom'].set_color('#333333')
ax3a.spines['left'].set_linewidth(0.8)
ax3a.spines['bottom'].set_linewidth(0.8)
ax3a.tick_params(colors='#333333', width=0.8, length=4)
ax3a.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc', axis='y')

# Right panel: Good outcomes
ax3b.bar(x_pos, [good_a, good_b], width, color='#2ca02c', alpha=0.8, edgecolor='none')
for i, (pos, val) in enumerate(zip(x_pos, [good_a, good_b])):
    if val > 0:
        ax3b.text(pos, val, str(val), ha='center', va='bottom', fontsize=10, color='#666666')

ax3b.set_xlim(-0.5, 2.5)
ax3b.set_xticks(x_pos)
ax3b.set_xticklabels(['Simulation A', 'Simulation B'])
ax3b.set_ylabel('Number of Patients', fontsize=11, color='#333333')
ax3b.set_title('Protocol Completions (Successful)', fontsize=12, color='#333333', pad=15)

# Tufte styling
ax3b.spines['top'].set_visible(False)
ax3b.spines['right'].set_visible(False)
ax3b.spines['left'].set_color('#333333')
ax3b.spines['bottom'].set_color('#333333')
ax3b.spines['left'].set_linewidth(0.8)
ax3b.spines['bottom'].set_linewidth(0.8)
ax3b.tick_params(colors='#333333', width=0.8, length=4)
ax3b.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc', axis='y')

plt.tight_layout()
st.pyplot(fig3)
plt.close(fig3)

# ==============================================================================
# VISUALIZATION 4: Proportional View (Percentages)
# ==============================================================================
st.markdown("---")
st.markdown("### Visualization 4: Proportional Breakdown")
st.markdown("""
**Concept:** Show each protocol's discontinuation pattern as percentages.
Helps answer: "Of the patients who discontinued, what was the typical reason?"
""")

fig4, ax4 = plt.subplots(figsize=(10, 6), facecolor='white')
ax4.set_facecolor('white')

# Calculate percentages
width = 0.6
x_positions = [0, 1.5]

# Build stacked bars as percentages
bottom_a = 0
bottom_b = 0

for reason in all_reasons:
    count_a = data_a['reason_counts'].get(reason, 0)
    count_b = data_b['reason_counts'].get(reason, 0)

    pct_a = (count_a / data_a['total_discontinued'] * 100) if data_a['total_discontinued'] > 0 else 0
    pct_b = (count_b / data_b['total_discontinued'] * 100) if data_b['total_discontinued'] > 0 else 0

    if pct_a == 0 and pct_b == 0:
        continue

    color = REASON_COLORS.get(reason, '#7f7f7f')
    label = REASON_LABELS.get(reason, reason)

    label_kwarg = {'label': label} if reason == all_reasons[0] or (pct_a > 0 or pct_b > 0) else {}

    if pct_a > 0:
        ax4.bar(x_positions[0], pct_a, width, bottom=bottom_a, color=color,
               edgecolor='white', linewidth=1, **label_kwarg)
        if pct_a > 5:  # Only label if >5%
            ax4.text(x_positions[0], bottom_a + pct_a/2, f'{pct_a:.0f}%',
                    ha='center', va='center', fontsize=9, color='white', fontweight='bold')
        bottom_a += pct_a

    if pct_b > 0:
        ax4.bar(x_positions[1], pct_b, width, bottom=bottom_b, color=color,
               edgecolor='white', linewidth=1)
        if pct_b > 5:
            ax4.text(x_positions[1], bottom_b + pct_b/2, f'{pct_b:.0f}%',
                    ha='center', va='center', fontsize=9, color='white', fontweight='bold')
        bottom_b += pct_b

# Styling
ax4.set_xlim(-0.5, 2.5)
ax4.set_ylim(0, 105)
ax4.set_xticks(x_positions)
ax4.set_xticklabels([f'Simulation A\n(n={data_a["total_discontinued"]})',
                      f'Simulation B\n(n={data_b["total_discontinued"]})'])
ax4.set_ylabel('Percentage of Discontinued Patients', fontsize=11, color='#333333')
ax4.set_title('Discontinuation Pattern: Proportional Breakdown', fontsize=12, color='#333333', pad=15)

# Tufte spines
ax4.spines['top'].set_visible(False)
ax4.spines['right'].set_visible(False)
ax4.spines['left'].set_color('#333333')
ax4.spines['bottom'].set_color('#333333')
ax4.spines['left'].set_linewidth(0.8)
ax4.spines['bottom'].set_linewidth(0.8)
ax4.tick_params(colors='#333333', width=0.8, length=4)
ax4.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc', axis='y')

ax4.legend(loc='upper right', frameon=False, fontsize=9)

plt.tight_layout()
st.pyplot(fig4)
plt.close(fig4)

# Data table
st.markdown("---")
st.markdown("### Raw Data")

data_table = pd.DataFrame({
    'Discontinuation Reason': [REASON_LABELS.get(r, r) for r in all_reasons],
    'Simulation A (count)': [data_a['reason_counts'].get(r, 0) for r in all_reasons],
    'Simulation A (%)': [f"{data_a['reason_counts'].get(r, 0) / data_a['total_discontinued'] * 100:.1f}%"
                          if data_a['total_discontinued'] > 0 else "0.0%" for r in all_reasons],
    'Simulation B (count)': [data_b['reason_counts'].get(r, 0) for r in all_reasons],
    'Simulation B (%)': [f"{data_b['reason_counts'].get(r, 0) / data_b['total_discontinued'] * 100:.1f}%"
                          if data_b['total_discontinued'] > 0 else "0.0%" for r in all_reasons],
})

st.dataframe(data_table, use_container_width=True)

st.markdown("---")
st.markdown("""
### Feedback
Which visualization approach works best for your analysis needs? Consider:
- **Viz 1**: Shows absolute volume difference clearly
- **Viz 2**: Makes reason-by-reason comparison easier
- **Viz 3**: Separates good outcomes from bad
- **Viz 4**: Shows the pattern/distribution within each protocol
""")
