# AMD Commissioning Guidance: Evidence Base (May 2024)

## Document Information
- **Publisher**: The Royal College of Ophthalmologists
- **Date**: May 2024
- **Review Date**: May 2025
- **Document ID**: 2024/PROF/482
- **NICE Accreditation**: Valid 5 years from 31 July 2020

## Key Information for Simulation Calibration

### Anti-VEGF Agents Available (Section 9.1)
- **Ranibizumab** (biosimilars and originator)
- **Aflibercept 2mg** and **Aflibercept 8mg**
- **Faricimab**
- **Brolucizumab**
- **Bevacizumab** (off-label use)

### Treatment Efficacy Notes
- Ranibizumab biosimilars: Less costly but "drying effect is not as effective as aflibercept 2 or 8mg or faricimab"
- Requires more frequent monitoring and injections
- Faricimab and Aflibercept 8mg: ~70% of patients require only 12-weekly or longer intervals after loading phase (clinical trial settings)

### Treatment Regimen (Section 10.3)
1. **Loading phase**: Based on SPC of each anti-VEGF agent
2. **Treat and extend regimen**: Based on visual acuity and OCT
3. **Extension protocol**: Extend by 2-4 weeks to maximum of 12-16 weeks based on disease activity and drug posology
4. **Monitor and extend option**: If dry macula after maximum extension maintained for 2-3 visits
5. **Long-term**: nAMD is lifelong; ~25-30% can reactivate
6. **Indefinite treatment**: Some patients require IVT indefinitely at individualized intervals

### Definition of Stable Disease (Section 10.4)
- **Clinical definition**: 2-3 visits at maximal extension (12 or 16 weeks) with dry retina and stable VA
- **Reactivation risk**: After 12 months treatment-free, 25-30% reactivate in subsequent 12 months
- **Monitoring**: OCT is only sensitive tool for assessing reactivation

### Visual Acuity Treatment Thresholds
- **NICE recommendation**: VA 6/12 or worse to start treatment
- **Real-world practice**: "For eyes with VA better than 6/12, waiting for VA to decrease results in delayed treatment and poorer outcomes"
- **Poor visual potential**: VA 6/96 or worse - clinician's discretion to treat

### Monitoring Protocol
- **IOP monitoring**: Before and 30 minutes after first injection, then yearly
- **Cardiovascular events**: Temporary pause in treatment may be required

## Summary Tables and Clinical Trial Data

### Appendix B References
The document includes comprehensive clinical trial data comparing:
- Ranibizumab trials
- Aflibercept trials
- Brolucizumab trials
- Bevacizumab trials
- Faricimab trials
- Biosimilar comparisons

## Key Simulation Parameters Extracted

### Treatment Intervals
- **Minimum extension**: 2-4 week increments
- **Maximum intervals**: 
  - Standard drugs: 12-16 weeks
  - Newer agents (Faricimab, Aflibercept 8mg): Potentially longer
- **Loading phase**: Drug-specific per SPC

### Disease Dynamics
- **Stable disease criteria**: 2-3 consecutive visits at maximum extension
- **Reactivation rate**: 25-30% within 12 months after stopping
- **Lifetime disease**: Requires indefinite monitoring

### Treatment Response
- **Non-responders**: Exist but percentage not specified
- **Switch criteria**: To reduce treatment burden
- **Discontinuation**: Rare, only after 2+ years stability

### Economic Considerations
- Biosimilars less costly but may require more frequent treatment
- Overall cost-effectiveness depends on injection frequency
- Patient and caregiver burden should be considered

## Clinical Trial Evidence Summary

### Ranibizumab
- **Landmark trials**: ANCHOR and MARINA
- **Posology**: Monthly until maximum VA achieved, then treat-and-extend
- **Extension protocol**: No more than 2 weeks at a time
- **Biosimilar comparison**: LUCAS study showed bevacizumab equivalent but required more injections

### Aflibercept
- **Standard dosing**: Every 8 weeks after loading
- **Clinical trials**: Demonstrated non-inferiority to ranibizumab

### Faricimab (Vabysmo)
- **Trials**: TENAYA and LUCERNE (non-inferiority to aflibercept)
- **Loading**: 6mg every 4 weeks for first 4 doses
- **Extension protocol**: 
  - Up to 16 weeks maximum
  - Extensions in 4-week increments
  - Reductions up to 8 weeks if needed
  - Minimum interval: 21 days
- **Results**: ~70% achieved 12-weekly or longer intervals

### Key Clinical Trial Findings for Simulation
1. **Visual acuity outcomes**: Generally 5-7 letter gains at 1 year
2. **Injection frequency**: Varies by drug and protocol
3. **Extension success**: Newer agents (faricimab, aflibercept 8mg) achieve longer intervals
4. **Discontinuous vs continuous**: Slightly worse efficacy with discontinuous treatment (IVAN study)

## Recommendations for Simulation Calibration

### Treatment Interval Parameters
- **Ranibizumab**: 2-week extensions, 12-week maximum
- **Aflibercept 2mg**: 4-week extensions, 16-week maximum  
- **Faricimab**: 4-week extensions, 16-week maximum
- **Aflibercept 8mg**: Potentially 20-week maximum (per cost calculator)

### Disease Activity Assumptions
- **Stable disease**: Requires 2-3 consecutive visits at maximum extension
- **Reactivation rate**: 25-30% annually after treatment cessation
- **Extension success**: ~70% reach 12+ week intervals with newer agents

### Real-World Adjustments
- NHS practice may differ from clinical trial protocols
- Earlier treatment (VA >6/12) becoming more common
- Biosimilar adoption driven by cost pressures
- Virtual monitoring increasing for stable patients
