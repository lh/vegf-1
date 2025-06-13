# Eylea 8mg Integration Plan for V2 Economics System

## Overview
The private repository contains valuable Eylea 8mg clinical trial data that can enhance our economic modeling capabilities. This plan outlines how to integrate this data into our V2 economics system.

## Available Data Summary

### Clinical Parameters (from eylea_8mg_clinical_data_summary.md)
- **Formulation**: 114.3 mg/mL concentration (vs 40 mg/mL for 2mg)
- **Volume**: 0.07 mL injection (vs 0.05 mL for 2mg)
- **Loading phase**: 3 monthly doses
- **Maintenance intervals**: 12-16 weeks for most patients
- **Interval shortening**: ~20-23% of patients require shorter intervals
- **Real-world safety**: 3.7% IOI incidence per injection vs 1% in trials

### Dose Modification Criteria (from clinical_parameters_extracted.json)
- BCVA loss >5 letters from week 12 AND
- Either: >25 μm increase in CRT from week 12 OR new foveal hemorrhage
- For 8mg groups: Both BCVA AND anatomic criteria must be met (vs either for 2mg)

### Treatment Intervals (extracted data points)
- Various interval patterns: 12, 16, 48, 56 weeks observed
- Percentage distributions available for different intervals

## Integration Strategy

### Phase 1: Enhanced Protocol Configuration
1. **Create Eylea 8mg protocol specification**
   - Extend existing eylea.yaml with 8mg variant
   - Include dose modification rules
   - Model loading phase + maintenance intervals

2. **Update cost parameters**
   - Higher drug cost for 8mg formulation
   - Potential monitoring costs for IOI surveillance
   - Reduced visit frequency economics

### Phase 2: Clinical Model Enhancements
1. **Implement dose modification logic**
   - BCVA + anatomic criteria checking
   - Interval shortening rules (both criteria vs either)
   - Real-world vs trial IOI rates

2. **Enhanced safety modeling**
   - IOI incidence parameters (trial: 1%, real-world: 3.7%)
   - Cost of IOI management
   - Impact on treatment adherence

### Phase 3: Economic Analysis Extensions
1. **Comparative cost analysis**
   - 8mg vs 2mg formulations
   - Extended interval economics
   - Real-world safety cost impact

2. **Sensitivity analysis**
   - IOI rate variations (1% vs 3.7%)
   - Interval shortening rates (20-23%)
   - Drug pricing scenarios

## Implementation Priority

### High Priority
1. Create eylea_8mg.yaml protocol specification
2. Add 8mg cost parameters to economics system
3. Simple interval comparison (q12/q16 vs q8)

### Medium Priority
1. Implement dose modification criteria
2. Add IOI safety modeling
3. Create comparative analysis tools

### Low Priority
1. Advanced subgroup analysis
2. Real-world data integration workflows
3. Dynamic safety parameter adjustment

## Technical Implementation

### Protocol Configuration Structure
```yaml
# protocols/eylea_8mg.yaml
name: "Eylea 8mg Treat and Extend"
drug:
  name: "aflibercept_8mg"
  concentration: 114.3  # mg/mL
  volume: 0.07  # mL

phases:
  loading:
    duration: 3  # months
    interval: 4  # weeks
  
  maintenance:
    initial_interval: 12  # weeks
    max_interval: 16  # weeks
    interval_adjustment: 4  # weeks

dose_modification:
  criteria:
    vision_loss_threshold: 5  # letters
    anatomy_threshold: 25  # μm CRT increase
    require_both: true  # vs either for 2mg
  
  shortening_rate: 0.22  # 22% of patients

safety:
  ioi_rate_trial: 0.01
  ioi_rate_real_world: 0.037
  ioi_management_cost: 500  # placeholder
```

### Cost Configuration Extension
```yaml
# protocols/parameter_sets/eylea_8mg/standard.yaml
drug_costs:
  aflibercept_8mg:
    unit_cost: 2000  # Higher than 2mg - TBD based on real pricing
    administration_cost: 150
    
safety_costs:
  ioi_management: 500
  monitoring_enhanced: 50  # Additional monitoring post-injection
```

## Next Steps
1. Create basic eylea_8mg.yaml protocol
2. Add cost parameters for 8mg formulation
3. Run comparative simulation (8mg vs 2mg)
4. Analyze economic implications of extended intervals
5. Consider real-world safety cost impact

## Data Sources
- Clinical trial data: PHOTON and PULSAR trials
- Real-world safety: Post-marketing surveillance
- Treatment patterns: Extracted from clinical_parameters_extracted.json
- Economic parameters: To be determined from cost data in private repo