# Economic Analysis Planning for AMD Simulation

## Overview
This document outlines the planning considerations for adding financial/economic analysis capabilities to the AMD treatment simulation framework. The goal is to systematically track, analyze, and visualize treatment costs throughout a patient's treatment journey.

## 1. Economic Perspective & Scope

**Key Question: What economic perspective are you taking?**

Options to consider:
- [xx] Healthcare payer perspective (NHS/insurance)
- [xxx] Provider/hospital perspective
- [x] Societal perspective (including indirect costs)
- [x] Multiple perspectives (ability to switch between views)

**Your Answer:**

The primary perspective will be the healthcare payer perspective, with the option to include societal costs for a broader analysis. This allows us to capture both direct medical costs and indirect costs such as patient productivity loss.
The model will be designed to switch between these perspectives as needed.


## 2. Cost Categories

**Key Question: What types of costs do you need to track?**

### Direct Medical Costs
- [x] Drug costs (per injection)
the drugs are supplied ready to use, there are different doses available, eg Eylea 8mg and Eylea 2mg, but these are different products, ie 4 eylea 2mg does not equal 1 eylea 8mg dose!
I can get reference costs for the drugs, we can use £800 as a placeholder for any of the injections at the moment.
- [x] Administration costs (injection procedure)
  - Physician time
  - Nurse time
  - Facility use
- [x] Monitoring visit costs
  - OCT scans
  - Visual acuity tests
  - Consultation fees
  We have at least 3 types of monitoring:
  - OCT scan done at time of injection, with a "virtual review" by the physician, physician looks at scans and vision, makes a decision, writes to patient. All done within an EPR system.
  - OCT scan done at a special AMD review visit, with a "face to face" review by the physician, physician looks at scans and vision, examines patient, makes a decision, discusses with patient, writes to patient. All done within an EPR system.
  - Visual acuity tests done at the same time as an OCT scan in a special visit, with a "virtual review" by the physician, physician looks at scans and vision, makes a decision, writes to patient. All done within an EPR system.
- [x] Adverse event management costs - hard to estimate, but we can use a placeholder value for now
  - Hospitalization costs
  - Additional treatments
- [x] Facility/overhead costs - I have asked for this to be provided, but we can use a placeholder value for now
  - Facility use per visit
  - Equipment costs (e.g., OCT machines)

### Indirect Costs (if societal perspective)
- [x] Patient time/productivity loss - patients are not usually of working age
- [ ] Caregiver time - this is needed for the wider societal perspedctive, not in the direct medical costs
- [ ] Transportation costs - we can assume these are negligible for now, but we can add them later if needed
- [ ] Vision aid/rehabilitation costs - will be added later if needed

### Other Costs
- [ ] [Add any missing categories]

**Your Answer:**
Are we pricing in the initial diagnosis or starting from the first injection? As initial diagnosis is the same regardless and we are interested in comparisons between drugs and between protocols probably not needed.

## 3. Cost Dynamics

**Key Question: How do costs vary in your model?**

Consider:
- [x] Different costs by drug agent (Eylea vs. others) - Yes, but surprisingly littel at the moment, although generics will substantially reduce costs and we will need to add generic ranubizumab and aflibercept.
- [ ] Loading dose phase vs. maintenance phase costs - I don't think these will need to be modelled specificaly as the differences in cost will be built up from the various tasks associated with the different phases.
- [ ] Monitoring intensity changes over treatment phases - again these shoudl be inherent in the modelling of the different phases, so we don't need to model these separately
- [ ] Costs associated with discontinuation events - this is interesting - I am not sure how to model this. We can assume that a retreatment after dicontinuation will incur societal costs as the patient will usually end up seekign re-referral.
- [x] Time-based cost changes (inflation adjustments) - I think for now we will assume that costs are constant, but we can add inflation adjustments later if needed. We will calculate on today's value (even looking back).
- [ ] Volume discounts or negotiated rates - these are inherent in the nhs costings I will get, we won't be using list prices.
- [x] Bilateral vs. unilateral treatment - I had not considered this and we do need to model it! Need to remmber this as an addition to our modelling. I also need to et the parameters fromt he literatiure to find out what the risk of second eye treatment is. We woudl need to work out how much to discoount the second eye treatment, as it is not a full cost.

