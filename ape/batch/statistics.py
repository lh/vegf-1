"""
Summary statistics for batch simulations.

Provides utilities to calculate summary statistics across multiple
simulation runs, including mean/SD of outcomes and comparison metrics.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

from ape.core.results.factory import ResultsFactory


def load_batch_results(batch_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load all simulation results from a batch.

    Args:
        batch_summary: Batch summary dictionary with simulation_ids

    Returns:
        Dictionary mapping sim_id to results object
    """
    results_dict = {}

    for sim_id in batch_summary['simulation_ids']:
        try:
            sim_path = ResultsFactory.DEFAULT_RESULTS_DIR / sim_id
            results = ResultsFactory.load_results(sim_path)
            results_dict[sim_id] = results
        except Exception as e:
            print(f"Warning: Could not load {sim_id}: {e}")

    return results_dict


def calculate_outcome_statistics(results_dict: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Calculate summary statistics for each protocol's outcomes.

    Args:
        results_dict: Dictionary mapping sim_id to results object

    Returns:
        Dictionary with statistics per simulation
    """
    stats = {}

    for sim_id, results in results_dict.items():
        try:
            patients_df = results.get_patients_df()

            # Calculate key metrics
            stats[sim_id] = {
                'n_patients': len(patients_df),
                'mean_final_vision': patients_df['final_vision'].mean(),
                'std_final_vision': patients_df['final_vision'].std(),
                'mean_baseline_vision': patients_df['baseline_vision'].mean(),
                'std_baseline_vision': patients_df['baseline_vision'].std(),
                'mean_vision_change': (patients_df['final_vision'] - patients_df['baseline_vision']).mean(),
                'std_vision_change': (patients_df['final_vision'] - patients_df['baseline_vision']).std(),
                'discontinuation_rate': patients_df['discontinued'].mean() * 100,
                'vision_maintained_pct': ((patients_df['final_vision'] - patients_df['baseline_vision']) >= -5).mean() * 100,
                'vision_improved_pct': ((patients_df['final_vision'] - patients_df['baseline_vision']) > 5).mean() * 100,
                'mean_total_injections': patients_df['total_injections'].mean() if 'total_injections' in patients_df.columns else None,
                'std_total_injections': patients_df['total_injections'].std() if 'total_injections' in patients_df.columns else None,
            }
        except Exception as e:
            print(f"Warning: Could not calculate statistics for {sim_id}: {e}")
            stats[sim_id] = {}

    return stats


def calculate_protocol_comparison(
    batch_summary: Dict[str, Any],
    stats: Dict[str, Dict[str, float]]
) -> pd.DataFrame:
    """
    Create a comparison table of protocols.

    Args:
        batch_summary: Batch summary with protocol names
        stats: Statistics dictionary from calculate_outcome_statistics

    Returns:
        DataFrame with protocol comparison
    """
    protocols = batch_summary['protocols']
    sim_ids = batch_summary['simulation_ids']

    comparison_data = []

    for protocol, sim_id in zip(protocols, sim_ids):
        if sim_id in stats:
            row = {
                'Protocol': protocol,
                'Simulation ID': sim_id,
                **stats[sim_id]
            }
            comparison_data.append(row)

    df = pd.DataFrame(comparison_data)

    # Reorder columns for better readability
    col_order = [
        'Protocol',
        'Simulation ID',
        'n_patients',
        'mean_baseline_vision',
        'mean_final_vision',
        'mean_vision_change',
        'std_vision_change',
        'discontinuation_rate',
        'vision_maintained_pct',
        'vision_improved_pct'
    ]

    # Include only columns that exist
    col_order = [c for c in col_order if c in df.columns]
    other_cols = [c for c in df.columns if c not in col_order]

    return df[col_order + other_cols]


def calculate_discontinuation_breakdown(results_dict: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate discontinuation reasons breakdown for each simulation.

    Args:
        results_dict: Dictionary mapping sim_id to results object

    Returns:
        Dictionary with discontinuation breakdowns
    """
    breakdowns = {}

    for sim_id, results in results_dict.items():
        try:
            patients_df = results.get_patients_df()

            # Get discontinued patients
            discontinued = patients_df[patients_df['discontinued'] == True]

            if len(discontinued) == 0:
                breakdowns[sim_id] = {
                    'total_discontinued': 0,
                    'reasons': {}
                }
                continue

            # Count by reason
            if 'discontinuation_reason' in discontinued.columns:
                reason_counts = discontinued['discontinuation_reason'].value_counts().to_dict()
            else:
                reason_counts = {'unknown': len(discontinued)}

            breakdowns[sim_id] = {
                'total_discontinued': len(discontinued),
                'total_patients': len(patients_df),
                'discontinuation_rate': len(discontinued) / len(patients_df) * 100,
                'reasons': reason_counts
            }
        except Exception as e:
            print(f"Warning: Could not calculate discontinuation breakdown for {sim_id}: {e}")
            breakdowns[sim_id] = {'total_discontinued': 0, 'reasons': {}}

    return breakdowns


def export_batch_statistics(batch_id: str, output_path: Optional[Path] = None) -> Path:
    """
    Export complete batch statistics to CSV files.

    Args:
        batch_id: Batch identifier
        output_path: Optional output directory (defaults to batch directory)

    Returns:
        Path to output directory
    """
    from ape.batch.status import get_batch_dir, BatchStatus

    batch_dir = get_batch_dir(batch_id)
    status_mgr = BatchStatus(batch_dir)

    summary = status_mgr.read_summary()
    if not summary:
        raise ValueError(f"No summary found for batch {batch_id}")

    # Load results
    results_dict = load_batch_results(summary)

    # Calculate statistics
    stats = calculate_outcome_statistics(results_dict)
    comparison_df = calculate_protocol_comparison(summary, stats)
    discontinuation = calculate_discontinuation_breakdown(results_dict)

    # Determine output location
    if output_path is None:
        output_path = batch_dir / "analysis"
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    # Export comparison table
    comparison_path = output_path / "protocol_comparison.csv"
    comparison_df.to_csv(comparison_path, index=False)

    # Export discontinuation breakdown
    disc_data = []
    for sim_id, data in discontinuation.items():
        for reason, count in data.get('reasons', {}).items():
            disc_data.append({
                'simulation_id': sim_id,
                'reason': reason,
                'count': count,
                'percentage': count / data['total_discontinued'] * 100 if data['total_discontinued'] > 0 else 0
            })

    disc_df = pd.DataFrame(disc_data)
    disc_path = output_path / "discontinuation_breakdown.csv"
    disc_df.to_csv(disc_path, index=False)

    print(f"Exported batch statistics to {output_path}")
    return output_path


def get_batch_summary_text(batch_id: str) -> str:
    """
    Generate a text summary of batch results.

    Args:
        batch_id: Batch identifier

    Returns:
        Formatted text summary
    """
    from ape.batch.status import get_batch_dir, BatchStatus

    batch_dir = get_batch_dir(batch_id)
    status_mgr = BatchStatus(batch_dir)

    summary = status_mgr.read_summary()
    if not summary:
        return f"No summary found for batch {batch_id}"

    results_dict = load_batch_results(summary)
    stats = calculate_outcome_statistics(results_dict)

    lines = [
        f"Batch Summary: {batch_id}",
        "=" * 60,
        f"Completed: {summary['completed_at']}",
        f"Parameters: {summary['parameters']['n_patients']} patients × {summary['parameters']['duration_years']} years",
        f"Random Seed: {summary['parameters']['seed']}",
        "",
        "Protocol Comparison:",
        "-" * 60
    ]

    for protocol, sim_id in zip(summary['protocols'], summary['simulation_ids']):
        if sim_id in stats:
            s = stats[sim_id]
            lines.extend([
                f"\n{protocol}:",
                f"  Simulation ID: {sim_id}",
                f"  Patients: {s['n_patients']}",
                f"  Mean Final Vision: {s['mean_final_vision']:.1f} ± {s['std_final_vision']:.1f} letters",
                f"  Mean Vision Change: {s['mean_vision_change']:.1f} ± {s['std_vision_change']:.1f} letters",
                f"  Discontinuation Rate: {s['discontinuation_rate']:.1f}%",
                f"  Vision Maintained (>=-5): {s['vision_maintained_pct']:.1f}%",
                f"  Vision Improved (>5): {s['vision_improved_pct']:.1f}%",
            ])

            if s['mean_total_injections'] is not None:
                lines.append(f"  Mean Injections: {s['mean_total_injections']:.1f} ± {s['std_total_injections']:.1f}")

    return "\n".join(lines)
