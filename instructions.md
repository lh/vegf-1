# Aflibercept 2mg Protocol and Financial Modeling Instructions

**Active Session**: Financial Analysis - Aflibercept 2mg
**Branch**: feature/financial-analysis
**Primary Goal**: Create protocol and financial model YAML files for aflibercept 2mg based on latest data

## Critical Constraints

1. **Drug Specificity**: 
   - ONLY use data pertaining to aflibercept 2mg
   - Do NOT use aflibercept 8mg data (pricing unreliable)
   - Do NOT use ranibizumab or bevacizumab data (different clinical profiles)

2. **Naming Conventions**:
   - Generic name: aflibercept
   - Trade name: Eylea
   - Clinical effectiveness: interchangeable
   - Financial modeling: must be specific to formulation

3. **Data Source**:
   - Primary source: `aflibercept_2mg_data/` submodule
   - Contains commercial-in-confidence reports
   - Most up-to-date information available

## Deliverables

### 1. Clinical Protocol YAML
Create `protocols/aflibercept_2mg_[protocol_name].yaml` containing:
- Treatment intervals
- Loading phase specifications
- Maintenance phase rules
- Monitoring requirements
- Discontinuation criteria
- Retreatment thresholds

### 2. Financial Model YAML
Create `protocols/cost_configs/aflibercept_2mg_nhs_2025.yaml` containing:
- Drug acquisition costs
- Administration costs
- Monitoring costs
- Visit type definitions
- Special event costs

## Implementation Plan

### Phase 1: Data Extraction (Day 1)
1. Use PDF extraction tools on aflibercept_2mg_data/ reports
2. Identify key clinical parameters:
   - Loading dose regimen (number of initial monthly doses)
   - Treatment intervals (min/max weeks between injections)
   - Visual acuity thresholds (letters gained/lost)
   - Discontinuation rules (when to stop treatment)
   - Disease activity indicators (OCT markers, VA changes)
