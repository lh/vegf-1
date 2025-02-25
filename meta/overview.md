# Project Overview

This project is a hybrid mixed discrete event simulation (DES) with agent-based simulation (ABS) for modeling Age-related Macular Degeneration (AMD) treatment protocols.

## Key Features

1. **Hybrid Simulation Approach**: The project implements both a pure DES and a hybrid DES/ABS approach, allowing for comparison between the two methodologies.

2. **Protocol-Driven Simulation**: We use YAML files to record treatment protocols, keeping them separate from the simulation engine. This approach allows for easy modification and testing of different protocols without changing the core simulation logic.

3. **Flexible Business Logic**: We aim to abstract decision-making processes into pluggable functions, allowing for easy modification and experimentation with different decision-making strategies.

4. **Visualization Capabilities**: 
   - Individual simulation results for both DES and ABS approaches.
   - Comparison visualization between DES and ABS results, allowing for direct comparison of mean acuity over time.
   - Customizable visualizations with options for time ranges and patient subgroups.

5. **Data Analysis**: The simulation provides comprehensive summary statistics and analysis tools for evaluating treatment outcomes and patient responses.

## Future Goals

1. **Real-life Scenario Integration**: We aim to populate the decision-making process with data extracted from real-life scenarios, enhancing the simulation's accuracy and relevance to clinical practice.

2. **Enhanced Business Logic**: Further development of the abstraction for complex business logic, potentially using a plugin architecture for decision-making functions.

3. **Expanded Visualization and Analysis**: Continuous improvement of visualization and analysis tools to provide more insights from the simulation data.

This project serves as a powerful tool for researchers and clinicians to model, visualize, and analyze different AMD treatment protocols, comparing outcomes between discrete event and agent-based simulation approaches.
