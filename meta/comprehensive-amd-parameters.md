# Comprehensive AMD Simulation Parameters
## Integrated Analysis from Multiple Studies

This document provides a consolidated set of parameters derived from multiple studies of aflibercept 2mg in neovascular AMD, with particular focus on:

1. **ALTAIR Study** (2020): Japanese treat-and-extend study with 2-week vs. 4-week adjustments, 96-week data
2. **VIEW 1/2 Studies** (2012): Pivotal Phase 3 fixed dosing studies comparing aflibercept regimens to ranibizumab, 52-week data with 96-week extension
3. **Mylight Study** (2024): Fixed dosing study comparing biosimilar to reference aflibercept, 52-week data
4. **Maruko et al. Study** (2020): Prospective study of treat-and-extend aflibercept with 1-month adjustments, 2-year data
5. **Aslanis et al. Study** (2021): Prospective study of treatment discontinuation after treat-and-extend, 12-month follow-up
6. **Artiaga et al. Study** (2023): Retrospective study of treatment discontinuation with long-term follow-up (5 years)

## Disease State Definitions

For simulation purposes, disease states are defined as:
- **NAIVE**: Patients before first injection
- **STABLE**: Patients with interval extension or maintaining the maximum interval
- **ACTIVE**: Patients maintaining their current interval (except those at the maximum interval)
- **HIGHLY_ACTIVE**: Patients requiring treatment interval reduction

## 1. Visual Acuity Parameters

### Treatment Response by Disease State

| Disease State | Mean Letter Change | Standard Deviation | Confidence | Primary Source |
|---------------|-------------------|-------------------|------------|--------|
| NAIVE         | +8.4              | 1.2-1.4           | High       | ALTAIR, VIEW 1/2, Mylight |
| STABLE        | +1.0 to +2.0      | 0.5-1.0           | Medium     | ALTAIR |
| ACTIVE        | +0.5 to +1.0      | 0.5-1.0           | Medium     | ALTAIR |
| HIGHLY_ACTIVE | -0.5 to +1.0      | 1.0-1.5           | Medium     | ALTAIR |

### Vision Change Without Treatment
*Note: Estimated from disease course and indirect evidence*

| Disease State | Estimated Letter Change | Confidence | Source |
|---------------|------------------------|------------|--------|
| NAIVE         | -2.0 to -3.0          | Medium     | Consensus from literature |
| STABLE        | -0.5 to -1.0          | Medium     | ALTAIR |
| ACTIVE        | -1.0 to -2.0          | Medium     | ALTAIR |
| HIGHLY_ACTIVE | -3.0 to -5.0          | Medium     | ALTAIR |

### Long-term Vision Trajectory

| Time Period | Mean Letter Change | Confidence | Source |
|-------------|-------------------|------------|--------|
| Year 1 (0-52 weeks) | +8.4 to +9.0 | High       | All three primary studies |
| Year 2 (52-96 weeks) | -1.4 to -2.3 | High       | ALTAIR, VIEW 1/2 extension |
| Overall (0-96 weeks) | +6.1 to +7.6 | High       | ALTAIR, VIEW 1/2 extension |

### Vision Changes After Treatment Discontinuation

| Parameter | Value | Confidence | Source |
|-----------|-------|------------|--------|
| Vision loss at recurrence | -3.6 letters | Medium | Aslanis et al. |
| Proportion losing ≥2 lines at recurrence | 16.7% | Medium | Aslanis et al. |
| Vision recovery after retreatment | Near complete (-0.3 letters from baseline) | Medium | Aslanis et al. |
| Permanent vision loss (≥2 lines) | 11.1% | Medium | Aslanis et al. |

## 2. Disease State Transition Probabilities

### From NAIVE State (after loading phase)

| Target State | Transition Probability | Confidence | Source |
|--------------|------------------------|------------|--------|
| STABLE       | 0.55-0.60             | High       | ALTAIR, supported by VIEW 1/2 & Mylight |
| ACTIVE       | 0.30-0.35             | Medium     | ALTAIR, supported by VIEW 1/2 |
| HIGHLY_ACTIVE | 0.05-0.10            | Medium     | ALTAIR |

### From STABLE State (per decision interval)

