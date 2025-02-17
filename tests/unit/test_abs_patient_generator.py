import pytest
from datetime import datetime, timedelta
from simulation.abs_patient_generator import ABSPatientGenerator

def test_abs_patient_generator_initialization():
    """Test that ABSPatientGenerator initializes correctly."""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    rate_per_week = 5
    
    generator = ABSPatientGenerator(rate_per_week, start_date, end_date, random_seed=42)
    assert generator.rate_per_week == rate_per_week
    assert generator.start_date == start_date
    assert generator.end_date == end_date

def test_generate_agents():
    """Test that generate_agents produces expected output format."""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)  # One month
    rate_per_week = 3
    
    generator = ABSPatientGenerator(rate_per_week, start_date, end_date, random_seed=42)
    agents = generator.generate_agents()
    
    # Check that we get a list of tuples
    assert isinstance(agents, list)
    assert all(isinstance(item, tuple) for item in agents)
    assert all(len(item) == 2 for item in agents)
    
    # Check first agent's structure
    arrival_time, state = agents[0]
    assert isinstance(arrival_time, datetime)
    assert isinstance(state, dict)
    
    # Check required state fields
    required_fields = {
        "patient_id", "baseline_vision", "current_vision", "treatment_naive",
        "risk_factors", "disease_activity", "treatment_history", "visit_history"
    }
    assert all(field in state for field in required_fields)
    
    # Check risk factors structure
    risk_factors = state["risk_factors"]
    assert "age" in risk_factors
    assert "diabetes" in risk_factors
    assert "hypertension" in risk_factors
    assert "smoking" in risk_factors

def test_arrival_time_distribution():
    """Test that arrival times follow expected distribution."""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    rate_per_week = 5
    
    generator = ABSPatientGenerator(rate_per_week, start_date, end_date, random_seed=42)
    agents = generator.generate_agents()
    
    # Extract arrival times
    arrival_times = [arrival for arrival, _ in agents]
    
    # Check times are within bounds
    assert all(start_date <= time <= end_date for time in arrival_times)
    
    # Check times are ordered
    assert arrival_times == sorted(arrival_times)
    
    # Check approximate number of arrivals
    expected_arrivals = rate_per_week * 52  # Full year
    actual_arrivals = len(agents)
    # Allow for 20% deviation from expected value
    assert abs(actual_arrivals - expected_arrivals) / expected_arrivals < 0.2

def test_disease_activity_calculation():
    """Test that disease activity is calculated appropriately based on risk factors."""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 2)
    generator = ABSPatientGenerator(1, start_date, end_date, random_seed=42)
    
    # Test with high-risk patient
    high_risk_factors = {
        "age": 85,
        "diabetes": True,
        "hypertension": True,
        "smoking": True
    }
    high_risk_activity = generator._generate_initial_disease_activity(high_risk_factors)
    
    # Test with low-risk patient
    low_risk_factors = {
        "age": 65,
        "diabetes": False,
        "hypertension": False,
        "smoking": False
    }
    low_risk_activity = generator._generate_initial_disease_activity(low_risk_factors)
    
    # High risk should have higher disease activity
    assert high_risk_activity > low_risk_activity
    # Both should be between 0 and 1
    assert 0 <= high_risk_activity <= 1
    assert 0 <= low_risk_activity <= 1

def test_risk_factor_generation():
    """Test that risk factors are generated with appropriate distributions."""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 2)
    generator = ABSPatientGenerator(1, start_date, end_date, random_seed=42)
    
    # Generate multiple sets of risk factors to check distributions
    num_samples = 1000
    risk_factors_list = [generator._generate_risk_factors() for _ in range(num_samples)]
    
    # Check age distribution
    ages = [rf["age"] for rf in risk_factors_list]
    mean_age = sum(ages) / len(ages)
    assert 70 <= mean_age <= 80  # Should be around 75
    
    # Check binary factor rates
    diabetes_rate = sum(1 for rf in risk_factors_list if rf["diabetes"]) / num_samples
    hypertension_rate = sum(1 for rf in risk_factors_list if rf["hypertension"]) / num_samples
    smoking_rate = sum(1 for rf in risk_factors_list if rf["smoking"]) / num_samples
    
    # Allow for some statistical variation
    assert 0.15 <= diabetes_rate <= 0.25  # Around 20%
    assert 0.45 <= hypertension_rate <= 0.55  # Around 50%
    assert 0.10 <= smoking_rate <= 0.20  # Around 15%
