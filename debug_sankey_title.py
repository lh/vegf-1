#!/usr/bin/env python3
"""Debug why Sankey title shows undefined."""
from pathlib import Path
from ape.core.results.factory import ResultsFactory
from ape.components.treatment_patterns.pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals
from ape.components.treatment_patterns.sankey_builder_enhanced import create_enhanced_sankey_with_terminals

# Load aged-lab simulation
results_dir = Path("simulation_results")
aged_lab = None
for sim in results_dir.glob("*aged-lab*"):
    if sim.is_dir():
        aged_lab = sim
        break

if aged_lab:
    print(f"Loading {aged_lab.name}")
    results = ResultsFactory.load_results(aged_lab)
    
    print(f"\nResults object type: {type(results)}")
    print(f"Has metadata: {hasattr(results, 'metadata')}")
    if hasattr(results, 'metadata'):
        print(f"Metadata type: {type(results.metadata)}")
        print(f"Has memorable_name: {hasattr(results.metadata, 'memorable_name')}")
        if hasattr(results.metadata, 'memorable_name'):
            print(f"Memorable name value: {results.metadata.memorable_name}")
    
    # Extract patterns
    transitions_df, visits_df = extract_treatment_patterns_with_terminals(results)
    
    # Create Sankey  
    print("\nCreating Sankey with results object...")
    fig = create_enhanced_sankey_with_terminals(transitions_df, results)
    
    # Check the title
    print(f"\nFigure layout title: {fig.layout.title}")
    if fig.layout.title:
        print(f"Title text: {fig.layout.title.text}")
else:
    print("Could not find aged-lab simulation")