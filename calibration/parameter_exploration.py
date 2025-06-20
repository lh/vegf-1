#!/usr/bin/env python3
"""
Parameter exploration tool for systematic grid search of Eylea parameters.

This tool explores parameter ranges systematically to find optimal values.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
import numpy as np
import itertools
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

from eylea_calibration_framework import EyleaCalibrationFramework, ParameterSet, CalibrationResult


@dataclass
class ParameterRange:
    """Define a range of values for a parameter."""
    name: str
    values: List[Any]
    description: str


class ParameterExplorer:
    """Systematic exploration of parameter space."""
    
    def __init__(self, base_protocol_path: str = "protocols/v2/eylea_treat_and_extend_v1.0.yaml"):
        self.framework = EyleaCalibrationFramework(base_protocol_path)
        self.parameter_ranges: List[ParameterRange] = []
        self.results: List[CalibrationResult] = []
        
    def add_parameter_range(self, name: str, values: List[Any], description: str = ""):
        """Add a parameter to explore."""
        self.parameter_ranges.append(ParameterRange(name, values, description))
    
    def generate_parameter_combinations(self) -> List[Dict[str, Any]]:
        """Generate all combinations of parameters."""
        if not self.parameter_ranges:
            return [{}]
        
        # Create all combinations
        param_names = [p.name for p in self.parameter_ranges]
        param_values = [p.values for p in self.parameter_ranges]
        
        combinations = []
        for values in itertools.product(*param_values):
            combo = dict(zip(param_names, values))
            combinations.append(combo)
        
        return combinations
    
    def create_parameter_set(self, combo: Dict[str, Any], index: int) -> ParameterSet:
        """Create a ParameterSet from a combination dictionary."""
        # Start with default values
        params = ParameterSet(
            name=f"exploration_{index}",
            description=f"Parameter combination {index}"
        )
        
        # Update with combination values
        for key, value in combo.items():
            if hasattr(params, key):
                setattr(params, key, value)
        
        return params
    
    def test_single_combination(self, combo: Dict[str, Any], index: int, n_patients: int = 100) -> CalibrationResult:
        """Test a single parameter combination."""
        params = self.create_parameter_set(combo, index)
        framework = EyleaCalibrationFramework()
        result = framework.test_parameters(params, n_patients=n_patients)
        return result
    
    def explore_parallel(self, n_patients: int = 100, max_workers: int = None):
        """Explore parameter space in parallel."""
        combinations = self.generate_parameter_combinations()
        print(f"Testing {len(combinations)} parameter combinations...")
        
        if max_workers is None:
            max_workers = max(1, multiprocessing.cpu_count() - 1)
        
        # Run in parallel
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_combo = {
                executor.submit(self.test_single_combination, combo, i, n_patients): (combo, i)
                for i, combo in enumerate(combinations)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_combo):
                combo, index = future_to_combo[future]
                try:
                    result = future.result()
                    self.results.append(result)
                    print(f"Completed combination {index + 1}/{len(combinations)}: score = {result.total_score:.2f}")
                except Exception as exc:
                    print(f"Combination {index} generated an exception: {exc}")
    
    def explore(self, n_patients: int = 100):
        """Explore parameter space (single-threaded version)."""
        combinations = self.generate_parameter_combinations()
        print(f"Testing {len(combinations)} parameter combinations...")
        
        for i, combo in enumerate(combinations):
            print(f"\nTesting combination {i + 1}/{len(combinations)}")
            print(f"Parameters: {combo}")
            
            params = self.create_parameter_set(combo, i)
            result = self.framework.test_parameters(params, n_patients=n_patients)
            self.results.append(result)
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze exploration results to find patterns."""
        if not self.results:
            return {}
        
        # Sort by total score
        sorted_results = sorted(self.results, key=lambda r: r.total_score)
        
        # Find best combination
        best = sorted_results[0]
        
        # Analyze parameter importance
        param_impacts = {}
        for param_range in self.parameter_ranges:
            param_name = param_range.name
            impacts = []
            
            for value in param_range.values:
                # Get all results with this parameter value
                matching_results = [r for r in self.results 
                                  if getattr(r.parameter_set, param_name) == value]
                if matching_results:
                    avg_score = np.mean([r.total_score for r in matching_results])
                    impacts.append((value, avg_score))
            
            param_impacts[param_name] = sorted(impacts, key=lambda x: x[1])
        
        return {
            'best_result': best,
            'top_10_results': sorted_results[:10],
            'parameter_impacts': param_impacts
        }
    
    def save_exploration_results(self, output_path: str = "calibration/exploration_results.json"):
        """Save detailed exploration results."""
        data = {
            'parameter_ranges': [
                {
                    'name': p.name,
                    'values': p.values,
                    'description': p.description
                }
                for p in self.parameter_ranges
            ],
            'results': [
                {
                    'index': i,
                    'parameters': {
                        p.name: getattr(result.parameter_set, p.name)
                        for p in self.parameter_ranges
                    },
                    'outcomes': {
                        'vision_gain_year1': result.vision_gain_year1,
                        'vision_year2': result.vision_year2,
                        'injections_year1': result.injections_year1,
                        'injections_year2': result.injections_year2,
                        'discontinuation_year1': result.discontinuation_year1,
                        'discontinuation_year2': result.discontinuation_year2
                    },
                    'scores': {
                        'vision_score': result.vision_score,
                        'injection_score': result.injection_score,
                        'discontinuation_score': result.discontinuation_score,
                        'total_score': result.total_score
                    }
                }
                for i, result in enumerate(sorted(self.results, key=lambda r: r.total_score))
            ],
            'analysis': self.analyze_results()
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"\nExploration results saved to {output_path}")
    
    def plot_parameter_impacts(self):
        """Visualize the impact of each parameter on outcomes."""
        analysis = self.analyze_results()
        param_impacts = analysis['parameter_impacts']
        
        if not param_impacts:
            print("No results to plot")
            return
        
        # Create subplots for each parameter
        n_params = len(param_impacts)
        fig, axes = plt.subplots(1, n_params, figsize=(5 * n_params, 6))
        if n_params == 1:
            axes = [axes]
        
        for i, (param_name, impacts) in enumerate(param_impacts.items()):
            values = [str(v) for v, _ in impacts]
            scores = [s for _, s in impacts]
            
            axes[i].bar(values, scores)
            axes[i].set_xlabel(param_name.replace('_', ' ').title())
            axes[i].set_ylabel('Average Total Score')
            axes[i].set_title(f'Impact of {param_name.replace("_", " ").title()}')
            
            # Rotate labels if needed
            if len(values) > 5:
                axes[i].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('calibration/parameter_impacts.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_outcome_heatmap(self):
        """Create heatmap of outcomes for different parameter combinations."""
        if len(self.parameter_ranges) != 2:
            print("Heatmap requires exactly 2 parameters to explore")
            return
        
        # Get parameter names and values
        param1 = self.parameter_ranges[0]
        param2 = self.parameter_ranges[1]
        
        # Create matrices for each outcome
        n1, n2 = len(param1.values), len(param2.values)
        vision_matrix = np.zeros((n1, n2))
        injection_matrix = np.zeros((n1, n2))
        discontinuation_matrix = np.zeros((n1, n2))
        score_matrix = np.zeros((n1, n2))
        
        # Fill matrices
        for result in self.results:
            i = param1.values.index(getattr(result.parameter_set, param1.name))
            j = param2.values.index(getattr(result.parameter_set, param2.name))
            
            vision_matrix[i, j] = result.vision_gain_year1
            injection_matrix[i, j] = result.injections_year1
            discontinuation_matrix[i, j] = result.discontinuation_year2
            score_matrix[i, j] = result.total_score
        
        # Create heatmaps
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Vision gain heatmap
        sns.heatmap(vision_matrix, annot=True, fmt='.1f', 
                   xticklabels=param2.values, yticklabels=param1.values,
                   ax=axes[0, 0], cmap='RdYlGn', center=9.0)
        axes[0, 0].set_title('Vision Gain Year 1')
        axes[0, 0].set_xlabel(param2.name.replace('_', ' ').title())
        axes[0, 0].set_ylabel(param1.name.replace('_', ' ').title())
        
        # Injections heatmap
        sns.heatmap(injection_matrix, annot=True, fmt='.1f',
                   xticklabels=param2.values, yticklabels=param1.values,
                   ax=axes[0, 1], cmap='RdYlGn_r', center=7.5)
        axes[0, 1].set_title('Injections Year 1')
        axes[0, 1].set_xlabel(param2.name.replace('_', ' ').title())
        axes[0, 1].set_ylabel(param1.name.replace('_', ' ').title())
        
        # Discontinuation heatmap
        sns.heatmap(discontinuation_matrix * 100, annot=True, fmt='.1f',
                   xticklabels=param2.values, yticklabels=param1.values,
                   ax=axes[1, 0], cmap='RdYlGn_r', center=12.5)
        axes[1, 0].set_title('Discontinuation Year 2 (%)')
        axes[1, 0].set_xlabel(param2.name.replace('_', ' ').title())
        axes[1, 0].set_ylabel(param1.name.replace('_', ' ').title())
        
        # Total score heatmap
        sns.heatmap(score_matrix, annot=True, fmt='.1f',
                   xticklabels=param2.values, yticklabels=param1.values,
                   ax=axes[1, 1], cmap='RdYlGn_r')
        axes[1, 1].set_title('Total Score (lower is better)')
        axes[1, 1].set_xlabel(param2.name.replace('_', ' ').title())
        axes[1, 1].set_ylabel(param1.name.replace('_', ' ').title())
        
        plt.tight_layout()
        plt.savefig('calibration/outcome_heatmap.png', dpi=300, bbox_inches='tight')
        plt.show()


def run_focused_exploration():
    """Run a focused exploration on key parameters."""
    explorer = ParameterExplorer()
    
    # Define parameter ranges to explore
    # Focus on discontinuation rates and response heterogeneity
    
    explorer.add_parameter_range(
        'discontinuation_year1',
        [0.03, 0.05, 0.08, 0.10, 0.125],
        'Year 1 discontinuation rate'
    )
    
    explorer.add_parameter_range(
        'discontinuation_year2',
        [0.10, 0.125, 0.15, 0.18],
        'Year 2 discontinuation rate'
    )
    
    explorer.add_parameter_range(
        'good_responder_ratio',
        [0.25, 0.30, 0.35, 0.40],
        'Proportion of good responders'
    )
    
    explorer.add_parameter_range(
        'good_responder_multiplier',
        [1.3, 1.5, 1.7, 2.0],
        'Vision response multiplier for good responders'
    )
    
    # Run exploration
    print("Starting focused parameter exploration...")
    explorer.explore(n_patients=150)  # Use fewer patients for faster exploration
    
    # Save and analyze results
    explorer.save_exploration_results("calibration/focused_exploration_results.json")
    explorer.plot_parameter_impacts()
    
    # Print best combination
    analysis = explorer.analyze_results()
    if 'best_result' in analysis:
        best = analysis['best_result']
        print(f"\n{'='*60}")
        print("BEST PARAMETER COMBINATION:")
        print(f"Total Score: {best.total_score:.2f}")
        print("\nParameters:")
        for param in explorer.parameter_ranges:
            value = getattr(best.parameter_set, param.name)
            print(f"  {param.name}: {value}")
        print("\nOutcomes:")
        print(f"  Vision gain Y1: {best.vision_gain_year1:.1f} letters")
        print(f"  Vision Y2: {best.vision_year2:.1f} letters")
        print(f"  Injections Y1: {best.injections_year1:.1f}")
        print(f"  Injections Y2: {best.injections_year2:.1f}")
        print(f"  Discontinuation Y2: {best.discontinuation_year2:.1%}")
        print(f"{'='*60}")


def run_2d_exploration():
    """Run a 2D exploration for heatmap visualization."""
    explorer = ParameterExplorer()
    
    # Explore 2 key parameters for heatmap
    explorer.add_parameter_range(
        'discontinuation_year2',
        [0.08, 0.10, 0.125, 0.15, 0.18],
        'Year 2 discontinuation rate'
    )
    
    explorer.add_parameter_range(
        'good_responder_multiplier',
        [1.2, 1.4, 1.6, 1.8, 2.0],
        'Good responder vision multiplier'
    )
    
    # Run exploration
    print("Starting 2D parameter exploration for heatmap...")
    explorer.explore(n_patients=150)
    
    # Save and visualize
    explorer.save_exploration_results("calibration/2d_exploration_results.json")
    explorer.plot_outcome_heatmap()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "2d":
        run_2d_exploration()
    else:
        run_focused_exploration()