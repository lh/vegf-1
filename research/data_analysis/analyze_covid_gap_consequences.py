"""
Analyze COVID-Era Treatment Gap Consequences

This script synthesizes the existing analyses to quantify the real-world impact
of treatment gaps during COVID-19, providing evidence-based parameters for
modeling unintended discontinuations and their consequences.
"""

import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import seaborn as sns
from scipy import stats

# Set up output directory
output_dir = Path("output/analysis_results")
output_dir.mkdir(exist_ok=True, parents=True)

# Database path
DB_PATH = "output/eylea_intervals.db"

# Key thresholds from existing analyses
REGULAR_TREATMENT_THRESHOLD = 90  # days - defines "regular" treatment
SHORT_GAP_THRESHOLD = 180  # 6 months - unplanned but recoverable
LONG_GAP_THRESHOLD = 365   # 1 year - significant disruption
NATURAL_DISCONTINUATION_THRESHOLD = 800  # ~2.2 years - from PCA analysis

def connect_to_db() -> sqlite3.Connection:
    """Connect to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def load_interval_data() -> pl.DataFrame:
    """Load the interval_va_data table into a Polars DataFrame."""
    conn = connect_to_db()
    
    # Use Polars to read from SQLite
    query = "SELECT * FROM interval_va_data"
    df = pl.read_database(query=query, connection=conn)
    
    # Convert date strings to datetime objects
    df = df.with_columns([
        pl.col("previous_date").str.to_datetime("%Y-%m-%d"),
        pl.col("current_date").str.to_datetime("%Y-%m-%d")
    ])
    
    conn.close()
    return df

def categorize_gaps(interval_data: pl.DataFrame) -> Dict:
    """
    Categorize treatment gaps into different types based on duration
    and calculate VA consequences for each category.
    """
    results = {
        'regular': {'intervals': [], 'va_changes': [], 'count': 0},
        'short_gap': {'intervals': [], 'va_changes': [], 'count': 0},
        'long_gap': {'intervals': [], 'va_changes': [], 'count': 0},
        'discontinuation': {'intervals': [], 'va_changes': [], 'count': 0}
    }
    
    # Process each interval
    for row in interval_data.iter_rows(named=True):
        interval = row['interval_days']
        va_before = row['prev_va']
        va_after = row['current_va']
        
        # Skip if data is missing
        if interval is None or va_before is None or va_after is None:
            continue
            
        va_change = va_after - va_before
        
        # Categorize based on interval length
        if interval <= REGULAR_TREATMENT_THRESHOLD:
            category = 'regular'
        elif interval <= SHORT_GAP_THRESHOLD:
            category = 'short_gap'
        elif interval <= LONG_GAP_THRESHOLD:
            category = 'long_gap'
        else:
            category = 'discontinuation'
        
        results[category]['intervals'].append(interval)
        results[category]['va_changes'].append(va_change)
        results[category]['count'] += 1
    
    # Calculate statistics for each category
    for category in results:
        if results[category]['va_changes']:
            va_changes = np.array(results[category]['va_changes'])
            results[category]['mean_va_change'] = np.mean(va_changes)
            results[category]['median_va_change'] = np.median(va_changes)
            results[category]['std_va_change'] = np.std(va_changes)
            results[category]['ci_95'] = stats.t.interval(
                0.95, len(va_changes)-1, 
                loc=np.mean(va_changes), 
                scale=stats.sem(va_changes)
            )
            
            intervals = np.array(results[category]['intervals'])
            results[category]['mean_interval'] = np.mean(intervals)
            results[category]['median_interval'] = np.median(intervals)
        else:
            results[category]['mean_va_change'] = 0
            results[category]['median_va_change'] = 0
            results[category]['std_va_change'] = 0
            results[category]['ci_95'] = (0, 0)
            results[category]['mean_interval'] = 0
            results[category]['median_interval'] = 0
    
    return results

def analyze_recovery_patterns(interval_data: pl.DataFrame) -> Dict:
    """
    Analyze recovery patterns after different types of gaps.
    Look at VA trajectory after patients return from gaps.
    """
    # Create patient-eye identifier
    interval_data = interval_data.with_columns([
        (pl.col("uuid") + "_" + pl.col("eye")).alias("patient_eye_id")
    ])
    
    recovery_patterns = {
        'short_gap_recovery': [],
        'long_gap_recovery': [],
        'discontinuation_recovery': []
    }
    
    # Process each patient
    for patient_eye_id in interval_data.select("patient_eye_id").unique().to_series():
        patient_data = interval_data.filter(
            pl.col("patient_eye_id") == patient_eye_id
        ).sort("previous_date")
        
        if len(patient_data) < 3:  # Need at least 3 visits to analyze recovery
            continue
        
        # Look for gaps and subsequent recovery
        for i in range(len(patient_data) - 2):
            interval = patient_data[i, "interval_days"]
            
            if interval is None:
                continue
            
            # Identify gap type
            if SHORT_GAP_THRESHOLD < interval <= LONG_GAP_THRESHOLD:
                gap_type = 'short_gap_recovery'
            elif LONG_GAP_THRESHOLD < interval <= NATURAL_DISCONTINUATION_THRESHOLD:
                gap_type = 'long_gap_recovery'
            elif interval > NATURAL_DISCONTINUATION_THRESHOLD:
                gap_type = 'discontinuation_recovery'
            else:
                continue
            
            # Get VA values
            va_before_gap = patient_data[i, "prev_va"]
            va_after_gap = patient_data[i, "current_va"]
            va_next_visit = patient_data[i+1, "current_va"] if i+1 < len(patient_data) else None
            
            if all(v is not None for v in [va_before_gap, va_after_gap, va_next_visit]):
                recovery_patterns[gap_type].append({
                    'interval': interval,
                    'va_before_gap': va_before_gap,
                    'va_after_gap': va_after_gap,
                    'va_next_visit': va_next_visit,
                    'immediate_loss': va_after_gap - va_before_gap,
                    'recovery': va_next_visit - va_after_gap,
                    'net_change': va_next_visit - va_before_gap
                })
    
    return recovery_patterns

def calculate_time_dependent_risk(interval_data: pl.DataFrame) -> Dict:
    """
    Calculate VA loss risk as a function of gap duration,
    similar to Aslanis recurrence curve but for unplanned gaps.
    """
    # Group intervals into time bins
    time_bins = [
        (0, 90, "0-3 months"),
        (90, 180, "3-6 months"),
        (180, 365, "6-12 months"),
        (365, 730, "1-2 years"),
        (730, float('inf'), "2+ years")
    ]
    
    risk_by_duration = {}
    
    for min_days, max_days, label in time_bins:
        # Filter intervals in this bin
        bin_data = interval_data.filter(
            (pl.col("interval_days") > min_days) & 
            (pl.col("interval_days") <= max_days)
        )
        
        # Calculate VA changes
        va_changes = []
        for row in bin_data.iter_rows(named=True):
            if row['prev_va'] is not None and row['current_va'] is not None:
                va_changes.append(row['current_va'] - row['prev_va'])
        
        if va_changes:
            risk_by_duration[label] = {
                'mean_va_loss': -np.mean(va_changes),  # Convert to loss (positive number)
                'median_va_loss': -np.median(va_changes),
                'percent_losing_5_letters': sum(1 for vc in va_changes if vc <= -5) / len(va_changes) * 100,
                'percent_losing_10_letters': sum(1 for vc in va_changes if vc <= -10) / len(va_changes) * 100,
                'percent_losing_15_letters': sum(1 for vc in va_changes if vc <= -15) / len(va_changes) * 100,
                'sample_size': len(va_changes)
            }
        else:
            risk_by_duration[label] = {
                'mean_va_loss': 0,
                'median_va_loss': 0,
                'percent_losing_5_letters': 0,
                'percent_losing_10_letters': 0,
                'percent_losing_15_letters': 0,
                'sample_size': 0
            }
    
    return risk_by_duration

def create_gap_consequence_model(gap_analysis: Dict, recovery_patterns: Dict, 
                                time_risk: Dict) -> Dict:
    """
    Create a comprehensive model of gap consequences for simulation parameters.
    """
    model = {
        'gap_categories': {
            'regular_treatment': {
                'interval_range': (0, 90),
                'mean_interval': gap_analysis['regular']['mean_interval'],
                'mean_va_change_per_interval': gap_analysis['regular']['mean_va_change'],
                'annual_va_change': gap_analysis['regular']['mean_va_change'] * (365 / gap_analysis['regular']['mean_interval']),
                'sample_size': gap_analysis['regular']['count']
            },
            'short_unplanned_gap': {
                'interval_range': (90, 180),
                'mean_interval': gap_analysis['short_gap']['mean_interval'],
                'mean_va_loss': -gap_analysis['short_gap']['mean_va_change'],
                'recovery_potential': np.mean([r['recovery'] for r in recovery_patterns['short_gap_recovery']]) if recovery_patterns['short_gap_recovery'] else 0,
                'net_impact': np.mean([r['net_change'] for r in recovery_patterns['short_gap_recovery']]) if recovery_patterns['short_gap_recovery'] else gap_analysis['short_gap']['mean_va_change'],
                'sample_size': gap_analysis['short_gap']['count']
            },
            'long_unplanned_gap': {
                'interval_range': (180, 365),
                'mean_interval': gap_analysis['long_gap']['mean_interval'],
                'mean_va_loss': -gap_analysis['long_gap']['mean_va_change'],
                'recovery_potential': np.mean([r['recovery'] for r in recovery_patterns['long_gap_recovery']]) if recovery_patterns['long_gap_recovery'] else 0,
                'net_impact': np.mean([r['net_change'] for r in recovery_patterns['long_gap_recovery']]) if recovery_patterns['long_gap_recovery'] else gap_analysis['long_gap']['mean_va_change'],
                'sample_size': gap_analysis['long_gap']['count']
            },
            'effective_discontinuation': {
                'interval_range': (365, 800),
                'mean_interval': gap_analysis['discontinuation']['mean_interval'],
                'mean_va_loss': -gap_analysis['discontinuation']['mean_va_change'],
                'recovery_potential': np.mean([r['recovery'] for r in recovery_patterns['discontinuation_recovery']]) if recovery_patterns['discontinuation_recovery'] else 0,
                'net_impact': np.mean([r['net_change'] for r in recovery_patterns['discontinuation_recovery']]) if recovery_patterns['discontinuation_recovery'] else gap_analysis['discontinuation']['mean_va_change'],
                'sample_size': gap_analysis['discontinuation']['count']
            }
        },
        'time_dependent_risk': time_risk,
        'key_findings': {
            'covid_gap_prevalence': (gap_analysis['short_gap']['count'] + gap_analysis['long_gap']['count']) / sum(cat['count'] for cat in gap_analysis.values()) * 100,
            'mean_va_loss_per_month_untreated': -gap_analysis['long_gap']['mean_va_change'] / (gap_analysis['long_gap']['mean_interval'] / 30) if gap_analysis['long_gap']['mean_interval'] > 0 else 0,
            'recovery_rate_after_short_gap': len([r for r in recovery_patterns['short_gap_recovery'] if r['recovery'] > 0]) / len(recovery_patterns['short_gap_recovery']) * 100 if recovery_patterns['short_gap_recovery'] else 0,
            'recovery_rate_after_long_gap': len([r for r in recovery_patterns['long_gap_recovery'] if r['recovery'] > 0]) / len(recovery_patterns['long_gap_recovery']) * 100 if recovery_patterns['long_gap_recovery'] else 0
        }
    }
    
    return model

def visualize_gap_consequences(model: Dict, output_dir: Path):
    """Create visualizations of gap consequences."""
    
    # 1. VA loss by gap duration
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Extract data for plotting
    categories = []
    mean_losses = []
    sample_sizes = []
    
    for cat_name, cat_data in model['gap_categories'].items():
        if 'mean_va_loss' in cat_data:
            categories.append(cat_name.replace('_', ' ').title())
            mean_losses.append(cat_data['mean_va_loss'])
            sample_sizes.append(cat_data['sample_size'])
    
    # Bar plot of mean VA loss
    bars = ax1.bar(categories, mean_losses, color=['green', 'yellow', 'orange', 'red'])
    ax1.set_ylabel('Mean VA Loss (letters)')
    ax1.set_title('Visual Acuity Loss by Gap Type')
    ax1.grid(True, alpha=0.3)
    
    # Add sample sizes as labels
    for bar, n in zip(bars, sample_sizes):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'n={n}', ha='center', va='bottom')
    
    # 2. Time-dependent risk curve
    time_labels = []
    mean_losses_time = []
    
    for period, data in model['time_dependent_risk'].items():
        time_labels.append(period)
        mean_losses_time.append(data['mean_va_loss'])
    
    ax2.plot(range(len(time_labels)), mean_losses_time, 'o-', linewidth=2, markersize=8)
    ax2.set_xticks(range(len(time_labels)))
    ax2.set_xticklabels(time_labels, rotation=45)
    ax2.set_ylabel('Mean VA Loss (letters)')
    ax2.set_title('VA Loss Risk Over Time')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'covid_gap_consequences.png', dpi=300)
    plt.close()

def main():
    """Main analysis function."""
    print("Loading interval data...")
    interval_data = load_interval_data()
    
    print("Categorizing gaps and calculating consequences...")
    gap_analysis = categorize_gaps(interval_data)
    
    print("Analyzing recovery patterns...")
    recovery_patterns = analyze_recovery_patterns(interval_data)
    
    print("Calculating time-dependent risk...")
    time_risk = calculate_time_dependent_risk(interval_data)
    
    print("Creating comprehensive gap consequence model...")
    model = create_gap_consequence_model(gap_analysis, recovery_patterns, time_risk)
    
    # Save the model
    with open(output_dir / 'covid_gap_consequence_model.json', 'w') as f:
        # Convert numpy types to Python types for JSON serialization
        def convert_to_serializable(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(convert_to_serializable(item) for item in obj)
            else:
                return obj
        
        serializable_model = convert_to_serializable(model)
        json.dump(serializable_model, f, indent=2)
    
    print("Creating visualizations...")
    visualize_gap_consequences(model, output_dir)
    
    # Print summary
    print("\n=== COVID Gap Consequence Analysis Summary ===")
    print(f"\nTotal intervals analyzed: {sum(cat['count'] for cat in gap_analysis.values())}")
    print(f"Regular treatment (<90 days): {gap_analysis['regular']['count']} ({gap_analysis['regular']['count']/sum(cat['count'] for cat in gap_analysis.values())*100:.1f}%)")
    print(f"Short gaps (90-180 days): {gap_analysis['short_gap']['count']} ({gap_analysis['short_gap']['count']/sum(cat['count'] for cat in gap_analysis.values())*100:.1f}%)")
    print(f"Long gaps (180-365 days): {gap_analysis['long_gap']['count']} ({gap_analysis['long_gap']['count']/sum(cat['count'] for cat in gap_analysis.values())*100:.1f}%)")
    print(f"Discontinuations (>365 days): {gap_analysis['discontinuation']['count']} ({gap_analysis['discontinuation']['count']/sum(cat['count'] for cat in gap_analysis.values())*100:.1f}%)")
    
    print("\n=== Mean VA Changes by Gap Type ===")
    for category, data in gap_analysis.items():
        if data['count'] > 0:
            print(f"{category}: {data['mean_va_change']:.2f} letters (n={data['count']})")
    
    print("\n=== Key Modeling Parameters ===")
    print(f"VA loss rate during gaps: {model['key_findings']['mean_va_loss_per_month_untreated']:.2f} letters/month")
    print(f"Recovery rate after short gaps: {model['key_findings']['recovery_rate_after_short_gap']:.1f}%")
    print(f"Recovery rate after long gaps: {model['key_findings']['recovery_rate_after_long_gap']:.1f}%")
    
    print("\nAnalysis complete. Results saved to:", output_dir)

if __name__ == "__main__":
    main()