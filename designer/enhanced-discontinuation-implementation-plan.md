# Enhanced Discontinuation Model Implementation Plan

**Author:** Luke Herbert 
**Date:** May 3, 2025  
**Version:** 1.0

## Overview

This document outlines the implementation plan for the enhanced discontinuation model as described in the design document. The implementation will proceed in four phases over a four-week period, with each phase building on the previous one.

## Implementation Approach

We'll proceed with the following approach:

1. Create a new `EnhancedDiscontinuationManager` class that inherits from the current `DiscontinuationManager`
2. Implement clinician variation as a configurable option with a perfect clinician as the default state
3. Use the comprehensive AMD parameters for time-dependent recurrence probability calculations
4. Maintain the proposed YAML configuration structure from the design document

## Phase 1: Basic Framework (Week 1) - COMPLETED

This phase establishes the core of the enhanced model:

**Status: Completed on May 3, 2025**

### 1.1 Create `EnhancedDiscontinuationManager` class

- Create a new class that inherits from `DiscontinuationManager`
- Override the `evaluate_discontinuation` method to return cessation type
- Add support for premature discontinuation type
- Enhance statistics tracking for different discontinuation types

```python
class EnhancedDiscontinuationManager(DiscontinuationManager):
    """Enhanced discontinuation manager with multiple discontinuation types and time-dependent recurrence.
    
    Extends the base DiscontinuationManager to provide:
    1. Multiple discontinuation types (protocol-based, administrative, time-based, premature)
    2. Type-specific monitoring schedules
    3. Time-dependent recurrence probabilities based on clinical data
    4. Tracking of discontinuation type in patient state
    """
```

### 1.2 Update patient state structure

- Add `cessation_type` to treatment status
- Add cost tracking for future economic analysis
- Add risk factor tracking (composite approach)

### 1.3 Update ABS and DES implementations

- Modify to use the enhanced manager
- Update patient state tracking
- Pass cessation type to patient records

### 1.4 Add enhanced statistics tracking

- Track discontinuations by type
- Track retreatments by discontinuation type
- Prepare for economic analysis with cost tracking

### 1.5 Create debug script for testing - COMPLETED

- Created `debug_enhanced_discontinuation.py` script for testing the enhanced discontinuation model
- Implemented mock data generation for testing different discontinuation types
- Added visualization of discontinuation patterns by type and clinician profile
- Implemented detailed statistics reporting for discontinuation types, PED prevalence, and retreatment rates

## Phase 2: Clinician Variation (Week 2) - COMPLETED

**Status: Completed on May 3, 2025**

### 2.1 Create `Clinician` class - COMPLETED

- Default "perfect" clinician with complete protocol adherence
- Configurable profiles with varying adherence characteristics
- Decision modification logic for discontinuation and retreatment

```python
class Clinician:
    """Model of an individual clinician with characteristic behaviors.
    
    This class represents a clinician with specific adherence characteristics
    that affect treatment decisions. The default "perfect" clinician follows
    protocol perfectly.
    """
```

### 2.2 Create `ClinicianManager` class - COMPLETED

- Configurable on/off setting
- Patient assignment logic
- Clinician profile distribution

```python
class ClinicianManager:
    """Manages a pool of clinicians and handles patient assignment.
    
    When enabled, creates a pool of clinicians with different profiles and
    assigns them to patients. When disabled, uses a single "perfect" clinician.
    """
```

### 2.3 Update `EnhancedDiscontinuationManager` - COMPLETED

- Accept clinician input for decisions
- Apply clinician-specific decision modifications
- Track clinician influence on decisions
- Enhanced statistics tracking for clinician decisions

### 2.4 Integrate clinician variation with simulation classes - COMPLETED

- Initialize and use clinician manager
- Pass clinician ID to discontinuation manager
- Track decision modifications
- Update monitoring visit scheduling to use clinician preferences

## Phase 3: Time-dependent Recurrence (Week 3) - IN PROGRESS

**Status: Partially completed on May 3, 2025**

### 3.1 Implement time-dependent recurrence model - COMPLETED

- Use Artiaga study data for recurrence rates
- Implement piecewise linear interpolation
- Add composite risk modifiers for PED

