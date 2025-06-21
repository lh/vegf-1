# Final Protocol Comparison Plan: T&E vs T&T for Aflibercept

## Objective

Create two directly comparable protocols that isolate the effect of treatment strategy:
1. **T&E (Treat-and-Extend)**: 8-week minimum interval, can extend to 16 weeks
2. **T&T (Treat-and-Treat)**: Fixed 8-week intervals indefinitely

Both protocols must:
- Use identical patient populations and disease models
- Produce identical outcomes for patients treated every 8 weeks
- Match real-world evidence as closely as possible
- Work with existing time-based simulation engines

## Design Principles

### 1. Identical Foundation
- **Same disease model**: Transition probabilities, vision changes
- **Same patient distribution**: Baseline vision, disease states
- **Same clinical improvements**: Response heterogeneity, loading phase benefits
- **Same discontinuation rules**: Vision thresholds, attrition rates

### 2. Protocol-Specific Differences
- **T&E**: Dynamic interval adjustment based on disease activity
- **T&T**: Fixed 8-week intervals regardless of disease activity

### 3. Outcome Equivalence
- If a T&E patient never extends (always needs 8 weeks), they must have identical outcomes to T&T
- This requires careful calibration of vision change parameters

## Implementation Strategy

### Phase 1: Create Base Protocol Configuration

```yaml
# Base configuration shared by both protocols
base_aflibercept_config:
  # Disease transitions calibrated to real-world evidence
  disease_transitions:
    NAIVE:
      STABLE: 0.45      # 45% achieve stability after loading
      ACTIVE: 0.45      # 45% remain active
      HIGHLY_ACTIVE: 0.10
    STABLE:
      STABLE: 0.88      # High retention when stable
      ACTIVE: 0.12      # Some recurrence
    ACTIVE:
      STABLE: 0.35      # Can improve with treatment
      ACTIVE: 0.55      # Many remain active
      HIGHLY_ACTIVE: 0.10
    HIGHLY_ACTIVE:
      STABLE: 0.10
      ACTIVE: 0.30
      HIGHLY_ACTIVE: 0.60

  # Vision changes calibrated to achieve target outcomes
  vision_change_model:
    stable_treated:
      mean: 1.5       # Positive gain when stable
      std: 1.5
    active_treated:
      mean: 0.5       # Small gain even when active
      std: 2.0
    highly_active_treated:
      mean: -0.5      # Minimal loss with treatment
      std: 2.0

  # Clinical improvements
  clinical_improvements:
    enabled: true
    use_loading_phase: true
    use_response_heterogeneity: true
    response_types:
      good:
        probability: 0.30
        multiplier: 1.8
      average:
        probability: 0.50
        multiplier: 1.0
      poor:
        probability: 0.20
        multiplier: 0.5
```

### Phase 2: Protocol-Specific Configurations

#### T&E Protocol (aflibercept_tae_8week_min.yaml)
```yaml
name: "Aflibercept T&E (8-week minimum)"
protocol_type: treat_and_extend
min_interval_days: 56    # 8 weeks minimum
max_interval_days: 112   # 16 weeks maximum
extension_days: 28       # 4-week extensions
shortening_days: 28      # 4-week reductions

# Inherit all base configurations
<<: *base_aflibercept_config
```

#### T&T Protocol (aflibercept_treat_and_treat.yaml)
```yaml
name: "Aflibercept Treat-and-Treat"
protocol_type: fixed_interval
min_interval_days: 56    # 8 weeks fixed
max_interval_days: 56    # No extension

loading_phase:
  enabled: true
  doses: 3
  interval_days: 28

# Inherit all base configurations
<<: *base_aflibercept_config
```

### Phase 3: Calibration Targets

Based on our literature review:

#### T&E Expected Outcomes (8-week minimum)
- **Year 1**: 5-6 letters gain, 7-8 injections
- **Year 2**: 4-5 letters total, 10-11 total injections
- **Extension success**: ~40% reach 12+ weeks
- **Persistent 8-week**: ~30-40% never extend

#### T&T Expected Outcomes (Fixed 8-week)
- **Year 1**: 7-8 letters gain, 7.5 injections
- **Year 2**: 5-6 letters total, 14 total injections
- **Stable disease**: Better control but more injections
- **Overtreatment**: ~40% could have extended

### Phase 4: Validation Strategy

1. **Individual Protocol Validation**
   - Run each protocol with n=1000 patients
   - Verify Year 1 and Year 2 outcomes match targets
   - Check injection frequencies align with evidence

2. **Equivalence Testing**
   - Identify T&E patients who never extend beyond 8 weeks
   - Compare their outcomes to matched T&T patients
   - Outcomes should be within 5% (allowing for random variation)

3. **Sensitivity Analysis**
   - Test with different baseline populations
   - Verify robustness across parameter ranges
   - Document confidence intervals

### Phase 5: Implementation Steps

1. **Create shared base configuration module**
   ```python
   # simulation_v2/protocols/base_configs.py
   AFLIBERCEPT_BASE_CONFIG = {
       'disease_transitions': {...},
       'vision_change_model': {...},
       'clinical_improvements': {...}
   }
   ```

2. **Implement protocol YAML files**
   - aflibercept_tae_8week_min.yaml
   - aflibercept_treat_and_treat.yaml

3. **Add validation tests**
   ```python
   # tests/test_protocol_equivalence.py
   def test_tae_tt_equivalence():
       """Verify patients treated q8w have same outcomes in both protocols."""
   ```

4. **Create comparison dashboard**
   - Side-by-side outcomes visualization
   - Injection frequency distributions
   - Cost-effectiveness analysis

## Success Criteria

### Must Have
- [ ] T&E achieves 5-6 letters Year 1 (real-world adjusted)
- [ ] T&T achieves 7-8 letters Year 1 (VIEW-comparable)
- [ ] Identical outcomes for non-extending patients
- [ ] Works with existing simulation engines
- [ ] Reproducible results (fixed random seeds)

### Should Have
- [ ] 30-40% of T&E patients at 8-week intervals
- [ ] 40% of T&E patients reach 12+ weeks
- [ ] Realistic discontinuation patterns
- [ ] Cost-effectiveness metrics

### Nice to Have
- [ ] Subgroup analysis capabilities
- [ ] Sensitivity to baseline characteristics
- [ ] Long-term (5-10 year) projections

## Risk Mitigation

### Risk 1: Parameter Coupling
**Issue**: Changing one parameter affects multiple outcomes
**Mitigation**: Use systematic calibration with clear priorities

### Risk 2: Overfitting to Specific Studies
**Issue**: Too closely matching one study, missing general patterns
**Mitigation**: Target ranges rather than point estimates

### Risk 3: Protocol Divergence
**Issue**: Protocols drift apart during calibration
**Mitigation**: Shared base configuration, regular equivalence checks

## Timeline

### Week 1
- Day 1-2: Finalize base configuration
- Day 3-4: Implement both protocols
- Day 5: Initial testing and debugging

### Week 2
- Day 1-2: Calibration iterations
- Day 3-4: Validation testing
- Day 5: Documentation and UI integration

## Deliverables

1. **Two protocol YAML files** (T&E and T&T)
2. **Shared configuration module**
3. **Validation test suite**
4. **Calibration report** with achieved vs target outcomes
5. **User documentation** for UI integration

## Next Actions

1. Commit and push current work
2. Merge to main
3. Create new branch: `feature/final-tae-tt-protocols`
4. Begin implementation with base configuration

---

*This plan represents our final push to create scientifically valid, directly comparable protocols that will enable meaningful treatment strategy comparisons in the UI.*