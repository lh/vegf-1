# Enhanced Discontinuation Model with Clinician Variation
## Design Document

**Author:** Cline  
**Date:** May 3, 2025  
**Version:** 1.0

## 1. Introduction

### 1.1 Problem Statement

The current discontinuation model in the AMD simulation has several limitations:

1. It treats all discontinuations as a single type, not distinguishing between protocol-based and non-protocol-based cessations
2. It lacks time-dependent recurrence probabilities based on clinical data
3. It doesn't account for clinician variation in protocol adherence
4. It doesn't incorporate patient risk factors that affect recurrence rates

These limitations reduce the realism of the simulation and prevent analysis of how different discontinuation patterns and clinician behaviors affect patient outcomes.

### 1.2 Goals

1. Implement multiple discontinuation types with different recurrence patterns
2. Add time-dependent recurrence probabilities based on clinical literature
3. Model clinician variation in protocol adherence
4. Incorporate patient risk factors that affect recurrence rates
5. Enable analysis of outcomes by discontinuation type and clinician profile

### 1.3 Scope

This enhancement will modify:
- The discontinuation parameter structure
- The DiscontinuationManager class
- Integration points in both ABS and DES implementations
- Statistics tracking and reporting

It will add:
- A Clinician class to model individual clinician behavior
- A ClinicianManager class to handle clinician assignment
- Patient risk factor modeling

## 2. Parameter Structure

### 2.1 Enhanced Discontinuation Configuration

```yaml
# Enhanced discontinuation configuration
discontinuation:
  enabled: true
  
  # Criteria for discontinuation
  criteria:
    # Planned discontinuation (protocol-based)
    stable_max_interval:
      consecutive_visits: 3       # Number of consecutive stable visits required
      probability: 0.2            # Probability of discontinuation when criteria met
      interval_weeks: 16          # Required interval for planned discontinuation
    
    # Unplanned discontinuations - administrative
    random_administrative:
      annual_probability: 0.05    # Annual probability of random discontinuation
    
    # Unplanned discontinuations - time-based
    treatment_duration:
      threshold_weeks: 52         # Weeks of treatment before considering discontinuation
      probability: 0.1            # Probability of discontinuation after threshold
    
    # Premature discontinuation (non-adherence to protocol)
    premature:
      min_interval_weeks: 8       # Minimum interval where premature discontinuation might occur
      probability_factor: 2.0     # Multiplier for discontinuation probability (relative to planned)
  
  # Post-discontinuation monitoring schedules by cessation type
  monitoring:
    planned:
      follow_up_schedule: [12, 24, 36]  # Weeks after discontinuation for follow-up visits
    unplanned:
      follow_up_schedule: [8, 16, 24]   # More frequent monitoring for unplanned cessation
    recurrence_detection_probability: 0.87  # Probability of detecting recurrence if present
  
  # Disease recurrence models
  recurrence:
    # Planned discontinuation (stable at max interval)
    planned:
      base_annual_rate: 0.13      # Annual base recurrence rate (from Arendt)
      cumulative_rates:           # Cumulative rates over time
        year_1: 0.13              # 1-year cumulative rate
        year_3: 0.40              # 3-year cumulative rate
        year_5: 0.65              # 5-year cumulative rate
    
    # Premature discontinuation (before reaching stability at max interval)
    premature:
      base_annual_rate: 0.53      # Annual base recurrence rate (from Aslanis)
      cumulative_rates:
        year_1: 0.53              # 1-year cumulative rate
        year_3: 0.85              # 3-year cumulative rate (estimated)
        year_5: 0.95              # 5-year cumulative rate (estimated)
    
    # Administrative discontinuation
    administrative:
      base_annual_rate: 0.30      # Annual base recurrence rate (estimated)
      cumulative_rates:
        year_1: 0.30              # 1-year cumulative rate
        year_3: 0.70              # 3-year cumulative rate
        year_5: 0.85              # 5-year cumulative rate
    
    # Time-based discontinuation (after fixed duration)
    duration_based:
      base_annual_rate: 0.32      # Annual base recurrence rate (from Artiaga)
      cumulative_rates:
        year_1: 0.21              # 1-year cumulative rate (from Artiaga)
        year_3: 0.74              # 3-year cumulative rate (from Artiaga)
        year_5: 0.88              # 5-year cumulative rate (from Artiaga)
    
    # Risk factors that modify recurrence rates
    risk_modifiers:
      with_PED: 1.54              # Multiplier for recurrence rate if PED is present (74%/48% from Aslanis)
      without_PED: 1.0            # Reference rate
  
  # Treatment re-entry criteria
  retreatment:
    eligibility_criteria:
      detected_fluid: true        # Fluid must be detected
      vision_loss_letters: 5      # Minimum vision loss to trigger retreatment
    probability: 0.95             # Probability of retreatment when eligible
```