**Your Answer:**
We also need to undersant demand and capcity; if the demand exceds the basic supply of injectors, OCT operators, clincian reviewers, then that work has to be purchased at a higher rate "ADH" rate. So not all costs are the same, some are higher if the demand exceeds the capacity.

## 4. Integration Points

**Key Question: Where in the existing simulation do costs accrue?**

Potential cost accrual points:
- [x] Each injection visit
- [x] Monitoring-only visits
- [x] Initial diagnosis/assessment
- [x] Discontinuation events
- [x] Adverse events
- [ ] Based on visual acuity outcomes (e.g., legal blindness) - for societal perspective, we can add this later
- [x] Treatment switching events - I have not modelled treatment switches yet, this is something else that would be good to model almost as a protocol comparison, but we can add this later. We need a future ideas section for all these great ideas!

**Your Answer:**
```
[To be filled in - map costs to simulation events]
```

## 5. Economic Outputs

**Key Question: What economic metrics do you need to calculate?**

Potential metrics:
- [x] Total cost per patient: this will have an impact in presentation and discussion but is not a core economic question
- [ ] Average cost per patient per year
- [x] Cost breakdown by category
- [ ] Cost accumulation over time (monthly/yearly)
- [ ] Cost per injection
- [x] Cost-effectiveness ratios (e.g., cost per vision-year saved)
- [ ] Budget impact for defined populations
- [x] Cost variance analysis
- [x] Protocol comparison costs

**Your Answer:**

prioritize Protocol comparison costs


## 6. Data Structure Considerations

**Key Question: How should we structure cost data for analysis and storage?**

Requirements:
- [ ] Patient-level cost accumulation
- [ ] Time-stamped cost events
- [ ] Category coding for cost types
- [x] Multi-dimensional aggregation capability
- [x] Parquet-compatible schema
- [x] Maintain compatibility with existing data structures

**Existing data format constraints?**

Need to determine form inputs into the V2 streamlit.

## 7. Visualization Requirements

**Key Question: What visualizations would be most helpful?**

Potential visualizations:
- [ ] Cost accumulation curves over time
- [ ] Cost breakdown pie/bar charts
- [ ] Cost distribution histograms
- [x] Cost vs. outcome scatter plots
- [x] Protocol cost comparison charts
- [x] Population-level budget impact projections
- [ ] Cost driver analysis (waterfall charts)
- [ ] Time-to-cost threshold analyses

**Primary questions visualizations should answer:**

What is the most effective, cheapest protocol for treating AMD?

## 8. Technical Implementation Considerations

**Additional technical questions:**

- How should costs integrate with existing patient state tracking? - I think they shoudl pobably be added to the existing patient state tracking, if we can achieve that without breaking the existing code. But if the only way is to break and redo, then we will do that.
- Should costs be tracked in the simulation events or as a separate module? - I don't understand this question properly.
- What currency and time period for costs (e.g., 2024 GBP)? - 2025 GBP
- Do we need sensitivity analysis capabilities for cost parameters? - Yes, we should be able to vary costs and see how it affects outcomes.
- Should cost accumulation be deterministic or stochastic? - I think it should be deterministic, but we can add stochasticity later if needed.

Just as the protocols are abstracted from the code, the costs should be abstracted as well. This will allow us to easily change costs without modifying the core simulation logic. So there will be a costs configuration file that defines all the costs, and the simulation will read from this file to apply costs to each patient. That way we can run two protocls with the smae costs, or two costs with the same protocol, or any combination thereof.
- How will we handle cost updates over time (e.g., inflation)? - We can add a cost update mechanism later, but for now we will assume costs are constant.

**Your thoughts:**
See above!

## 9. Validation and Testing

**How will we validate the economic model?**

- [x] Comparison with published economic studies
- [x] Clinical expert review
- [x] Sensitivity testing
- [x] Edge case handling

**Your validation approach:**

