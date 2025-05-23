# Design Decisions

1. **YAML Structure**: Using nested YAML structure for protocols to balance human readability with machine parsing needs
2. **Condition System**: Simple key/value conditions with comparators for treatment decisions
3. **Temporal Logic**: Using interval/week-based scheduling for injections and assessments
4. **Agent-Based**: Protocol steps designed to work with both individual patient agents and population-level simulations
5. **Event Priority System**: Using priority levels to ensure correct ordering of visit/decision events
6. **State Management**: Keeping patient state separate from visit history for clean data analysis
7. **Protocol Flexibility**: Supporting multiple protocols per agent with dynamic interval adjustments
8. **Simulation Architecture**: Separate base, DES, and ABS implementations for comparison studies
9. **Visit Types**: Standardized visit definitions in YAML for consistency across protocols
10. **Decision Pipeline**: Structured nurse->doctor decision flow matching clinical practice
11. **Vision Modeling**: Realistic vision change simulation with treatment memory and ceiling effects
12. **DES Event Scheduling**: End date must be set before adding patients to ensure proper event validation
13. **Daily Capacity Model**: Using daily slot allocation and clinic day awareness (Mon-Fri) to better reflect real clinic operations
14. **Event Processing**: Strict event processing order with visit scheduling based on daily capacity limits
15. **Clinic Scheduling**: Rescheduling logic respects working days and daily patient limits to prevent overloading
16. **Simplified Clinical Model**: Implemented a streamlined disease state model with three states (STABLE, ACTIVE, HIGHLY_ACTIVE) and fixed transition probabilities. This simplification allows for easier validation and calibration while still capturing the essential dynamics of AMD progression. Vision changes are modeled using normal distributions, differentiating between injection and non-injection visits, to maintain biological plausibility while reducing complexity.
