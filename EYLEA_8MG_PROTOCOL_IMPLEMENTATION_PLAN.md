# Eylea 8mg Protocol YAML Implementation Plan

## Executive Summary

This plan outlines the creation of a comprehensive Eylea 8mg protocol YAML file that meets V2 simulation requirements while capturing all necessary data for economic analysis. The protocol will integrate clinical trial data from the private repository with NHS cost data to enable accurate simulation of both clinical outcomes and economic impacts.

## 1. Protocol Structure Requirements

### 1.1 V2 Compliance Requirements
- **No defaults allowed**: Every parameter must be explicitly defined
- **Complete specification**: All disease states, transitions, and outcomes
- **Audit trail**: Version control, timestamps, and checksums
- **Validation**: All probabilities must sum correctly, all states defined

### 1.2 Clinical Simulation Requirements
- **Treatment phases**: Loading and maintenance with precise timing
- **Dose modification**: Criteria for interval adjustments
- **Disease progression**: State transitions based on treatment response
- **Vision outcomes**: Realistic modeling of visual acuity changes
- **Safety events**: IOI incidence and management

### 1.3 Economic Data Capture Requirements
- **Visit composition**: What procedures occur at each visit type
- **Resource utilization**: Staff time, equipment use, consumables
- **Drug administration**: Preparation, injection, monitoring
- **Safety management**: IOI treatment pathways and costs
- **Discontinuation tracking**: Reasons and economic implications

## 2. Data Integration Strategy

### 2.1 Clinical Data Sources
From `eylea_high_dose_data/`:
- **Treatment protocols**: Loading phase (3 monthly), maintenance (q12/q16)
- **Interval maintenance**: 79% q12, 77% q16 success rates
- **Extension criteria**: 71% eligible for extension in year 2
- **Visual outcomes**: Mean BCVA gains of 6.2-6.7 letters
- **Safety profile**: 1% trial IOI, 3.7% real-world IOI

### 2.2 Economic Data Sources
From `compass_artifact`:
- **NHS drug costs**: £1,750 per 8mg injection
- **Visit costs**: £497 per injection visit (excluding drug)
- **Staff costs**: £82/hour consultant, £26/hour nurse
- **Safety costs**: £500 IOI management
- **Monitoring costs**: £126 per OCT scan

### 2.3 Protocol-Economic Linkage
Key integration points:
- **Visit types** → Cost components
- **Disease states** → Monitoring frequency
- **Treatment intervals** → Annual costs
- **Safety events** → Additional resource use
- **Discontinuation** → Cost implications

## 3. Protocol YAML Structure

### 3.1 Core V2 Fields
```yaml
# Metadata (required for V2)
name: "Eylea 8mg Treat and Extend"
version: "1.0.0"
created_date: "2024-01-XX"
author: "Clinical Economics Team"
description: "High-dose aflibercept with extended intervals based on PULSAR/PHOTON"

# Protocol type and intervals (days)
protocol_type: "treat_and_extend"
min_interval_days: 56    # 8 weeks
max_interval_days: 168   # 24 weeks (year 2)
extension_days: 28       # 4 weeks
shortening_days: 28      # 4 weeks
```

### 3.2 Disease Model Integration
```yaml
# Disease state transitions (probabilities must sum to 1.0)
disease_transitions:
  NAIVE:
    NAIVE: 0.0
    STABLE: 0.4      # 40% respond well to loading
    ACTIVE: 0.5      # 50% have active disease
    HIGHLY_ACTIVE: 0.1
    
  STABLE:
    NAIVE: 0.0
    STABLE: 0.79     # 79% maintain stability (q12 data)
    ACTIVE: 0.20     # 20% reactivate
    HIGHLY_ACTIVE: 0.01
    
  # Similar for ACTIVE and HIGHLY_ACTIVE states

# Vision change model (letters per interval)
vision_change_model:
  naive_treated:
    mean: 2.2        # Initial gain during loading
    std: 3.0
  stable_treated:
    mean: 0.1        # Maintenance of gains
    std: 1.5
  # Complete for all state/treatment combinations
```

### 3.3 Economic Data Capture Extensions
```yaml
# Economic integration points
economic_capture:
  visit_types:
    loading_injection:
      procedures: ["injection", "oct_scan", "va_test"]
      duration_minutes: 60
      staff_required: ["consultant", "nurse"]
      
    maintenance_injection:
      procedures: ["injection", "oct_scan", "va_test"]
      duration_minutes: 45
      staff_required: ["consultant", "nurse"]
      
    monitoring_only:
      procedures: ["oct_scan", "va_test"]
      duration_minutes: 30
      staff_required: ["nurse"]
      
  # Resource tracking
  resource_utilization:
    drug_preparation_time: 15
    injection_time: 10
    monitoring_time: 20
    
  # Safety event pathways
  adverse_event_management:
    ioi_mild:
      visits_required: 2
      procedures: ["examination", "topical_treatment"]
      resolution_days: 14
```