| Target State | Transition Probability | Confidence | Source |
|--------------|------------------------|------------|--------|
| STABLE       | 0.80-0.85             | Medium     | ALTAIR |
| ACTIVE       | 0.10-0.15             | Medium     | ALTAIR |
| HIGHLY_ACTIVE | 0.05-0.10            | Medium     | ALTAIR |

### From ACTIVE State (per decision interval)

| Target State | Transition Probability | Confidence | Source |
|--------------|------------------------|------------|--------|
| STABLE       | 0.30-0.35             | Medium     | ALTAIR |
| ACTIVE       | 0.55-0.60             | Medium     | ALTAIR |
| HIGHLY_ACTIVE | 0.10-0.15            | Medium     | ALTAIR |

### From HIGHLY_ACTIVE State (per decision interval)

| Target State | Transition Probability | Confidence | Source |
|--------------|------------------------|------------|--------|
| STABLE       | 0.05-0.10             | Low        | ALTAIR (estimated) |
| ACTIVE       | 0.30-0.40             | Low        | ALTAIR (estimated) |
| HIGHLY_ACTIVE | 0.50-0.65            | Low        | ALTAIR (estimated) |

### Persistent States

| Disease State | Probability of Persistence | Confidence | Source |
|---------------|---------------------------|------------|--------|
| Persistently ACTIVE | 0.22-0.28           | High       | ALTAIR, supported by VIEW 1/2 |
| Persistently STABLE | 0.41-0.46           | High       | ALTAIR (at 16-week interval through week 96) |

### Transition After Treatment Discontinuation

| Transition | Probability | Timeframe | Confidence | Source |
|------------|------------|-----------|------------|--------|
| STABLE→ACTIVE | 13-53% | 12 months | High | Aslanis et al., Artiaga et al. |
| STABLE→ACTIVE | 32.2% | Over 5 years | High | Artiaga et al. |
| Time-dependent recurrence | 20.7%, 73.9%, 88.0% | 1, 3, 5 years respectively | High | Artiaga et al. |
| Mean time to recurrence | 29.4 ± 22.4 months | - | High | Artiaga et al. |

## 3. Treatment Protocol Parameters

### Treat-and-Extend Regimen

| Parameter | Value | Confidence | Source |
|-----------|-------|------------|--------|
| Loading phase injections | 3 | High | All studies |
| Initial interval | 8 weeks | High | All studies |
| Minimum interval | 8 weeks | High | ALTAIR |
| Maximum interval | 16 weeks | High | ALTAIR |
| Extension increment | 2 or 4 weeks | High | ALTAIR |
| Reduction increment | 2 or 4 weeks | High | ALTAIR |

### Treatment Intervals at Key Time Points

| Time Point | Mean Interval (weeks) | % with ≥12 week interval | % at 16 week interval | Confidence | Source |
|------------|----------------------|--------------------------|----------------------|------------|--------|
| Week 52    | 10.7-11.8            | 42.3-49.6%              | 0.0-40.7%            | High       | ALTAIR |
| Week 96    | 12.2-12.5            | 56.9-60.2%              | 41.5-46.3%           | High       | ALTAIR |

### Treatment Burden

| Dosing Strategy | Year 1 | Year 2 | Total (2 years) | Confidence | Source |
|-----------------|--------|--------|----------------|------------|--------|
| Fixed q8w       | 7.5    | 3.7    | 11.2           | High       | VIEW 1/2 |
| Treat-and-extend | 6.9-7.2 | 3.6-3.7 | 10.4          | High       | ALTAIR |
| Treat-and-extend (1-month) | - | - | 13.0 ± 3.9 | High | Maruko et al. |

### Treatment Discontinuation Criteria and Outcomes

| Discontinuation Protocol | Recurrence Rate | Follow-up | Confidence | Source |
|-------------------------|-----------------|-----------|------------|--------|
| After three 12-week intervals | 52.9% | 12 months | High | Aslanis et al. |
| After three 12-week intervals + 6 months | 32.2% | 60 months | High | Artiaga et al. |
| After three 16-week intervals | 13% | 40.5 weeks | Medium | Arendt et al. (via Artiaga) |
| With PED at baseline | 74% | 12 months | Medium | Aslanis et al. |
| Without PED at baseline | 48% | 12 months | Medium | Aslanis et al. |

## 4. Time-Dependent Parameters

### Duration of Effect

