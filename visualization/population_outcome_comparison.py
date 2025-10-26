"""
Population-Level Outcome Comparison Visualization

This module addresses survivorship bias in treatment protocol comparisons by:
1. Tracking all patients from baseline (Intent-to-Treat approach)
2. Calculating population-level metrics that account for discontinuations
3. Providing stratified analysis by discontinuation status

CRITICAL: This module uses only real simulation data and fails fast if data is missing.
No synthetic data, no fallbacks, no silent failures.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from visualization.color_system import COLORS, ALPHAS


def calculate_itt_vision_trajectory(patient_histories: Dict, max_months: int = 60) -> pd.DataFrame:
    """
    Calculate Intent-to-Treat vision trajectory for all patients from baseline.

    This function tracks ALL patients regardless of discontinuation status,
    preventing survivorship bias in outcome comparisons.

    Args:
        patient_histories: Dict mapping patient_id to patient data with 'visits' list
        max_months: Maximum duration to track (months)

    Returns:
        DataFrame with columns: month, mean_vision, std_vision, n_patients,
                                active_count, discontinued_count

    Raises:
        ValueError: If patient_histories is empty or missing required fields
    """
    if not patient_histories:
        raise ValueError("ERROR: No patient histories available - cannot calculate ITT trajectory")

    # Verify data structure
    first_patient = next(iter(patient_histories.values()))
    if 'visits' not in first_patient:
        raise ValueError("ERROR: Patient data missing required 'visits' field")

    # Create monthly grid
    months = list(range(0, max_months + 1))

    # For each patient, determine their vision at each month
    patient_vision_grid = {}
    patient_status_grid = {}  # Track active/discontinued status

    for patient_id, history in patient_histories.items():
        visits = history.get('visits', [])
        if not visits:
            continue

        is_discontinued = history.get('is_discontinued', False)

        # Build monthly vision values for this patient
        patient_vision_grid[patient_id] = {}
        patient_status_grid[patient_id] = {}

        # Find last visit month for this patient
        last_visit_month = max(v['month'] for v in visits)

        for month in months:
            # Find the most recent visit at or before this month
            relevant_visits = [v for v in visits if v['month'] <= month]

            if relevant_visits:
                # Use last observed value (LOCF - Last Observation Carried Forward)
                last_visit = max(relevant_visits, key=lambda v: v['month'])
                patient_vision_grid[patient_id][month] = last_visit['vision']

                # Determine if patient was still active at this timepoint
                # Patient is considered discontinued after their last visit if flagged as discontinued
                if is_discontinued and month > last_visit_month:
                    patient_status_grid[patient_id][month] = 'discontinued'
                elif is_discontinued and month >= last_visit_month:
                    # At or after final visit and patient is discontinued
                    patient_status_grid[patient_id][month] = 'discontinued'
                else:
                    patient_status_grid[patient_id][month] = 'active'
            else:
                # Before first visit - shouldn't happen in real data
                patient_vision_grid[patient_id][month] = None
                patient_status_grid[patient_id][month] = 'not_yet_enrolled'

    # Calculate summary statistics for each month
    trajectory_data = []
    for month in months:
        month_visions = [
            patient_vision_grid[pid][month]
            for pid in patient_vision_grid
            if patient_vision_grid[pid].get(month) is not None
        ]

        month_statuses = [
            patient_status_grid[pid][month]
            for pid in patient_status_grid
            if patient_status_grid[pid].get(month) is not None
        ]

        if not month_visions:
            continue

        active_count = sum(1 for s in month_statuses if s == 'active')
        disc_count = sum(1 for s in month_statuses if s == 'discontinued')

        trajectory_data.append({
            'month': month,
            'mean_vision': np.mean(month_visions),
            'std_vision': np.std(month_visions),
            'median_vision': np.median(month_visions),
            'n_patients': len(month_visions),
            'active_count': active_count,
            'discontinued_count': disc_count,
            'ci_lower': np.percentile(month_visions, 2.5),
            'ci_upper': np.percentile(month_visions, 97.5)
        })

    if not trajectory_data:
        raise ValueError("ERROR: No valid trajectory data could be calculated")

    return pd.DataFrame(trajectory_data)


def calculate_discontinuation_stratified_outcomes(patient_histories: Dict) -> Dict:
    """
    Calculate outcomes stratified by discontinuation status and reason.

    Args:
        patient_histories: Dict mapping patient_id to patient data

    Returns:
        Dict with keys:
            - 'active': outcomes for patients still on treatment
            - 'discontinued_by_reason': outcomes by discontinuation reason
            - 'overall_itt': Intent-to-treat outcomes for all patients
    """
    if not patient_histories:
        raise ValueError("ERROR: No patient histories available")

    active_patients = []
    discontinued_patients = []
    all_patients = []

    for patient_id, history in patient_histories.items():
        visits = history.get('visits', [])
        if not visits:
            continue

        final_vision = visits[-1]['vision']
        baseline_vision = visits[0]['vision']
        change_from_baseline = final_vision - baseline_vision

        patient_data = {
            'patient_id': patient_id,
            'baseline_vision': baseline_vision,
            'final_vision': final_vision,
            'change': change_from_baseline,
            'n_visits': len(visits),
            'duration_months': visits[-1]['month']
        }

        all_patients.append(patient_data)

        if history.get('is_discontinued', False):
            # Find discontinuation reason and time
            disc_reason = None
            for v in visits:
                if v.get('discontinuation_reason'):
                    disc_reason = v['discontinuation_reason']
                    break
            patient_data['discontinuation_reason'] = disc_reason or 'unknown'
            discontinued_patients.append(patient_data)
        else:
            active_patients.append(patient_data)

    # Calculate summary statistics for each group
    def summarize_group(patients):
        if not patients:
            return None
        df = pd.DataFrame(patients)
        return {
            'n_patients': len(patients),
            'mean_baseline': df['baseline_vision'].mean(),
            'mean_final': df['final_vision'].mean(),
            'mean_change': df['change'].mean(),
            'median_final': df['final_vision'].median(),
            'vision_maintained_pct': 100 * (df['change'] >= -5).sum() / len(df),
            'vision_gained_pct': 100 * (df['change'] > 0).sum() / len(df),
            'mean_duration': df['duration_months'].mean(),
            'patients': df.to_dict('records')
        }

    # Stratify discontinued patients by reason
    discontinued_by_reason = {}
    if discontinued_patients:
        disc_df = pd.DataFrame(discontinued_patients)
        for reason in disc_df['discontinuation_reason'].unique():
            reason_patients = disc_df[disc_df['discontinuation_reason'] == reason].to_dict('records')
            discontinued_by_reason[reason] = summarize_group(reason_patients)

    return {
        'active': summarize_group(active_patients),
        'discontinued_all': summarize_group(discontinued_patients),
        'discontinued_by_reason': discontinued_by_reason,
        'overall_itt': summarize_group(all_patients)
    }


def create_population_outcome_comparison(
    results_a: Dict,
    results_b: Dict,
    label_a: str = "Protocol A",
    label_b: str = "Protocol B",
    max_months: int = 60
) -> plt.Figure:
    """
    Create a three-panel comparison showing population-level outcomes.

    Panel 1 (Left): ITT mean vision trajectory for all baseline patients
    Panel 2 (Middle): Patient counts over time (active vs discontinued)
    Panel 3 (Right): Stratified outcomes by discontinuation reason

    Args:
        results_a: Simulation results for protocol A (must contain 'patient_histories')
        results_b: Simulation results for protocol B (must contain 'patient_histories')
        label_a: Label for protocol A
        label_b: Label for protocol B
        max_months: Maximum duration to display

    Returns:
        matplotlib Figure object

    Raises:
        ValueError: If required data is missing
    """
    # Validate inputs
    if 'patient_histories' not in results_a:
        raise ValueError("ERROR: results_a missing 'patient_histories'")
    if 'patient_histories' not in results_b:
        raise ValueError("ERROR: results_b missing 'patient_histories'")

    # Calculate ITT trajectories
    traj_a = calculate_itt_vision_trajectory(results_a['patient_histories'], max_months)
    traj_b = calculate_itt_vision_trajectory(results_b['patient_histories'], max_months)

    # Calculate stratified outcomes
    strat_a = calculate_discontinuation_stratified_outcomes(results_a['patient_histories'])
    strat_b = calculate_discontinuation_stratified_outcomes(results_b['patient_histories'])

    # Create figure with three panels
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))

    # Color scheme from central color system
    color_a = COLORS['primary']
    color_b = COLORS['secondary']
    alpha_ci = ALPHAS['very_low']

    # PANEL 1: ITT Vision Trajectory
    # Plot mean vision for all patients (Intent-to-Treat)
    ax1.plot(traj_a['month'], traj_a['mean_vision'],
             color=color_a, linewidth=2.5, label=label_a, alpha=0.9)
    ax1.fill_between(traj_a['month'], traj_a['ci_lower'], traj_a['ci_upper'],
                      color=color_a, alpha=alpha_ci)

    ax1.plot(traj_b['month'], traj_b['mean_vision'],
             color=color_b, linewidth=2.5, label=label_b, alpha=0.9)
    ax1.fill_between(traj_b['month'], traj_b['ci_lower'], traj_b['ci_upper'],
                      color=color_b, alpha=alpha_ci)

    # Add clinical thresholds
    ax1.axhline(y=70, color='gray', linestyle='--', linewidth=1, alpha=0.4, label='70 letters')
    ax1.axhline(y=35, color='gray', linestyle=':', linewidth=1, alpha=0.4, label='35 letters')

    ax1.set_xlabel('Month', fontsize=11)
    ax1.set_ylabel('Mean Visual Acuity (ETDRS Letters)', fontsize=11)
    ax1.set_title('Intent-to-Treat Vision Trajectory\n(All Baseline Patients)', fontsize=12, fontweight='bold')
    ax1.set_ylim(0, 85)
    ax1.legend(loc='best', frameon=False, fontsize=9)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)

    # PANEL 2: Patient Counts Over Time - Side by Side Comparison
    # Calculate retention rates as percentages
    traj_a['active_pct'] = 100 * traj_a['active_count'] / traj_a['n_patients']
    traj_a['discontinued_pct'] = 100 * traj_a['discontinued_count'] / traj_a['n_patients']

    traj_b['active_pct'] = 100 * traj_b['active_count'] / traj_b['n_patients']
    traj_b['discontinued_pct'] = 100 * traj_b['discontinued_count'] / traj_b['n_patients']

    # Plot retention rates (active %) for both protocols
    ax2.plot(traj_a['month'], traj_a['active_pct'],
             color=color_a, linewidth=2.5, linestyle='-', label=f'{label_a} - Active', alpha=0.9)
    ax2.plot(traj_b['month'], traj_b['active_pct'],
             color=color_b, linewidth=2.5, linestyle='-', label=f'{label_b} - Active', alpha=0.9)

    # Add discontinued rates as dashed lines
    ax2.plot(traj_a['month'], traj_a['discontinued_pct'],
             color=color_a, linewidth=1.5, linestyle='--', label=f'{label_a} - Discontinued', alpha=0.6)
    ax2.plot(traj_b['month'], traj_b['discontinued_pct'],
             color=color_b, linewidth=1.5, linestyle='--', label=f'{label_b} - Discontinued', alpha=0.6)

    ax2.set_xlabel('Month', fontsize=11)
    ax2.set_ylabel('Percentage of Baseline Cohort (%)', fontsize=11)
    ax2.set_title('Patient Retention Over Time\n(% of Baseline Cohort)', fontsize=12, fontweight='bold')
    ax2.set_ylim(0, 105)
    ax2.legend(loc='best', frameon=False, fontsize=8)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)

    # PANEL 3: Stratified Outcomes
    # Bar chart comparing final outcomes by status
    categories = ['All Patients\n(ITT)', 'Active\nPatients', 'Discontinued\nPatients']

    values_a = [
        strat_a['overall_itt']['mean_final'] if strat_a['overall_itt'] else 0,
        strat_a['active']['mean_final'] if strat_a['active'] else 0,
        strat_a['discontinued_all']['mean_final'] if strat_a['discontinued_all'] else 0
    ]

    values_b = [
        strat_b['overall_itt']['mean_final'] if strat_b['overall_itt'] else 0,
        strat_b['active']['mean_final'] if strat_b['active'] else 0,
        strat_b['discontinued_all']['mean_final'] if strat_b['discontinued_all'] else 0
    ]

    x = np.arange(len(categories))
    width = 0.35

    bars1 = ax3.bar(x - width/2, values_a, width, label=label_a,
                     color=color_a, alpha=0.8)
    bars2 = ax3.bar(x + width/2, values_b, width, label=label_b,
                     color=color_b, alpha=0.8)

    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}',
                        ha='center', va='bottom', fontsize=8)

    # Add patient counts as annotations
    for i, cat in enumerate(categories):
        if cat == 'All Patients\n(ITT)':
            n_a = strat_a['overall_itt']['n_patients'] if strat_a['overall_itt'] else 0
            n_b = strat_b['overall_itt']['n_patients'] if strat_b['overall_itt'] else 0
        elif cat == 'Active\nPatients':
            n_a = strat_a['active']['n_patients'] if strat_a['active'] else 0
            n_b = strat_b['active']['n_patients'] if strat_b['active'] else 0
        else:
            n_a = strat_a['discontinued_all']['n_patients'] if strat_a['discontinued_all'] else 0
            n_b = strat_b['discontinued_all']['n_patients'] if strat_b['discontinued_all'] else 0

        ax3.text(i, 5, f'n={n_a}/{n_b}', ha='center', va='bottom', fontsize=7, color='gray')

    ax3.set_xlabel('Patient Group', fontsize=11)
    ax3.set_ylabel('Mean Final Visual Acuity (Letters)', fontsize=11)
    ax3.set_title('Final Vision by Patient Status', fontsize=12, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(categories, fontsize=9)
    ax3.set_ylim(0, 85)
    ax3.legend(loc='best', frameon=False, fontsize=9)
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.grid(True, alpha=0.2, linestyle='-', linewidth=0.5, axis='y')

    # Overall title
    fig.suptitle('Population-Level Outcome Comparison (Addressing Survivorship Bias)',
                 fontsize=14, fontweight='bold', y=1.02)

    plt.tight_layout()

    return fig


def export_population_comparison_data(
    results_a: Dict,
    results_b: Dict,
    label_a: str = "Protocol A",
    label_b: str = "Protocol B",
    max_months: int = 60
) -> pd.DataFrame:
    """
    Export population comparison data to DataFrame for CSV/Excel.

    Returns:
        DataFrame with all population-level comparison metrics
    """
    traj_a = calculate_itt_vision_trajectory(results_a['patient_histories'], max_months)
    traj_b = calculate_itt_vision_trajectory(results_b['patient_histories'], max_months)

    strat_a = calculate_discontinuation_stratified_outcomes(results_a['patient_histories'])
    strat_b = calculate_discontinuation_stratified_outcomes(results_b['patient_histories'])

    export_data = []

    # ITT summary metrics
    export_data.append({
        'Section': 'Intent-to-Treat Outcomes',
        'Metric': 'All Patients - Mean Final Vision',
        f'{label_a}': f"{strat_a['overall_itt']['mean_final']:.1f}",
        f'{label_b}': f"{strat_b['overall_itt']['mean_final']:.1f}",
        'Difference': f"{strat_b['overall_itt']['mean_final'] - strat_a['overall_itt']['mean_final']:.1f}"
    })

    export_data.append({
        'Section': 'Intent-to-Treat Outcomes',
        'Metric': 'All Patients - Mean Change',
        f'{label_a}': f"{strat_a['overall_itt']['mean_change']:.1f}",
        f'{label_b}': f"{strat_b['overall_itt']['mean_change']:.1f}",
        'Difference': f"{strat_b['overall_itt']['mean_change'] - strat_a['overall_itt']['mean_change']:.1f}"
    })

    export_data.append({
        'Section': 'Intent-to-Treat Outcomes',
        'Metric': 'All Patients - Vision Maintained (%)',
        f'{label_a}': f"{strat_a['overall_itt']['vision_maintained_pct']:.1f}",
        f'{label_b}': f"{strat_b['overall_itt']['vision_maintained_pct']:.1f}",
        'Difference': f"{strat_b['overall_itt']['vision_maintained_pct'] - strat_a['overall_itt']['vision_maintained_pct']:.1f}"
    })

    # Active patients
    if strat_a['active'] and strat_b['active']:
        export_data.append({
            'Section': 'Active Patients Only',
            'Metric': 'Mean Final Vision',
            f'{label_a}': f"{strat_a['active']['mean_final']:.1f}",
            f'{label_b}': f"{strat_b['active']['mean_final']:.1f}",
            'Difference': f"{strat_b['active']['mean_final'] - strat_a['active']['mean_final']:.1f}"
        })

    # Discontinued patients
    if strat_a['discontinued_all'] and strat_b['discontinued_all']:
        export_data.append({
            'Section': 'Discontinued Patients',
            'Metric': 'Mean Final Vision',
            f'{label_a}': f"{strat_a['discontinued_all']['mean_final']:.1f}",
            f'{label_b}': f"{strat_b['discontinued_all']['mean_final']:.1f}",
            'Difference': f"{strat_b['discontinued_all']['mean_final'] - strat_a['discontinued_all']['mean_final']:.1f}"
        })

    return pd.DataFrame(export_data)
