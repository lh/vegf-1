"""
Comprehensive test suite for V2 economics integration.

Tests the complete V2 economics system including:
- Engine creation with cost tracking
- Cost enhancement functionality  
- Financial analysis and calculations
- EconomicsIntegration API
- Edge cases and error handling
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# V2 simulation components
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.disease_model import DiseaseModel, DiseaseState
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.core.patient import Patient
from simulation_v2.engines.abs_engine import ABSEngine
from simulation_v2.engines.des_engine import DESEngine

# V2 economics components
from simulation_v2.economics import (
    CostConfig, 
    CostAnalyzerV2, 
    CostEvent,
    CostTrackerV2,
    FinancialResults,
    PatientCostSummary,
    create_v2_cost_enhancer,
    EconomicsIntegration
)


class TestCostConfig:
    """Test V2 CostConfig functionality."""
    
    def test_cost_config_creation(self):
        """Test creating CostConfig from dictionary."""
        config_data = {
            'metadata': {'name': 'Test Config', 'currency': 'GBP'},
            'drug_costs': {'eylea_2mg': 800.0, 'avastin': 50.0},
            'visit_components': {'vision_test': 25.0, 'oct_scan': 150.0, 'injection': 100.0},
            'visit_types': {
                'loading_injection_visit': {
                    'components': ['vision_test', 'oct_scan', 'injection']
                }
            },
            'special_events': {'discontinuation_admin': 50.0}
        }
        
        config = CostConfig(**config_data)
        
        assert config.metadata['name'] == 'Test Config'
        assert config.get_drug_cost('eylea_2mg') == 800.0
        assert config.get_component_cost('vision_test') == 25.0
        assert config.get_special_event_cost('discontinuation_admin') == 50.0
        
    def test_cost_config_from_yaml(self):
        """Test loading CostConfig from YAML file."""
        config_data = {
            'metadata': {'name': 'Test YAML Config'},
            'drug_costs': {'eylea_2mg': 800.0},
            'visit_components': {'vision_test': 25.0},
            'visit_types': {},
            'special_events': {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
            
        try:
            config = CostConfig.from_yaml(temp_path)
            assert config.metadata['name'] == 'Test YAML Config'
            assert config.get_drug_cost('eylea_2mg') == 800.0
        finally:
            Path(temp_path).unlink()
            
    def test_visit_cost_calculation(self):
        """Test visit cost calculation with components."""
        config_data = {
            'metadata': {},
            'drug_costs': {},
            'visit_components': {
                'vision_test': 25.0,
                'oct_scan': 150.0,
                'injection': 100.0
            },
            'visit_types': {
                'injection_visit': {
                    'components': ['vision_test', 'oct_scan', 'injection']
                },
                'monitoring_visit': {
                    'components': ['vision_test', 'oct_scan']
                },
                'override_visit': {
                    'total_override': 500.0
                }
            },
            'special_events': {}
        }
        
        config = CostConfig(**config_data)
        
        # Test component-based calculation
        assert config.get_visit_cost('injection_visit') == 275.0  # 25 + 150 + 100
        assert config.get_visit_cost('monitoring_visit') == 175.0  # 25 + 150
        
        # Test override
        assert config.get_visit_cost('override_visit') == 500.0
        
        # Test unknown visit type
        assert config.get_visit_cost('unknown_visit') == 0.0


class TestCostEnhancer:
    """Test V2 cost enhancer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.patient = Patient("P001", baseline_vision=70)
        self.cost_config = CostConfig(
            metadata={},
            drug_costs={'eylea_2mg': 800.0},
            visit_components={'vision_test': 25.0, 'oct_scan': 150.0, 'injection': 100.0},
            visit_types={},
            special_events={}
        )
        
    def test_enhancer_creation(self):
        """Test creating a cost enhancer."""
        enhancer = create_v2_cost_enhancer(self.cost_config, "eylea")
        assert callable(enhancer)
        
    def test_visit_enhancement_injection(self):
        """Test enhancing an injection visit."""
        enhancer = create_v2_cost_enhancer(self.cost_config, "eylea")
        
        visit = {
            'date': datetime.now(),
            'disease_state': DiseaseState.ACTIVE,
            'treatment_given': True,
            'vision': 75
        }
        
        enhanced = enhancer(visit, self.patient)
        
        # Check metadata was added
        assert 'metadata' in enhanced
        metadata = enhanced['metadata']
        
        assert metadata['phase'] == 'loading'  # First visit
        assert metadata['visit_number'] == 1
        assert 'injection' in metadata['components_performed']
        assert metadata['drug'] == 'eylea_2mg'
        assert metadata['visit_subtype'] == 'loading_injection_visit'
        
    def test_visit_enhancement_monitoring(self):
        """Test enhancing a monitoring visit."""
        enhancer = create_v2_cost_enhancer(self.cost_config, "eylea")
        
        # Add some visits to patient to get to maintenance phase
        for i in range(4):
            self.patient.visit_history.append({
                'date': datetime.now() - timedelta(days=30*(4-i)),
                'treatment_given': True
            })
        
        visit = {
            'date': datetime.now(),
            'disease_state': DiseaseState.STABLE,
            'treatment_given': False,
            'vision': 78
        }
        
        enhanced = enhancer(visit, self.patient)
        
        metadata = enhanced['metadata']
        assert metadata['phase'] == 'maintenance'
        assert metadata['visit_number'] == 5
        assert 'injection' not in metadata['components_performed']
        assert metadata['visit_subtype'] == 'maintenance_monitoring_visit'