| Parameter | Value | Confidence | Source |
|-----------|-------|------------|--------|
| Maximum extension interval | 16 weeks | High | ALTAIR |
| Proportion achieving maximum interval | 43.1-54.5% | High | ALTAIR |
| Proportion maintaining maximum interval | 41.5-46.3% | High | ALTAIR |
| Time factor (max weeks) | 12-16 weeks | High | ALTAIR, pharmacokinetic studies |

### Time to Disease State Transitions

| Transition | Timeframe | Confidence | Source |
|------------|-----------|------------|--------|
| NAIVE to STABLE | 16 weeks | High | ALTAIR |
| Additional transitions to STABLE | By week 52 | Medium | ALTAIR, VIEW 1/2 |
| Late transitions to STABLE | Weeks 52-96 | Medium | ALTAIR, VIEW 1/2 extension |

## 5. Anatomic Parameters

### Fluid Resolution by Time Point

| Time Point | Patients without Fluid | Confidence | Source |
|------------|------------------------|------------|--------|
| Week 16    | 53.7-62.6%             | High       | ALTAIR |
| Week 52    | 63.4-71.9%             | High       | VIEW 1/2, ALTAIR, Mylight |
| Week 96    | 67.5%                  | High       | ALTAIR |
| 2 years (Maruko) | 72.2% | High | Maruko et al. |

### CRT Changes

| Time Point | Mean CRT Change (μm) | Confidence | Source |
|------------|----------------------|------------|--------|
| Week 52    | -126 to -140         | High       | ALTAIR, VIEW 1/2, Mylight |
| Week 96    | -125 to -130         | High       | ALTAIR |
| 2 years (Maruko) | -105 | High | Maruko et al. |

### CRT Changes with Treatment Discontinuation

| Time Point | CRT Change | Confidence | Source |
|------------|------------|------------|--------|
| At recurrence | +43 μm | Medium | Aslanis et al. |
| After resumed treatment | Normalized (-3 μm from baseline) | Medium | Aslanis et al. |

## 6. Age and Baseline Vision Dependence

### Age-Related Response Differences

| Age Group | Response Modifier | Confidence | Source |
|-----------|-------------------|------------|--------|
| <65 years | 1.1-1.2× better response | Low | Subgroup analyses from literature |
| 65-75 years | 1.0× (reference) | - | All studies |
| 75-85 years | 0.9× response | Low | Subgroup analyses from literature |
| >85 years | 0.7-0.8× response | Low | Subgroup analyses from literature |

### Baseline Vision Impact

| Baseline BCVA | Response Modifier | Confidence | Source |
|---------------|-------------------|------------|--------|
| <40 letters | 1.2-1.5× letter gain | Low | Subgroup analyses from literature |
| 40-60 letters | 1.0× (reference) | - | All studies |
| 60-70 letters | 0.7-0.8× letter gain | Low | Subgroup analyses from literature |
| >70 letters | 0.4-0.6× letter gain (ceiling effect) | Low | Subgroup analyses from literature |

## 7. Monitoring Parameters for Treatment Discontinuation

### Recurrence Detection Methods

| Detection Method | Sensitivity/Performance | Confidence | Source |
|------------------|------------------------|------------|--------|
| Scheduled monitoring | 87% of recurrences | High | Artiaga et al. |
| Patient-initiated visits | 13% of recurrences | High | Artiaga et al. |
| OCT sensitivity | Not directly measured | - | Assumed high based on studies |

### Symptomatology of Recurrence

| Parameter | Value | Confidence | Source |
|-----------|-------|------------|--------|
| Symptomatic recurrence | 60.9% | Medium | Artiaga et al. |
| Asymptomatic recurrence | 39.1% | Medium | Artiaga et al. |
| Blurring of vision | 44.6% of recurrences | Medium | Artiaga et al. |
| Metamorphopsia | 12.0% of recurrences | Medium | Artiaga et al. |
| Scotoma | 4.4% of recurrences | Medium | Artiaga et al. |

### Optimal Monitoring Schedule

| Phase | Recommended Interval | Confidence | Evidence |
|-------|----------------------|------------|----------|
| First year | Every 1-3 months | High | Aslanis et al., Artiaga et al. |
| Years 2-3 | Every 3-4 months | Medium | Artiaga et al. |
| Years 4-5 | Every 6 months | Low | Extrapolated from Artiaga et al. |

## 8. Aflibercept 2mg Pharmacokinetic/Pharmacodynamic Parameters

