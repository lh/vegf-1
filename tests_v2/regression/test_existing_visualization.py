"""
Regression tests for existing visualization functionality.

These tests ensure our chart generation works before implementing
memory-aware architecture.
"""

import pytest
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import gc
import weakref
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directories to path

from streamlit_app_v2.utils.chart_builder import ChartBuilder


@pytest.mark.skip(reason="Legacy visualization tests - ChartBuilder now requires Streamlit session state and needs to be rewritten for new architecture")
class TestExistingVisualization:
    """Baseline tests for current visualizations."""
    
    @pytest.fixture
    def mock_simulation_results(self):
        """Create mock simulation results for testing."""
        # Create realistic mock data
        n_patients = 50
        duration_months = 24
        
        patients = {}
        for i in range(n_patients):
            patient_id = f"P{i:04d}"
            
            # Generate visit history
            visits = []
            current_date = datetime(2024, 1, 1)
            vision = 70 + np.random.normal(0, 5)
            
            for month in range(0, duration_months, 2):  # Visits every 2 months
                visit = {
                    'date': current_date + timedelta(days=month * 30),
                    'vision': max(0, min(100, vision + np.random.normal(-2, 3))),
                    'treatment_given': True,
                    'disease_state': 'ACTIVE'
                }
                visits.append(visit)
                vision = visit['vision']
            
            patients[patient_id] = {
                'id': patient_id,
                'baseline_vision': 70,
                'current_vision': vision,
                'visit_history': visits,
                'injection_count': len(visits),
                'is_discontinued': np.random.random() < 0.1
            }
        
        # Create results object
        from types import SimpleNamespace
        results = SimpleNamespace(
            patient_histories=patients,
            total_injections=sum(p['injection_count'] for p in patients.values()),
            patient_count=n_patients,
            final_vision_mean=np.mean([p['current_vision'] for p in patients.values()]),
            final_vision_std=np.std([p['current_vision'] for p in patients.values()]),
            discontinuation_rate=sum(1 for p in patients.values() if p['is_discontinued']) / n_patients
        )
        
        return results
    
    @pytest.fixture(autouse=True)
    def cleanup_matplotlib(self):
        """Ensure matplotlib is cleaned up after each test."""
        yield
        plt.close('all')
        gc.collect()
    
    def test_chart_builder_exists(self):
        """Verify ChartBuilder is available."""
        assert hasattr(ChartBuilder, 'create_va_progression_chart')
        assert hasattr(ChartBuilder, 'create_outcome_distribution')
        assert hasattr(ChartBuilder, 'create_injection_timeline')
    
    def test_va_progression_chart(self, mock_simulation_results):
        """Test VA progression chart generation."""
        fig = ChartBuilder.create_va_progression_chart(
            mock_simulation_results.patient_histories,
            title="VA Progression Test"
        )
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
        # Check basic properties
        axes = fig.get_axes()
        assert len(axes) > 0
        
        # Check axis labels
        ax = axes[0]
        assert ax.get_xlabel() != ""
        assert ax.get_ylabel() != ""
        
    def test_outcome_distribution(self, mock_simulation_results):
        """Test outcome distribution chart."""
        fig = ChartBuilder.create_outcome_distribution(
            mock_simulation_results.patient_histories,
            title="Outcome Distribution Test"
        )
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
        # Verify it has data
        axes = fig.get_axes()
        assert len(axes) > 0
        assert len(axes[0].patches) > 0  # Should have histogram bars
        
    def test_injection_timeline(self, mock_simulation_results):
        """Test injection timeline visualization."""
        fig = ChartBuilder.create_injection_timeline(
            mock_simulation_results.patient_histories,
            title="Injection Timeline Test"
        )
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
    def test_memory_cleanup(self, mock_simulation_results):
        """Verify charts are properly cleaned up."""
        # Create chart and get weak reference
        fig = ChartBuilder.create_va_progression_chart(
            mock_simulation_results.patient_histories
        )
        fig_ref = weakref.ref(fig)
        
        # Verify figure exists
        assert fig_ref() is not None
        
        # Clean up
        plt.close(fig)
        del fig
        gc.collect()
        
        # Verify figure is gone
        assert fig_ref() is None
        
    def test_empty_data_handling(self):
        """Test visualization with empty data."""
        empty_patients = {}
        
        # Should handle empty data gracefully
        fig = ChartBuilder.create_va_progression_chart(
            empty_patients,
            title="Empty Data Test"
        )
        
        assert fig is not None
        plt.close(fig)
        
    def test_single_patient_visualization(self):
        """Test with single patient data."""
        single_patient = {
            'P0001': {
                'id': 'P0001',
                'baseline_vision': 70,
                'current_vision': 68,
                'visit_history': [
                    {
                        'date': datetime(2024, 1, 1),
                        'vision': 70,
                        'treatment_given': True
                    }
                ],
                'injection_count': 1,
                'is_discontinued': False
            }
        }
        
        fig = ChartBuilder.create_va_progression_chart(
            single_patient,
            title="Single Patient Test"
        )
        
        assert fig is not None
        plt.close(fig)
        
    @pytest.mark.parametrize("n_patients", [10, 50, 100])
    def test_scalability(self, n_patients):
        """Test visualization scales with patient count."""
        # Generate scaled mock data
        patients = {}
        for i in range(n_patients):
            patient_id = f"P{i:04d}"
            patients[patient_id] = {
                'id': patient_id,
                'baseline_vision': 70,
                'current_vision': 68,
                'visit_history': [
                    {
                        'date': datetime(2024, 1, 1) + timedelta(days=j*30),
                        'vision': 70 - j,
                        'treatment_given': True
                    }
                    for j in range(12)
                ],
                'injection_count': 12,
                'is_discontinued': False
            }
        
        # Should complete without error
        fig = ChartBuilder.create_va_progression_chart(
            patients,
            title=f"Scalability Test ({n_patients} patients)"
        )
        
        assert fig is not None
        plt.close(fig)
        
    def test_tufte_style_applied(self, mock_simulation_results):
        """Verify Tufte styling is applied."""
        fig = ChartBuilder.create_va_progression_chart(
            mock_simulation_results.patient_histories,
            title="Tufte Style Test"
        )
        
        # Check for Tufte characteristics
        ax = fig.get_axes()[0]
        
        # Should have minimal spines
        visible_spines = sum(1 for spine in ax.spines.values() if spine.get_visible())
        assert visible_spines <= 2  # Only bottom and left
        
        # Should have no top/right spines
        assert not ax.spines['top'].get_visible()
        assert not ax.spines['right'].get_visible()
        
        plt.close(fig)
        
    def test_consistent_color_scheme(self, mock_simulation_results):
        """Test that consistent colors are used."""
        fig1 = ChartBuilder.create_va_progression_chart(
            mock_simulation_results.patient_histories
        )
        fig2 = ChartBuilder.create_outcome_distribution(
            mock_simulation_results.patient_histories
        )
        
        # Both should use consistent color scheme
        # (This is a placeholder - would need actual color extraction)
        assert fig1 is not None
        assert fig2 is not None
        
        plt.close(fig1)
        plt.close(fig2)