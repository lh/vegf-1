#!/usr/bin/env python3
"""
Framework for calibrating Eylea treat-and-extend simulation parameters
to match clinical trial data (VIEW and other studies).

Target outcomes from literature (2-year data):
- Vision gain Year 1: +8-10 letters
- Vision Year 2: Maintain or slight decline from peak
- Injections Year 1: 7-8
- Injections Year 2: 5-6
- Total 2-year injections: 12-14
- Discontinuation by Year 2: ~10-15%
"""

import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json
import matplotlib.pyplot as plt
import seaborn as sns

# Add parent directory to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.simulation_runner import SimulationRunner


class EyleaCalibrationTarget:
    """Target metrics from Eylea clinical trials."""
    
    # Vision outcomes (ETDRS letters)
    VISION_GAIN_YEAR1_MEAN = 9.0  # VIEW trials: 8-10 letters
    VISION_GAIN_YEAR1_RANGE = (7.0, 11.0)
    
    VISION_YEAR2_MEAN = 8.0  # Slight decline from peak
    VISION_YEAR2_RANGE = (6.0, 10.0)
    
    # Injection counts
    INJECTIONS_YEAR1_MEAN = 7.5
    INJECTIONS_YEAR1_RANGE = (7.0, 8.0)
    
    INJECTIONS_YEAR2_MEAN = 5.5  
    INJECTIONS_YEAR2_RANGE = (5.0, 6.0)
    
    INJECTIONS_2YEAR_TOTAL_MEAN = 13.0
    INJECTIONS_2YEAR_TOTAL_RANGE = (12.0, 14.0)
    
    # Discontinuation
    DISCONTINUATION_YEAR2_MEAN = 0.125  # 12.5%
    DISCONTINUATION_YEAR2_RANGE = (0.10, 0.15)
    
    # Extension success (% achieving 12+ week intervals)
    EXTENSION_SUCCESS_YEAR2 = 0.50  # ~50% on 12+ week intervals


class ParameterSet:
    """A set of parameters to test."""
    
    def __init__(self, name: str, description: str, params: Dict[str, Any]):
        self.name = name
        self.description = description
        self.params = params
        self.results = None
        self.score = None


