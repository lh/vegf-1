#!/usr/bin/env python3
"""
Script to update the main Simulations page to include cost tracking support.

This adds cost tracking as an optional feature without breaking existing functionality.
"""

import sys
from pathlib import Path

def update_simulations_page():
    """Update the main simulations page to support cost tracking."""
    
    simulations_file = Path("pages/2_Simulations.py")
    
    if not simulations_file.exists():
        print(f"Error: {simulations_file} not found")
        return False
        
    # Read the file
    with open(simulations_file, 'r') as f:
        content = f.read()
    
    # Make the updates
    updates = [
        # Update imports to include cost-aware components
        {
            'find': 'from ape.components.simulation_ui_v2 import (\n    render_enhanced_parameter_inputs, render_preset_buttons_v2,\n    calculate_runtime_estimate_v2\n)',
            'replace': '''from ape.components.simulation_ui_v2 import (
    render_preset_buttons_v2,
    calculate_runtime_estimate_v2
)
# Import cost-aware version if available, fallback to standard
try:
    from ape.components.simulation_ui_v2_with_costs import (
        render_enhanced_parameter_inputs_with_costs as render_enhanced_parameter_inputs
    )
    COST_TRACKING_AVAILABLE = True
except ImportError:
    from ape.components.simulation_ui_v2 import render_enhanced_parameter_inputs
    COST_TRACKING_AVAILABLE = False'''
        },
        
        # Update parameter collection to handle cost config
        {
            'find': '# Get parameters - always need them for running simulation\nengine_type, recruitment_params, seed = render_enhanced_parameter_inputs()',
            'replace': '''# Get parameters - always need them for running simulation
if COST_TRACKING_AVAILABLE:
    params_result = render_enhanced_parameter_inputs()
    if len(params_result) == 4:
        engine_type, recruitment_params, seed, cost_config = params_result
    else:
        engine_type, recruitment_params, seed = params_result
        cost_config = None
else:
    engine_type, recruitment_params, seed = render_enhanced_parameter_inputs()
    cost_config = None'''
        },
        
        # Store cost config in session state
        {
            'find': '    # Store parameters for the simulation run\n    st.session_state.recruitment_params = recruitment_params',
            'replace': '''    # Store parameters for the simulation run
    st.session_state.recruitment_params = recruitment_params
    if COST_TRACKING_AVAILABLE and 'cost_config' in locals():
        st.session_state.cost_config = cost_config'''
        },
        
        # Retrieve cost config after rerun
        {
            'find': '    # Retrieve recruitment parameters\n    recruitment_params = st.session_state.get(\'recruitment_params\', {',
            'replace': '''    # Retrieve parameters
    recruitment_params = st.session_state.get('recruitment_params', {'''
        },
        
        # Add cost config retrieval
        {
            'find': '    })\n    \n    # Get runtime estimate',
            'replace': '''    })
    
    cost_config = st.session_state.get('cost_config') if COST_TRACKING_AVAILABLE else None
    
    # Get runtime estimate'''
        },
        
        # Update runner creation
        {
            'find': '        progress_bar.progress(5)\n        status_text.caption("Initializing...")\n        runner = SimulationRunner(spec)',
            'replace': '''        progress_bar.progress(5)
        status_text.caption("Initializing...")
        
        # Create runner with cost configuration if available
        if COST_TRACKING_AVAILABLE and cost_config and cost_config.get('enabled'):
            try:
                from ape.core.simulation_runner_with_costs import SimulationRunnerWithCosts
                from simulation_v2.economics.cost_config import CostConfig
                cost_config_obj = cost_config['cost_config']
                runner = SimulationRunnerWithCosts(spec, cost_config_obj)
            except Exception as e:
                st.warning(f"Cost tracking unavailable: {e}")
                from ape.core.simulation_runner import SimulationRunner
                runner = SimulationRunner(spec)
                cost_config = None
        else:
            from ape.core.simulation_runner import SimulationRunner
            runner = SimulationRunner(spec)'''
        },
        
        # Update simulation run calls to include drug type
        {
            'find': '''            results = runner.run(
                engine_type=recruitment_params['engine_type'],
                n_patients=recruitment_params['n_patients'],
                duration_years=recruitment_params['duration_years'],
                seed=recruitment_params['seed'],
                show_progress=False,  # We have our own progress bar
                recruitment_mode="Fixed Total"
            )''',
            'replace': '''            # Build run parameters
            run_params = {
                'engine_type': recruitment_params['engine_type'],
                'n_patients': recruitment_params['n_patients'],
                'duration_years': recruitment_params['duration_years'],
                'seed': recruitment_params['seed'],
                'show_progress': False,  # We have our own progress bar
                'recruitment_mode': "Fixed Total"
            }
            
            # Add drug type if cost tracking enabled
            if COST_TRACKING_AVAILABLE and cost_config and cost_config.get('enabled'):
                run_params['drug_type'] = cost_config.get('drug_type', 'eylea_2mg_biosimilar')
                
            results = runner.run(**run_params)'''
        },
        
        # Similar update for constant rate mode
        {
            'find': '''            results = runner.run(
                engine_type=recruitment_params['engine_type'],
                n_patients=expected_total,  # Use expected total
                duration_years=recruitment_params['duration_years'],
                seed=recruitment_params['seed'],
                show_progress=False,  # We have our own progress bar
                recruitment_mode="Constant Rate",
                patient_arrival_rate=recruitment_params['recruitment_rate']
            )''',
            'replace': '''            # Build run parameters
            run_params = {
                'engine_type': recruitment_params['engine_type'],
                'n_patients': expected_total,  # Use expected total
                'duration_years': recruitment_params['duration_years'],
                'seed': recruitment_params['seed'],
                'show_progress': False,  # We have our own progress bar
                'recruitment_mode': "Constant Rate",
                'patient_arrival_rate': recruitment_params['recruitment_rate']
            }
            
            # Add drug type if cost tracking enabled
            if COST_TRACKING_AVAILABLE and cost_config and cost_config.get('enabled'):
                run_params['drug_type'] = cost_config.get('drug_type', 'eylea_2mg_biosimilar')
                
            results = runner.run(**run_params)'''
        },
        
        # Add cost tracking to simulation data
        {
            'find': '''            'audit_trail': runner.audit_log  # Add audit trail to simulation data
        }''',
            'replace': '''            'audit_trail': runner.audit_log,  # Add audit trail to simulation data
            'cost_tracking': cost_config if COST_TRACKING_AVAILABLE and cost_config and cost_config.get('enabled') else None
        }'''
        },
        
        # Update success message
        {
            'find': '        # Simple success message\n        st.success(f"Simulation completed in {runtime:.1f} seconds")',
            'replace': '''        # Simple success message
        success_msg = f"Simulation completed in {runtime:.1f} seconds"
        if COST_TRACKING_AVAILABLE and cost_config and cost_config.get('enabled'):
            success_msg += " with cost tracking"
        st.success(success_msg)'''
        }
    ]
    
    # Apply updates
    modified_content = content
    for update in updates:
        if update['find'] in modified_content:
            modified_content = modified_content.replace(update['find'], update['replace'])
            print(f"✅ Applied update: {update['find'][:50]}...")
        else:
            print(f"❌ Could not find: {update['find'][:50]}...")
    
    # Create backup
    backup_file = simulations_file.with_suffix('.py.backup')
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"\n✅ Created backup: {backup_file}")
    
    # Write updated file
    with open(simulations_file, 'w') as f:
        f.write(modified_content)
    print(f"✅ Updated: {simulations_file}")
    
    return True


if __name__ == "__main__":
    print("Updating Simulations page to support cost tracking...")
    if update_simulations_page():
        print("\n✅ Successfully updated Simulations page!")
        print("\nThe page now supports cost tracking as an optional feature.")
        print("Cost tracking will be available when the cost UI components are present.")
    else:
        print("\n❌ Failed to update Simulations page")