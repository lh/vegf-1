# Cost Tracking: NHS Model Comparison

## Overview
This document compares our proposed cost tracking implementation with the NHS AMD Commissioning Guidance (May 2024) and wAMD cost calculator approaches.

## 1. Treatment Protocol Alignment

### Our Model vs NHS Guidance

| Aspect | Our Model | NHS Guidance | Alignment |
|--------|-----------|--------------|-----------|
| **Loading Phase** | 3 monthly injections | "Based on SPC of each anti-VEGF agent" | ✓ Aligned |
| **T&E Extensions** | 2-4 week increments | "Extend by 2-4 weeks" | ✓ Aligned |
| **Maximum Intervals** | 16 weeks (standard) | "12-16 weeks based on drug" | ✓ Aligned |
| **Stable Disease** | Not explicitly modeled | "2-3 visits at max extension" | ⚠️ To implement |
| **Reactivation Rate** | In disease transitions | "25-30% within 12 months" | ✓ Conceptually aligned |

### Drug-Specific Intervals (from Cost Calculator)

| Drug | Our Model | NHS Cost Calculator | Variance |
|------|-----------|-------------------|----------|
| **Ranibizumab** | Not yet implemented | 2-week extensions, 12-week max | - |
| **Aflibercept 2mg** | 4-week extensions, 16-week max | 4-week extensions, 16-week max | ✓ Exact match |
| **Faricimab** | Not yet implemented | 4-week extensions, 16-week max | - |
| **Aflibercept 8mg** | Not yet implemented | 4-week extensions, 20-week max | - |

## 2. Visit Type Classification

### Our Model
```
T&E Protocol:
- Every visit = Full assessment (OCT + decision + injection)
- Cost: £220-370 per visit

T&T Protocol:
- Injection visits = Nurse-led (injection only)
- Assessment visits = Quarterly full review
- Cost: £160 (injection) vs £370 (full)
```

### NHS Guidance Implications
- **OCT at every visit**: "OCT is only sensitive tool for assessing reactivation"
- **Virtual monitoring**: "Virtual monitoring increasing for stable patients"
- **Nurse-led services**: Implied for stable patients on fixed regimens

**Alignment**: Our T&E/T&T distinction matches NHS practice patterns

## 3. Cost Assumptions Comparison

### Drug Costs
| Component | Our Default | NHS Calculator Range | Notes |
|-----------|-------------|---------------------|-------|
| Eylea 2mg | £800 | £979.20 (originator) / £354.78 (biosimilar) | Our slider covers this range |

### Visit Components
| Component | Our Model | NHS Typical | Source |
|-----------|-----------|-------------|---------|
| Injection admin | £150 | £134 | HRG BZ86B |
| OCT scan | £75 | £110 | HRG BZ88A |
| Clinical review | £120 | £152 (first) / £69 (follow-up) | Consultant-led service |
| VA test | £25 | Included in review | Local variation |

**Key Difference**: Our costs are slightly conservative but within reasonable range

## 4. Workload Metrics

### Our Model
- **Injection workload**: Each injection counted
- **Decision-maker workload**: Full assessments only
- **Peak tracking**: Monthly aggregation

### NHS Commissioning Guidance
- Emphasizes "patient and caregiver burden"
- Notes biosimilars "require more frequent monitoring and injections"
- Highlights capacity constraints driving virtual clinic adoption

**Enhancement Needed**: Add caregiver burden metrics (travel, time off work)

## 5. Expected Outcomes Comparison

### Injection Frequencies (Year 1)

| Protocol | Our Model | NHS Calculator | Clinical Trials |
|----------|-----------|----------------|-----------------|
| T&E (Aflibercept) | 7-8 injections | 6 injections | 7-8 (VIEW) |
| Fixed q8w | 7.5 injections | 7.5 injections | 7.5 (exact) |

### Visual Outcomes

| Metric | Our Target | NHS Guidance | Clinical Trials |
|--------|------------|--------------|-----------------|
| Year 1 VA gain | 5-7 letters | "Generally 5-7 letter gains" | 7-10 letters |
| Maintaining vision | 80%+ | Not specified | ~95% |

## 6. Key Differences and Gaps

### 1. Biosimilar Modeling
**Gap**: We don't yet model different efficacy for biosimilars
- NHS: "drying effect is not as effective as aflibercept"
- Impact: More frequent visits, higher total cost despite lower drug price

### 2. Stable Disease Management
**Gap**: We don't explicitly model stable disease criteria
- NHS: Can extend to "monitor and extend" after 2-3 stable visits
- Impact: Potential overestimation of long-term visit frequency

### 3. Virtual Clinic Integration
**Enhancement**: Add virtual vs face-to-face visit options
- Cost difference: £50 (virtual) vs £120 (F2F)
- Applicable to: Stable patients, monitoring visits

### 4. Multi-Drug Support
**Future**: Extend beyond Aflibercept
- Ranibizumab: More frequent, lower drug cost
- Faricimab: Potentially fewer injections, higher drug cost
- Impact: Different cost-effectiveness profiles

## 7. Recommendations for Alignment

### Immediate Adjustments
1. **Adjust base costs** to match NHS HRG codes more closely
2. **Add stable disease tracking** to enable monitor-and-extend
3. **Include virtual clinic option** for appropriate visits

### Phase 2 Enhancements
1. **Biosimilar efficacy modeling** with adjusted transition rates
2. **Multi-drug support** with switching logic
3. **Caregiver burden metrics** (indirect costs)

### Validation Approach
1. Compare total costs with NHS calculator outputs
2. Verify injection frequencies match real-world data
3. Validate workload estimates with clinical teams

## 8. Cost-Effectiveness Targets

### NHS Benchmarks (from literature)
- Cost per QALY: £20,000-30,000 threshold
- Cost per patient year 1: £5,000-8,000 (biosimilar pathway)
- Cost per vision year saved: Not explicitly stated

### Our Model Targets
- Cost per patient: £8,750 (T&E) / £10,200 (T&T)
- Cost per vision year: £14,800-15,200
- Within NICE threshold: Yes, assuming 0.1 QALY/vision year

## 9. Summary

### Strengths of Our Approach
1. **Flexible cost configuration** matches NHS need for local adaptation
2. **Workload tracking** addresses key NHS capacity concern
3. **Protocol comparison** enables evidence-based commissioning
4. **Real-time calculation** supports service planning

### Areas for Improvement
1. **Biosimilar modeling** to reflect real-world effectiveness
2. **Stable disease criteria** for more accurate long-term costs
3. **Virtual clinic integration** to model modern pathways
4. **Indirect costs** for comprehensive economic evaluation

### Overall Assessment
Our cost tracking design is well-aligned with NHS guidance and addresses key commissioning questions. The flexible architecture allows for iterative improvements as we validate against real-world data.