### 2.2 Clinician Configuration

```yaml
# Clinician configuration
clinicians:
  enabled: true
  
  # Clinician profiles with different adherence characteristics
  profiles:
    # Protocol-adherent "by the book" clinician
    adherent:
      protocol_adherence_rate: 0.95
      probability: 0.25  # 25% of clinicians follow this profile
      characteristics:
        risk_tolerance: "low"      # Affects discontinuation decisions
        conservative_retreatment: true  # More likely to restart treatment
    
    # Average clinician
    average:
      protocol_adherence_rate: 0.80
      probability: 0.50  # 50% of clinicians follow this profile
      characteristics:
        risk_tolerance: "medium"
        conservative_retreatment: false
    
    # Less adherent "freestyle" clinician
    non_adherent:
      protocol_adherence_rate: 0.50
      probability: 0.25  # 25% of clinicians follow this profile
      characteristics:
        risk_tolerance: "high"     # More willing to discontinue early
        conservative_retreatment: false
  
  # Clinician decision biases
  decision_biases:
    # Different thresholds for considering "stable" disease
    stability_thresholds:
      adherent: 3       # Requires 3 consecutive stable visits
      average: 2        # Requires 2 consecutive stable visits
      non_adherent: 1   # Only requires 1 stable visit
    
    # Different preferences for treatment intervals
    interval_preferences:
      adherent:
        min_interval: 8
        max_interval: 16
        extension_threshold: 2   # Letters of improvement needed to extend
      average:
        min_interval: 8
        max_interval: 12        # More conservative max interval
        extension_threshold: 1
      non_adherent:
        min_interval: 6         # May use shorter intervals
        max_interval: 16
        extension_threshold: 0   # Extends even with no improvement
  
  # Patient assignment model
  patient_assignment:
    mode: "fixed"  # Options: "fixed", "random_per_visit", "weighted"
    continuity_of_care: 0.9  # Probability of seeing the same clinician (if mode="weighted")
```

## 3. Class Design

### 3.1 Enhanced DiscontinuationManager

