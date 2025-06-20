#!/usr/bin/env python3
"""
Calibration framework for Eylea treat-and-extend protocol parameters.

This framework helps find optimal parameter values by comparing simulation
outcomes to known clinical trial results (VIEW trials, 2-year data).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from pathlib import Path
import yaml
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.core.simulation_runner import ABSEngineWithSpecs
from simulation_v2.clinical_improvements import ClinicalImprovements


@dataclass
class EyleaCalibrationTarget:
    """Target values from VIEW trials (2-year data)."""
    # Vision outcomes (ETDRS letters)
    VISION_GAIN_YEAR1_MEAN = 9.0      # VIEW trials: 8-10 letters
    VISION_GAIN_YEAR1_STD = 1.0       # Acceptable range
    VISION_YEAR2_MEAN = 8.0           # Slight decline from peak
    VISION_YEAR2_STD = 1.5            # Acceptable range
    
    # Injection counts
    INJECTIONS_YEAR1_MEAN = 7.5       # VIEW: 7-8 injections
    INJECTIONS_YEAR1_STD = 0.5        # Acceptable range
    INJECTIONS_YEAR2_MEAN = 5.5       # VIEW: 5-6 injections
    INJECTIONS_YEAR2_STD = 0.5        # Acceptable range
    
    # Discontinuation rates
    DISCONTINUATION_YEAR1_MEAN = 0.05  # 5% by year 1
    DISCONTINUATION_YEAR2_MEAN = 0.125 # 12.5% by year 2


@dataclass
class ParameterSet:
    """A set of parameters to test."""
    name: str
    description: str
    
    # Clinical improvements toggles
    use_loading_phase: bool = True
    use_time_based_discontinuation: bool = True
    use_response_based_vision: bool = True
    use_baseline_distribution: bool = True
    use_response_heterogeneity: bool = True
    
    # Response heterogeneity parameters
    good_responder_ratio: float = 0.3
    average_responder_ratio: float = 0.5
    poor_responder_ratio: float = 0.2
    
    # Vision response multipliers
    good_responder_multiplier: float = 1.5
    average_responder_multiplier: float = 1.0
    poor_responder_multiplier: float = 0.5
    
    # Time-based discontinuation rates (annual)
    discontinuation_year1: float = 0.125
    discontinuation_year2: float = 0.15
    discontinuation_year3: float = 0.12
    discontinuation_year4: float = 0.08
    discontinuation_year5_plus: float = 0.075
    
    # Protocol-specific parameters
    protocol_interval: int = 56  # Days between visits after loading


@dataclass
class CalibrationResult:
    """Results from a single calibration run."""
    parameter_set: ParameterSet
    
    # Actual outcomes
    vision_gain_year1: float
    vision_year2: float
    injections_year1: float
    injections_year2: float
    discontinuation_year1: float
    discontinuation_year2: float
    
    # Scores (lower is better)
    vision_score: float
    injection_score: float
    discontinuation_score: float
    total_score: float
    
    # Raw data for detailed analysis
    patient_data: Optional[pd.DataFrame] = None


class EyleaCalibrationFramework:
    """Framework for calibrating Eylea protocol parameters."""
    
    def __init__(self, base_protocol_path: str = "protocols/v2/eylea_treat_and_extend_v1.0.yaml"):
        self.base_protocol_path = Path(base_protocol_path)
        self.targets = EyleaCalibrationTarget()
        self.results: List[CalibrationResult] = []
        
    def create_test_protocol(self, params: ParameterSet, output_path: Path) -> Path:
        """Create a test protocol with specified parameters."""
        # Load base protocol
        with open(self.base_protocol_path) as f:
            protocol = yaml.safe_load(f)
        
        # Add clinical improvements section
        protocol['clinical_improvements'] = {
            'enabled': True,
            'use_loading_phase': params.use_loading_phase,
            'use_time_based_discontinuation': params.use_time_based_discontinuation,
            'use_response_based_vision': params.use_response_based_vision,
            'use_baseline_distribution': params.use_baseline_distribution,
            'use_response_heterogeneity': params.use_response_heterogeneity,
            'response_types': {
                'good': {
                    'probability': params.good_responder_ratio,
                    'multiplier': params.good_responder_multiplier
                },
                'average': {
                    'probability': params.average_responder_ratio,
                    'multiplier': params.average_responder_multiplier
                },
                'poor': {
                    'probability': params.poor_responder_ratio,
                    'multiplier': params.poor_responder_multiplier
                }
            },
            'discontinuation_probabilities': {
                1: params.discontinuation_year1,
                2: params.discontinuation_year2,
                3: params.discontinuation_year3,
                4: params.discontinuation_year4,
                5: params.discontinuation_year5_plus
            }
        }
        
        # Update protocol interval if specified
        if hasattr(params, 'protocol_interval'):
            protocol['min_interval_days'] = params.protocol_interval
            protocol['max_interval_days'] = max(params.protocol_interval * 2, 112)
        
        # Save test protocol
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(protocol, f, sort_keys=False)
        
        return output_path
    
    def run_simulation(self, protocol_path: Path, n_patients: int = 200, 
                      simulation_months: int = 24) -> Dict:
        """Run simulation with given protocol."""
        # Load protocol specification
        spec = ProtocolSpecification.from_yaml(protocol_path)
        
        # Create disease model and protocol
        disease_model = DiseaseModel(
            transition_probabilities=spec.disease_transitions,
            treatment_effect_multipliers=spec.treatment_effect_on_transitions
        )
        protocol = StandardProtocol(
            min_interval_days=spec.min_interval_days,
            max_interval_days=spec.max_interval_days,
            extension_days=spec.extension_days,
            shortening_days=spec.shortening_days
        )
        
        # Check if clinical improvements are enabled
        clinical_improvements = None
        if hasattr(spec, 'clinical_improvements') and spec.clinical_improvements:
            improvements_config = spec.clinical_improvements
            if improvements_config.get('enabled', False):
                # Create clinical improvements config
                config_data = {
                    'use_loading_phase': improvements_config.get('use_loading_phase', False),
                    'use_time_based_discontinuation': improvements_config.get('use_time_based_discontinuation', False),
                    'use_response_based_vision': improvements_config.get('use_response_based_vision', False),
                    'use_baseline_distribution': improvements_config.get('use_baseline_distribution', False),
                    'use_response_heterogeneity': improvements_config.get('use_response_heterogeneity', False)
                }
                
                # Add optional parameters if present
                if 'response_types' in improvements_config:
                    config_data['response_types'] = improvements_config['response_types']
                if 'discontinuation_probabilities' in improvements_config:
                    config_data['discontinuation_probabilities'] = improvements_config['discontinuation_probabilities']
                    
                clinical_improvements = ClinicalImprovements(**config_data)
        
        # Create and run engine
        engine = ABSEngineWithSpecs(
            disease_model=disease_model,
            protocol=protocol,
            protocol_spec=spec,
            n_patients=n_patients,
            seed=42,  # Fixed seed for reproducibility
            clinical_improvements=clinical_improvements
        )
        
        results = engine.run(
            duration_years=simulation_months / 12.0  # Convert months to years
        )
        
        return results
    
    def analyze_results(self, results) -> Tuple[float, float, float, float, float, float]:
        """Extract key metrics from simulation results."""
        # Access patient histories from SimulationResults object
        patient_histories = results.patient_histories
        
        # Convert to DataFrame for easier analysis
        records = []
        for patient_id, patient in patient_histories.items():
            # Patient histories are Patient objects, not dicts
            for visit in patient.visit_history:
                # Calculate time in months from enrollment
                if hasattr(patient, 'enrollment_date') and patient.enrollment_date:
                    enrollment_date = patient.enrollment_date
                else:
                    enrollment_date = visit['date']
                
                time_months = (visit['date'] - enrollment_date).days / 30.44
                
                records.append({
                    'patient_id': patient_id,
                    'time': time_months,
                    'vision': visit['vision'],
                    'received_injection': visit['treatment_given'],
                    'discontinuation_type': visit.get('discontinuation_type'),
                    'is_discontinuation_visit': patient.is_discontinued and visit == patient.visit_history[-1]
                })
        
        df = pd.DataFrame(records)
        
        # Calculate metrics
        baseline_vision = {}
        year1_vision = {}
        year2_vision = {}
        injections_year1 = {}
        injections_year2 = {}
        discontinued_year1 = set()
        discontinued_year2 = set()
        
        for patient_id in patient_histories:
            patient_df = df[df['patient_id'] == patient_id].sort_values('time')
            
            # Baseline vision (first visit)
            baseline_vision[patient_id] = patient_df.iloc[0]['vision']
            
            # Year 1 metrics (around month 12)
            year1_df = patient_df[patient_df['time'] <= 12]
            if not year1_df.empty:
                year1_vision[patient_id] = year1_df.iloc[-1]['vision']
                injections_year1[patient_id] = year1_df['received_injection'].sum()
                if year1_df['is_discontinuation_visit'].any():
                    discontinued_year1.add(patient_id)
            
            # Year 2 metrics (around month 24)
            year2_df = patient_df[patient_df['time'] <= 24]
            year2_only_df = patient_df[(patient_df['time'] > 12) & (patient_df['time'] <= 24)]
            if not year2_df.empty:
                year2_vision[patient_id] = year2_df.iloc[-1]['vision']
                injections_year2[patient_id] = year2_only_df['received_injection'].sum()
                if year2_df['is_discontinuation_visit'].any():
                    discontinued_year2.add(patient_id)
        
        # Calculate aggregate metrics
        vision_gains_year1 = [year1_vision[pid] - baseline_vision[pid] 
                             for pid in year1_vision if pid in baseline_vision]
        vision_year2_values = [year2_vision[pid] - baseline_vision[pid] 
                              for pid in year2_vision if pid in baseline_vision]
        
        vision_gain_year1 = np.mean(vision_gains_year1) if vision_gains_year1 else 0
        vision_year2 = np.mean(vision_year2_values) if vision_year2_values else 0
        injections_year1_mean = np.mean(list(injections_year1.values())) if injections_year1 else 0
        injections_year2_mean = np.mean(list(injections_year2.values())) if injections_year2 else 0
        discontinuation_year1 = len(discontinued_year1) / len(patient_histories)
        discontinuation_year2 = len(discontinued_year2) / len(patient_histories)
        
        return (vision_gain_year1, vision_year2, injections_year1_mean, 
                injections_year2_mean, discontinuation_year1, discontinuation_year2)
    
    def calculate_scores(self, vision_gain_year1: float, vision_year2: float,
                        injections_year1: float, injections_year2: float,
                        discontinuation_year1: float, discontinuation_year2: float) -> Tuple[float, float, float, float]:
        """Calculate scores for each metric (lower is better)."""
        # Vision score
        vision_score = (
            abs(vision_gain_year1 - self.targets.VISION_GAIN_YEAR1_MEAN) / self.targets.VISION_GAIN_YEAR1_STD +
            abs(vision_year2 - self.targets.VISION_YEAR2_MEAN) / self.targets.VISION_YEAR2_STD
        )
        
        # Injection score
        injection_score = (
            abs(injections_year1 - self.targets.INJECTIONS_YEAR1_MEAN) / self.targets.INJECTIONS_YEAR1_STD +
            abs(injections_year2 - self.targets.INJECTIONS_YEAR2_MEAN) / self.targets.INJECTIONS_YEAR2_STD
        )
        
        # Discontinuation score
        discontinuation_score = (
            abs(discontinuation_year1 - self.targets.DISCONTINUATION_YEAR1_MEAN) * 20 +  # Weight year 1 less
            abs(discontinuation_year2 - self.targets.DISCONTINUATION_YEAR2_MEAN) * 40   # Weight year 2 more
        )
        
        # Total score (weighted sum)
        total_score = vision_score * 2 + injection_score * 1.5 + discontinuation_score
        
        return vision_score, injection_score, discontinuation_score, total_score
    
    def test_parameters(self, params: ParameterSet, n_patients: int = 200) -> CalibrationResult:
        """Test a single parameter set."""
        print(f"\nTesting parameter set: {params.name}")
        print(f"Description: {params.description}")
        
        # Create test protocol
        protocol_path = Path(f"calibration/test_protocols/{params.name}.yaml")
        self.create_test_protocol(params, protocol_path)
        
        # Run simulation
        results = self.run_simulation(protocol_path, n_patients=n_patients)
        
        # Analyze results
        metrics = self.analyze_results(results)
        vision_gain_year1, vision_year2, injections_year1, injections_year2, disc_year1, disc_year2 = metrics
        
        # Calculate scores
        scores = self.calculate_scores(*metrics)
        vision_score, injection_score, discontinuation_score, total_score = scores
        
        # Create result
        result = CalibrationResult(
            parameter_set=params,
            vision_gain_year1=vision_gain_year1,
            vision_year2=vision_year2,
            injections_year1=injections_year1,
            injections_year2=injections_year2,
            discontinuation_year1=disc_year1,
            discontinuation_year2=disc_year2,
            vision_score=vision_score,
            injection_score=injection_score,
            discontinuation_score=discontinuation_score,
            total_score=total_score
        )
        
        self.results.append(result)
        
        # Print summary
        print(f"\nResults:")
        print(f"  Vision gain Y1: {vision_gain_year1:.1f} letters (target: {self.targets.VISION_GAIN_YEAR1_MEAN})")
        print(f"  Vision Y2: {vision_year2:.1f} letters (target: {self.targets.VISION_YEAR2_MEAN})")
        print(f"  Injections Y1: {injections_year1:.1f} (target: {self.targets.INJECTIONS_YEAR1_MEAN})")
        print(f"  Injections Y2: {injections_year2:.1f} (target: {self.targets.INJECTIONS_YEAR2_MEAN})")
        print(f"  Discontinuation Y1: {disc_year1:.1%} (target: {self.targets.DISCONTINUATION_YEAR1_MEAN:.1%})")
        print(f"  Discontinuation Y2: {disc_year2:.1%} (target: {self.targets.DISCONTINUATION_YEAR2_MEAN:.1%})")
        print(f"\nScores (lower is better):")
        print(f"  Vision score: {vision_score:.2f}")
        print(f"  Injection score: {injection_score:.2f}")
        print(f"  Discontinuation score: {discontinuation_score:.2f}")
        print(f"  Total score: {total_score:.2f}")
        
        return result
    
    def save_results(self, output_path: str = "calibration/calibration_results.json"):
        """Save calibration results to file."""
        results_data = []
        for result in self.results:
            data = {
                'name': result.parameter_set.name,
                'description': result.parameter_set.description,
                'parameters': {
                    'use_loading_phase': result.parameter_set.use_loading_phase,
                    'use_time_based_discontinuation': result.parameter_set.use_time_based_discontinuation,
                    'use_response_based_vision': result.parameter_set.use_response_based_vision,
                    'use_baseline_distribution': result.parameter_set.use_baseline_distribution,
                    'use_response_heterogeneity': result.parameter_set.use_response_heterogeneity,
                    'good_responder_ratio': result.parameter_set.good_responder_ratio,
                    'average_responder_ratio': result.parameter_set.average_responder_ratio,
                    'poor_responder_ratio': result.parameter_set.poor_responder_ratio,
                    'good_responder_multiplier': result.parameter_set.good_responder_multiplier,
                    'average_responder_multiplier': result.parameter_set.average_responder_multiplier,
                    'poor_responder_multiplier': result.parameter_set.poor_responder_multiplier,
                    'discontinuation_year1': result.parameter_set.discontinuation_year1,
                    'discontinuation_year2': result.parameter_set.discontinuation_year2,
                    'protocol_interval': result.parameter_set.protocol_interval
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
            results_data.append(data)
        
        # Sort by total score
        results_data.sort(key=lambda x: x['scores']['total_score'])
        
        # Save to file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\nResults saved to {output_path}")
    
    def plot_results(self):
        """Create visualization of calibration results."""
        if not self.results:
            print("No results to plot")
            return
        
        # Sort results by total score
        sorted_results = sorted(self.results, key=lambda r: r.total_score)
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Eylea Parameter Calibration Results', fontsize=16)
        
        # Extract data for plotting
        names = [r.parameter_set.name for r in sorted_results[:10]]  # Top 10
        vision_y1 = [r.vision_gain_year1 for r in sorted_results[:10]]
        vision_y2 = [r.vision_year2 for r in sorted_results[:10]]
        inj_y1 = [r.injections_year1 for r in sorted_results[:10]]
        inj_y2 = [r.injections_year2 for r in sorted_results[:10]]
        disc_y1 = [r.discontinuation_year1 * 100 for r in sorted_results[:10]]
        disc_y2 = [r.discontinuation_year2 * 100 for r in sorted_results[:10]]
        
        # Plot each metric
        axes[0, 0].barh(names, vision_y1)
        axes[0, 0].axvline(self.targets.VISION_GAIN_YEAR1_MEAN, color='r', linestyle='--')
        axes[0, 0].set_xlabel('Vision Gain Year 1 (letters)')
        axes[0, 0].set_title('Vision Gain Year 1')
        
        axes[0, 1].barh(names, vision_y2)
        axes[0, 1].axvline(self.targets.VISION_YEAR2_MEAN, color='r', linestyle='--')
        axes[0, 1].set_xlabel('Vision Year 2 (letters)')
        axes[0, 1].set_title('Vision Year 2')
        
        axes[0, 2].barh(names, inj_y1)
        axes[0, 2].axvline(self.targets.INJECTIONS_YEAR1_MEAN, color='r', linestyle='--')
        axes[0, 2].set_xlabel('Injections Year 1')
        axes[0, 2].set_title('Injections Year 1')
        
        axes[1, 0].barh(names, inj_y2)
        axes[1, 0].axvline(self.targets.INJECTIONS_YEAR2_MEAN, color='r', linestyle='--')
        axes[1, 0].set_xlabel('Injections Year 2')
        axes[1, 0].set_title('Injections Year 2')
        
        axes[1, 1].barh(names, disc_y1)
        axes[1, 1].axvline(self.targets.DISCONTINUATION_YEAR1_MEAN * 100, color='r', linestyle='--')
        axes[1, 1].set_xlabel('Discontinuation Year 1 (%)')
        axes[1, 1].set_title('Discontinuation Year 1')
        
        axes[1, 2].barh(names, disc_y2)
        axes[1, 2].axvline(self.targets.DISCONTINUATION_YEAR2_MEAN * 100, color='r', linestyle='--')
        axes[1, 2].set_xlabel('Discontinuation Year 2 (%)')
        axes[1, 2].set_title('Discontinuation Year 2')
        
        plt.tight_layout()
        plt.savefig('calibration/calibration_results.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Create score comparison plot
        fig2, ax = plt.subplots(figsize=(10, 8))
        scores = [(r.parameter_set.name, r.vision_score, r.injection_score, 
                  r.discontinuation_score, r.total_score) for r in sorted_results[:10]]
        
        df_scores = pd.DataFrame(scores, columns=['Name', 'Vision', 'Injection', 'Discontinuation', 'Total'])
        df_scores.set_index('Name')[['Vision', 'Injection', 'Discontinuation']].plot(kind='barh', stacked=True, ax=ax)
        ax.set_xlabel('Score (lower is better)')
        ax.set_title('Component Scores for Top 10 Parameter Sets')
        plt.tight_layout()
        plt.savefig('calibration/score_breakdown.png', dpi=300, bbox_inches='tight')
        plt.show()


def main():
    """Run calibration with a few test parameter sets."""
    framework = EyleaCalibrationFramework()
    
    # Define test parameter sets
    test_sets = [
        # Baseline - all improvements enabled with default values
        ParameterSet(
            name="baseline",
            description="All improvements enabled with default values"
        ),
        
        # Adjusted discontinuation rates
        ParameterSet(
            name="lower_discontinuation",
            description="Lower discontinuation rates to match VIEW trials",
            discontinuation_year1=0.05,
            discontinuation_year2=0.125,
            discontinuation_year3=0.10,
            discontinuation_year4=0.08,
            discontinuation_year5_plus=0.05
        ),
        
        # Adjusted response heterogeneity
        ParameterSet(
            name="better_responders",
            description="More good responders (40/45/15 split)",
            good_responder_ratio=0.4,
            average_responder_ratio=0.45,
            poor_responder_ratio=0.15
        ),
        
        # Adjusted vision multipliers
        ParameterSet(
            name="stronger_response",
            description="Stronger vision response in good responders",
            good_responder_multiplier=1.8,
            average_responder_multiplier=1.2,
            poor_responder_multiplier=0.6
        ),
        
        # Combined adjustments
        ParameterSet(
            name="combined_v1",
            description="Combined: lower discontinuation + better responders",
            discontinuation_year1=0.05,
            discontinuation_year2=0.125,
            good_responder_ratio=0.35,
            average_responder_ratio=0.50,
            poor_responder_ratio=0.15,
            good_responder_multiplier=1.6,
            average_responder_multiplier=1.1,
            poor_responder_multiplier=0.6
        )
    ]
    
    # Test each parameter set
    for params in test_sets:
        framework.test_parameters(params, n_patients=200)
    
    # Save and visualize results
    framework.save_results()
    framework.plot_results()
    
    # Print best parameter set
    if framework.results:
        best = min(framework.results, key=lambda r: r.total_score)
        print(f"\n{'='*60}")
        print(f"BEST PARAMETER SET: {best.parameter_set.name}")
        print(f"Total Score: {best.total_score:.2f}")
        print(f"Description: {best.parameter_set.description}")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()