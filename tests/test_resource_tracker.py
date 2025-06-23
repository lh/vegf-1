"""
Tests for ResourceTracker class.

Ensures resource tracking works correctly and fails fast on missing data.
"""

import pytest
from datetime import date
from simulation_v2.economics.resource_tracker import ResourceTracker, load_resource_config


class TestResourceTracker:
    """Test resource tracking functionality."""
    
    @pytest.fixture
    def resource_config(self):
        """Minimal resource configuration for testing."""
        return {
            'resources': {
                'roles': {
                    'injector': {'capacity_per_session': 14, 'description': 'Injector'},
                    'injector_assistant': {'capacity_per_session': 14, 'description': 'Assistant'},
                    'vision_tester': {'capacity_per_session': 20, 'description': 'Vision tester'},
                    'oct_operator': {'capacity_per_session': 16, 'description': 'OCT operator'},
                    'decision_maker': {'capacity_per_session': 12, 'description': 'Decision maker'}
                },
                'visit_requirements': {
                    'injection_only': {
                        'roles_needed': {'injector': 1, 'injector_assistant': 1},
                        'duration_minutes': 15
                    },
                    'decision_with_injection': {
                        'roles_needed': {
                            'vision_tester': 1, 'oct_operator': 1, 'decision_maker': 1,
                            'injector': 1, 'injector_assistant': 1
                        },
                        'duration_minutes': 30
                    },
                    'decision_only': {
                        'roles_needed': {
                            'vision_tester': 1, 'oct_operator': 1, 'decision_maker': 1
                        },
                        'duration_minutes': 20
                    }
                },
                'session_parameters': {
                    'session_duration_hours': 4,
                    'sessions_per_day': 2,
                    'working_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
                }
            },
            'costs': {
                'procedures': {
                    'intravitreal_injection': {'unit_cost': 134},
                    'outpatient_assessment': {'unit_cost': 75},
                    'oct_scan': {'unit_cost': 110}
                },
                'drugs': {
                    'aflibercept_2mg': {'unit_cost': 816}
                }
            }
        }
    
    def test_initialization(self, resource_config):
        """Test tracker initializes correctly."""
        tracker = ResourceTracker(resource_config)
        assert tracker.roles == resource_config['resources']['roles']
        assert tracker.visit_requirements == resource_config['resources']['visit_requirements']
        assert len(tracker.visits) == 0
        assert len(tracker.daily_usage) == 0
    
    def test_initialization_empty_config(self):
        """Test tracker fails with empty config."""
        with pytest.raises(ValueError, match="Resource configuration cannot be empty"):
            ResourceTracker(None)
    
    def test_track_injection_only_visit(self, resource_config):
        """Test tracking injection-only visit."""
        tracker = ResourceTracker(resource_config)
        monday = date(2024, 1, 15)  # Monday
        
        visit = tracker.track_visit(monday, 'injection_only', 'P001', injection_given=True)
        
        # Check visit record
        assert visit['date'] == monday
        assert visit['patient_id'] == 'P001'
        assert visit['visit_type'] == 'injection_only'
        assert visit['injection_given'] is True
        assert visit['resources_used'] == {'injector': 1, 'injector_assistant': 1}
        
        # Check costs
        assert visit['costs']['drug'] == 816
        assert visit['costs']['injection_procedure'] == 134
        assert 'consultation' not in visit['costs']
        
        # Check daily usage
        usage = tracker.get_daily_usage(monday)
        assert usage['injector'] == 1
        assert usage['injector_assistant'] == 1
        assert usage.get('vision_tester', 0) == 0
    
    def test_track_decision_with_injection_visit(self, resource_config):
        """Test tracking full assessment with injection."""
        tracker = ResourceTracker(resource_config)
        tuesday = date(2024, 1, 16)  # Tuesday
        
        visit = tracker.track_visit(tuesday, 'decision_with_injection', 'P002', 
                                   injection_given=True, oct_performed=True)
        
        # Check resources used
        assert visit['resources_used']['injector'] == 1
        assert visit['resources_used']['vision_tester'] == 1
        assert visit['resources_used']['oct_operator'] == 1
        assert visit['resources_used']['decision_maker'] == 1
        
        # Check costs
        assert visit['costs']['drug'] == 816
        assert visit['costs']['injection_procedure'] == 134
        assert visit['costs']['consultation'] == 75
        assert visit['costs']['oct_scan'] == 110
    
    def test_track_decision_only_visit(self, resource_config):
        """Test tracking assessment-only visit."""
        tracker = ResourceTracker(resource_config)
        wednesday = date(2024, 1, 17)  # Wednesday
        
        visit = tracker.track_visit(wednesday, 'decision_only', 'P003', oct_performed=True)
        
        # No injection resources or costs
        assert 'injector' not in visit['resources_used']
        assert 'drug' not in visit['costs']
        assert 'injection_procedure' not in visit['costs']
        
        # Has assessment resources and costs
        assert visit['resources_used']['decision_maker'] == 1
        assert visit['costs']['consultation'] == 75
        assert visit['costs']['oct_scan'] == 110
    
    def test_weekend_visit_rejected(self, resource_config):
        """Test that weekend visits are rejected."""
        tracker = ResourceTracker(resource_config)
        saturday = date(2024, 1, 20)  # Saturday
        
        with pytest.raises(ValueError, match="Visit scheduled on weekend"):
            tracker.track_visit(saturday, 'injection_only', 'P001')
    
    def test_unknown_visit_type_rejected(self, resource_config):
        """Test that unknown visit types are rejected."""
        tracker = ResourceTracker(resource_config)
        monday = date(2024, 1, 15)
        
        with pytest.raises(KeyError, match="Unknown visit type: unknown_type"):
            tracker.track_visit(monday, 'unknown_type', 'P001')
    
    def test_get_daily_usage_no_data(self, resource_config):
        """Test getting usage for date with no visits fails fast."""
        tracker = ResourceTracker(resource_config)
        
        with pytest.raises(ValueError, match="No visit data available"):
            tracker.get_daily_usage(date(2024, 1, 15))
    
    def test_calculate_sessions_needed(self, resource_config):
        """Test session calculation."""
        tracker = ResourceTracker(resource_config)
        monday = date(2024, 1, 15)
        
        # Track multiple visits
        for i in range(10):
            tracker.track_visit(monday, 'injection_only', f'P{i:03d}', injection_given=True)
        
        # 10 injections / 14 capacity = 0.714 sessions
        sessions = tracker.calculate_sessions_needed(monday, 'injector')
        assert abs(sessions - 10/14) < 0.001
    
    def test_multiple_visits_accumulate(self, resource_config):
        """Test that multiple visits accumulate resources correctly."""
        tracker = ResourceTracker(resource_config)
        monday = date(2024, 1, 15)
        
        # Track 3 injection visits
        tracker.track_visit(monday, 'injection_only', 'P001', injection_given=True)
        tracker.track_visit(monday, 'injection_only', 'P002', injection_given=True)
        tracker.track_visit(monday, 'injection_only', 'P003', injection_given=True)
        
        usage = tracker.get_daily_usage(monday)
        assert usage['injector'] == 3
        assert usage['injector_assistant'] == 3
    
    def test_workload_summary(self, resource_config):
        """Test workload summary generation."""
        tracker = ResourceTracker(resource_config)
        
        # Add various visits
        monday = date(2024, 1, 15)
        tuesday = date(2024, 1, 16)
        
        tracker.track_visit(monday, 'injection_only', 'P001', injection_given=True)
        tracker.track_visit(monday, 'injection_only', 'P002', injection_given=True)
        tracker.track_visit(tuesday, 'decision_with_injection', 'P003', 
                          injection_given=True, oct_performed=True)
        
        summary = tracker.get_workload_summary()
        
        assert summary['total_visits'] == 3
        assert summary['visits_by_type']['injection_only'] == 2
        assert summary['visits_by_type']['decision_with_injection'] == 1
        assert summary['dates_with_visits'] == 2
        assert summary['peak_daily_demand']['injector'] == 2
        assert summary['average_daily_demand']['injector'] == 1.5  # (2+1)/2
    
    def test_identify_bottlenecks(self, resource_config):
        """Test bottleneck identification."""
        tracker = ResourceTracker(resource_config)
        monday = date(2024, 1, 15)
        
        # Add more decision visits than capacity allows
        # Decision maker capacity is 12 per session, 2 sessions per day = 24 total
        for i in range(30):
            tracker.track_visit(monday, 'decision_only', f'P{i:03d}', oct_performed=True)
        
        bottlenecks = tracker.identify_bottlenecks()
        
        assert len(bottlenecks) > 0
        decision_bottleneck = [b for b in bottlenecks if b['role'] == 'decision_maker'][0]
        assert decision_bottleneck['date'] == monday
        assert decision_bottleneck['sessions_needed'] > 2  # More than available
        assert decision_bottleneck['procedures_affected'] == 30
    
    def test_total_costs_calculation(self, resource_config):
        """Test total cost calculation across all visits."""
        tracker = ResourceTracker(resource_config)
        
        # Track some visits
        monday = date(2024, 1, 15)
        tracker.track_visit(monday, 'injection_only', 'P001', injection_given=True)
        tracker.track_visit(monday, 'decision_only', 'P002', oct_performed=True)
        
        total_costs = tracker.get_total_costs()
        
        # First visit: drug (816) + injection (134) = 950
        # Second visit: consultation (75) + OCT (110) = 185
        # Total = 1135
        assert total_costs['drug'] == 816
        assert total_costs['injection_procedure'] == 134
        assert total_costs['consultation'] == 75
        assert total_costs['oct_scan'] == 110
        assert total_costs['total'] == 1135