```python
def calculate_recurrence_probability(self, weeks_since_discontinuation, cessation_type, has_PED=False):
    """Calculate disease recurrence probability based on time and cessation type.
    
    Uses clinical data from Artiaga et al. and Aslanis et al. to determine
    time-dependent recurrence probabilities.
    """
```

### 3.2 Enhance monitoring visit processing - COMPLETED

- Use time-dependent recurrence probabilities - COMPLETED
- Apply appropriate probabilities by cessation type - COMPLETED
- Implement Year 2 monitoring schedule from Artiaga - COMPLETED

### 3.3 Update `process_monitoring_visit` method - COMPLETED

- Track discontinuation type for statistics
- Apply appropriate recurrence detection probabilities
- Track clinician influence on retreatment decisions

### 3.4 Implement basic reporting - IN PROGRESS

- Graph discontinuation types - COMPLETED
- Track recurrence rates by time - COMPLETED
- Report retreatment rates by discontinuation type - COMPLETED
- Visualize clinician influence on decisions - COMPLETED

## Phase 4: Testing and Integration (Week 4) - PENDING

### 4.1 Create comprehensive test suite - PARTIALLY COMPLETED

- Unit tests for each component - PARTIALLY COMPLETED
  - Test for `EnhancedDiscontinuationManager` - COMPLETED
  - Test for `Clinician` and `ClinicianManager` - COMPLETED
  - Integration tests for ABS and DES implementations - PENDING
  - Clinical validation tests - PENDING

### 4.2 Validate against clinical data - PENDING

- Verify recurrence rates match Artiaga study
- Validate clinician variation effects
- Test different discontinuation scenarios

### 4.3 Documentation and reporting - PARTIALLY COMPLETED

- Update docstrings with numpy format - COMPLETED
- Create visual reports of outcomes - PARTIALLY COMPLETED
- Document parameter configurations - PENDING

### 4.4 Final integration - PENDING

- Ensure compatibility with both simulation types
- Verify statistics collection
- Prepare for future economic analysis

## Implementation Details

### File Structure

```
simulation/
├── discontinuation_manager.py  # Existing file to be extended
├── enhanced_discontinuation_manager.py  # New file - COMPLETED
├── clinician.py  # New file - COMPLETED (includes ClinicianManager)
```

### Key Classes and Methods

#### EnhancedDiscontinuationManager

```python
class EnhancedDiscontinuationManager(DiscontinuationManager):
    def __init__(self, config):
        # Initialize with enhanced configuration
        
    def evaluate_discontinuation(self, patient_state, current_time, clinician_id=None, treatment_start_time=None):
        # Return discontinue flag, reason, probability, and cessation_type
        
    def schedule_monitoring(self, discontinuation_time, cessation_type="planned"):
        # Schedule monitoring based on cessation type
        
    def calculate_recurrence_probability(self, weeks_since_discontinuation, cessation_type, has_PED=False):
        # Calculate time-dependent recurrence probability
        
    def process_monitoring_visit(self, patient_state, actions):
        # Process monitoring with time-dependent recurrence
        
    def get_statistics(self):
        # Return enhanced statistics
```

#### Clinician

```python
class Clinician:
    def __init__(self, profile_name="perfect", profile_config=None):
        # Initialize clinician with profile
        
    def follows_protocol(self):
        # Determine if clinician follows protocol
        
    def evaluate_discontinuation(self, patient_state, protocol_decision, protocol_probability):
        # Modify discontinuation decision
        
    def evaluate_retreatment(self, patient_state, protocol_decision, protocol_probability):
        # Modify retreatment decision
```

#### ClinicianManager

```python
class ClinicianManager:
    def __init__(self, config, enabled=False):
        # Initialize clinician pool
        
    def _initialize_clinicians(self):
        # Create clinicians based on configuration
        
    def assign_clinician(self, patient_id, visit_time):
        # Assign clinician to patient
        
    def get_clinician(self, clinician_id):
        # Get clinician by ID
        
    def get_performance_metrics(self):
        # Get clinician performance metrics
```

### Integration with ABS

```python
# In TreatAndExtendABS.__init__
def __init__(self, config, start_date=None):
    # Initialize enhanced discontinuation manager
    # Initialize clinician manager if enabled
    
# In TreatAndExtendABS.process_event
def process_event(self, event):
    # Assign clinician to patient
    # Get enhanced discontinuation decision with cessation type
    # Update patient state with cessation type
```