```python
class EnhancedDiscontinuationManager:
    """Enhanced manager for treatment discontinuation decisions and monitoring.
    
    Tracks different types of discontinuation and applies appropriate recurrence models.
    """
    
    def __init__(self, config):
        # Existing initialization plus:
        self.protocol_adherence = config.get("discontinuation", {}).get("protocol_adherence", {}).get("adherence_rate", 1.0)
        self.recurrence_models = config.get("discontinuation", {}).get("recurrence", {})
        
        # Enhanced statistics
        self.stats = {
            "stable_max_interval_discontinuations": 0,
            "random_administrative_discontinuations": 0,
            "treatment_duration_discontinuations": 0,
            "premature_discontinuations": 0,
            "total_discontinuations": 0,
            "retreatments": 0,
            "retreatments_by_type": {
                "planned": 0,
                "premature": 0,
                "administrative": 0,
                "duration_based": 0
            }
        }
    
    def evaluate_discontinuation(self, patient_state, current_time, clinician_id=None, treatment_start_time=None):
        """Evaluate whether a patient should discontinue treatment.
        
        Returns discontinue flag, reason, probability, and cessation_type.
        """
        # Similar to existing logic, but adds:
        
        # 1. Check if clinician follows protocol
        follows_protocol = np.random.random() < self.protocol_adherence
        
        # 2. Check for premature discontinuation if not following protocol
        if not follows_protocol and not max_interval_reached:
            current_interval = disease_activity.get("current_interval", 0)
            min_premature_interval = self.criteria.get("premature", {}).get("min_interval_weeks", 8)
            
            if current_interval >= min_premature_interval:
                premature_factor = self.criteria.get("premature", {}).get("probability_factor", 2.0)
                probability = stable_max_interval.get("probability", 0.2) * premature_factor
                
                if np.random.random() < probability:
                    self.stats["premature_discontinuations"] += 1
                    self.stats["total_discontinuations"] += 1
                    return True, "premature", probability, "premature"
        
        # 3. Return cessation_type with other results
        # For existing discontinuation types:
        if standard_discontinuation_occurs:
            return True, reason, probability, reason  # reason becomes cessation_type
            
        return False, "", 0.0, None
    
    def schedule_monitoring(self, discontinuation_time, cessation_type="planned"):
        """Schedule monitoring visits based on cessation type."""
        follow_up_schedule = self.monitoring.get(cessation_type, {}).get(
            "follow_up_schedule",
            self.monitoring.get("planned", {}).get("follow_up_schedule", [12, 24, 36])
        )
        # Rest similar to current implementation
    
    def calculate_recurrence_probability(self, weeks_since_discontinuation, cessation_type, has_PED=False):
        """Calculate disease recurrence probability based on time and cessation type."""
        # Get the appropriate recurrence model
        recurrence_model = self.recurrence_models.get(cessation_type, self.recurrence_models.get("planned", {}))
        
        # Get base annual rate
        base_annual_rate = recurrence_model.get("base_annual_rate", 0.13)
        
        # Get cumulative rates
        cumulative_rates = recurrence_model.get("cumulative_rates", {})
        year_1_rate = cumulative_rates.get("year_1", base_annual_rate)
        year_3_rate = cumulative_rates.get("year_3", year_1_rate * 2.5)
        year_5_rate = cumulative_rates.get("year_5", year_3_rate * 1.2)
        
        # Calculate time-dependent rate using piecewise linear interpolation
        weeks_in_year = 52
        if weeks_since_discontinuation <= weeks_in_year:
            # Linear interpolation from 0 to year_1_rate
            rate = (weeks_since_discontinuation / weeks_in_year) * year_1_rate
        elif weeks_since_discontinuation <= 3 * weeks_in_year:
            # Linear interpolation from year_1_rate to year_3_rate
            progress = (weeks_since_discontinuation - weeks_in_year) / (2 * weeks_in_year)
            rate = year_1_rate + progress * (year_3_rate - year_1_rate)
        elif weeks_since_discontinuation <= 5 * weeks_in_year:
            # Linear interpolation from year_3_rate to year_5_rate
            progress = (weeks_since_discontinuation - 3 * weeks_in_year) / (2 * weeks_in_year)
            rate = year_3_rate + progress * (year_5_rate - year_3_rate)
        else:
            # Cap at year_5_rate
            rate = year_5_rate
        
        # Apply risk modifiers
        if has_PED:
            PED_modifier = self.recurrence_models.get("risk_modifiers", {}).get("with_PED", 1.54)
            rate = min(1.0, rate * PED_modifier)  # Cap at 100%
        
        return rate
    
    def process_monitoring_visit(self, patient_state, actions):
        """Process a monitoring visit for a discontinued patient."""
        # Similar to existing, but add:
        
        # Get cessation type and time since discontinuation
        cessation_type = patient_state.get("treatment_status", {}).get("discontinuation_reason", "planned")
        discontinuation_date = patient_state.get("treatment_status", {}).get("discontinuation_date")
        
        if discontinuation_date:
            current_time = datetime.now()  # Or get from simulation context
            weeks_since_discontinuation = (current_time - discontinuation_date).days / 7
            
            # Calculate recurrence probability for this visit
            has_PED = patient_state.get("disease_characteristics", {}).get("has_PED", False)
            recurrence_probability = self.calculate_recurrence_probability(
                weeks_since_discontinuation, cessation_type, has_PED
            )
            
            # Determine if disease has recurred
            disease_recurred = np.random.random() < recurrence_probability
            
            if disease_recurred:
                # Update patient's disease activity
                patient_state["disease_activity"]["fluid_detected"] = True
                
                # Apply detection probability
                recurrence_detected = np.random.random() < self.monitoring.get("recurrence_detection_probability", 0.87)
                
                if recurrence_detected and "oct_scan" in actions:
                    # Update retreatment statistics by cessation type
                    if self.evaluate_retreatment(patient_state)[0]:
                        self.stats["retreatments_by_type"][cessation_type] += 1
                        # Existing logic for retreatment...
```

