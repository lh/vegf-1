"""
Direct tests for weekend scheduling behavior.
"""

import pytest
from datetime import datetime, timedelta

from simulation_v2.core.weekday_scheduler import WeekdayScheduler
from simulation_v2.core.weekday_protocol import WeekdayStandardProtocol
from simulation_v2.economics.resource_tracker import ResourceTracker


class TestWeekendSchedulingDirect:
    """Direct tests of weekend scheduling components."""
    
    def test_scheduler_basic_behavior(self):
        """Test basic scheduler behavior without weekend working."""
        scheduler = WeekdayScheduler(allow_saturday=False, allow_sunday=False)
        
        # Test each day of the week
        monday = datetime(2024, 1, 1)     # Monday
        tuesday = datetime(2024, 1, 2)    # Tuesday
        wednesday = datetime(2024, 1, 3)  # Wednesday
        thursday = datetime(2024, 1, 4)   # Thursday
        friday = datetime(2024, 1, 5)     # Friday
        saturday = datetime(2024, 1, 6)   # Saturday
        sunday = datetime(2024, 1, 7)     # Sunday
        
        # Weekdays should not be adjusted
        assert scheduler.adjust_to_weekday(monday) == monday
        assert scheduler.adjust_to_weekday(tuesday) == tuesday
        assert scheduler.adjust_to_weekday(wednesday) == wednesday
        assert scheduler.adjust_to_weekday(thursday) == thursday
        assert scheduler.adjust_to_weekday(friday) == friday
        
        # Weekend should be adjusted
        assert scheduler.adjust_to_weekday(saturday, prefer_earlier=True) == friday
        assert scheduler.adjust_to_weekday(sunday, prefer_earlier=True) == friday
        assert scheduler.adjust_to_weekday(saturday, prefer_earlier=False) == monday + timedelta(days=7)
        assert scheduler.adjust_to_weekday(sunday, prefer_earlier=False) == monday + timedelta(days=7)
    
    def test_resource_tracker_weekend_rejection(self):
        """Test that resource tracker rejects weekend visits by default."""
        config = {
            'resources': {
                'roles': {
                    'injector': {'capacity_per_session': 14},
                    'injector_assistant': {'capacity_per_session': 14},
                    'vision_tester': {'capacity_per_session': 12},
                    'oct_operator': {'capacity_per_session': 8},
                    'decision_maker': {'capacity_per_session': 12}
                },
                'visit_requirements': {
                    'injection_only': {
                        'roles_needed': {
                            'injector': 1,
                            'injector_assistant': 1
                        }
                    },
                    'decision_with_injection': {
                        'roles_needed': {
                            'injector': 1,
                            'injector_assistant': 1,
                            'decision_maker': 1
                        }
                    },
                    'decision_only': {
                        'roles_needed': {
                            'decision_maker': 1
                        }
                    }
                },
                'session_parameters': {
                    'sessions_per_day': 2
                }
            },
            'costs': {
                'drugs': {
                    'aflibercept_2mg': {
                        'unit_cost': 816
                    }
                },
                'procedures': {
                    'intravitreal_injection': {
                        'unit_cost': 134
                    },
                    'oct_scan': {
                        'unit_cost': 115
                    },
                    'outpatient_assessment': {
                        'unit_cost': 82.5
                    }
                }
            }
        }
        
        # Tracker without weekend working
        tracker = ResourceTracker(config, allow_saturday=False, allow_sunday=False)
        
        saturday = datetime(2024, 1, 6).date()
        sunday = datetime(2024, 1, 7).date()
        
        # Should reject Saturday
        with pytest.raises(ValueError, match="Visit scheduled on Saturday"):
            tracker.track_visit(saturday, 'injection_only', 'P001', injection_given=True)
        
        # Should reject Sunday
        with pytest.raises(ValueError, match="Visit scheduled on Sunday"):
            tracker.track_visit(sunday, 'injection_only', 'P001', injection_given=True)
    
    def test_resource_tracker_saturday_allowed(self):
        """Test that resource tracker accepts Saturday when configured."""
        config = {
            'resources': {
                'roles': {
                    'injector': {'capacity_per_session': 14},
                    'injector_assistant': {'capacity_per_session': 14},
                    'vision_tester': {'capacity_per_session': 12},
                    'oct_operator': {'capacity_per_session': 8},
                    'decision_maker': {'capacity_per_session': 12}
                },
                'visit_requirements': {
                    'injection_only': {
                        'roles_needed': {
                            'injector': 1,
                            'injector_assistant': 1
                        }
                    },
                    'decision_with_injection': {
                        'roles_needed': {
                            'injector': 1,
                            'injector_assistant': 1,
                            'decision_maker': 1
                        }
                    },
                    'decision_only': {
                        'roles_needed': {
                            'decision_maker': 1
                        }
                    }
                },
                'session_parameters': {
                    'sessions_per_day': 2
                }
            },
            'costs': {
                'drugs': {
                    'aflibercept_2mg': {
                        'unit_cost': 816
                    }
                },
                'procedures': {
                    'intravitreal_injection': {
                        'unit_cost': 134
                    },
                    'oct_scan': {
                        'unit_cost': 115
                    },
                    'outpatient_assessment': {
                        'unit_cost': 82.5
                    }
                }
            }
        }
        
        # Tracker with Saturday working
        tracker = ResourceTracker(config, allow_saturday=True, allow_sunday=False)
        
        saturday = datetime(2024, 1, 6).date()
        sunday = datetime(2024, 1, 7).date()
        monday = datetime(2024, 1, 8).date()
        
        # Should accept Saturday
        visit_record = tracker.track_visit(saturday, 'injection_only', 'P001', injection_given=True)
        assert visit_record is not None
        assert visit_record['date'] == saturday
        
        # Should still reject Sunday
        with pytest.raises(ValueError, match="Visit scheduled on Sunday"):
            tracker.track_visit(sunday, 'injection_only', 'P002', injection_given=True)
        
        # Should accept Monday
        visit_record = tracker.track_visit(monday, 'injection_only', 'P003', injection_given=True)
        assert visit_record is not None
    
    def test_protocol_weekend_configuration(self):
        """Test that protocol respects weekend configuration."""
        from simulation_v2.core.patient import Patient
        
        # Create protocol without weekend working
        protocol = WeekdayStandardProtocol(
            min_interval_days=28,
            max_interval_days=112,
            allow_saturday=False,
            allow_sunday=False
        )
        
        # Verify scheduler configuration
        assert protocol.scheduler.allow_saturday == False
        assert protocol.scheduler.allow_sunday == False
        
        # Test with Saturday working allowed
        protocol_sat = WeekdayStandardProtocol(
            min_interval_days=28,
            max_interval_days=112,
            allow_saturday=True,
            allow_sunday=False
        )
        
        assert protocol_sat.scheduler.allow_saturday == True
        assert protocol_sat.scheduler.allow_sunday == False
        
        # Test direct adjustment behavior
        saturday = datetime(2024, 1, 6)  # Saturday
        
        # Without Saturday working, Saturday should be adjusted
        adjusted = protocol.scheduler.adjust_to_weekday(saturday, prefer_earlier=True)
        assert adjusted.weekday() == 4  # Friday
        
        # With Saturday working, Saturday should NOT be adjusted
        adjusted_sat = protocol_sat.scheduler.adjust_to_weekday(saturday, prefer_earlier=True)
        assert adjusted_sat.weekday() == 5  # Saturday