I am a clinical expert and I have colleagues who are also clinical experts who can review the model. We will also compare with published studies and do sensitivity testing to ensure the model is robust.

## Next Steps

Once this planning document is completed, we will:
1. Design the cost tracking data structures
2. Create a cost parameter configuration system
3. Implement cost accumulation in the simulation
4. Develop visualization components
5. Create documentation and validation tests

---

**Notes Section:**

This is huge, we will need to break this down into smaller tasks and be certain we are happy with the design before we start implementing. We will use a TDD approach to ensure we have a solid foundation before adding complexity.

---

## Follow-up Questions & Design Decisions

### 10. Cost Configuration Architecture

Based on your requirement that "costs should be abstracted like protocols", we need to design the configuration structure.

**Question: How should we structure cost configuration files?**

Option A - Mirror protocol structure:

Would it be better to have a structure that has multiple combinations of costs, or has the individual costs that are then built up: we could extend granularity up or down eg injection could be further broken down into drops costs, personel costs, needles etc; we don't need to start with that - we will start with an estimate of total non-drug injection costs but have in mind a framework that woudl allow further breakdown - does that make sense?


```yaml
# cost_configs/nhs_standard_2025.yaml
drug_costs:
  eylea_2mg: 800
  eylea_8mg: 800




visit_componant_costs:
  injection:
  oct:
  visual_acuity:
  pressure:
  virtual_review:
  face_to_face_review:


visit_types:
  injection_virtual: # (contains injection, oct, pressure, virtual review)
  injection_only: #(containts injection, vision)
  monitoring_oct: #(oct, virtual review)
  monitoring_virtual: #(oct, vision, pressure, virtual review)
  monitoring_face_to_face_review: #(vision, pressure, oct, face to face review)
```


Option B - Activity-based structure:
```yaml
# cost_configs/nhs_standard_2025.yaml
activities:
  drug_administration:
    eylea_2mg: 800
  monitoring:
    oct_scan: ???
    virtual_review: ???
```

**Your preference:**
This is a diffiiculat one to decinde on and I think we need a serparate discussion to decide on the best approach. I think we should start with a simple structure that can be easily extended later.

### 11. Bilateral Treatment Details

You mentioned bilateral treatment is important but not yet modeled.

**Questions about bilateral treatment:**
- Do both eyes follow independent treatment protocols?
- Are monitoring visits combined when treating bilaterally?
- What's the typical discount/efficiency for second eye treatment?
- How should we track which eye is being treated?

**Your answers:**
```
[We will not model bilateral treatment at the moment, but we will add it later. We will need to track which eye is being treated, and we will need to add a discount for second eye treatment. We will also need to decide how to handle monitoring visits for bilateral treatment. But just gettign ing the basic costs is more important for now.]
```

### 12. Capacity-Based Pricing (ADH Rates)

You mentioned costs increase when demand exceeds capacity.

**Implementation questions:**
- Should this be modeled at population level or per-patient?
- What are typical capacity thresholds (e.g., X injections/month)?
- Which activities are most affected (injections, OCT, reviews)?
- Is this a simple multiplier (e.g., 1.5x) or more complex?

**Your approach:**
```
[It will ahve to be modelled at the hospital level, as we don't have enough data to model it at the patient level. We will need to track the number of injections, OCT scans, and reviews per week, and apply a multiplier if the demand exceeds capacity. The multiplier will be a simple 1.5x for now, but we can make it more complex later if needed.]
```

### 13. Visit Type Classification

You identified 3 monitoring patterns.

**Current state question:**
Do visits in the current simulation already have these subtypes, or do we need to enhance the visit classification system?

**Your answer:**
```
[We have implicit in the simulation that vision and oct are done on visits where a decision is made, but we don't have explicit visit types for these. I am not sure how we handle the loading doeses for instance - they should just be vision and inject visits. We may need to enhance the visit classification system to include these subtypes. We can start with a simple classification and add more complexity later if needed.]
```

### 14. Cost Data Structure

**Where should costs be stored?**

