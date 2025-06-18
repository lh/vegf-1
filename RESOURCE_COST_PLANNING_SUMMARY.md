# Resource and Cost Tracking Planning Summary

## Status: Planning Phase Complete ✓

All planning documentation has been completed for the resource tracking and cost analysis features. Implementation is pending the ABS engine merge.

## Completed Planning Documents

### 1. Core Planning
- **RESOURCE_COST_PLANNING.md**: Main planning document outlining requirements, architecture, and implementation phases
- **COST_QUICK_REFERENCE.md**: Unit cost reference including VAT (drug prices, staff costs, procedures)
- **RESOURCE_COST_DATA_SPEC.md**: Detailed YAML configuration specifications for costs and resources

### 2. Implementation Details  
- **RESOURCE_COST_IMPLEMENTATION_ROADMAP.md**: Phased implementation plan with timelines and dependencies
- **RESOURCE_COST_UI_SPEC.md**: Detailed UI/UX specifications for Resources and Costs pages
- **RESOURCE_COST_TESTING_STRATEGY.md**: Comprehensive testing approach with validation criteria

## Key Decisions Made

### 1. VAT Handling
- NHS trusts pay 20% VAT on drug purchases (non-recoverable)
- All drug costs include VAT in the actual NHS cost
- Example: Aflibercept generic £228 net → £274 with VAT

### 2. Architecture Approach
- Separate `ape/economics/` namespace for clean integration
- Event-based hooks into ABS engine (no core modifications)
- Configuration-driven for flexibility
- Feature flags for gradual rollout

### 3. Data Model
- ResourceUsage tracks individual resource consumption events
- CostItem records individual cost components
- Aggregation at patient and simulation levels
- Parquet storage for efficiency

### 4. User Interface
- New "Resources" page: Timeline, utilization, planning tables
- New "Costs" page: Dashboard, breakdowns, distributions
- Integration into existing Compare page
- Export functionality for all data

### 5. Testing Strategy
- Unit tests for all calculations
- Integration tests with real simulation data
- Validation against NHS reference costs
- Performance targets: <5% overhead, <100ms per patient

## Pre-Implementation Checklist

### Completed ✓
- [x] Cost data structure design
- [x] Resource tracking schema
- [x] Integration architecture
- [x] UI/UX mockups and specifications
- [x] Testing strategy and validation approach
- [x] Performance benchmarks defined
- [x] YAML configuration format
- [x] VAT considerations documented

### Pending Dependencies
- [ ] ABS engine merge completion
- [ ] Final cost data validation with NHS sources
- [ ] Stakeholder review of UI designs

## Next Steps (Post-ABS Merge)

### Week 1: Foundation
- Create `ape/economics/` module structure
- Implement CostConfig with VAT handling
- Build ResourceTracker base class
- Set up unit test framework

### Week 2: ABS Integration  
- Hook into visit scheduling events
- Implement resource recording
- Add cost accumulation logic
- Extend SimulationResults

### Week 3: Data Layer
- Implement parquet storage
- Create aggregation functions
- Build query interfaces
- Add caching layer

### Week 4-6: UI Implementation
- Build Resources page
- Build Costs page
- Integrate with Compare page
- Add export functionality

## Implementation Principles

1. **No Synthetic Data**: Use only real simulation results
2. **Fail Fast**: No silent fallbacks or missing data handling
3. **Clean Integration**: No modifications to existing ABS code
4. **Performance First**: Track overhead, optimize early
5. **Validation Focus**: Every calculation must be verifiable

## Risk Mitigation

### Technical Risks
- ABS integration complexity → Clean interface design
- Performance impact → Async tracking, caching
- Data volume → Aggregation strategies

### Data Risks  
- Cost accuracy → Multiple source validation
- Regional variations → Flexible configuration

## Success Metrics

- Track 100% of resource usage events
- Calculate costs within 1% accuracy
- Generate reports in <5 seconds
- Support 10,000+ patient simulations
- <100ms overhead per visit event

## Documentation Location

All planning documents are in the project root:
- RESOURCE_COST_*.md files
- COST_QUICK_REFERENCE.md

Ready for implementation once ABS engine merge is complete.