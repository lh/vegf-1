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
    figsize: Tuple[float, float] = (4, 3),
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
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize, dpi=100)
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
    
    # Styling
    ax.set_xlabel('Baseline Vision (ETDRS)', fontsize=9)
    ax.set_ylabel('Density', fontsize=9)
    if title:
        ax.set_title(title, fontsize=10, pad=5)
    else:
        ax.set_title(dist.get_description(), fontsize=9, pad=5)
    
    ax.set_xlim(0, 100)
    ax.set_ylim(bottom=0)
    
    # Clean styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='both', which='major', labelsize=8)
    ax.grid(True, axis='y', alpha=0.2)
    
    # Only show x-axis at key points
    ax.set_xticks([0, 20, 40, 60, 70, 80, 100])
    
    plt.tight_layout()
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