def create_parameter_sets() -> List[ParameterSet]:
    """Create different parameter combinations to test."""
    
    parameter_sets = []
    
    # Baseline - current defaults
    parameter_sets.append(ParameterSet(
        name="baseline",
        description="Current default parameters",
        params={
            "clinical_improvements": {
                "enabled": False
            }
        }
    ))
    
    # With clinical improvements - default settings
    parameter_sets.append(ParameterSet(
        name="ci_default",
        description="Clinical improvements with default settings",
        params={
            "clinical_improvements": {
                "enabled": True,
                "use_loading_phase": True,
                "use_time_based_discontinuation": True,
                "use_response_based_vision": True,
                "use_baseline_distribution": False,
                "use_response_heterogeneity": True
            }
        }
    ))
    
    # Adjusted vision response
    parameter_sets.append(ParameterSet(
        name="ci_vision_adjusted",
        description="CI with adjusted vision response curve",
        params={
            "clinical_improvements": {
                "enabled": True,
                "use_loading_phase": True,
                "use_time_based_discontinuation": True,
                "use_response_based_vision": True,
                "use_baseline_distribution": True,  # More realistic baseline
                "use_response_heterogeneity": True,
                "vision_response_parameters": {
                    "loading": {"mean": 4.0, "std": 1.0},  # Stronger initial response
                    "year1": {"mean": 0.3, "std": 0.5},    # Slower gains
                    "year2": {"mean": -0.1, "std": 0.5},   # Slight decline
                    "year3plus": {"mean": -0.3, "std": 0.3}
                }
            }
        }
    ))
    
    # Adjusted discontinuation
    parameter_sets.append(ParameterSet(
        name="ci_disc_adjusted",
        description="CI with lower discontinuation rates",
        params={
            "clinical_improvements": {
                "enabled": True,
                "use_loading_phase": True,
                "use_time_based_discontinuation": True,
                "use_response_based_vision": True,
                "use_baseline_distribution": True,
                "use_response_heterogeneity": True,
                "discontinuation_parameters": {
                    "annual_probabilities": {
                        1: 0.08,   # 8% year 1 (was 12.5%)
                        2: 0.06,   # 6% year 2 (was 15%)
                        3: 0.05,
                        4: 0.04,
                        5: 0.04
                    }
                }
            }
        }
    ))
    
    # Combined adjustments
    parameter_sets.append(ParameterSet(
        name="ci_combined",
        description="CI with all adjustments",
        params={
            "clinical_improvements": {
                "enabled": True,
                "use_loading_phase": True,
                "use_time_based_discontinuation": True,
                "use_response_based_vision": True,
                "use_baseline_distribution": True,
                "use_response_heterogeneity": True,
                "vision_response_parameters": {
                    "loading": {"mean": 4.0, "std": 1.0},
                    "year1": {"mean": 0.3, "std": 0.5},
                    "year2": {"mean": -0.1, "std": 0.5},
                    "year3plus": {"mean": -0.3, "std": 0.3}
                },
                "discontinuation_parameters": {
                    "annual_probabilities": {
                        1: 0.08,
                        2: 0.06,
                        3: 0.05,
                        4: 0.04,
                        5: 0.04
                    }
                }
            }
        }
    ))
    
    # Disease transition adjustments
    parameter_sets.append(ParameterSet(
        name="disease_adjusted",
        description="Adjusted disease transition probabilities",
        params={
            "disease_transitions": {
                # More stable disease with treatment
                "STABLE": {"STABLE": 0.85, "ACTIVE": 0.14, "HIGHLY_ACTIVE": 0.01, "NAIVE": 0.0},
                "ACTIVE": {"STABLE": 0.25, "ACTIVE": 0.70, "HIGHLY_ACTIVE": 0.05, "NAIVE": 0.0},
                # Add other states...
            },
            "treatment_effect_on_transitions": {
                "ACTIVE": {
                    "multipliers": {
                        "STABLE": 1.5,  # More likely to stabilize
                        "ACTIVE": 0.8,  # Less likely to stay active
                        "HIGHLY_ACTIVE": 0.5  # Much less likely to worsen
                    }
                }
            }
        }
    ))
    
    return parameter_sets


def run_simulation_with_params(protocol_path: Path, params: Dict[str, Any], 
                               n_patients: int = 500, duration_years: float = 2.0,
                               seed: int = 42) -> Dict[str, Any]:
    """Run simulation with specific parameters and extract key metrics."""
    
    # Load base protocol
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Apply parameter overrides
    for key, value in params.items():
        if hasattr(spec, key):
            if isinstance(value, dict) and isinstance(getattr(spec, key), dict):
                # Update nested dict
                current = getattr(spec, key) or {}
                current.update(value)
                setattr(spec, key, current)
            else:
                setattr(spec, key, value)
    
    # Run simulation
    runner = SimulationRunner(spec)
    results = runner.run(
        engine_type='abs',
        n_patients=n_patients,
        duration_years=duration_years,
        seed=seed
    )
    
    # Extract detailed metrics
    metrics = extract_detailed_metrics(results, duration_years)
    
    return metrics


