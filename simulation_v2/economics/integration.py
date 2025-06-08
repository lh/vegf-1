"""
Economics Integration API for V2 simulations.

Provides a simple, clean API for adding economic analysis to V2 simulations.
"""

from typing import Union, Optional, Dict, Any
from pathlib import Path

from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.engines.abs_engine import ABSEngine
from simulation_v2.engines.des_engine import DESEngine
from simulation_v2.protocols.protocol_spec import ProtocolSpecification

from .cost_enhancer import create_v2_cost_enhancer
from .financial_results import FinancialResults
from .cost_config import CostConfig
from .cost_analyzer import CostAnalyzerV2
from .cost_tracker import CostTrackerV2


class EconomicsIntegration:
    """
    Simple API for adding economics to V2 simulations.
    
    This class provides factory methods and utilities to easily integrate
    cost tracking and financial analysis into V2 simulations.
    """
    
    @staticmethod
    def create_enhanced_engine(
        engine_type: str,
        protocol_spec: ProtocolSpecification,
        cost_config: CostConfig,
        n_patients: int,
        seed: Optional[int] = None,
        **kwargs
    ) -> Union[ABSEngine, DESEngine]:
        """
        Create a simulation engine with integrated cost tracking.
        
        This is the primary method for creating cost-aware simulations.
        It handles all the setup automatically.
        
        Args:
            engine_type: 'abs' or 'des'
            protocol_spec: V2 protocol specification
            cost_config: Cost configuration
            n_patients: Number of patients to simulate
            seed: Random seed for reproducibility
            **kwargs: Additional arguments passed to engine
            
        Returns:
            Configured engine with cost tracking enabled
            
        Example:
            >>> protocol = ProtocolSpecification.from_yaml("eylea.yaml")
            >>> costs = CostConfig.from_yaml("nhs_standard.yaml")
            >>> engine = EconomicsIntegration.create_enhanced_engine(
            ...     'abs', protocol, costs, n_patients=100
            ... )
            >>> results = engine.run(duration_years=2.0)
        """
        # Create disease model from protocol
        disease_model = DiseaseModel(
            transition_probabilities=protocol_spec.disease_transitions,
            treatment_effect_multipliers=protocol_spec.treatment_effect_on_transitions,
            seed=seed
        )
        
        # Create protocol instance
        protocol = StandardProtocol(
            min_interval_days=protocol_spec.min_interval_days,
            max_interval_days=protocol_spec.max_interval_days,
            extension_days=protocol_spec.extension_days,
            shortening_days=protocol_spec.shortening_days
        )
        
        # Create cost enhancer
        enhancer = create_v2_cost_enhancer(cost_config, protocol_spec.name)
        
        # Create appropriate engine with enhancement
        engine_class = ABSEngine if engine_type.lower() == 'abs' else DESEngine
        
        return engine_class(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=n_patients,
            seed=seed,
            visit_metadata_enhancer=enhancer,
            **kwargs
        )
    
    @staticmethod
    def analyze_results(
        results: 'SimulationResults',
        cost_config: CostConfig
    ) -> FinancialResults:
        """
        Analyze financial outcomes from simulation results.
        
        This method processes simulation results and returns comprehensive
        financial analysis.
        
        Args:
            results: V2 SimulationResults object
            cost_config: Cost configuration used for analysis
            
        Returns:
            FinancialResults with all financial metrics
            
        Example:
            >>> results = engine.run(duration_years=2.0)
            >>> financial = EconomicsIntegration.analyze_results(results, costs)
            >>> print(f"Cost per patient: £{financial.cost_per_patient:,.2f}")
        """
        # Create analyzer and tracker
        analyzer = CostAnalyzerV2(cost_config)
        tracker = CostTrackerV2(analyzer)
        
        # Process results
        tracker.process_v2_results(results)
        
        # Get financial results
        return tracker.get_financial_results(
            cost_config_name=cost_config.metadata.get('name', 'Unknown')
        )
    
    @staticmethod
    def create_from_files(
        engine_type: str,
        protocol_path: Union[str, Path],
        cost_config_path: Union[str, Path],
        n_patients: int,
        seed: Optional[int] = None,
        **kwargs
    ) -> Union[ABSEngine, DESEngine]:
        """
        Convenience method to create engine from file paths.
        
        Args:
            engine_type: 'abs' or 'des'
            protocol_path: Path to protocol YAML file
            cost_config_path: Path to cost configuration YAML file
            n_patients: Number of patients
            seed: Random seed
            **kwargs: Additional engine arguments
            
        Returns:
            Configured engine with cost tracking
            
        Example:
            >>> engine = EconomicsIntegration.create_from_files(
            ...     'abs',
            ...     'protocols/eylea.yaml',
            ...     'costs/nhs_standard.yaml',
            ...     n_patients=100
            ... )
        """
        protocol_spec = ProtocolSpecification.from_yaml(Path(protocol_path))
        cost_config = CostConfig.from_yaml(Path(cost_config_path))
        
        return EconomicsIntegration.create_enhanced_engine(
            engine_type=engine_type,
            protocol_spec=protocol_spec,
            cost_config=cost_config,
            n_patients=n_patients,
            seed=seed,
            **kwargs
        )
    
    @staticmethod
    def run_with_economics(
        engine_type: str,
        protocol_spec: ProtocolSpecification,
        cost_config: CostConfig,
        n_patients: int,
        duration_years: float,
        seed: Optional[int] = None,
        **kwargs
    ) -> tuple['SimulationResults', FinancialResults]:
        """
        Run a complete simulation with economic analysis.
        
        This is an all-in-one method that creates the engine, runs the
        simulation, and analyzes the costs.
        
        Args:
            engine_type: 'abs' or 'des'
            protocol_spec: Protocol specification
            cost_config: Cost configuration
            n_patients: Number of patients
            duration_years: Simulation duration in years
            seed: Random seed
            **kwargs: Additional engine arguments
            
        Returns:
            Tuple of (SimulationResults, FinancialResults)
            
        Example:
            >>> clinical, financial = EconomicsIntegration.run_with_economics(
            ...     'abs', protocol, costs, 100, 2.0
            ... )
            >>> print(f"VA change: {clinical.mean_va_change:.1f}")
            >>> print(f"Cost/patient: £{financial.cost_per_patient:,.2f}")
        """
        # Create enhanced engine
        engine = EconomicsIntegration.create_enhanced_engine(
            engine_type=engine_type,
            protocol_spec=protocol_spec,
            cost_config=cost_config,
            n_patients=n_patients,
            seed=seed,
            **kwargs
        )
        
        # Run simulation
        results = engine.run(duration_years)
        
        # Analyze costs
        financial_results = EconomicsIntegration.analyze_results(results, cost_config)
        
        return results, financial_results
    
    @staticmethod
    def export_results(
        financial_results: FinancialResults,
        output_dir: Union[str, Path],
        format: str = 'all'
    ) -> Dict[str, Path]:
        """
        Export financial results in various formats.
        
        Args:
            financial_results: Financial analysis results
            output_dir: Directory to save outputs
            format: 'json', 'parquet', 'csv', or 'all'
            
        Returns:
            Dictionary mapping format to output path
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        outputs = {}
        
        if format in ['json', 'all']:
            import json
            json_path = output_dir / 'financial_results.json'
            with open(json_path, 'w') as f:
                json.dump(financial_results.to_dict(), f, indent=2)
            outputs['json'] = json_path
        
        if format in ['csv', 'all']:
            import pandas as pd
            
            # Summary CSV
            summary_data = {
                'metric': ['Total Cost', 'Cost per Patient', 'Cost per Injection', 
                          'Cost per Letter Gained', 'Total Patients', 'Total Injections'],
                'value': [
                    financial_results.total_cost,
                    financial_results.cost_per_patient,
                    financial_results.cost_per_injection,
                    financial_results.cost_per_letter_gained or 0,
                    financial_results.total_patients,
                    financial_results.total_injections
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            csv_path = output_dir / 'financial_summary.csv'
            summary_df.to_csv(csv_path, index=False)
            outputs['csv'] = csv_path
            
        return outputs