#!/usr/bin/env python3
"""
Systematic parameter exploration for Eylea calibration.
Allows testing specific parameter ranges to find optimal values.
"""

import numpy as np
from itertools import product
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Any
import json

# Add parent directory
import sys
sys.path.append(str(Path(__file__).parent.parent))

from eylea_calibration_framework import (
    run_simulation_with_params, 
    calculate_match_score,
    EyleaCalibrationTarget
)


class ParameterGrid:
    """Define parameter ranges to explore."""
    
    # Vision response parameters (with clinical improvements)
    VISION_LOADING_MEAN = [3.0, 3.5, 4.0, 4.5]  # Initial gain per month
    VISION_YEAR1_MEAN = [0.2, 0.3, 0.4, 0.5]    # Continued gain
    VISION_YEAR2_MEAN = [-0.2, -0.1, 0.0, 0.1]  # Plateau/slight decline
    
    # Discontinuation rates
    DISC_YEAR1 = [0.06, 0.08, 0.10, 0.12]  # Year 1 annual probability
    DISC_YEAR2 = [0.04, 0.06, 0.08, 0.10]  # Year 2 annual probability
    
    # Response heterogeneity
    GOOD_RESPONDER_PCT = [0.25, 0.30, 0.35]     # % of good responders
    GOOD_RESPONDER_MULT = [1.2, 1.3, 1.4]       # Vision gain multiplier
    POOR_RESPONDER_MULT = [0.5, 0.6, 0.7]       # Vision gain multiplier
    
    # Disease transition adjustments
    STABLE_TO_ACTIVE = [0.10, 0.12, 0.14, 0.16]  # Monthly probability
    TREATMENT_EFFECT_MULT = [1.3, 1.5, 1.7, 2.0]  # Treatment benefit


def create_focused_parameter_sets():
    """Create focused parameter combinations based on likely ranges."""
    
    parameter_sets = []
    
    # Test 1: Vision response curve variations
    for loading, year1, year2 in product(
        [3.5, 4.0, 4.5],
        [0.2, 0.3, 0.4],
        [-0.2, -0.1, 0.0]
    ):
        params = {
            "clinical_improvements": {
                "enabled": True,
                "use_loading_phase": True,
                "use_time_based_discontinuation": True,
                "use_response_based_vision": True,
                "use_baseline_distribution": True,
                "use_response_heterogeneity": True,
                "vision_response_parameters": {
                    "loading": {"mean": loading, "std": 1.0},
                    "year1": {"mean": year1, "std": 0.5},
                    "year2": {"mean": year2, "std": 0.5},
                    "year3plus": {"mean": -0.3, "std": 0.3}
                }
            }
        }
        parameter_sets.append({
            'name': f'vision_L{loading}_Y1_{year1}_Y2_{year2}',
            'params': params,
            'category': 'vision_response'
        })
    
    # Test 2: Discontinuation rate variations
    for disc_y1, disc_y2 in product([0.06, 0.08, 0.10], [0.04, 0.06, 0.08]):
        params = {
            "clinical_improvements": {
                "enabled": True,
                "use_loading_phase": True,
                "use_time_based_discontinuation": True,
                "use_response_based_vision": True,
                "use_baseline_distribution": True,
                "use_response_heterogeneity": True,
                "discontinuation_parameters": {
                    "annual_probabilities": {
                        1: disc_y1,
                        2: disc_y2,
                        3: disc_y2 * 0.8,
                        4: disc_y2 * 0.6,
                        5: disc_y2 * 0.6
                    }
                }
            }
        }
        parameter_sets.append({
            'name': f'disc_Y1_{int(disc_y1*100)}_Y2_{int(disc_y2*100)}',
            'params': params,
            'category': 'discontinuation'
        })
    
    return parameter_sets


def run_grid_search(protocol_path: Path, parameter_sets: List[Dict],
                   n_patients: int = 300, n_seeds: int = 3):
    """Run simulations for all parameter combinations with multiple seeds."""
    
    results = []
    
    print(f"Running {len(parameter_sets)} parameter combinations with {n_seeds} seeds each...")
    print(f"Total simulations: {len(parameter_sets) * n_seeds}")
    print("-" * 60)
    
    for i, param_info in enumerate(parameter_sets):
        print(f"\n[{i+1}/{len(parameter_sets)}] Testing: {param_info['name']}")
        
        # Run with multiple seeds
        seed_results = []
        for seed in range(42, 42 + n_seeds):
            try:
                metrics = run_simulation_with_params(
                    protocol_path,
                    param_info['params'],
                    n_patients=n_patients,
                    duration_years=2.0,
                    seed=seed
                )
                
                score, components = calculate_match_score(metrics)
                
                seed_results.append({
                    'metrics': metrics,
                    'score': score,
                    'components': components
                })
                
            except Exception as e:
                print(f"  Error with seed {seed}: {str(e)}")
        
        if seed_results:
            # Average across seeds
            avg_metrics = {}
            for key in seed_results[0]['metrics'].keys():
                values = [r['metrics'][key] for r in seed_results]
                avg_metrics[key] = np.mean(values)
                avg_metrics[f'{key}_std'] = np.std(values)
            
            avg_score = np.mean([r['score'] for r in seed_results])
            
            results.append({
                'name': param_info['name'],
                'category': param_info['category'],
                'params': param_info['params'],
                'metrics': avg_metrics,
                'score': avg_score,
                'n_seeds': len(seed_results)
            })
            
            # Print summary
            print(f"  Avg Score: {avg_score*100:.1f}%")
            print(f"  Vision Y1: {avg_metrics['vision_gain_year1_mean']:.1f}±{avg_metrics['vision_gain_year1_mean_std']:.1f}")
            print(f"  Injections Y1: {avg_metrics['year1_injections_mean']:.1f}±{avg_metrics['year1_injections_mean_std']:.1f}")
    
    return results