### 3.2 Clinician Class

```python
class Clinician:
    """Model of an individual clinician with characteristic behaviors."""
    
    def __init__(self, profile_name, profile_config):
        self.profile_name = profile_name
        self.adherence_rate = profile_config.get("protocol_adherence_rate", 0.8)
        self.risk_tolerance = profile_config.get("characteristics", {}).get("risk_tolerance", "medium")
        self.conservative_retreatment = profile_config.get("characteristics", {}).get("conservative_retreatment", False)
        
        # Decision thresholds from global config
        self.stability_threshold = None  # Will be set from global config
        self.interval_preferences = None  # Will be set from global config
    
    def follows_protocol(self):
        """Determine if the clinician follows protocol for this decision."""
        return np.random.random() < self.adherence_rate
    
    def evaluate_discontinuation(self, patient_state, protocol_decision, protocol_probability):
        """Apply clinician-specific modification to discontinuation decisions."""
        # If protocol says to discontinue
        if protocol_decision:
            # High risk tolerance clinicians almost always agree to discontinue
            if self.risk_tolerance == "high":
                return True, min(1.0, protocol_probability * 1.3)
            # Low risk tolerance clinicians sometimes override to continue
            elif self.risk_tolerance == "low":
                override_chance = 0.3  # 30% chance of overriding discontinuation
                if np.random.random() < override_chance:
                    return False, 0.0
            
            # Default: follow protocol decision
            return True, protocol_probability
        
        # If protocol says to continue
        else:
            # High risk tolerance clinicians sometimes discontinue anyway
            if self.risk_tolerance == "high":
                premature_chance = 0.15  # 15% chance of premature discontinuation
                if np.random.random() < premature_chance:
                    return True, 0.15
            
            # Default: follow protocol decision
            return False, 0.0
    
    def evaluate_retreatment(self, patient_state, protocol_decision, protocol_probability):
        """Apply clinician-specific modification to retreatment decisions."""
        # Conservative clinicians almost always retreat
        if self.conservative_retreatment:
            return protocol_decision, min(1.0, protocol_probability * 1.2)
        
        # Risk-taking clinicians might decide against retreatment
        if self.risk_tolerance == "high" and protocol_decision:
            skip_chance = 0.2  # 20% chance of skipping retreatment
            if np.random.random() < skip_chance:
                return False, 0.0
        
        # Default: follow protocol decision
        return protocol_decision, protocol_probability
```

### 3.3 ClinicianManager Class

```python
class ClinicianManager:
    """Manages a pool of clinicians and handles patient assignment."""
    
    def __init__(self, config):
        self.config = config
        self.clinicians = {}
        self.patient_assignments = {}  # Maps patient_id to clinician_id
        self.mode = config.get("clinicians", {}).get("patient_assignment", {}).get("mode", "fixed")
        self.continuity = config.get("clinicians", {}).get("patient_assignment", {}).get("continuity_of_care", 0.9)
        
        # Initialize clinician pool
        self._initialize_clinicians()
    
    def _initialize_clinicians(self):
        """Create the pool of clinicians based on configuration."""
        profiles = self.config.get("clinicians", {}).get("profiles", {})
        biases = self.config.get("clinicians", {}).get("decision_biases", {})
        
        # Calculate how many of each type to create (for a pool of 10 clinicians)
        total_clinicians = 10
        clinician_counts = {}
        
        for profile_name, profile in profiles.items():
            probability = profile.get("probability", 0.0)
            count = max(1, round(probability * total_clinicians))
            clinician_counts[profile_name] = count
        
        # Create the clinicians
        clinician_id = 1
        for profile_name, count in clinician_counts.items():
            for i in range(count):
                # Create clinician with this profile
                clinician = Clinician(profile_name, profiles[profile_name])
                
                # Set decision thresholds
                clinician.stability_threshold = biases.get("stability_thresholds", {}).get(profile_name, 2)
                clinician.interval_preferences = biases.get("interval_preferences", {}).get(profile_name, {})
                
                # Add to pool
                self.clinicians[f"CLINICIAN{clinician_id:03d}"] = clinician
                clinician_id += 1
    
    def assign_clinician(self, patient_id, visit_time):
        """Assign a clinician to a patient for this visit."""
        # If mode is fixed and patient already has an assignment, keep it
        if self.mode == "fixed" and patient_id in self.patient_assignments:
            return self.patient_assignments[patient_id]
        
        # If mode is random_per_visit, always pick a random clinician
        if self.mode == "random_per_visit":
            clinician_id = np.random.choice(list(self.clinicians.keys()))
            return clinician_id
        
        # If mode is weighted or this is the first visit for a fixed assignment
        if self.mode == "weighted" and patient_id in self.patient_assignments:
            # Check continuity of care
            if np.random.random() < self.continuity:
                return self.patient_assignments[patient_id]
            else:
                # Assign to a new clinician
                current = self.patient_assignments[patient_id]
                options = [cid for cid in self.clinicians.keys() if cid != current]
                clinician_id = np.random.choice(options)
                self.patient_assignments[patient_id] = clinician_id
                return clinician_id
        
        # Default: new random assignment
        clinician_id = np.random.choice(list(self.clinicians.keys()))
        self.patient_assignments[patient_id] = clinician_id
        return clinician_id
    
    def get_clinician(self, clinician_id):
        """Get a clinician by ID."""
        return self.clinicians.get(clinician_id)
```