def extract_detailed_metrics(results, duration_years: float) -> Dict[str, Any]:
    """Extract detailed metrics for comparison with trial data."""
    
    metrics = {
        'total_patients': results.patient_count,
        'total_injections': results.total_injections,
        'mean_injections_per_patient': results.total_injections / results.patient_count,
        'final_vision_mean': results.final_vision_mean,
        'final_vision_std': results.final_vision_std,
        'discontinuation_rate': results.discontinuation_rate
    }
    
    # Analyze by time period
    year1_patients = 0
    year1_injections = 0
    year2_injections = 0
    vision_gains_year1 = []
    vision_gains_year2 = []
    extension_intervals = []
    
    for patient in results.patient_histories.values():
        if len(patient.visit_history) == 0:
            continue
            
        year1_patients += 1
        baseline_vision = patient.visit_history[0]['vision']
        
        # Year 1 analysis
        year1_visits = [v for v in patient.visit_history 
                       if (v['date'] - patient.enrollment_date).days <= 365]
        year1_injections += sum(1 for v in year1_visits if v['treatment_given'])
        
        if year1_visits:
            year1_final_vision = year1_visits[-1]['vision']
            vision_gains_year1.append(year1_final_vision - baseline_vision)
        
        # Year 2 analysis
        year2_visits = [v for v in patient.visit_history 
                       if 365 < (v['date'] - patient.enrollment_date).days <= 730]
        year2_injections += sum(1 for v in year2_visits if v['treatment_given'])
        
        if duration_years >= 2 and len(patient.visit_history) > 1:
            final_visit = patient.visit_history[-1]
            if (final_visit['date'] - patient.enrollment_date).days >= 365:
                vision_gains_year2.append(final_visit['vision'] - baseline_vision)
        
        # Extension intervals
        if len(patient.visit_history) >= 3:
            for i in range(1, len(patient.visit_history)):
                interval = (patient.visit_history[i]['date'] - 
                           patient.visit_history[i-1]['date']).days
                if interval > 0:
                    extension_intervals.append(interval)
    
    # Calculate aggregates
    metrics['year1_injections_mean'] = year1_injections / year1_patients if year1_patients > 0 else 0
    metrics['year2_injections_mean'] = year2_injections / year1_patients if year1_patients > 0 else 0
    metrics['vision_gain_year1_mean'] = np.mean(vision_gains_year1) if vision_gains_year1 else 0
    metrics['vision_gain_year1_std'] = np.std(vision_gains_year1) if vision_gains_year1 else 0
    metrics['vision_gain_year2_mean'] = np.mean(vision_gains_year2) if vision_gains_year2 else 0
    metrics['vision_gain_year2_std'] = np.std(vision_gains_year2) if vision_gains_year2 else 0
    
    # Extension success
    if extension_intervals:
        metrics['pct_12week_intervals'] = sum(1 for i in extension_intervals if i >= 84) / len(extension_intervals)
        metrics['median_interval'] = np.median(extension_intervals)
    else:
        metrics['pct_12week_intervals'] = 0
        metrics['median_interval'] = 0
    
    return metrics


def calculate_match_score(metrics: Dict[str, Any], targets: Any = EyleaCalibrationTarget) -> Tuple[float, Dict[str, float]]:
    """Calculate how well simulation matches target outcomes."""
    
    scores = {}
    
    # Vision gain Year 1 (weight: 25%)
    vision_y1_error = abs(metrics['vision_gain_year1_mean'] - targets.VISION_GAIN_YEAR1_MEAN)
    vision_y1_score = max(0, 1 - vision_y1_error / 5.0)  # 5 letter tolerance
    scores['vision_year1'] = vision_y1_score * 0.25
    
    # Vision Year 2 (weight: 20%)
    vision_y2_error = abs(metrics['vision_gain_year2_mean'] - targets.VISION_YEAR2_MEAN)
    vision_y2_score = max(0, 1 - vision_y2_error / 5.0)
    scores['vision_year2'] = vision_y2_score * 0.20
    
    # Injections Year 1 (weight: 20%)
    inj_y1_error = abs(metrics['year1_injections_mean'] - targets.INJECTIONS_YEAR1_MEAN)
    inj_y1_score = max(0, 1 - inj_y1_error / 2.0)  # 2 injection tolerance
    scores['injections_year1'] = inj_y1_score * 0.20
    
    # Injections Year 2 (weight: 15%)
    inj_y2_error = abs(metrics['year2_injections_mean'] - targets.INJECTIONS_YEAR2_MEAN)
    inj_y2_score = max(0, 1 - inj_y2_error / 2.0)
    scores['injections_year2'] = inj_y2_score * 0.15
    
    # Discontinuation (weight: 10%)
    disc_error = abs(metrics['discontinuation_rate'] - targets.DISCONTINUATION_YEAR2_MEAN)
    disc_score = max(0, 1 - disc_error / 0.10)  # 10% tolerance
    scores['discontinuation'] = disc_score * 0.10
    
    # Extension success (weight: 10%)
    ext_error = abs(metrics.get('pct_12week_intervals', 0) - targets.EXTENSION_SUCCESS_YEAR2)
    ext_score = max(0, 1 - ext_error / 0.20)  # 20% tolerance
    scores['extension_success'] = ext_score * 0.10
    
    total_score = sum(scores.values())
    
    return total_score, scores


