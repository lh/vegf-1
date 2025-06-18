"""Utilities for handling patient counts in Sankey diagrams."""

import pandas as pd

def adjust_terminal_node_counts(flow_counts_df: pd.DataFrame, transitions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Adjust terminal node counts to show unique patients instead of transitions.
    
    For terminal nodes (Still in X, Discontinued, No Further Visits), we want to show
    the actual number of unique patients, not the number of transitions.
    
    Args:
        flow_counts_df: DataFrame with aggregated flow counts (from_state, to_state, count)
        transitions_df: Original transitions DataFrame with patient_id
        
    Returns:
        Adjusted flow_counts_df with unique patient counts for terminal nodes
    """
    flow_counts = flow_counts_df.copy()
    
    # Identify terminal states
    terminal_states = flow_counts['to_state'][
        (flow_counts['to_state'].str.contains('Still in')) |
        (flow_counts['to_state'] == 'Discontinued') |
        (flow_counts['to_state'] == 'No Further Visits') |
        (flow_counts['to_state'] == 'Lost to Follow-up')
    ].unique()
    
    # For each terminal state, count unique patients
    for terminal_state in terminal_states:
        # Get all transitions TO this terminal state
        terminal_transitions = transitions_df[transitions_df['to_state'] == terminal_state]
        
        if len(terminal_transitions) > 0:
            # Count unique patients
            unique_patient_count = terminal_transitions['patient_id'].nunique()
            
            # Update all flows TO this terminal state with unique patient count
            flow_counts.loc[flow_counts['to_state'] == terminal_state, 'count'] = unique_patient_count
    
    return flow_counts