Option A - Separate cost tracking:
```python
# Attached to each patient
patient.cost_history = {
    'events': [
        {'time': 0, 'type': 'drug', 'amount': 800, 'category': 'eylea_2mg'},
        {'time': 1, 'type': 'visit', 'amount': 150, 'category': 'injection_virtual'}
    ]
}
```

Option B - Embedded in existing events:
```python
# Add cost to existing visit structure
visit = {
    'time': 0,
    'type': 'injection',
    'costs': {
        'drug': 800,
        'administration': 150,
        'monitoring': 50
    }
}
```

**Your preference and reasoning:**
```
[Not sure on this. Please discuss more]
```

### 15. Implementation Phasing

**Proposed phases:**

**Phase 1: Core Cost Infrastructure**
- Design cost configuration schema
- Create cost accumulator data structures
- Add cost tracking to existing visit events
- Basic unit tests

**Phase 2: Unilateral Cost Tracking**
- Implement drug costs
- Implement visit-type-specific costs
- Create basic cost reporting
- Validate against known scenarios

**Phase 3: Advanced Features**
- Bilateral treatment modeling
- Capacity-based cost adjustments
- Societal perspective costs
- Treatment switching costs

**Phase 4: Analysis & Visualization**
- Protocol comparison tools
- Cost-effectiveness calculations
- Budget impact projections

**Do you agree with this phasing? Any adjustments needed?**
```
[Bilateral treatment modeling is not a priority at the moment. Also less important than phase four are societal perspective costs and treatment switching costs. These can go in a phase 5 ("Augmentation" phase)]
```

### 16. Immediate Priorities

**What should we implement first to provide immediate value?**
- [ ] Basic cost tracking for existing simulations
- [ ] Cost configuration system
- [ ] Simple cost reporting
- [ ] Other: _______________

**Your top 3 priorities:**
```
1. Basic cost tracking for existing simulations
2.
3.
```

### 17. Future Features Parking Lot

Based on our discussion, these features are important but not immediate:
- Treatment switching costs
- Generic drug pricing
- Inflation adjustments
- Vision aids/rehabilitation costs
- Complex societal costs

**Any other future features to note?**
```
[To be filled in]
```

---

## Design Discussion Points

### 18. Cost Configuration Structure - Detailed Options

Based on your component-based suggestion, here are refined options:

**Option 1 - Component-Based Hybrid:**
```yaml
# Define atomic cost components
visit_component_costs:
  injection: 150
  oct: 75
  visual_acuity: 25
  pressure: 10
  virtual_review: 50
  face_to_face_review: 120

# Define visit types as compositions
visit_types:
  injection_virtual:
    components: [injection, oct, pressure, virtual_review]
  injection_only:
    components: [injection, visual_acuity]
  monitoring_oct:
    components: [oct, virtual_review]
  monitoring_virtual:
    components: [oct, visual_acuity, pressure, virtual_review]
  monitoring_face_to_face:
    components: [visual_acuity, pressure, oct, face_to_face_review]
```

**Option 2 - With Override Capability:**
```yaml
visit_types:
  injection_virtual:
    total_cost: 285  # Optional override for negotiated rates
    components: [injection, oct, pressure, virtual_review]
```

**Benefits of component approach:**
- Flexibility: Can adjust individual component costs
- Transparency: Clear what makes up each visit type
- Extensibility: Easy to add new components or visit types
- Granularity control: Can start simple, add detail later

**Your preference:**
```
[Option 2 - it gives us the ability to put in sensibel paceholders very quickly too]
```

### 19. Cost Data Structure - Detailed Analysis

**Option A - Separate Cost Tracking:**
```python
# Costs tracked separately from clinical events
patient.cost_history = CostTracker()
patient.clinical_history = [visits...]

# When visit happens:
visit = create_visit(...)
costs = calculate_costs(visit, cost_config)
patient.cost_history.add(costs)
```

**Pros:**
- Clean separation of concerns
- Easy to add/remove cost tracking without touching clinical code
- Can run cost analysis on existing simulation outputs
- Easy to run multiple cost scenarios on same clinical data

**Cons:**
- Need to maintain synchronization between events and costs
- Potential for costs and clinical events to get out of sync
- Duplicate some temporal information