| Parameter | Value | Confidence | Source |
|-----------|-------|------------|--------|
| Systemic concentrations 24h post-dose | ~32-33 ng/mL | High | Mylight |
| Maximum plasma concentration | 0.02 μg/mL | High | VIEW 1/2 |
| Time to maximum concentration | 1-3 days | High | VIEW 1/2 |
| Plasma elimination time | <14 days | High | VIEW 1/2 |
| VEGF-binding threshold | ~2.91 μg/mL | Medium | Mylight |
| Vitreous half-life | ~9 days | Medium | Literature |
| Time factor (max weeks) | 16 weeks | High | ALTAIR |

## 9. Recommended Comprehensive Parameter Sets

### Core Parameter Set for Treatment Phase

| Parameter | Recommended Value | Confidence | Primary Source |
|-----------|-------------------|------------|----------------|
| **Visual Acuity Parameters** |  |  |  |
| NAIVE treatment response | +8.4 letters (SD 1.3) | High | Multiple studies |
| STABLE treatment response | +1.5 letters (SD 0.7) | Medium | ALTAIR |
| ACTIVE treatment response | +0.8 letters (SD 0.7) | Medium | ALTAIR |
| HIGHLY_ACTIVE treatment response | +0.3 letters (SD 1.2) | Medium | ALTAIR |
| **Transition Probabilities** |  |  |  |
| NAIVE to STABLE | 0.58 | High | ALTAIR |
| NAIVE to ACTIVE | 0.32 | Medium | ALTAIR |
| NAIVE to HIGHLY_ACTIVE | 0.10 | Medium | ALTAIR |
| STABLE persistence | 0.83 | Medium | ALTAIR |
| ACTIVE persistence | 0.57 | Medium | ALTAIR |
| HIGHLY_ACTIVE persistence | 0.58 | Low | ALTAIR (estimated) |
| **Treatment Protocol** |  |  |  |
| Loading injections | 3 | High | All studies |
| Initial interval | 8 weeks | High | All studies |
| Maximum interval | 16 weeks | High | ALTAIR |
| **Anatomic Parameters** |  |  |  |
| Week 52 patients without fluid | 68% | High | Multiple studies |
| CRT reduction at Week 52 | -135 μm | High | Multiple studies |

### Parameter Set for Treatment Discontinuation Phase

| Parameter | Value | Confidence | Source |
|-----------|-------|------------|--------|
| **Recurrence Rates** |  |  |  |
| 1-year recurrence | 20.7% | High | Artiaga et al. |
| 3-year recurrence | 73.9% | High | Artiaga et al. |
| 5-year recurrence | 88.0% | High | Artiaga et al. |
| Recurrence with PED | 74% | Medium | Aslanis et al. |
| Recurrence without PED | 48% | Medium | Aslanis et al. |
| **Visual Impact** |  |  |  |
| VA loss at recurrence | -3.6 letters | Medium | Aslanis et al. |
| VA recovery after retreatment | Near complete | Medium | Aslanis et al. |
| **Monitoring Parameters** |  |  |  |
| Asymptomatic recurrence rate | 39.1% | Medium | Artiaga et al. |
| Symptomatic detection rate | ~100% of symptomatic cases | Medium | Artiaga et al. |
| Scheduled monitoring sensitivity | 87% | High | Artiaga et al. |

## 10. Simulation Applications

1. **Treatment Protocol Optimization**
   - Compare different T&E protocols (2-week vs. 4-week adjustments)
   - Model optimal maximum extension intervals (12 vs. 16 weeks)
   - Simulate different criteria for treatment discontinuation

2. **Resource Utilization Modeling**
   - Project injection burden for different protocols
   - Estimate clinic capacity requirements
   - Model cost-effectiveness of treatment discontinuation strategies

3. **Patient Outcome Prediction**
   - Predict visual acuity trajectories for individual patients
   - Estimate likelihood of reaching stable disease
   - Project long-term outcomes after treatment discontinuation

4. **Monitoring Strategy Optimization**
   - Simulate different post-discontinuation monitoring schedules
   - Model impact of virtual clinic pathways
   - Evaluate cost-effectiveness of monitoring frequency

5. **Risk Stratification**
   - Identify patients suitable for extended intervals
   - Predict patients at high risk for recurrence after discontinuation
   - Personalize treatment and monitoring strategies based on risk factors