### 3.4 Clinical Trial Parameters
```yaml
# PULSAR/PHOTON specific parameters
clinical_trial_data:
  loading_phase:
    injections: 3
    interval_weeks: 4
    
  maintenance_outcomes:
    q12_maintenance_rate: 0.79
    q16_maintenance_rate: 0.77
    
  year2_extension:
    eligible_for_extension: 0.71
    achieve_20_weeks: 0.47
    achieve_24_weeks: 0.28
    
  visual_outcomes:
    mean_bcva_gain_48wk: 6.7
    std_bcva_gain: 12.6
```

### 3.5 Dose Modification Rules
```yaml
# Stricter criteria for 8mg vs 2mg
dose_modification:
  assessment_weeks: [16, 20, 24, 28, 32, 36, 40, 44, 48]
  
  criteria:
    visual_loss:
      threshold: 5        # letters from week 12
      comparison: "week_12"
      
    anatomic_change:
      crt_increase: 25    # micrometers
      new_hemorrhage: true
      
    requirement: "BOTH"   # Both visual AND anatomic
    
  action_rules:
    stable: "maintain_or_extend"
    active: "shorten_by_4_weeks"
    highly_active: "shorten_to_minimum"
```

### 3.6 Discontinuation Framework
```yaml
discontinuation_rules:
  planned:
    stable_24_weeks:
      threshold: 2         # consecutive stable assessments
      action: "discharge"
      
  administrative:
    missed_appointments:
      threshold: 3
      action: "discharge_non_compliant"
      
  clinical:
    vision_loss_severe:
      threshold: 30        # letters lost
      action: "switch_therapy"
      
    no_response:
      assessment_visits: 6
      improvement_threshold: 5
      action: "discontinue"
```

## 4. Implementation Steps

### Phase 1: Core Protocol Development (Days 1-2)
1. Create base YAML structure with V2 required fields
2. Implement disease transition matrices from clinical data
3. Define vision change models based on PULSAR outcomes
4. Add dose modification criteria (stricter for 8mg)

### Phase 2: Economic Integration (Days 3-4)
1. Define visit type compositions for cost calculation
2. Map procedures to NHS cost components
3. Create resource utilization tracking
4. Implement safety event cost pathways

### Phase 3: Validation and Testing (Day 5)
1. Validate against V2 ProtocolSpecification requirements
2. Test probability sums and state completeness
3. Verify economic data capture points
4. Run test simulations with cost analysis

## 5. Key Design Decisions

### 5.1 Interval Modeling
- Use **week-based intervals** internally, convert to days for V2
- Model both q12 and q16 paths with stochastic selection
- Allow year 2 extensions based on trial data

### 5.2 Economic Granularity
- Track **individual procedures** not just visit types
- Separate drug costs from administration costs
- Enable time-based resource costing

### 5.3 Safety Integration
- Model IOI as both clinical event and cost driver
- Use real-world rates (3.7%) for base case
- Include management pathways and resolution

### 5.4 Discontinuation Tracking
- Capture reason codes for economic analysis
- Model impact on future costs
- Track switching vs stopping

## 6. Expected Outputs

### 6.1 Clinical Metrics
- Visual acuity trajectories
- Treatment interval distributions
- Time to discontinuation
- Safety event rates

### 6.2 Economic Metrics
- Total treatment costs by component
- Cost per vision year saved
- Budget impact projections
- Resource utilization reports

### 6.3 Combined Analyses
- Cost-effectiveness ratios
- Interval achievement vs costs
- Safety cost impacts
- Discontinuation economic effects

## 7. Next Steps

1. **Review and approve** this implementation plan
2. **Create draft protocol YAML** with core V2 fields
3. **Integrate clinical parameters** from private repository
4. **Add economic capture points** for comprehensive costing
5. **Validate and test** with sample simulations
6. **Document** usage for clinical and economic teams

## 8. Success Criteria

- ✓ Meets all V2 protocol requirements (no defaults, complete specification)
- ✓ Accurately represents PULSAR/PHOTON clinical data
- ✓ Captures all NHS cost components from compass_artifact
- ✓ Enables integrated clinical-economic simulation
- ✓ Produces NICE-compatible economic outputs
- ✓ Maintains scientific rigor and reproducibility

---

*This plan integrates clinical trial data from the private Eylea_high_dose repository with NHS economic data to create a comprehensive simulation protocol for both clinical outcomes and economic evaluation.*