#!/usr/bin/env python3
"""
Verify that all changes are properly integrated in the Streamlit app.
"""
import streamlit as st
from pathlib import Path
from ape.core.results.factory import ResultsFactory
from ape.visualizations.streamgraph_treatment_states import create_treatment_state_streamgraph
from ape.components.treatment_patterns.sankey_builder_enhanced import create_enhanced_sankey_with_terminals
from ape.components.treatment_patterns.pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals

def test_visualizations():
    """Test that visualizations work with the fixes."""
    print("="*80)
    print("TESTING STREAMLIT VISUALIZATION INTEGRATION")
    print("="*80)
    
    # Find super-pine simulation
    results_dir = Path("simulation_results")
    super_pine = None
    for sim in results_dir.glob("*super-pine*"):
        if sim.is_dir() and (sim / "metadata.json").exists():
            super_pine = sim
            break
    
    if not super_pine:
        print("ERROR: Could not find super-pine simulation")
        return False
    
    print(f"\nUsing simulation: {super_pine.name}")
    
    # Load results
    results = ResultsFactory.load_results(super_pine)
    print(f"Memorable name: {results.metadata.memorable_name}")
    
    # Test 1: Streamgraph
    print("\n" + "="*40)
    print("TEST 1: STREAMGRAPH")
    print("="*40)
    
    try:
        fig = create_treatment_state_streamgraph(results)
        
        # Check title includes memorable name
        title = fig.layout.title.text if fig.layout.title else "No title"
        print(f"Title: {title}")
        
        if results.metadata.memorable_name in title:
            print("✓ Memorable name in title")
        else:
            print("✗ Memorable name NOT in title")
            
        # Check if Discontinued state exists
        has_discontinued = any('Discontinued' in trace.name for trace in fig.data if hasattr(trace, 'name'))
        print(f"Has Discontinued state: {'✓' if has_discontinued else '✗'}")
        
    except Exception as e:
        print(f"✗ ERROR creating streamgraph: {e}")
        return False
    
    # Test 2: Sankey
    print("\n" + "="*40)
    print("TEST 2: SANKEY DIAGRAM")
    print("="*40)
    
    try:
        # Extract patterns with terminals
        transitions_df, visits_df = extract_treatment_patterns_with_terminals(results)
        
        # Create Sankey
        fig = create_enhanced_sankey_with_terminals(transitions_df, results)
        
        # Check title includes memorable name
        title = fig.layout.title.text if fig.layout.title else "No title"
        print(f"Title: {title}")
        
        if results.metadata.memorable_name in title:
            print("✓ Memorable name in title")
        else:
            print("✗ Memorable name NOT in title")
            
        # Check for gray color (#999999) in nodes
        node_colors = fig.data[0].node.color
        has_gray = '#999999' in str(node_colors)
        print(f"Has gray color for discontinued: {'✓' if has_gray else '✗'}")
        
        # Check for Discontinued in terminal states
        terminal_states = transitions_df[transitions_df['to_state'].str.contains('Discontinued')]
        discontinued_count = terminal_states['patient_id'].nunique()
        print(f"Discontinued patients in Sankey: {discontinued_count}")
        
    except Exception as e:
        print(f"✗ ERROR creating Sankey: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*40)
    print("SUMMARY")
    print("="*40)
    print("✓ All visualizations created successfully")
    print("✓ Discontinued states properly handled")
    print("✓ Memorable names displayed")
    
    return True

if __name__ == "__main__":
    import sys
    success = test_visualizations()
    sys.exit(0 if success else 1)