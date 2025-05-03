# Disease State Definitions for AMD Simulation

This document maps the disease states used in our simulation model to real-world clinical criteria and findings.

## Disease State Overview

Our simulation uses four distinct disease states to represent the spectrum of AMD activity:

1. **NAIVE**: Treatment-naive patients at initial presentation
2. **STABLE**: Disease under control with minimal activity
3. **ACTIVE**: Disease showing signs of activity requiring treatment
4. **HIGHLY_ACTIVE**: Disease with significant activity and rapid progression

## Clinical Criteria for Disease States

### NAIVE State

**Definition**: Patients with newly diagnosed neovascular AMD who have not received any prior anti-VEGF treatment.

**Clinical Characteristics**:
- New-onset symptoms (vision loss, metamorphopsia)
- No prior anti-VEGF injections
- Presence of macular neovascularization on imaging

**OCT Findings**:
- Presence of subretinal fluid (SRF)
- Presence of intraretinal fluid (IRF)
- Presence of pigment epithelial detachment (PED)
- Subretinal hyperreflective material (SHRM)

**Angiographic Findings**:
- Active leakage on fluorescein angiography (FA)
- Neovascular membrane on OCT angiography (OCTA)

### STABLE State

**Definition**: Disease with minimal or no signs of activity following treatment, indicating good response to therapy.

**Clinical Characteristics**:
- Stable or improved visual acuity (change ≤5 ETDRS letters)
- No new symptoms
- No hemorrhage on clinical examination

**OCT Findings**:
- Absence of new fluid (SRF or IRF)
- Reduction or resolution of pre-existing fluid
- Stable PED without growth
- No new SHRM

**Treatment Implications**:
- Candidate for extended treatment intervals
- Low risk of disease progression if treatment interval extended

### ACTIVE State

**Definition**: Disease showing signs of activity despite treatment, indicating ongoing need for therapy but not rapid progression.

**Clinical Characteristics**:
- Fluctuating visual acuity (loss of 5-10 ETDRS letters)
- Recurrent symptoms
- Small hemorrhages may be present

**OCT Findings**:
- Recurrent or persistent SRF (≤200μm height)
- Recurrent or persistent IRF (mild to moderate)
- Fluctuating PED height
- Stable or slowly increasing SHRM

**Treatment Implications**:
- Requires regular treatment
- Not suitable for significant interval extension
- May benefit from fixed interval dosing

### HIGHLY_ACTIVE State

**Definition**: Disease with significant activity and rapid progression despite treatment, indicating aggressive disease phenotype.

**Clinical Characteristics**:
- Significant visual acuity loss (>10 ETDRS letters)
- Progressive symptoms despite treatment
- Moderate to large hemorrhages
- Rapid expansion of lesion size

**OCT Findings**:
- Substantial SRF (>200μm height)
- Extensive IRF with cystoid changes
- Rapidly growing or large PED
- Increasing SHRM
- Possible development of fibrosis or atrophy

**Treatment Implications**:
- Requires intensive treatment
- May need shorter treatment intervals
- Consider adjunctive therapies
- Poor prognosis for visual outcomes

## Mapping to Clinical Trial Terminology

| Simulation State | VIEW 1 & 2 Terminology | HARBOR Terminology | Clinical Practice Terms |
|------------------|------------------------|--------------------|-----------------------|
| NAIVE | Treatment-naive | Treatment-naive | New wet AMD |
| STABLE | "Dry" on OCT | Inactive CNV | Controlled/Dry AMD |
| ACTIVE | "Some fluid" on OCT | Active CNV | Active wet AMD |
| HIGHLY_ACTIVE | "Significant fluid" on OCT | Highly active CNV | Aggressive/Refractory wet AMD |

## Quantitative Criteria for State Classification

### OCT-Based Classification

| Parameter | STABLE | ACTIVE | HIGHLY_ACTIVE |
|-----------|--------|--------|---------------|
| Central Retinal Thickness (CRT) | <300μm or <10% increase from baseline | 300-450μm or 10-25% increase | >450μm or >25% increase |
| Subretinal Fluid (SRF) | None or <50μm | 50-200μm | >200μm |
| Intraretinal Fluid (IRF) | None or isolated small cysts | Multiple cysts <200μm | Large cysts >200μm or confluent cysts |
| Pigment Epithelial Detachment (PED) | Stable or <10% increase | 10-25% increase | >25% increase or new PED |

### Visual Acuity-Based Classification

| Parameter | STABLE | ACTIVE | HIGHLY_ACTIVE |
|-----------|--------|--------|---------------|
| VA Change from Previous Visit | Gain or loss ≤5 letters | Loss of 5-10 letters | Loss >10 letters |
| VA Stability | Stable over 3 months | Fluctuating over 3 months | Progressive decline over 3 months |
| Response to Last Injection | Improvement or stability | Temporary improvement with recurrence | Minimal or no improvement |

## State Transition Triggers in Clinical Practice

### STABLE → ACTIVE Transition
- New SRF or IRF after previous resolution
- Increase in CRT >10% from baseline
- VA loss >5 letters with OCT changes
- New hemorrhage on examination

### ACTIVE → HIGHLY_ACTIVE Transition
- Persistent fluid despite monthly treatment for 3 consecutive injections
- Progressive increase in fluid despite treatment
- VA loss >10 letters with increasing OCT changes
- Expansion of CNV area on OCTA or FA

### HIGHLY_ACTIVE → ACTIVE Transition
- Reduction in fluid with intensive treatment
- Stabilization of VA loss
- Reduction in hemorrhage

### ACTIVE → STABLE Transition
- Resolution of fluid with treatment
- Stable or improved VA
- No new hemorrhage

## Literature Sources for State Definitions

1. **CATT and IVAN Trials**:
   - Used qualitative assessment of "active" vs "inactive" disease
   - Active defined as presence of fluid on OCT, leakage on FA, or new hemorrhage

2. **HARBOR Trial**:
   - Defined activity based on presence and quantity of fluid on OCT
   - Used CRT thresholds for retreatment decisions

3. **VIEW 1 & 2 Trials**:
   - Used qualitative "dry" vs "wet" retina on OCT
   - Defined activity based on presence of any fluid

4. **FLUID Study**:
   - Provided evidence that some SRF (≤200μm) may be tolerated without VA impact
   - Helps define threshold between ACTIVE and HIGHLY_ACTIVE states

5. **Protocol T**:
   - Defined thresholds for "persistent DME" that can be adapted for AMD
   - Used CRT thresholds and VA change for treatment decisions

## Implementation Considerations

1. **Measurement Variability**:
   - OCT measurement variability: ±10μm for CRT
   - VA measurement variability: ±5 ETDRS letters
   - Consider these when determining state transitions

2. **Individual Baselines**:
   - Some patients may have chronic fluid but stable VA
   - Consider percent change from individual baseline rather than absolute thresholds

3. **Asymmetric Transitions**:
   - Threshold for worsening (e.g., STABLE → ACTIVE) may differ from threshold for improvement
   - Generally, higher confidence needed for extension than for intensification

4. **Multiple Criteria**:
   - In clinical practice, combination of VA, OCT, and clinical findings used
   - Model should incorporate multiple parameters for state determination