3. Extract financial data:
   - List prices (BNF or manufacturer's list)
   - NHS discounts (commercial-in-confidence percentages)
   - Administration tariffs (HRG codes and costs)

### Phase 2: Protocol Development (Day 2)
1. Create base aflibercept 2mg protocol YAML
2. Define treatment phases:
   - Loading phase schedule
   - Maintenance phase algorithms
   - Extension protocols if applicable
3. Validate against clinical guidelines

### Phase 3: Financial Modeling (Day 3)
1. Create NHS cost configuration for aflibercept 2mg
2. Define cost components:
   - Drug costs (with appropriate discounts)
   - Injection procedure costs
   - Monitoring costs (OCT, VA tests)
   - Follow-up visit costs
3. Map costs to visit types

### Phase 4: Integration and Validation (Day 4)
1. Test protocol with simulation engine
2. Validate cost calculations
3. Compare with known NHS tariffs
4. Document assumptions and sources

## Data Extraction Guidelines

When extracting data from PDFs:
1. Note the source document and page number
2. Distinguish between:
   - Clinical trial data
   - Real-world evidence
   - Economic modeling assumptions
3. Flag any uncertainty or conflicting information
4. Preserve units and confidence intervals

## Common Pitfalls to Avoid

1. **Unit Confusion**: 
   - Clinical papers often use weeks, our system uses days
   - Always convert: weeks × 7 = days
   - Document original units in comments

2. **Missing Disease States**:
   - Even if a transition never happens (e.g., HIGHLY_ACTIVE → NAIVE), set it to 0.0
   - The matrix must be complete

3. **Protocol Naming**:
   - Use descriptive suffixes: `aflibercept_2mg_treat_and_extend.yaml`
   - Avoid generic names like `aflibercept_2mg_standard.yaml`

4. **Data Gaps**:
   - If data is missing, DO NOT guess or use defaults
   - Mark as `[MISSING: reason]` and seek clarification
   - Better to have incomplete YAML than incorrect data

## YAML File Structure (Using Established Standards)

### Clinical Protocol Structure (protocols/aflibercept_2mg_[variant].yaml)
```yaml
# Required metadata
name: "Aflibercept 2mg [Protocol Variant]"
version: "1.0.0"
created_date: "2025-06-08"
author: "Extracted from [source document]"
description: "Aflibercept 2mg protocol based on [clinical trial/RWE source]"

# Core protocol parameters
protocol_type: "treat_and_extend" | "pro_re_nata" | "fixed"
min_interval_days: [number]  # Note: V2 uses days, not weeks
max_interval_days: [number]
extension_days: [number]     # Days to extend when stable
shortening_days: [number]    # Days to shorten when active

# Required: Complete disease state transition matrix
disease_transitions:
  NAIVE:
    NAIVE: 0.0
    STABLE: [probability]
    ACTIVE: [probability]
    HIGHLY_ACTIVE: [probability]
  STABLE:
    NAIVE: 0.0
    STABLE: [probability]
    ACTIVE: [probability]
    HIGHLY_ACTIVE: [probability]
  ACTIVE:
    # All transitions required
  HIGHLY_ACTIVE:
    # All transitions required

# Required: Vision change model for all 8 scenarios
vision_change_model:
  naive_treated:
    mean: [value]
    std: [value]
  naive_untreated:
    mean: [value]
    std: [value]
  stable_treated:
    mean: [value]
    std: [value]
  stable_untreated:
    mean: [value]
    std: [value]
  active_treated:
    mean: [value]
    std: [value]
  active_untreated:
    mean: [value]
    std: [value]
  highly_active_treated:
    mean: [value]
    std: [value]
  highly_active_untreated:
    mean: [value]
    std: [value]

# Treatment effect on state transitions
treatment_effect_on_transitions:
  NAIVE:
    multipliers:
      STABLE: [value]
      ACTIVE: [value]
      HIGHLY_ACTIVE: [value]
  STABLE:
    multipliers:
      STABLE: [value]  # Often 1.0 (no change)
      ACTIVE: [value]
      HIGHLY_ACTIVE: [value]
  ACTIVE:
    multipliers:
      STABLE: [value]
      ACTIVE: [value]
      HIGHLY_ACTIVE: [value]
  HIGHLY_ACTIVE:
    multipliers:
      STABLE: [value]
      ACTIVE: [value]
      HIGHLY_ACTIVE: [value]

# Baseline vision parameters
baseline_vision:
  mean: 55
  std: 15
  min: 25
  max: 85

# Discontinuation rules
discontinuation_rules:
  stable_extended_interval:
    criteria:
      consecutive_stable_visits: [number]
      minimum_interval_weeks: [number]  # Note: inconsistent with days elsewhere
    probability: [value]
    reason: "stable_disease"
  poor_response:
    criteria:
      va_loss_from_baseline: [value]
      assessment_months: [number]
    probability: [value]
    reason: "poor_response"
  # Add all relevant discontinuation scenarios
```

### Financial Model Structure (protocols/cost_configs/aflibercept_2mg_nhs_2025.yaml)
```yaml
# Required metadata
metadata:
  name: "Aflibercept 2mg NHS Costs 2025"
  currency: "GBP"
  effective_date: "2025-01-01"
  version: "1.0"
  source: "[Document references with page numbers]"

# Drug costs with NHS pricing structure
drug_costs:
  aflibercept_2mg:
    unit_cost: [net_price]      # After NHS discount
    list_price: [official_price] # Published list price
    procurement_discount: [percentage] # NHS discount rate
    note: "Source: [specific reference]"

# Component costs (NHS tariffs)
visit_components:
  injection: [value]
  oct_scan: [value]
  visual_acuity_test: [value]
  pressure_check: [value]
  virtual_review: [value]
  face_to_face_review: [value]
  nurse_review: [value]
  adverse_event_assessment: [value]
  fluorescein_angiography: [value]

# Visit type definitions (combinations)
visit_types:
  injection_virtual:
    components: [injection, oct_scan, pressure_check, virtual_review]
    total_override: null  # null = sum components
  injection_loading:
    components: [injection, visual_acuity_test]
    total_override: null
  monitoring_virtual:
    components: [oct_scan, visual_acuity_test, virtual_review]
    total_override: null
  monitoring_face_to_face:
    components: [oct_scan, visual_acuity_test, pressure_check, face_to_face_review]
    total_override: null

# Special events
special_events:
  initial_assessment: [value]
  discontinuation_admin: [value]
  retreatment_assessment: [value]
  adverse_event_mild: [value]
  adverse_event_severe: [value]

# Optional: Detailed visit cost breakdowns
visit_costs:
  injection_visit:
    oct_monitoring: [value]
    injection_procedure: [value]
    consumables_setup: [value]
    total_excluding_drug: [calculated]

# Optional: Annual cost projections
annual_costs:
  aflibercept_2mg_q8:
    loading_phase: [number_injections]
    maintenance: [number_injections]
    total_injections: [total]
    drug_cost: [calculated]
    procedure_costs: [calculated]
    annual_total: [calculated]
```

## Formal Format Requirements

### Clinical Protocol Requirements
1. **All parameters must be explicit** - No defaults or missing values
2. **Disease state transitions must sum to 1.0** for each source state
3. **All 8 vision scenarios must be defined** (4 states × 2 treatment conditions)
4. **Time units**: V2 system uses days (not weeks) for all intervals
5. **No negative values** for any parameter
6. **Complete coverage** - Every possible state/scenario must be addressed

### Financial Model Requirements
1. **NHS pricing structure** must include:
   - List price (official published price)
   - Procurement discount (percentage)
   - Net unit cost (calculated price after discount)
2. **All costs in GBP** unless otherwise specified
3. **Source attribution** required for all values
4. **Visit types** must reference only defined components
5. **Component reusability** - Define once, use in multiple visit types

### Key Differences from Generic Formats
- Our system requires **complete state matrices** (no sparse definitions)
- **V2 uses days** throughout (convert weeks to days: weeks × 7)
  - Note: Clinical sources typically use weeks; we convert for computational precision
  - Future enhancement: Consider explicit units in YAML (e.g., `interval_weeks: 12`)
- **No implicit defaults** - everything must be specified
- **Audit trail requirements** - source and date for all values

## Quality Checks

Before finalizing YAML files:
1. Verify all numerical values against source documents
2. Ensure units are consistent (weeks vs months, etc.)
3. Check for internal consistency
4. Validate YAML syntax
5. Run through simulation to ensure compatibility

## Documentation Requirements

Each YAML file must include:
- Clear metadata section
- Source attribution
- Extraction date
- Version number
- Key assumptions
- Any limitations or uncertainties

## Next Steps

1. Set up PDF extraction environment
2. Begin systematic review of aflibercept_2mg_data/
3. Create extraction template/checklist
4. Start with clinical protocol extraction
5. Follow with financial data extraction

## Example Extraction Checklist

### Clinical Parameters
- [ ] Loading phase: ___ doses at ___ week intervals
- [ ] Maintenance min interval: ___ weeks (× 7 = ___ days)
- [ ] Maintenance max interval: ___ weeks (× 7 = ___ days)
- [ ] Extension increment: ___ weeks (× 7 = ___ days)
- [ ] VA improvement threshold: ___ letters
- [ ] VA deterioration threshold: ___ letters
- [ ] Discontinuation criteria documented
- [ ] Source: Document ___, Page ___

### Financial Parameters
- [ ] Aflibercept 2mg list price: £___
- [ ] NHS discount: ___% 
- [ ] Net price: £___ (calculated)
- [ ] Injection procedure cost: £___
- [ ] OCT scan cost: £___
- [ ] Source: Document ___, Page ___

## Success Criteria

- [ ] Clinical protocol accurately reflects aflibercept 2mg usage
- [ ] Financial model captures all relevant NHS costs
- [ ] YAML files pass validation
- [ ] Integration with existing simulation framework works
- [ ] Documentation is complete and traceable