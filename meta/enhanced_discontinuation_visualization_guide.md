# Enhanced Discontinuation Model Visualization Guide

This document explains the key metrics and visualizations used in the enhanced discontinuation model.

## Visualization Components

The enhanced discontinuation model generates visualizations that show three key aspects of the model:

1. **Discontinuations by Type**
2. **Discontinuations by Clinician Profile**
3. **Clinician Decision Influence**

## Understanding "Modified Decisions"

In the "Clinician Decision Influence" visualization, there are two types of bars:

1. **Total Decisions**: The total number of treatment decisions made by clinicians of each profile type.
2. **Modified Decisions**: The number of decisions where clinicians deviated from the protocol recommendation.

### What are Modified Decisions?

"Modified Decisions" represents the number of treatment decisions that were altered by clinicians based on their individual profiles and adherence characteristics, rather than strictly following the protocol.

The enhanced discontinuation model includes clinician variation, where different clinician profiles (adherent, average, and non-adherent) can modify protocol-based decisions according to their risk tolerance and practice patterns. 

Specifically:

1. When a protocol would recommend discontinuing treatment (e.g., after stable disease at maximum interval), a conservative clinician might override this and continue treatment.

2. When a protocol would recommend retreating a patient with recurrent disease, a less conservative clinician might decide against retreatment.

### Interpretation

The visualization shows both the total number of decisions made by each clinician profile type and how many of those decisions were modified from what the protocol would have recommended. This highlights the impact of clinician variation on treatment patterns.

For example, in a typical simulation:
- Adherent clinicians modify only 15% of decisions (high protocol adherence)
- Average clinicians modify 30% of decisions (moderate protocol adherence)
- Non-adherent clinicians modify 60% of decisions (low protocol adherence)

This reflects the implementation of the clinician variation component of the enhanced discontinuation model, where clinicians with different adherence rates have varying tendencies to deviate from protocol recommendations.

## Discontinuation Types

The model includes several types of treatment discontinuation:

1. **Stable Max Interval**: Protocol-based discontinuation after achieving stable disease at maximum treatment interval
2. **Premature**: Non-protocol based early discontinuation
3. **Random Administrative**: Administrative discontinuation (e.g., patient moved, insurance changes)
4. **Treatment Duration**: Time-based discontinuation after a certain treatment duration

## Clinician Profiles

The model includes three clinician profiles:

1. **Adherent**: High protocol adherence (95%), low risk tolerance, conservative retreatment
2. **Average**: Moderate protocol adherence (80%), medium risk tolerance, variable retreatment
3. **Non-adherent**: Low protocol adherence (50%), high risk tolerance, less conservative retreatment

## Statistics Tracking

The model tracks detailed statistics including:

1. Discontinuations by type
2. Retreatment rates by discontinuation type
3. Clinician decision modifications by:
   - Decision type (discontinuation vs. retreatment)
   - Clinician profile
4. Patient characteristics (e.g., PED status)

## Interpreting the Visualization

When analyzing the visualization:

1. Look for patterns in discontinuation types to understand the most common reasons for treatment cessation
2. Compare clinician profiles to see which types of clinicians are more likely to discontinue treatment
3. Examine the modified decisions to understand the impact of clinician variation on treatment patterns
4. Consider the retreatment rates by discontinuation type to understand which patients are most likely to need retreatment

This information can help inform protocol design, clinician education, and patient management strategies.