def visualize_calibration_results(parameter_sets: List[ParameterSet], 
                                 save_path: Path = None):
    """Create visualization comparing parameter sets to targets."""
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Eylea Treat-and-Extend Calibration Results', fontsize=16)
    
    # Prepare data
    names = [ps.name for ps in parameter_sets if ps.results]
    
    # Vision gains
    ax = axes[0, 0]
    y1_gains = [ps.results['vision_gain_year1_mean'] for ps in parameter_sets if ps.results]
    y2_gains = [ps.results['vision_gain_year2_mean'] for ps in parameter_sets if ps.results]
    
    x = np.arange(len(names))
    width = 0.35
    
    ax.bar(x - width/2, y1_gains, width, label='Year 1', alpha=0.8)
    ax.bar(x + width/2, y2_gains, width, label='Year 2', alpha=0.8)
    ax.axhline(y=EyleaCalibrationTarget.VISION_GAIN_YEAR1_MEAN, color='red', 
               linestyle='--', label='Target Y1')
    ax.axhline(y=EyleaCalibrationTarget.VISION_YEAR2_MEAN, color='darkred', 
               linestyle='--', label='Target Y2')
    ax.set_ylabel('Vision Gain (ETDRS letters)')
    ax.set_title('Vision Gains vs Target')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Injection counts
    ax = axes[0, 1]
    y1_inj = [ps.results['year1_injections_mean'] for ps in parameter_sets if ps.results]
    y2_inj = [ps.results['year2_injections_mean'] for ps in parameter_sets if ps.results]
    
    ax.bar(x - width/2, y1_inj, width, label='Year 1', alpha=0.8)
    ax.bar(x + width/2, y2_inj, width, label='Year 2', alpha=0.8)
    ax.axhline(y=EyleaCalibrationTarget.INJECTIONS_YEAR1_MEAN, color='red', 
               linestyle='--', label='Target Y1')
    ax.axhline(y=EyleaCalibrationTarget.INJECTIONS_YEAR2_MEAN, color='darkred', 
               linestyle='--', label='Target Y2')
    ax.set_ylabel('Mean Injections')
    ax.set_title('Injection Frequency vs Target')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Discontinuation rates
    ax = axes[0, 2]
    disc_rates = [ps.results['discontinuation_rate'] * 100 for ps in parameter_sets if ps.results]
    
    ax.bar(names, disc_rates, alpha=0.8)
    ax.axhline(y=EyleaCalibrationTarget.DISCONTINUATION_YEAR2_MEAN * 100, 
               color='red', linestyle='--', label='Target')
    ax.fill_between([-0.5, len(names)-0.5], 
                    [EyleaCalibrationTarget.DISCONTINUATION_YEAR2_RANGE[0] * 100] * 2,
                    [EyleaCalibrationTarget.DISCONTINUATION_YEAR2_RANGE[1] * 100] * 2,
                    alpha=0.2, color='red', label='Target range')
    ax.set_ylabel('Discontinuation Rate (%)')
    ax.set_title('2-Year Discontinuation vs Target')
    ax.set_xticklabels(names, rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Match scores
    ax = axes[1, 0]
    scores = [ps.score * 100 for ps in parameter_sets if ps.score is not None]
    
    bars = ax.bar(names, scores, alpha=0.8)
    # Color code by score
    for bar, score in zip(bars, scores):
        if score >= 80:
            bar.set_color('green')
        elif score >= 60:
            bar.set_color('orange')
        else:
            bar.set_color('red')
    
    ax.set_ylabel('Match Score (%)')
    ax.set_title('Overall Match to Trial Data')
    ax.set_xticklabels(names, rotation=45)
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    
    # Extension success
    ax = axes[1, 1]
    ext_success = [ps.results.get('pct_12week_intervals', 0) * 100 
                   for ps in parameter_sets if ps.results]
    
    ax.bar(names, ext_success, alpha=0.8)
    ax.axhline(y=EyleaCalibrationTarget.EXTENSION_SUCCESS_YEAR2 * 100, 
               color='red', linestyle='--', label='Target')
    ax.set_ylabel('% Patients on 12+ Week Intervals')
    ax.set_title('Extension Success at Year 2')
    ax.set_xticklabels(names, rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Parameter summary table
    ax = axes[1, 2]
    ax.axis('tight')
    ax.axis('off')
    
    # Create summary table
    table_data = []
    for ps in parameter_sets:
        if ps.results and ps.score is not None:
            table_data.append([
                ps.name,
                f"{ps.score*100:.1f}%",
                ps.description
            ])
    
    table = ax.table(cellText=table_data,
                     colLabels=['Parameter Set', 'Score', 'Description'],
                     cellLoc='left',
                     loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def main():
    """Run calibration analysis."""
    
    print("Eylea Treat-and-Extend Calibration Analysis")
    print("=" * 60)
    
    # Setup
    protocol_path = Path(__file__).parent.parent / "protocols" / "v2" / "eylea_treat_and_extend_v1.0.yaml"
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Create parameter sets
    parameter_sets = create_parameter_sets()
    
    # Run simulations
    print(f"\nTesting {len(parameter_sets)} parameter combinations...")
    print("-" * 60)
    
    for i, param_set in enumerate(parameter_sets):
        print(f"\n[{i+1}/{len(parameter_sets)}] {param_set.name}: {param_set.description}")
        
        try:
            # Run simulation
            metrics = run_simulation_with_params(
                protocol_path,
                param_set.params,
                n_patients=500,  # Increase for final calibration
                duration_years=2.0,
                seed=42
            )
            
            param_set.results = metrics
            
            # Calculate match score
            score, component_scores = calculate_match_score(metrics)
            param_set.score = score
            
            # Print results
            print(f"  Vision gain Y1: {metrics['vision_gain_year1_mean']:.1f} letters (target: {EyleaCalibrationTarget.VISION_GAIN_YEAR1_MEAN})")
            print(f"  Vision gain Y2: {metrics['vision_gain_year2_mean']:.1f} letters (target: {EyleaCalibrationTarget.VISION_YEAR2_MEAN})")
            print(f"  Injections Y1: {metrics['year1_injections_mean']:.1f} (target: {EyleaCalibrationTarget.INJECTIONS_YEAR1_MEAN})")
            print(f"  Injections Y2: {metrics['year2_injections_mean']:.1f} (target: {EyleaCalibrationTarget.INJECTIONS_YEAR2_MEAN})")
            print(f"  Discontinuation: {metrics['discontinuation_rate']*100:.1f}% (target: {EyleaCalibrationTarget.DISCONTINUATION_YEAR2_MEAN*100:.1f}%)")
            print(f"  12+ week intervals: {metrics.get('pct_12week_intervals', 0)*100:.1f}% (target: {EyleaCalibrationTarget.EXTENSION_SUCCESS_YEAR2*100:.1f}%)")
            print(f"  → Match score: {score*100:.1f}%")
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            param_set.results = None
            param_set.score = 0
    
    # Find best parameter set
    best_set = max(parameter_sets, key=lambda ps: ps.score or 0)
    print(f"\n{'='*60}")
    print(f"BEST MATCH: {best_set.name} (score: {best_set.score*100:.1f}%)")
    print(f"Description: {best_set.description}")
    
    # Save detailed results
    results_data = []
    for ps in parameter_sets:
        if ps.results:
            result_row = {
                'name': ps.name,
                'description': ps.description,
                'score': ps.score,
                **ps.results,
                'params': json.dumps(ps.params)
            }
            results_data.append(result_row)
    
    results_df = pd.DataFrame(results_data)
    results_df.to_csv(output_dir / 'calibration_results.csv', index=False)
    print(f"\nDetailed results saved to: {output_dir / 'calibration_results.csv'}")
    
    # Create visualization
    fig = visualize_calibration_results(parameter_sets, 
                                       save_path=output_dir / 'calibration_comparison.png')
    print(f"Visualization saved to: {output_dir / 'calibration_comparison.png'}")
    
    # Save best parameters
    if best_set.params:
        with open(output_dir / 'best_parameters.json', 'w') as f:
            json.dump({
                'name': best_set.name,
                'score': best_set.score,
                'parameters': best_set.params,
                'metrics': best_set.results
            }, f, indent=2)
        print(f"Best parameters saved to: {output_dir / 'best_parameters.json'}")
    
    return parameter_sets, best_set


if __name__ == "__main__":
    parameter_sets, best_set = main()