### 3.4 Patient Risk Factors

```python
# Add to Patient class in ABS implementation
def __init__(self, patient_id, initial_vision, start_date):
    # Existing initialization...
    
    # Add disease characteristics including risk factors
    self.disease_characteristics = {
        "has_PED": np.random.random() < 0.3,  # 30% of patients have PED
        "lesion_size": np.random.choice(["small", "medium", "large"], p=[0.3, 0.5, 0.2]),
        "lesion_type": np.random.choice(["classic", "occult", "mixed"], p=[0.2, 0.5, 0.3])
    }
```

## 4. Integration Points

### 4.1 ABS Implementation

```python
# In TreatAndExtendABS.__init__
def __init__(self, config, start_date=None):
    # Existing initialization...
    
    # Initialize clinician manager
    self.clinician_manager = ClinicianManager(self.config.parameters)
    
    # Initialize enhanced discontinuation manager
    discontinuation_params = self.config.get_treatment_discontinuation_params()
    self.discontinuation_manager = EnhancedDiscontinuationManager({"discontinuation": discontinuation_params})

# In TreatAndExtendABS.process_event
def process_event(self, event):
    # Existing code...
    
    # Get the assigned clinician for this visit
    clinician_id = self.clinician_manager.assign_clinician(patient_id, event.time)
    event.data["clinician_id"] = clinician_id  # Store for reference
    
    # When evaluating discontinuation:
    should_discontinue, reason, probability, cessation_type = self.discontinuation_manager.evaluate_discontinuation(
        patient_state=patient_state,
        current_time=event.time,
        clinician_id=clinician_id,
        treatment_start_time=patient.treatment_start
    )
    
    if should_discontinue:
        # Update patient status with cessation_type
        patient.treatment_status["active"] = False
        patient.treatment_status["discontinuation_date"] = event.time
        patient.treatment_status["discontinuation_reason"] = reason
        patient.treatment_status["cessation_type"] = cessation_type
        self.stats["protocol_discontinuations"] += 1
```

### 4.2 DES Implementation

Similar modifications to the DES implementation.

## 5. Statistics and Reporting

### 5.1 Enhanced Statistics

```python
# In EnhancedDiscontinuationManager
def get_statistics(self):
    """Get enhanced discontinuation statistics."""
    stats = self.stats.copy()
    
    # Calculate additional metrics
    if stats["total_discontinuations"] > 0:
        stats["retreatment_rate"] = stats["retreatments"] / stats["total_discontinuations"]
        
        # Retreatment rates by cessation type
        stats["retreatment_rates_by_type"] = {}
        for cessation_type, count in stats["retreatments_by_type"].items():
            type_count = stats.get(f"{cessation_type}_discontinuations", 0)
            if type_count > 0:
                stats["retreatment_rates_by_type"][cessation_type] = count / type_count
            else:
                stats["retreatment_rates_by_type"][cessation_type] = 0.0
    else:
        stats["retreatment_rate"] = 0.0
    
    return stats
```

