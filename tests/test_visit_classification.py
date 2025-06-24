"""
Tests for visit classification logic.

Ensures T&E and T&T protocols classify visits correctly.
"""

import pytest
from datetime import date, timedelta
from simulation_v2.economics.visit_classifier import VisitClassifier


class TestVisitClassification:
    """Test visit classification for both protocols."""
    
    def test_tnt_loading_phase(self):
        """Test T&T loading phase visits."""
        classifier = VisitClassifier('T&T')
        
        assert classifier.get_visit_type(1, 0) == 'injection_only'
        assert classifier.get_visit_type(2, 28) == 'injection_only'
        assert classifier.get_visit_type(3, 56) == 'injection_only'
    
    def test_tnt_post_loading_assessment(self):
        """Test T&T post-loading assessment."""
        classifier = VisitClassifier('T&T')
        
        # Visit 4 is assessment
        assert classifier.get_visit_type(4, 84, is_assessment=True) == 'decision_only'
    
    def test_tnt_maintenance_phase(self):
        """Test T&T maintenance phase."""
        classifier = VisitClassifier('T&T')
        
        # Regular maintenance visits
        assert classifier.get_visit_type(5, 112) == 'injection_only'
        assert classifier.get_visit_type(6, 168) == 'injection_only'
        assert classifier.get_visit_type(7, 224) == 'injection_only'
        assert classifier.get_visit_type(8, 280) == 'injection_only'
    
    def test_tnt_annual_reviews(self):
        """Test T&T annual review visits."""
        classifier = VisitClassifier('T&T')
        
        # Annual reviews are decision only
        assert classifier.get_visit_type(10, 365, is_annual=True) == 'decision_only'
        assert classifier.get_visit_type(17, 730, is_annual=True) == 'decision_only'
    
    def test_tae_year_one_matches_tnt(self):
        """Test T&E Year 1 is identical to T&T."""
        tae = VisitClassifier('T&E')
        tnt = VisitClassifier('T&T')
        
        # Loading phase
        assert tae.get_visit_type(1, 0) == tnt.get_visit_type(1, 0)
        assert tae.get_visit_type(2, 28) == tnt.get_visit_type(2, 28)
        assert tae.get_visit_type(3, 56) == tnt.get_visit_type(3, 56)
        
        # Post-loading assessment
        assert tae.get_visit_type(4, 84, is_assessment=True) == tnt.get_visit_type(4, 84, is_assessment=True)
        
        # Maintenance through visit 7
        assert tae.get_visit_type(5, 112) == tnt.get_visit_type(5, 112)
        assert tae.get_visit_type(6, 168) == tnt.get_visit_type(6, 168)
        assert tae.get_visit_type(7, 224) == tnt.get_visit_type(7, 224)
    
    def test_tae_year_two_all_decisions(self):
        """Test T&E Year 2+ has decisions at every visit."""
        classifier = VisitClassifier('T&E')
        
        # From visit 8 onwards, all have decisions
        assert classifier.get_visit_type(8, 280) == 'decision_with_injection'
        assert classifier.get_visit_type(9, 336) == 'decision_with_injection'
        assert classifier.get_visit_type(10, 400) == 'decision_with_injection'
        assert classifier.get_visit_type(15, 600) == 'decision_with_injection'
        assert classifier.get_visit_type(20, 800) == 'decision_with_injection'
    
    def test_invalid_protocol_type(self):
        """Test invalid protocol type is rejected."""
        with pytest.raises(ValueError, match="Unknown protocol type"):
            VisitClassifier('INVALID')
    
    def test_edge_cases(self):
        """Test edge cases in classification."""
        tae = VisitClassifier('T&E')
        tnt = VisitClassifier('T&T')
        
        # T&E visit 7 is still injection only (not decision)
        assert tae.get_visit_type(7, 224) == 'injection_only'
        
        # T&E visit 8 is first with decision
        assert tae.get_visit_type(8, 280) == 'decision_with_injection'
        
        # T&T never has decision_with_injection
        for visit_num in range(5, 20):
            if visit_num != 4:  # Skip assessment
                visit_type = tnt.get_visit_type(visit_num, visit_num * 56)
                assert visit_type != 'decision_with_injection'


class TestProtocolVisitPatterns:
    """Test realistic visit patterns for both protocols."""
    
    def test_tnt_two_year_pattern(self):
        """Test realistic T&T pattern over 2 years."""
        classifier = VisitClassifier('T&T')
        visits = []
        
        # Year 1 pattern
        # Loading: 0, 28, 56 days
        visits.append((1, 0, 'injection_only'))
        visits.append((2, 28, 'injection_only'))
        visits.append((3, 56, 'injection_only'))
        # Assessment after loading
        visits.append((4, 84, 'decision_only'))  # is_assessment=True
        # Maintenance every 56 days
        visits.append((5, 112, 'injection_only'))
        visits.append((6, 168, 'injection_only'))
        visits.append((7, 224, 'injection_only'))
        visits.append((8, 280, 'injection_only'))
        visits.append((9, 336, 'injection_only'))
        # Annual review around day 365
        visits.append((10, 365, 'decision_only'))  # is_annual=True
        
        # Verify pattern
        for visit_num, day, expected in visits:
            is_assessment = (visit_num == 4)
            is_annual = (day >= 360 and day <= 380)
            actual = classifier.get_visit_type(visit_num, day, is_assessment, is_annual)
            assert actual == expected, f"Visit {visit_num} on day {day}: expected {expected}, got {actual}"
    
    def test_tae_transition_at_year_two(self):
        """Test T&E transition from fixed to adaptive."""
        classifier = VisitClassifier('T&E')
        
        # Year 1: Identical to T&T
        year_one_visits = [
            (1, 0, 'injection_only'),
            (2, 28, 'injection_only'),
            (3, 56, 'injection_only'),
            (4, 84, 'decision_only'),  # assessment
            (5, 112, 'injection_only'),
            (6, 168, 'injection_only'),
            (7, 224, 'injection_only'),
        ]
        
        for visit_num, day, expected in year_one_visits:
            is_assessment = (visit_num == 4)
            actual = classifier.get_visit_type(visit_num, day, is_assessment)
            assert actual == expected
        
        # Year 2: All visits have decisions
        year_two_visits = [
            (8, 280, 'decision_with_injection'),
            (9, 336, 'decision_with_injection'),
            (10, 392, 'decision_with_injection'),
            (11, 448, 'decision_with_injection'),
        ]
        
        for visit_num, day, expected in year_two_visits:
            actual = classifier.get_visit_type(visit_num, day)
            assert actual == expected