class TestCostAnalyzer:
    """Test V2 CostAnalyzerV2 functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cost_config = CostConfig(
            metadata={'name': 'Test Config'},
            drug_costs={'eylea_2mg': 800.0},
            visit_components={
                'vision_test': 25.0,
                'oct_scan': 150.0,
                'injection': 100.0,
                'virtual_review': 50.0
            },
            visit_types={},
            special_events={'discontinuation_admin': 50.0}
        )
        self.analyzer = CostAnalyzerV2(self.cost_config)
        
    def test_analyze_injection_visit(self):
        """Test analyzing an injection visit."""
        visit = {
            'date': datetime.now(),
            'disease_state': DiseaseState.ACTIVE,
            'treatment_given': True,
            'patient_id': 'P001',
            'metadata': {
                'components_performed': ['vision_test', 'oct_scan', 'injection'],
                'drug': 'eylea_2mg',
                'phase': 'loading',
                'visit_subtype': 'loading_injection_visit'
            }
        }
        
        event = self.analyzer.analyze_visit(visit)
        
        assert event is not None
        assert event.patient_id == 'P001'
        assert event.event_type == 'visit'
        assert event.category == 'loading_injection_visit'
        assert event.amount == 1075.0  # 25 + 150 + 100 + 800 (drug)
        assert event.metadata['drug_cost'] == 800.0
        assert event.metadata['visit_cost'] == 275.0
        
    def test_analyze_monitoring_visit(self):
        """Test analyzing a monitoring visit."""
        visit = {
            'date': datetime.now(),
            'disease_state': DiseaseState.STABLE,
            'treatment_given': False,
            'patient_id': 'P001',
            'metadata': {
                'components_performed': ['vision_test', 'oct_scan', 'virtual_review'],
                'phase': 'maintenance',
                'visit_subtype': 'maintenance_monitoring_visit'
            }
        }
        
        event = self.analyzer.analyze_visit(visit)
        
        assert event is not None
        assert event.amount == 225.0  # 25 + 150 + 50, no drug cost
        assert event.metadata['drug_cost'] == 0.0
        assert event.metadata['visit_cost'] == 225.0
        
    def test_analyze_patient_with_discontinuation(self):
        """Test analyzing a patient with discontinuation event."""
        patient = Patient("P002", baseline_vision=65)
        patient.current_vision = 70
        patient.is_discontinued = True
        patient.discontinuation_date = datetime.now()
        patient.discontinuation_type = "planned"
        patient.discontinuation_reason = "response_achieved"
        
        # Add some visit history
        patient.visit_history = [
            {
                'date': datetime.now() - timedelta(days=60),
                'treatment_given': True,
                'patient_id': 'P002',
                'metadata': {
                    'components_performed': ['vision_test', 'oct_scan', 'injection'],
                    'drug': 'eylea_2mg'
                }
            }
        ]
        
        events = self.analyzer.analyze_patient(patient)
        
        # Should have visit event + discontinuation event
        assert len(events) == 2
        
        visit_event = events[0]
        disc_event = events[1]
        
        assert visit_event.event_type == 'visit'
        assert disc_event.event_type == 'special'
        assert disc_event.category == 'discontinuation_admin'
        assert disc_event.amount == 50.0


class TestCostTracker:
    """Test V2 CostTrackerV2 functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cost_config = CostConfig(
            metadata={'name': 'Test Config'},
            drug_costs={'eylea_2mg': 800.0},
            visit_components={
                'vision_test': 25.0,
                'oct_scan': 150.0,
                'injection': 100.0
            },
            visit_types={},
            special_events={}
        )
        self.analyzer = CostAnalyzerV2(self.cost_config)
        self.tracker = CostTrackerV2(self.analyzer)
        
    def test_empty_financial_results(self):
        """Test financial results with no events."""
        results = self.tracker.get_financial_results("Test Config")
        
        assert results.total_cost == 0.0
        assert results.total_patients == 0
        assert results.cost_per_patient == 0.0
        assert results.total_injections == 0
        assert results.cost_per_injection == 0.0
        
    def test_financial_results_calculation(self):
        """Test financial results calculation with mock events."""
        # Create mock patient events
        patient1_events = [
            CostEvent(
                date=datetime.now(),
                patient_id='P001',
                event_type='visit',
                category='injection_visit',
                amount=1075.0,
                metadata={'treatment_given': True, 'drug_cost': 800.0, 'visit_cost': 275.0}
            ),
            CostEvent(
                date=datetime.now(),
                patient_id='P001', 
                event_type='visit',
                category='monitoring_visit',
                amount=175.0,
                metadata={'treatment_given': False, 'drug_cost': 0.0, 'visit_cost': 175.0}
            )
        ]
        
        self.tracker.events = {'P001': patient1_events}
        
        results = self.tracker.get_financial_results("Test Config")
        
        assert results.total_cost == 1250.0
        assert results.total_patients == 1
        assert results.cost_per_patient == 1250.0
        assert results.total_injections == 1
        assert results.cost_per_injection == 1250.0
        assert len(results.patient_costs) == 1
        
        patient_cost = results.patient_costs['P001']
        assert patient_cost.total_cost == 1250.0
        assert patient_cost.injection_count == 1
        assert patient_cost.visit_count == 2


