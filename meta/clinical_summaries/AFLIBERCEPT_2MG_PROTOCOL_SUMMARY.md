# Aflibercept 2mg Protocol Development Summary

## Date: 2025-06-08
## Branch: feature/financial-analysis

### Completed Deliverables

#### 1. Clinical Protocol YAML
**File**: `protocols/aflibercept_2mg_treat_and_extend.yaml`

Key parameters extracted:
- **Protocol type**: Treat-and-extend
- **Min interval**: 7 weeks (49 days)
- **Max interval**: 20 weeks (140 days)
- **Extension increment**: 2 weeks (14 days)
- **Discontinuation thresholds**:
  - Primary: VA < 25 letters on 2 consecutive visits
  - Critical: VA < 15 letters on 2 consecutive visits
  - Treatment burden: Unable to extend beyond 7 weeks after 2 attempts

**Data gaps filled with placeholders**:
- Loading phase: Assumed standard 3 monthly doses
- Disease state transitions: Used reasonable clinical assumptions
- Vision change model: Conservative estimates based on treatment patterns

#### 2. Financial Model YAML
**File**: `protocols/cost_configs/aflibercept_2mg_nhs_2025.yaml`

Key financial parameters:
- **Drug cost**: £457 per injection (net after 44% NHS discount)
- **List price**: £816
- **Typical annual drug cost**: £3,153 (6.9 injections year 1)
- **Total annual cost**: ~£5,123 (including procedures)

Visit costs defined:
- Loading phase injection: £647 (drug + simplified procedure)
- Standard injection visit: £742 (drug + virtual review)
- Monitoring visit: £150 (no drug)

### Data Sources Used

1. **Clinical parameters**: 
   - Based on best available knowledge as of June 2025
   - Current clinical best practice guidelines

2. **Financial parameters**:
   - Current NHS pricing structures
   - Market pricing data
   - Standard NHS tariff assumptions

### Key Findings

1. **Treatment pathway**: Current best practice emphasizes:
   - Maximum 3 lines of therapy per eye
   - Aflibercept 2mg biosimilar as first choice when available
   - Clear switching criteria based on extension capability

2. **Pricing insights**:
   - Aflibercept 2mg currently £457 net
   - Biosimilar expected at ~£228 (50% reduction)
   - Note: Aflibercept 8mg is paradoxically cheaper at £339

3. **Cost drivers**:
   - Drug cost represents 60-65% of total
   - Each 2-week interval extension saves ~£95
   - Virtual clinics save £70 per visit

### Integration Notes

Both YAML files are compatible with the existing simulation framework:
- Follow V2 format requirements
- Use days for all intervals
- Include required metadata
- Maintain complete state matrices

### Recommendations for Next Steps

1. **Clinical validation**: 
   - Review placeholder values with clinical team
   - Obtain actual trial data for vision outcomes
   - Refine disease state transitions

2. **Financial validation**:
   - Confirm NHS tariffs with recent HRG codes
   - Verify biosimilar pricing projections
   - Add regional variations if needed

3. **Simulation testing**:
   - Run with existing framework
   - Compare outputs to real-world data
   - Calibrate parameters as needed

### Files Created
1. `/protocols/aflibercept_2mg_treat_and_extend.yaml` - Clinical protocol
2. `/protocols/cost_configs/aflibercept_2mg_nhs_2025.yaml` - Financial model
3. `/aflibercept_2mg_data/extract_aflibercept_2mg_data.py` - PDF extraction script
4. `/aflibercept_2mg_data/data_extraction_progress.md` - Extraction notes
5. `/aflibercept_2mg_data/extracted_aflibercept_2mg_data.json` - Raw extraction results