def analyze_sensitivity(results: List[Dict], output_dir: Path):
    """Analyze parameter sensitivity and create visualizations."""
    
    # Convert to DataFrame for easier analysis
    data = []
    for r in results:
        row = {
            'name': r['name'],
            'category': r['category'],
            'score': r['score'],
            **r['metrics']
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Create sensitivity plots by category
    categories = df['category'].unique()
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Parameter Sensitivity Analysis', fontsize=16)
    axes = axes.flatten()
    
    for i, category in enumerate(categories):
        if i >= len(axes):
            break
            
        ax = axes[i]
        cat_data = df[df['category'] == category].sort_values('score', ascending=False)
        
        # Create heatmap-style visualization
        scores = cat_data['score'].values * 100
        names = cat_data['name'].str.replace(f'{category}_', '').values
        
        bars = ax.barh(names[:10], scores[:10])  # Top 10
        
        # Color by score
        for bar, score in zip(bars, scores[:10]):
            if score >= 80:
                bar.set_color('green')
            elif score >= 60:
                bar.set_color('orange')
            else:
                bar.set_color('red')
        
        ax.set_xlabel('Match Score (%)')
        ax.set_title(f'{category.replace("_", " ").title()} Parameters')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'parameter_sensitivity.png', dpi=300, bbox_inches='tight')
    
    # Find correlations
    print("\nParameter Impact Analysis:")
    print("=" * 60)
    
    # Correlation between specific parameters and outcomes
    vision_params = df[df['category'] == 'vision_response'].copy()
    if len(vision_params) > 0:
        # Extract loading parameter from name
        vision_params['loading_gain'] = vision_params['name'].str.extract(r'L(\d+\.?\d*)')[0].astype(float)
        
        corr = vision_params[['loading_gain', 'vision_gain_year1_mean', 'score']].corr()
        print("\nVision Loading Gain Correlation:")
        print(f"  With Year 1 outcome: {corr.loc['loading_gain', 'vision_gain_year1_mean']:.3f}")
        print(f"  With overall score: {corr.loc['loading_gain', 'score']:.3f}")
    
    return df


def recommend_parameters(results_df: pd.DataFrame) -> Dict[str, Any]:
    """Recommend best parameters based on analysis."""
    
    # Find top performers
    top_5 = results_df.nlargest(5, 'score')
    
    print("\nTop 5 Parameter Combinations:")
    print("=" * 60)
    
    for idx, row in top_5.iterrows():
        print(f"\n{row['name']} (Score: {row['score']*100:.1f}%)")
        print(f"  Vision Y1: {row['vision_gain_year1_mean']:.1f} letters")
        print(f"  Vision Y2: {row['vision_gain_year2_mean']:.1f} letters")
        print(f"  Injections Y1: {row['year1_injections_mean']:.1f}")
        print(f"  Injections Y2: {row['year2_injections_mean']:.1f}")
        print(f"  Discontinuation: {row['discontinuation_rate']*100:.1f}%")
    
    # Best overall
    best = top_5.iloc[0]
    
    # Create recommendation
    recommendation = {
        'best_score': best['score'],
        'best_name': best['name'],
        'recommended_parameters': {
            'clinical_improvements': {
                'enabled': True,
                'use_loading_phase': True,
                'use_time_based_discontinuation': True,
                'use_response_based_vision': True,
                'use_baseline_distribution': True,
                'use_response_heterogeneity': True
            }
        },
        'key_outcomes': {
            'vision_gain_year1': best['vision_gain_year1_mean'],
            'vision_gain_year2': best['vision_gain_year2_mean'],
            'injections_year1': best['year1_injections_mean'],
            'injections_year2': best['year2_injections_mean'],
            'discontinuation_2year': best['discontinuation_rate']
        }
    }
    
    return recommendation


def main():
    """Run parameter exploration."""
    
    print("Eylea Parameter Exploration")
    print("=" * 60)
    
    # Setup
    protocol_path = Path(__file__).parent.parent / "protocols" / "v2" / "eylea_treat_and_extend_v1.0.yaml"
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Create parameter sets
    parameter_sets = create_focused_parameter_sets()
    
    # Run grid search
    results = run_grid_search(
        protocol_path, 
        parameter_sets,
        n_patients=300,  # Moderate size for exploration
        n_seeds=3        # Multiple seeds for stability
    )
    
    # Analyze results
    results_df = analyze_sensitivity(results, output_dir)
    
    # Save detailed results
    results_df.to_csv(output_dir / 'parameter_exploration_results.csv', index=False)
    
    # Get recommendations
    recommendation = recommend_parameters(results_df)
    
    # Save recommendation
    with open(output_dir / 'recommended_parameters.json', 'w') as f:
        json.dump(recommendation, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Analysis complete!")
    print(f"Results saved to: {output_dir}")
    print(f"Best score achieved: {recommendation['best_score']*100:.1f}%")
    
    return results_df, recommendation


if __name__ == "__main__":
    results_df, recommendation = main()