"""
Test patient state management.

Patients track:
- Current disease state (FOV)
- Treatment history
- Vision over time
- Discontinuation status
"""

import pytest
from datetime import datetime, timedelta
from simulation_v2.core.patient import Patient
from simulation_v2.core.disease_model import DiseaseState


class TestPatient:
    """Test patient state and history tracking."""
    
    def test_patient_creation(self):
        """Patient should initialize with proper defaults."""
        patient = Patient(patient_id="P001")
        
        assert patient.id == "P001"
        assert patient.current_state == DiseaseState.NAIVE
        assert patient.baseline_vision == 70  # Default starting vision
        assert patient.current_vision == 70
        assert len(patient.visit_history) == 0
        assert patient.is_discontinued == False
        assert patient.discontinuation_type is None
        
    def test_custom_baseline_vision(self):
        """Should accept custom baseline vision."""
        patient = Patient(patient_id="P002", baseline_vision=65)
        assert patient.baseline_vision == 65
        assert patient.current_vision == 65
        
    def test_record_visit(self):
        """Should track visit history."""
        patient = Patient("P003")
        visit_date = datetime(2024, 1, 15)
        
        patient.record_visit(
            date=visit_date,
            disease_state=DiseaseState.ACTIVE,
            treatment_given=True,
            vision=68
        )
        
        assert len(patient.visit_history) == 1
        visit = patient.visit_history[0]
        assert visit['date'] == visit_date
        assert visit['disease_state'] == DiseaseState.ACTIVE
        assert visit['treatment_given'] == True
        assert visit['vision'] == 68
        
        # Current state should update
        assert patient.current_state == DiseaseState.ACTIVE
        assert patient.current_vision == 68
        
    def test_injection_count(self):
        """Should track number of injections."""
        patient = Patient("P004")
        
        # Initial count
        assert patient.injection_count == 0
        
        # Record visits with and without injections
        patient.record_visit(
            date=datetime(2024, 1, 1),
            disease_state=DiseaseState.ACTIVE,
            treatment_given=True,
            vision=70
        )
        assert patient.injection_count == 1
        
        patient.record_visit(
            date=datetime(2024, 2, 1),
            disease_state=DiseaseState.STABLE,
            treatment_given=False,
            vision=71
        )
        assert patient.injection_count == 1  # No change
        
        patient.record_visit(
            date=datetime(2024, 3, 1),
            disease_state=DiseaseState.ACTIVE,
            treatment_given=True,
            vision=69
        )
        assert patient.injection_count == 2
        
    def test_days_since_last_injection(self):
        """Should calculate days since last injection."""
        patient = Patient("P005")
        
        # No injections yet
        assert patient.days_since_last_injection is None
        
        # First injection
        patient.record_visit(
            date=datetime(2024, 1, 1),
            disease_state=DiseaseState.ACTIVE,
            treatment_given=True,
            vision=70
        )
        
        # Check after 28 days (4 weeks)
        days = patient.days_since_last_injection_at(datetime(2024, 1, 29))
        assert days == 28
        
        # Another injection
        patient.record_visit(
            date=datetime(2024, 2, 1),
            disease_state=DiseaseState.ACTIVE,
            treatment_given=True,
            vision=70
        )
        
        # Should measure from most recent injection
        days = patient.days_since_last_injection_at(datetime(2024, 2, 15))
        assert days == 14
        
        # Test convenience method for weeks
        weeks = patient.weeks_since_last_injection_at(datetime(2024, 2, 15))
        assert weeks == 2.0
        
    def test_discontinuation(self):
        """Should track discontinuation status."""
        patient = Patient("P006")
        
        # Not discontinued initially
        assert patient.is_discontinued == False
        assert patient.discontinuation_date is None
        assert patient.discontinuation_type is None
        
        # Discontinue patient
        disc_date = datetime(2024, 6, 1)
        patient.discontinue(
            date=disc_date,
            discontinuation_type="planned"
        )
        
        assert patient.is_discontinued == True
        assert patient.discontinuation_date == disc_date
        assert patient.discontinuation_type == "planned"
        
    def test_cannot_treat_discontinued_patient(self):
        """Should not allow treatment after discontinuation."""
        patient = Patient("P007")
        
        # Discontinue
        patient.discontinue(
            date=datetime(2024, 6, 1),
            discontinuation_type="planned"
        )
        
        # Try to record treatment visit
        with pytest.raises(ValueError, match="Cannot give treatment to discontinued patient"):
            patient.record_visit(
                date=datetime(2024, 7, 1),
                disease_state=DiseaseState.ACTIVE,
                treatment_given=True,
                vision=70
            )
            
    def test_monitoring_visits_allowed_after_discontinuation(self):
        """Should allow monitoring visits after discontinuation."""
        patient = Patient("P008")
        
        # Discontinue
        patient.discontinue(
            date=datetime(2024, 6, 1),
            discontinuation_type="planned"
        )
        
        # Monitoring visit (no treatment)
        patient.record_visit(
            date=datetime(2024, 7, 1),
            disease_state=DiseaseState.STABLE,
            treatment_given=False,
            vision=72
        )
        
        assert len(patient.visit_history) == 1
        assert patient.current_vision == 72
        
    def test_retreatment(self):
        """Should handle retreatment after discontinuation."""
        patient = Patient("P009")
        
        # Initial treatment
        patient.record_visit(
            date=datetime(2024, 1, 1),
            disease_state=DiseaseState.ACTIVE,
            treatment_given=True,
            vision=70
        )
        
        # Discontinue
        patient.discontinue(
            date=datetime(2024, 3, 1),
            discontinuation_type="planned"
        )
        
        # Disease recurrence - restart treatment
        patient.restart_treatment(date=datetime(2024, 6, 1))
        
        assert patient.is_discontinued == False
        assert patient.retreatment_count == 1
        assert patient.retreatment_dates == [datetime(2024, 6, 1)]
        
        # Can now receive treatment again
        patient.record_visit(
            date=datetime(2024, 6, 1),
            disease_state=DiseaseState.ACTIVE,
            treatment_given=True,
            vision=68
        )