### 5.2 Clinician Performance Metrics

```python
# In ClinicianManager
def get_performance_metrics(self):
    """Get performance metrics by clinician profile."""
    metrics = {
        "profile_counts": {},
        "patient_counts": {},
        "discontinuation_rates": {},
        "retreatment_rates": {}
    }
    
    # Count clinicians by profile
    for clinician in self.clinicians.values():
        metrics["profile_counts"][clinician.profile_name] = metrics["profile_counts"].get(clinician.profile_name, 0) + 1
    
    # Count patients by assigned clinician profile
    for patient_id, clinician_id in self.patient_assignments.items():
        clinician = self.clinicians.get(clinician_id)
        if clinician:
            metrics["patient_counts"][clinician.profile_name] = metrics["patient_counts"].get(clinician.profile_name, 0) + 1
    
    # Additional metrics would be calculated from simulation results
    
    return metrics
```

## 6. Implementation Strategy

### 6.1 Phase 1: Basic Framework (Week 1)

1. Update the YAML configuration format
2. Create skeleton classes for EnhancedDiscontinuationManager, Clinician, and ClinicianManager
3. Implement basic patient risk factor tracking
4. Add cessation type tracking to the discontinuation process

### 6.2 Phase 2: Clinician Variation (Week 2)

1. Implement the Clinician class with protocol adherence logic
2. Implement the ClinicianManager for patient assignment
3. Integrate clinician decision-making with the discontinuation process
4. Add basic statistics tracking for clinician performance

### 6.3 Phase 3: Time-dependent Recurrence (Week 3)

1. Implement the calculate_recurrence_probability method
2. Update the monitoring visit processing to use time-dependent probabilities
3. Differentiate monitoring schedules by cessation type
4. Enhance statistics tracking for different cessation types

### 6.4 Phase 4: Testing and Validation (Week 4)

1. Create unit tests for the new functionality
2. Validate recurrence rates against clinical data
3. Run simulations with different clinician profiles
4. Generate reports comparing outcomes by cessation type and clinician profile

## 7. Testing Approach

### 7.1 Unit Tests

1. Test the EnhancedDiscontinuationManager
   - Test different discontinuation types
   - Test time-dependent recurrence calculation
   - Test monitoring visit scheduling

2. Test the Clinician class
   - Test protocol adherence logic
   - Test decision modifications

3. Test the ClinicianManager
   - Test clinician assignment modes
   - Test continuity of care

### 7.2 Integration Tests

1. Test the integration with ABS implementation
2. Test the integration with DES implementation
3. Test end-to-end simulation with the enhanced model

### 7.3 Validation Tests

1. Compare simulated recurrence rates to clinical data
2. Validate clinician behavior against expected patterns
3. Verify that patient risk factors appropriately modify recurrence rates

## 8. Expected Outcomes

### 8.1 Simulation Results

1. More realistic discontinuation patterns
   - Mix of protocol-based and non-protocol-based discontinuations
   - Time-dependent recurrence rates

2. Clinician variation effects
   - Different outcomes based on clinician profile
   - Impact of protocol adherence on patient outcomes

3. Risk stratification
   - Higher recurrence rates for patients with risk factors
   - Different monitoring needs based on risk profile

### 8.2 Analysis Capabilities

1. Compare outcomes by discontinuation type
2. Evaluate the impact of clinician protocol adherence
3. Identify optimal monitoring schedules for different patient groups
4. Assess the cost-effectiveness of different discontinuation strategies

## 9. Future Extensions

1. More sophisticated clinician decision models
2. Additional patient risk factors
3. Machine learning-based prediction of recurrence risk
4. Economic modeling of different discontinuation strategies
5. Patient preference modeling for treatment decisions

## 10. References

1. Aslanis et al. (2021): Prospective study of treatment discontinuation after treat-and-extend
2. Artiaga et al. (2023): Retrospective study of treatment discontinuation with long-term follow-up
3. Arendt et al.: Study of discontinuation after three 16-week intervals
4. ALTAIR Study (2020): Japanese treat-and-extend study with 2-week vs. 4-week adjustments
