# Cost Tracking: NHS Calculator Specific Alignment

## Executive Summary
Our cost model needs adjustment to better align with NHS cost calculator values. Key finding: **Our default Eylea cost of £800 is reasonable as a midpoint between biosimilar (£355) and originator (£979)**.

## 1. Cost Component Comparison

### Drug Costs
| Drug | Our Model | NHS Calculator | Action Needed |
|------|-----------|----------------|---------------|
| **Eylea 2mg** | £800 (adjustable) | £979.20 (orig) / £354.78 (bio) | ✓ Good default |
| **Eylea 8mg** | Not implemented | £1,197.60 | Add in Phase 2 |
| **Lucentis** | Not implemented | £613.20 / £628.14 | Add in Phase 2 |
| **Faricimab** | Not implemented | £1,028.40 | Add in Phase 2 |

**Key Insight**: Biosimilar Eylea (£355) is 64% cheaper than originator - massive impact on cost-effectiveness

### Procedure Costs
| Component | Our Model | NHS Calculator | Adjustment |
|-----------|-----------|----------------|------------|
| **Injection** | £150 | £134 | Reduce by £16 |
| **OCT Scan** | £75 | £110 | Increase by £35 |
| **Consultation (first)** | £120 | £152-168 | Increase to £160 |
| **Consultation (follow-up)** | £120 | £69-81 | Add two-tier pricing |

**Total Visit Cost Impact**:
- Our T&E visit: £370 → Should be £404 (injection + OCT + consultation)
- Our injection-only: £160 → Should be £134 (aligned)

## 2. Expected Treatment Patterns

### Year 1 Injection Counts
| Protocol | Our Target | NHS Calculator | Variance |
|----------|------------|----------------|----------|
| **Aflibercept T&E** | 7-8 | 6 | Slightly high |
| **Aflibercept T&T** | 7.5 | 7.5 | ✓ Exact match |

### Total Year 1 Costs (from NHS Calculator)
| Pathway | Drug + Procedures | Our Estimate | Variance |
|---------|------------------|--------------|----------|
| **Aflibercept biosimilar** | £2,400 | ~£3,200 | 33% high |
| **Aflibercept originator** | £6,600 | ~£7,800 | 18% high |

## 3. Critical Adjustments Needed

### Immediate Changes
1. **Update procedure costs** to match HRG codes:
   ```yaml
   component_costs:
     injection_administration: 134  # was 150
     oct_scan: 110                  # was 75
     consultant_first: 160          # was 120
     consultant_follow_up: 75       # was 120
   ```

2. **Add biosimilar option** to drug slider:
   ```python
   drug_cost_option = st.radio(
       "Eylea type",
       ["Biosimilar (£355)", "Originator (£979)", "Custom"]
   )
   ```

3. **Adjust injection frequency** for T&E:
   - Target 6 injections Year 1 (not 7-8)
   - Achievable with faster extension after loading

### Phase 2 Additions
1. **Multi-drug support** with correct costs
2. **Switching logic** with reloading requirements
3. **Two-tier consultation** pricing

## 4. Workload Implications

### From NHS Calculator Assumptions
- **VA assessments**: Only at loading (first/last) and with T&E injections
- **Annual consultation**: Additional visit beyond regular schedule
- **Monitoring without injection**: Rare in Year 1, more common Year 2+

### Our Model Adjustments
- T&E: Every visit has full assessment ✓ (matches)
- T&T: Quarterly assessments → Should be annual + loading
- Add "VA assessment only" visits for stable patients

## 5. Cost per Injection Episode

### NHS Calculator Ranges
| Drug + Procedure + Scan | Cost |
|------------------------|------|
| **Aflibercept biosimilar** | £599 |
| **Aflibercept originator** | £1,223 |
| **Aflibercept 8mg** | £1,442 |

### Our Model (after adjustment)
| Scenario | Cost |
|----------|------|
| **T&E visit (biosimilar)** | £599 ✓ |
| **T&E visit (£800 drug)** | £1,044 |
| **Injection-only** | £489-934 |

## 6. Key Economic Insights

### Extension Benefits (from NHS)
- Each avoided injection saves £244-1,332
- Our model should emphasize this in outputs

### Biosimilar Impact
- 64% drug cost reduction
- Changes Year 1 cost from £6,600 to £2,400
- Should be default assumption for NHS planning

### Real-World vs Trial
- NHS expects 6 injections Year 1 (not 7-8 trial frequency)
- Stable patients achieve 3 injections/year by Year 2
- 20-30% need interval shortening annually

## 7. Validation Metrics

### Cost Targets (per patient)
| Metric | Year 1 | Year 2 | Total 5-year |
|--------|--------|--------|--------------|
| **Biosimilar pathway** | £2,400 | £1,200 | £7,000 |
| **Originator pathway** | £6,600 | £3,300 | £20,000 |
| **Our model (£800)** | £5,000 | £2,500 | £15,000 |

### Workload Targets (300 patients)
| Month | Injections | Assessments |
|-------|------------|-------------|
| Month 1-3 | 600-700 | 600-700 |
| Month 12 | 150-200 | 150-200 |
| Month 24 | 75-100 | 25-50 |

## 8. Implementation Priority

### Must Have (Phase 1)
1. Correct procedure costs to HRG values
2. Add biosimilar/originator toggle
3. Reduce T&E Year 1 injections to 6
4. Show cost per avoided injection

### Should Have (Phase 2)
1. Multi-drug support
2. Two-tier consultation pricing
3. Annual review visits
4. Stable disease tracking

### Nice to Have (Phase 3)
1. Switching pathways
2. Virtual clinic modeling
3. Capacity planning tools
4. QALY calculations

## 9. Summary Recommendations

1. **Adjust base costs** to match NHS HRG exactly
2. **Default to biosimilar** pricing (£355) with option for originator
3. **Target 6 injections** Year 1 for T&E validation
4. **Emphasize extension benefits** in economic outputs
5. **Add workload validation** against NHS calculator expectations

With these adjustments, our model will closely match NHS cost calculator while providing additional insights on workload and protocol comparison.