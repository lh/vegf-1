# wAMD Cost Calculator Protocols Summary

## Overview
The cost calculator includes several treatment protocols for different anti-VEGF agents with specific assumptions about injection frequency, intervals, and switching patterns.

## Drugs Included
1. **Ranibizumab** (originator and biosimilar)
2. **Aflibercept 2mg** (originator and biosimilar)
3. **Faricimab** (originator)
4. **Aflibercept 8mg** (originator)

## Protocol Structure

### Loading Phase (All drugs)
- **Number of injections**: 3
- **Interval**: 4 weeks between injections
- **End of loading phase**: Week 8

### Post-Loading Treatment Approach
- **No disease activity**: Treat-and-extend (all drugs)
- **Disease activity**: 
  - Ranibizumab: 4-week intervals
  - Aflibercept 2mg: 8-week intervals
  - Faricimab: 8-week intervals
  - Aflibercept 8mg: 8-week intervals

### Treat-and-Extend Parameters

#### Ranibizumab
- **Increment interval**: 2 weeks
- **Maximum interval**: 12 weeks
- **Starting interval**: 4 weeks (if disease activity)

#### Aflibercept 2mg
- **Increment interval**: 4 weeks
- **Maximum interval**: 16 weeks
- **Starting interval**: 8 weeks (if disease activity)

#### Faricimab
- **Increment interval**: 4 weeks
- **Maximum interval**: 16 weeks
- **Starting interval**: 8 weeks (if disease activity)

#### Aflibercept 8mg
- **Increment interval**: 4 weeks
- **Maximum interval**: 20 weeks (notably longer than others)
- **Starting interval**: 8 weeks (if disease activity)

## Switching Assumptions

### Treatment Pathways
1. Ranibizumab biosimilar → Aflibercept 2mg biosimilar
2. Aflibercept 2mg biosimilar → Aflibercept 8mg originator
3. Faricimab originator → Aflibercept 8mg originator
4. Aflibercept 8mg originator → Faricimab originator

### Reloading Requirements
- **Required** (True): 
  - Ranibizumab to Aflibercept 2mg
  - Faricimab to Aflibercept 8mg
  - Aflibercept 8mg to Faricimab
- **Not required** (False):
  - Aflibercept 2mg to Aflibercept 8mg

## Monitoring Assumptions

### Visual Acuity Assessments (Scans)
- **Loading phase - first injection**: 1 scan
- **Loading phase - last injection**: 1 scan
- **With treat-and-extend injections**: 1 scan per injection
- **All other injections**: 0 scans

### Consultations
- **First injection (loading)**: Yes
- **Last injection (loading)**: Yes
- **Annual consultation**: Yes
- **First attendance**: £152
- **Follow-up**: £69

## Expected Injection Frequencies

### Year 1 (from calculator outputs)
- Ranibizumab: 7 injections
- Aflibercept 2mg: 6 injections
- Faricimab: 6 injections
- Aflibercept 8mg: 5 injections

### Year 2
- Ranibizumab: 4 injections
- Aflibercept 2mg: 3 injections
- Faricimab: 3 injections
- Aflibercept 8mg: 3 injections

### Year 3+
- Ranibizumab: 5 injections
- Aflibercept 2mg: 3 injections
- Faricimab: 3 injections
- Aflibercept 8mg: 3 injections

## Key Insights for Our Simulation

1. **Different Extension Strategies**: 
   - Ranibizumab uses smaller increments (2 weeks) but lower max (12 weeks)
   - Others use larger increments (4 weeks) with higher max (16-20 weeks)

2. **Disease Activity Response**:
   - Ranibizumab shortens to 4 weeks (more aggressive)
   - Others maintain 8 weeks minimum (aligns with NHS constraints)

3. **Aflibercept 8mg Advantage**:
   - Longest maximum interval (20 weeks)
   - Fewer Year 1 injections (5 vs 6-7)

4. **Switching Complexity**:
   - Most switches require reloading (3 additional injections)
   - Only Aflibercept 2mg → 8mg doesn't require reloading

5. **Cost Implications**:
   - Procedure cost: £134 per injection (HRG BZ86B)
   - Scan cost: £110 per assessment (HRG BZ88A)
   - Consultation: £152-168 (first), £69-81 (follow-up)

## Drug Cost Details (Essential for Economic Modeling)

### Unit Costs (including 20% VAT)
- **Ranibizumab originator (Lucentis)**: £613.20
- **Ranibizumab biosimilar**: £628.14
- **Aflibercept 2mg originator (Eylea)**: £979.20
- **Aflibercept 2mg biosimilar**: £354.78 (64% cost reduction)
- **Faricimab (Vabysmo)**: £1,028.40
- **Aflibercept 8mg (Eylea HD)**: £1,197.60

### Key Economic Insights for Simulation Tuning
1. **Biosimilar adoption**: Aflibercept 2mg biosimilar dramatically changes cost-effectiveness (£354.78 vs £979.20)
2. **Total treatment costs Year 1** (drug + procedures): 
   - Aflibercept 2mg biosimilar: ~£2,400
   - Ranibizumab biosimilar: ~£5,100
   - Faricimab: ~£7,000
   - Aflibercept 8mg: ~£6,600
3. **Cost per injection episode** (drug + procedure + scan):
   - Ranges from £599 (Aflibercept biosimilar) to £1,442 (Aflibercept 8mg)
4. **Extension benefit**: Each avoided injection saves £244-1,332 depending on drug choice

## Implications for Calibration

This aligns with our understanding that:
- NHS protocols maintain 8-week minimum for most drugs
- Ranibizumab may use 4-week intervals (older protocol)
- Newer drugs (Faricimab, Aflibercept 8mg) achieve longer intervals
- Real-world injection counts are lower than clinical trials
- Economic pressures favor biosimilar adoption and extension protocols

## Validation Benchmarks for Simulation Outputs

### Expected Annual Injection Counts (from calculator)
These can validate if our simulation produces realistic injection frequencies:

| Drug | Year 1 | Year 2 | Year 3+ |
|------|--------|--------|---------|
| Ranibizumab | 7 | 4 | 5 |
| Aflibercept 2mg | 6 | 3 | 3 |
| Faricimab | 6 | 3 | 3 |
| Aflibercept 8mg | 5 | 3 | 3 |

### Treatment Interval Distribution Targets
Based on treat-and-extend assumptions:
- **Year 1**: Most patients still extending (mix of 8-12 week intervals)
- **Year 2+**: Stable patients at/near maximum intervals
- **Disease recurrence**: Approximately 20-30% need interval shortening annually

### Cost Validation Targets
Annual per-patient costs (drug + procedures):
- **Biosimilar pathway**: £2,400-5,100
- **Originator pathway**: £6,600-8,000
- **Switching scenarios**: Add ~£2,000 for reloading phase