**Option B - Embedded Costs:**
```python
# Costs embedded in visit events
visit = {
    'time': 0,
    'type': 'injection',
    'clinical_data': {...},
    'costs': {
        'drug': 800,
        'components': {'injection': 150, 'oct': 75},
        'total': 1025
    }
}
```

**Pros:**
- Single source of truth
- Costs always linked to their generating events
- Natural for event-based analysis
- No synchronization issues

**Cons:**
- Changes existing data structures
- Harder to run different cost scenarios
- Couples clinical and economic models

**Option C - Hybrid Reference Approach:**
```python
# Minimal cost reference in visits
visit = {
    'time': 0,
    'type': 'injection',
    'visit_type': 'injection_virtual',  # Reference to cost profile
    'drug': 'eylea_2mg'  # Drug reference
}

# Separate cost calculation layer
cost_analyzer = CostAnalyzer(cost_config)
total_costs = cost_analyzer.calculate_patient_costs(patient_history)
```

**Pros:**
- Minimal changes to existing structures
- Easy to swap cost configurations
- Can run cost analysis as post-processing
- Maintains separation of concerns

**Cons:**
- Need to ensure visit types are properly tagged
- Cost calculation happens separately from simulation

**Your preference and why:**
```
[Option C]
```

### 20. Visit Type Classification Enhancement

You mentioned loading doses might just be "vision and inject" visits. Here are options:

**Option A - Enhance visit types now:**
```python
# Explicit visit subtypes
visit_types = {
    'injection_loading': ['injection', 'visual_acuity'],
    'injection_maintenance': ['injection', 'oct', 'pressure', 'virtual_review'],
    'monitoring_routine': ['oct', 'virtual_review'],
    'monitoring_comprehensive': ['oct', 'visual_acuity', 'pressure', 'face_to_face_review'],
    'injection_only': ['injection', 'visual_acuity']
}
```

**Option B - Use existing structure with inference:**
```python
# Infer from context
def determine_visit_components(visit, patient_state):
    if patient_state.phase == 'loading':
        return ['injection', 'visual_acuity']
    elif visit.type == 'injection':
        return ['injection', 'oct', 'pressure', 'virtual_review']
    # etc...
```

**Option C - Add metadata without changing core:**
```python
visit = {
    'type': 'injection',  # Keep existing
    'metadata': {
        'phase': 'loading',
        'components': ['injection', 'visual_acuity']
    }
}
```

**Your preference:**
```
[Option A ]
```

### 21. Revised Implementation Roadmap

Based on your priorities:

**Phase 1: Core Cost Infrastructure**
- Design cost configuration schema (YAML structure)
- Create cost calculation module
- Implement cost accumulator/tracker
- Add basic unit tests
- Create simple cost report generator

**Phase 2: Basic Cost Implementation**
- Implement drug costs from config
- Implement visit-type costs from config
- Add cost tracking to simulation runs
- Create cost summary outputs
- Validate against known NHS tariffs

**Phase 3: Cost Analysis & Visualization**
- Protocol cost comparison tools
- Cost accumulation curves
- Cost breakdown charts
- Basic cost-effectiveness metrics (cost per vision-year maintained)
- Export to parquet for streamlit integration

**Phase 4: Advanced Economic Analysis**
- Budget impact projections for populations
- Sensitivity analysis on cost parameters
- Monte Carlo simulations for uncertainty
- Advanced visualizations (tornado diagrams, etc.)

**Phase 5: Future Enhancements (Lower Priority)**
- Bilateral treatment modeling
- Societal perspective costs
- Treatment switching economics
- Capacity-based (ADH) pricing
- Time-varying costs (inflation)

**Agreement with this phasing?**
```
[To be filled in]
```

### 22. Implementation Starting Point

Given your top priority is "Basic cost tracking for existing simulations", we could start with:

1. **Minimal MVP**: Add cost post-processing to existing simulation outputs
2. **Integrated approach**: Modify simulation to track costs during runs
3. **Configuration first**: Build cost config system, then add tracking

**Which approach appeals most for getting started quickly?**
```
[To be filled in]
```