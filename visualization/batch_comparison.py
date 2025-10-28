"""
Batch comparison visualizations.

Provides visualization utilities for comparing results across multiple
simulations in a batch, including protocol comparisons and outcome distributions.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from pathlib import Path

from visualization.color_system import COLORS, ALPHAS
from ape.batch.statistics import (
    load_batch_results,
    calculate_outcome_statistics,
    calculate_discontinuation_breakdown
)


def create_protocol_comparison_chart(
    batch_summary: Dict[str, Any],
    stats: Dict[str, Dict[str, float]],
    figsize: tuple = (14, 6)
) -> plt.Figure:
    """
    Create a comparison chart showing key metrics for each protocol.

    Args:
        batch_summary: Batch summary dictionary
        stats: Statistics from calculate_outcome_statistics()
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    protocols = batch_summary['protocols']
    sim_ids = batch_summary['simulation_ids']

    # Prepare data
    metrics = {
        'Final Vision': [],
        'Vision Change': [],
        'Discontinuation Rate': [],
        'Vision Maintained': []
    }

    for sim_id in sim_ids:
        if sim_id in stats:
            s = stats[sim_id]
            metrics['Final Vision'].append(s['mean_final_vision'])
            metrics['Vision Change'].append(s['mean_vision_change'])
            metrics['Discontinuation Rate'].append(s['discontinuation_rate'])
            metrics['Vision Maintained'].append(s['vision_maintained_pct'])

    # Create figure with 4 subplots
    fig, axes = plt.subplots(2, 2, figsize=figsize, facecolor='white')
    fig.suptitle('Protocol Comparison', fontsize=14, color='#333333', y=0.98)

    # Define colors for protocols
    protocol_colors = [COLORS['primary'], COLORS['secondary'], COLORS['tertiary'], '#7f7f7f']

    # Plot 1: Final Vision
    ax = axes[0, 0]
    x = np.arange(len(protocols))
    bars = ax.bar(x, metrics['Final Vision'], color=protocol_colors[:len(protocols)], alpha=0.8, edgecolor='none')

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, metrics['Final Vision'])):
        ax.text(bar.get_x() + bar.get_width()/2, val, f'{val:.1f}',
               ha='center', va='bottom', fontsize=9, color='#666666')

    ax.set_ylabel('Mean Final Vision (letters)', fontsize=10, color='#333333')
    ax.set_title('Final Visual Acuity', fontsize=11, color='#333333', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(protocols, rotation=15, ha='right', fontsize=9)
    ax.set_ylim(0, 85)

    # Tufte styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#333333')
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    ax.tick_params(colors='#333333', width=0.8, length=4)
    ax.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc', axis='y')

    # Plot 2: Vision Change
    ax = axes[0, 1]
    bars = ax.bar(x, metrics['Vision Change'], color=protocol_colors[:len(protocols)], alpha=0.8, edgecolor='none')

    for i, (bar, val) in enumerate(zip(bars, metrics['Vision Change'])):
        ax.text(bar.get_x() + bar.get_width()/2, val, f'{val:+.1f}',
               ha='center', va='bottom' if val >= 0 else 'top', fontsize=9, color='#666666')

    ax.axhline(y=0, color='#999999', linestyle='--', linewidth=0.8, alpha=0.5)
    ax.set_ylabel('Mean Vision Change (letters)', fontsize=10, color='#333333')
    ax.set_title('Vision Change from Baseline', fontsize=11, color='#333333', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(protocols, rotation=15, ha='right', fontsize=9)

    # Tufte styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#333333')
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    ax.tick_params(colors='#333333', width=0.8, length=4)
    ax.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc', axis='y')

    # Plot 3: Discontinuation Rate
    ax = axes[1, 0]
    bars = ax.bar(x, metrics['Discontinuation Rate'], color=protocol_colors[:len(protocols)], alpha=0.8, edgecolor='none')

    for i, (bar, val) in enumerate(zip(bars, metrics['Discontinuation Rate'])):
        ax.text(bar.get_x() + bar.get_width()/2, val, f'{val:.1f}%',
               ha='center', va='bottom', fontsize=9, color='#666666')

    ax.set_ylabel('Discontinuation Rate (%)', fontsize=10, color='#333333')
    ax.set_title('Treatment Discontinuation', fontsize=11, color='#333333', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(protocols, rotation=15, ha='right', fontsize=9)
    ax.set_ylim(0, 100)

    # Tufte styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#333333')
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    ax.tick_params(colors='#333333', width=0.8, length=4)
    ax.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc', axis='y')

    # Plot 4: Vision Maintained
    ax = axes[1, 1]
    bars = ax.bar(x, metrics['Vision Maintained'], color=protocol_colors[:len(protocols)], alpha=0.8, edgecolor='none')

    for i, (bar, val) in enumerate(zip(bars, metrics['Vision Maintained'])):
        ax.text(bar.get_x() + bar.get_width()/2, val, f'{val:.1f}%',
               ha='center', va='bottom', fontsize=9, color='#666666')

    ax.set_ylabel('Patients (%)', fontsize=10, color='#333333')
    ax.set_title('Vision Maintained (≤5 letter loss)', fontsize=11, color='#333333', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(protocols, rotation=15, ha='right', fontsize=9)
    ax.set_ylim(0, 100)

    # Tufte styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#333333')
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    ax.tick_params(colors='#333333', width=0.8, length=4)
    ax.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc', axis='y')

    plt.tight_layout()
    return fig


def create_discontinuation_comparison(
    batch_summary: Dict[str, Any],
    discontinuation_data: Dict[str, Dict[str, Any]],
    figsize: tuple = (12, 6)
) -> plt.Figure:
    """
    Create discontinuation reason comparison chart.

    Args:
        batch_summary: Batch summary dictionary
        discontinuation_data: Discontinuation breakdown from calculate_discontinuation_breakdown()
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    protocols = batch_summary['protocols']
    sim_ids = batch_summary['simulation_ids']

    # Get all unique reasons
    all_reasons = set()
    for sim_id in sim_ids:
        if sim_id in discontinuation_data:
            all_reasons.update(discontinuation_data[sim_id]['reasons'].keys())

    all_reasons = sorted(all_reasons)

    if not all_reasons:
        # No discontinuations - create placeholder
        fig, ax = plt.subplots(figsize=figsize, facecolor='white')
        ax.text(0.5, 0.5, 'No discontinuations in batch',
               ha='center', va='center', fontsize=14, color='#666666')
        ax.axis('off')
        return fig

    # Prepare data
    x = np.arange(len(protocols))
    width = 0.8 / len(all_reasons)

    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    fig.suptitle('Discontinuation Reasons by Protocol', fontsize=14, color='#333333', y=0.98)

    # Reason colors (reuse from discontinuation analysis page)
    REASON_COLORS = {
        'death': '#d62728',
        'mortality': '#d62728',
        'deterioration': '#ff7f0e',
        'poor_response': '#ff7f0e',
        'poor_vision': '#ff9896',
        'treatment_decision_no_improvement': '#ffbb78',
        'administrative': '#bcbd22',
        'system_discontinuation': '#bcbd22',
        'attrition': '#17becf',
        'reauthorization_failure': '#17becf',
        'premature': '#9467bd',
        'treatment_decision_stable': '#2ca02c',
        'stable_max_interval': '#2ca02c',
        'unknown': '#7f7f7f'
    }

    # Plot grouped bars
    for i, reason in enumerate(all_reasons):
        counts = []
        for sim_id in sim_ids:
            if sim_id in discontinuation_data:
                count = discontinuation_data[sim_id]['reasons'].get(reason, 0)
                counts.append(count)
            else:
                counts.append(0)

        color = REASON_COLORS.get(reason, '#7f7f7f')
        offset = (i - len(all_reasons)/2) * width + width/2
        bars = ax.bar(x + offset, counts, width, label=reason.replace('_', ' ').title(),
                     color=color, alpha=0.8, edgecolor='none')

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2, height,
                       f'{int(height)}', ha='center', va='bottom', fontsize=8, color='#666666')

    ax.set_ylabel('Number of Patients', fontsize=10, color='#333333')
    ax.set_xticks(x)
    ax.set_xticklabels(protocols, rotation=15, ha='right', fontsize=9)
    ax.legend(loc='upper right', frameon=False, fontsize=8)

    # Tufte styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#333333')
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    ax.tick_params(colors='#333333', width=0.8, length=4)
    ax.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc', axis='y')

    plt.tight_layout()
    return fig


def create_batch_summary_figure(batch_id: str, figsize: tuple = (16, 10)) -> plt.Figure:
    """
    Create a comprehensive summary figure for a batch.

    Args:
        batch_id: Batch identifier
        figsize: Figure size

    Returns:
        Matplotlib figure with multiple panels
    """
    from ape.batch.status import get_batch_dir, BatchStatus

    batch_dir = get_batch_dir(batch_id)
    status_mgr = BatchStatus(batch_dir)

    summary = status_mgr.read_summary()
    if not summary:
        raise ValueError(f"No summary found for batch {batch_id}")

    # Load data
    results_dict = load_batch_results(summary)
    stats = calculate_outcome_statistics(results_dict)
    discontinuation = calculate_discontinuation_breakdown(results_dict)

    # Create multi-panel figure
    fig = plt.figure(figsize=figsize, facecolor='white')
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # Title
    fig.suptitle(f'Batch Summary: {batch_id}', fontsize=16, color='#333333', y=0.98)

    # Panel 1: Protocol Comparison (spans 2 columns)
    ax1 = fig.add_subplot(gs[0, :])
    protocols = summary['protocols']
    sim_ids = summary['simulation_ids']

    # Prepare comparison data
    final_visions = [stats[sid]['mean_final_vision'] for sid in sim_ids if sid in stats]
    vision_changes = [stats[sid]['mean_vision_change'] for sid in sim_ids if sid in stats]

    x = np.arange(len(protocols))
    width = 0.35

    protocol_colors = [COLORS['primary'], COLORS['secondary'], COLORS['tertiary'], '#7f7f7f']

    # Plot final vision and vision change side by side
    bars1 = ax1.bar(x - width/2, final_visions, width, label='Final Vision',
                   color=protocol_colors[0], alpha=0.8, edgecolor='none')
    bars2 = ax1.bar(x + width/2, [v + 65 for v in vision_changes], width, label='Vision Change (offset +65)',
                   color=protocol_colors[1], alpha=0.8, edgecolor='none')

    ax1.set_ylabel('Visual Acuity (letters)', fontsize=10, color='#333333')
    ax1.set_title('Vision Outcomes Comparison', fontsize=12, color='#333333', pad=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(protocols, rotation=15, ha='right', fontsize=9)
    ax1.legend(frameon=False, fontsize=9)

    # Tufte styling
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color('#333333')
    ax1.spines['bottom'].set_color('#333333')
    ax1.spines['left'].set_linewidth(0.8)
    ax1.spines['bottom'].set_linewidth(0.8)
    ax1.tick_params(colors='#333333', width=0.8, length=4)
    ax1.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc', axis='y')

    # Panels 2-5: Individual metrics
    metrics_data = [
        ('Discontinuation Rate (%)', [stats[sid]['discontinuation_rate'] for sid in sim_ids if sid in stats], (1, 0)),
        ('Vision Maintained (%)', [stats[sid]['vision_maintained_pct'] for sid in sim_ids if sid in stats], (1, 1)),
        ('Vision Improved (%)', [stats[sid]['vision_improved_pct'] for sid in sim_ids if sid in stats], (2, 0)),
        ('Mean Injections', [stats[sid].get('mean_total_injections', 0) for sid in sim_ids if sid in stats], (2, 1)),
    ]

    for title, values, (row, col) in metrics_data:
        ax = fig.add_subplot(gs[row, col])
        bars = ax.bar(x, values, color=protocol_colors[:len(protocols)], alpha=0.8, edgecolor='none')

        # Add value labels
        for bar, val in zip(bars, values):
            if val is not None and val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, val, f'{val:.1f}',
                       ha='center', va='bottom', fontsize=8, color='#666666')

        ax.set_title(title, fontsize=10, color='#333333', pad=8)
        ax.set_xticks(x)
        ax.set_xticklabels(protocols, rotation=15, ha='right', fontsize=8)

        # Tufte styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#333333')
        ax.spines['bottom'].set_color('#333333')
        ax.spines['left'].set_linewidth(0.8)
        ax.spines['bottom'].set_linewidth(0.8)
        ax.tick_params(colors='#333333', width=0.8, length=4)
        ax.grid(True, alpha=0.1, linewidth=0.5, color='#cccccc', axis='y')

    return fig
