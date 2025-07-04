"""
Compact vision distribution visualization for protocol comparison.

This module provides a compact visualization of baseline vision distributions
for use in the protocol comparison page.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from typing import Dict, Any, Optional, Tuple
from simulation_v2.models.baseline_vision_distributions import (
    NormalDistribution, BetaWithThresholdDistribution, UniformDistribution,
    DistributionFactory
)
from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS


def create_compact_vision_distribution_plot(
    distribution_config: Dict[str, Any],
    figsize: Tuple[float, float] = (1.0, 0.25),
    show_stats: bool = True,
    title: Optional[str] = None
) -> plt.Figure:
    """
    Create a compact vision distribution plot for protocol comparison.
    
    Parameters
    ----------
    distribution_config : Dict[str, Any]
        Configuration dictionary for the distribution with 'type' and parameters
    figsize : Tuple[float, float], optional
        Figure size in inches, by default (4, 3)
    show_stats : bool, optional
        Whether to show distribution statistics, by default True
    title : str, optional
        Plot title, by default uses distribution description
        
    Returns
    -------
    plt.Figure
        The matplotlib figure object
    """
    # Create the distribution object
    dist = DistributionFactory.create_distribution(distribution_config)
    dist_type = distribution_config.get('type', 'normal')
    
    # Create figure and axis with lower DPI for smaller size
    fig, ax = plt.subplots(figsize=figsize, dpi=72)
    x = np.linspace(0, 100, 1000)
    
    # Plot based on distribution type
    if dist_type == 'normal':
        mean = distribution_config.get('mean', 70)
        std = distribution_config.get('std', 10)
        min_val = distribution_config.get('min', 20)
        max_val = distribution_config.get('max', 90)
        
        # Plot PDF
        y = stats.norm.pdf(x, mean, std)
        ax.plot(x, y, color=SEMANTIC_COLORS['acuity_data'], linewidth=2)
        
        # Shade allowed range
        ax.fill_between(x, 0, y, where=(x >= min_val) & (x <= max_val), 
                       alpha=ALPHAS['low'], color=SEMANTIC_COLORS['acuity_data'])
        
        # Stats text
        if show_stats:
            stats_text = f'μ={mean:.0f}, σ={std:.0f}'
            ax.text(0.95, 0.95, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', horizontalalignment='right',
                   fontsize=8, bbox=dict(boxstyle='round,pad=0.3', 
                   facecolor='white', alpha=0.8))
    
    elif dist_type == 'beta_with_threshold':
        # Use the distribution's pre-calculated PDF
        beta_dist = dist
        ax.plot(beta_dist.x_values, beta_dist.pdf, 
               color=SEMANTIC_COLORS['acuity_data'], linewidth=2)
        
        # Show threshold line
        threshold = distribution_config.get('threshold', 70)
        ax.axvline(threshold, color=COLORS['secondary'], linestyle='--', 
                  alpha=0.5, linewidth=1)
        
        # Calculate and show statistics
        if show_stats:
            samples = [dist.sample() for _ in range(5000)]
            mean_val = np.mean(samples)
            pct_above_70 = sum(s > 70 for s in samples) / len(samples) * 100
            
            stats_text = f'Mean: {mean_val:.0f}\n>70: {pct_above_70:.0f}%'
            ax.text(0.95, 0.95, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', horizontalalignment='right',
                   fontsize=8, bbox=dict(boxstyle='round,pad=0.3', 
                   facecolor='white', alpha=0.8))
    
    elif dist_type == 'uniform':
        min_val = distribution_config.get('min', 20)
        max_val = distribution_config.get('max', 90)
        
        # Plot uniform distribution
        y = np.zeros_like(x)
        mask = (x >= min_val) & (x <= max_val)
        y[mask] = 1.0 / (max_val - min_val)
        ax.plot(x, y, color=SEMANTIC_COLORS['acuity_data'], linewidth=2)
        ax.fill_between(x, 0, y, where=mask, alpha=ALPHAS['low'], 
                       color=SEMANTIC_COLORS['acuity_data'])
        
        # Stats text
        if show_stats:
            mean_val = (min_val + max_val) / 2
            stats_text = f'[{min_val}, {max_val}]\nMean: {mean_val:.0f}'
            ax.text(0.95, 0.95, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', horizontalalignment='right',
                   fontsize=8, bbox=dict(boxstyle='round,pad=0.3', 
                   facecolor='white', alpha=0.8))
    
    # Minimal styling - no labels, no title, no axis
    ax.set_xlim(0, 100)
    ax.set_ylim(bottom=0)
    
    # Remove all spines and ticks
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    
    # No tick labels
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Add subtle vertical lines at 20 and 70
    ax.axvline(20, color='gray', alpha=0.3, linewidth=0.5)
    ax.axvline(70, color='gray', alpha=0.3, linewidth=0.5)
    
    # Remove margins
    ax.margins(0)
    
    plt.tight_layout(pad=0)
    return fig


def get_distribution_summary_stats(distribution_config: Dict[str, Any]) -> Dict[str, float]:
    """
    Get summary statistics for a distribution configuration.
    
    Parameters
    ----------
    distribution_config : Dict[str, Any]
        Configuration dictionary for the distribution
        
    Returns
    -------
    Dict[str, float]
        Dictionary containing:
        - mean: Expected value
        - median: Median value
        - std: Standard deviation
        - pct_above_70: Percentage above 70 ETDRS letters
        - q25: 25th percentile
        - q75: 75th percentile
    """
    dist = DistributionFactory.create_distribution(distribution_config)
    
    # Sample to estimate statistics
    samples = [dist.sample() for _ in range(10000)]
    
    return {
        'mean': np.mean(samples),
        'median': np.median(samples),
        'std': np.std(samples),
        'pct_above_70': sum(s > 70 for s in samples) / len(samples) * 100,
        'q25': np.percentile(samples, 25),
        'q75': np.percentile(samples, 75)
    }