### Integration with DES

Similar modifications to the DES implementation.

## Parameter Structure

We'll use the YAML configuration structure as outlined in the design document, with sections for:

1. Discontinuation criteria by type
2. Monitoring schedules by cessation type, including no-monitoring option for administrative cessation
3. Recurrence models with time-dependent rates
4. Risk modifiers for recurrence
5. Clinician profiles and characteristics

## Notable Implementation Decisions

1. **Composite Risk Approach**: Rather than tracking PED development separately, we've applied a single risk modifier based on the Aslanis study (74% vs 48% recurrence with/without PED).

2. **Monitoring Schedule**: We're implementing only the Year 2 recommendations from Artiaga, following a simplified approach.

3. **Clinician Influence Tracking**: We've added detailed tracking of clinician influence on decisions, including statistics by clinician profile and decision type.

4. **Enhanced Visualization**: We've created visualizations for discontinuation types, clinician profiles, and clinician decision influence.

5. **Backward Compatibility**: The enhanced manager is compatible with existing code while providing new functionality.

6. **Cessation-specific Monitoring**: Different cessation types will have different monitoring behaviors:
   - Planned cessation (stable_max_interval): Standard year-dependent monitoring
   - Premature and time-based cessation: More frequent monitoring
   - Administrative cessation (random_administrative): No monitoring visits scheduled, reflecting real-world administrative discontinuations (e.g., insurance changes) where patients are completely lost to follow-up

## Testing Strategy

1. **Unit Tests**: Test each component in isolation - PARTIALLY COMPLETED
   - Test different discontinuation types - COMPLETED
   - Test time-dependent recurrence calculation - COMPLETED
   - Test clinician decision modifications - COMPLETED

2. **Integration Tests**: Test components working together - PENDING
   - Test ABS with enhanced discontinuation
   - Test DES with enhanced discontinuation
   - Test clinician variation effects

3. **Validation Tests**: Verify against clinical data - PENDING
   - Compare recurrence rates to Artiaga study
   - Validate clinician behavior patterns
   - Test different risk factor scenarios

## Expected Outcomes

1. More realistic discontinuation patterns with multiple types - ACHIEVED
2. Time-dependent recurrence probabilities based on clinical data - ACHIEVED
3. Clinician variation effects on treatment decisions - ACHIEVED
4. Foundation for future economic analysis - PARTIALLY ACHIEVED
5. Enhanced reporting and statistics - ACHIEVED

## Next Steps

1. ✅ Implement no-monitoring option for random administrative cessation:
   - ✅ Modify `schedule_monitoring` method to return empty list for random_administrative cessation type
   - ✅ Update YAML configuration to explicitly indicate which cessation types receive monitoring
   - ✅ Add test cases to verify no monitoring visits are scheduled for administrative cessation
   - ✅ Update documentation to reflect this behavioral distinction
2. Finalize integration tests for ABS and DES implementations:
   - Create comprehensive test cases for ABS implementation with enhanced discontinuation
   - Create comprehensive test cases for DES implementation with enhanced discontinuation
   - Test different cessation types and their impact on patient trajectories
3. Validate the model against clinical data:
   - Compare recurrence rates to Artiaga study data
   - Validate clinician variation effects against published adherence rates
   - Test different risk factor scenarios and compare to literature
4. Complete documentation and parameter configurations:
   - Update all docstrings with numpy format
   - Create comprehensive parameter documentation
   - Add examples of different configuration scenarios
5. Prepare for future economic analysis:
   - Add cost tracking for different cessation types
   - Implement utility calculations for QALYs
   - Create reporting framework for economic outcomes
6. Consider adding more sophisticated clinician decision models for future extensions:
   - Implement learning behavior for clinicians
   - Add more nuanced decision factors
   - Create clinician profiles based on real-world data

## References

1. Aslanis et al. (2021): Prospective study of treatment discontinuation after treat-and-extend
2. Artiaga et al. (2023): Retrospective study of treatment discontinuation with long-term follow-up
3. Arendt et al.: Study of discontinuation after three 16-week intervals
4. ALTAIR Study (2020): Japanese treat-and-extend study with 2-week vs. 4-week adjustments
5. Comprehensive AMD Parameters document (meta/comprehensive-amd-parameters.md)