class TestEconomicsIntegration:
    """Test EconomicsIntegration API."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Load real protocol spec from file
        protocol_path = Path("streamlit_app_v2/protocols/eylea.yaml")
        if protocol_path.exists():
            self.protocol_spec = ProtocolSpecification.from_yaml(protocol_path)
        else:
            # Fallback - create minimal test protocol with required fields
            protocol_data = {
                'name': 'Test Protocol',
                'version': '1.0',
                'created_date': '2025-01-01',
                'author': 'Test',
                'description': 'Test protocol',
                'protocol_type': 'treat_and_extend',
                'disease_transitions': {
                    'naive_to_stable': 0.3,
                    'stable_to_active': 0.1,
                    'active_to_highly_active': 0.05,
                    'highly_active_to_active': 0.4
                },
                'treatment_effect_on_transitions': {
                    'naive_to_stable': 1.5,
                    'stable_to_active': 0.7,
                    'active_to_highly_active': 0.5,
                    'highly_active_to_active': 1.2
                },
                'min_interval_days': 28,
                'max_interval_days': 84,
                'extension_days': 14,
                'shortening_days': 14,
                'vision_change_model': {'type': 'simple'},
                'baseline_vision_mean': 70,
                'baseline_vision_std': 10,
                'baseline_vision_min': 20,
                'baseline_vision_max': 90,
                'discontinuation_rules': {'max_no_benefit_visits': 3}
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(protocol_data, f)
                temp_path = f.name
                
            self.protocol_spec = ProtocolSpecification.from_yaml(temp_path)
            Path(temp_path).unlink()
        
        # Create test cost config
        self.cost_config = CostConfig(
            metadata={'name': 'Test Config', 'currency': 'GBP'},
            drug_costs={'eylea_2mg': 800.0},
            visit_components={
                'vision_test': 25.0,
                'oct_scan': 150.0,
                'injection': 100.0,
                'pressure_check': 20.0,
                'virtual_review': 50.0
            },
            visit_types={},
            special_events={'discontinuation_admin': 50.0}
        )
        
    def test_create_enhanced_abs_engine(self):
        """Test creating ABS engine with economics."""
        engine = EconomicsIntegration.create_enhanced_engine(
            'abs',
            self.protocol_spec,
            self.cost_config,
            n_patients=5,
            seed=42
        )
        
        assert isinstance(engine, ABSEngine)
        assert len(engine.patients) == 5
        
        # Check that patients have cost enhancers
        first_patient = next(iter(engine.patients.values()))
        assert hasattr(first_patient, 'visit_metadata_enhancer')
        assert first_patient.visit_metadata_enhancer is not None
        
    def test_create_enhanced_des_engine(self):
        """Test creating DES engine with economics."""
        engine = EconomicsIntegration.create_enhanced_engine(
            'des',
            self.protocol_spec,
            self.cost_config,
            n_patients=5,
            seed=42
        )
        
        assert isinstance(engine, DESEngine)
        # DES engine doesn't pre-create patients, but enhancer should be configured
        
    def test_analyze_results_static_method(self):
        """Test the analyze_results static method."""
        # Create mock simulation results
        class MockResults:
            def __init__(self):
                self.patient_histories = {
                    'P001': self._create_mock_patient()
                }
                
            def _create_mock_patient(self):
                patient = Patient("P001", baseline_vision=70)
                patient.current_vision = 75
                patient.visit_history = [
                    {
                        'date': datetime.now(),
                        'treatment_given': True,
                        'metadata': {
                            'components_performed': ['vision_test', 'oct_scan', 'injection'],
                            'drug': 'eylea_2mg',
                            'phase': 'loading'
                        }
                    }
                ]
                return patient
        
        mock_results = MockResults()
        
        financial = EconomicsIntegration.analyze_results(mock_results, self.cost_config)
        
        assert isinstance(financial, FinancialResults)
        assert financial.total_patients == 1
        assert financial.total_cost > 0
        assert financial.cost_config_name == 'Test Config'
        
    def test_run_with_economics_abs(self):
        """Test run_with_economics with ABS engine."""
        clinical, financial = EconomicsIntegration.run_with_economics(
            'abs',
            self.protocol_spec,
            self.cost_config,
            n_patients=3,
            duration_years=1.0,
            seed=42
        )
        
        # Check clinical results
        assert hasattr(clinical, 'patient_histories')
        assert len(clinical.patient_histories) == 3
        
        # Check financial results
        assert isinstance(financial, FinancialResults)
        assert financial.total_patients == 3
        assert financial.total_cost > 0
        assert financial.cost_per_patient > 0
        
    def test_create_from_files_method(self):
        """Test the create_from_files convenience method."""
        # Use existing files if available
        protocol_path = Path("streamlit_app_v2/protocols/eylea.yaml")
        cost_path = Path("protocols/cost_configs/nhs_standard_2025.yaml")
        
        if not protocol_path.exists() or not cost_path.exists():
            pytest.skip("Required protocol or cost config files not available")
            
        engine = EconomicsIntegration.create_from_files(
            'abs',
            str(protocol_path),
            str(cost_path),
            n_patients=2
        )
        
        assert isinstance(engine, ABSEngine)
        assert len(engine.patients) == 2


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_cost_config_missing_file(self):
        """Test CostConfig with missing file."""
        with pytest.raises(FileNotFoundError):
            CostConfig.from_yaml("nonexistent_file.yaml")
            
    def test_analyzer_with_missing_visit_data(self):
        """Test analyzer with incomplete visit data."""
        config = CostConfig(
            metadata={},
            drug_costs={},
            visit_components={},
            visit_types={},
            special_events={}
        )
        analyzer = CostAnalyzerV2(config)
        
        # Visit without date
        visit = {'treatment_given': True}
        result = analyzer.analyze_visit(visit)
        assert result is None
        
        # Visit with date but components create zero cost
        visit = {
            'date': datetime.now(),
            'treatment_given': False,
            'metadata': {'components_performed': ['unknown_component']}
        }
        result = analyzer.analyze_visit(visit)
        # This will create an event with zero cost, not None
        assert result is not None
        assert result.amount == 0.0
        
    def test_invalid_engine_type(self):
        """Test EconomicsIntegration with invalid engine type defaults to DES."""
        # Use the same cost config from setup
        cost_config = CostConfig(
            metadata={},
            drug_costs={},
            visit_components={},
            visit_types={},
            special_events={}
        )
        
        # Load a real protocol or use test fixture
        protocol_path = Path("streamlit_app_v2/protocols/eylea.yaml")
        if protocol_path.exists():
            protocol_spec = ProtocolSpecification.from_yaml(protocol_path)
        else:
            # Skip this test if no protocol file available
            pytest.skip("No protocol file available for testing")
        
        # Invalid engine type defaults to DES (not ideal, but current behavior)
        engine = EconomicsIntegration.create_enhanced_engine(
            'invalid_engine',
            protocol_spec,
            cost_config,
            n_patients=1
        )
        
        # Should default to DES engine
        assert isinstance(engine, DESEngine)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])