"""
Analyze Inappropriate Clinical Discontinuations

This script specifically analyzes cases where patients were inappropriately
discontinued from treatment despite having good vision and being on regular
treatment schedules - reflecting clinical misunderstanding of AMD as a chronic disease.
"""

import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sqlite3
import json
from datetime import datetime, timedelta
import seaborn as sns

# Set up output directory
output_dir = Path("output/analysis_results")
output_dir.mkdir(exist_ok=True, parents=True)

# Database path
DB_PATH = "output/eylea_intervals.db"

def connect_to_db() -> sqlite3.Connection:
    """Connect to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def load_premature_discontinuation_data() -> pl.DataFrame:
    """Load the already identified premature discontinuation data."""
    # Try to load the CSV file created by identify_premature_discontinuations.py
    csv_path = output_dir / "all_premature_discontinuations.csv"
    if csv_path.exists():
        return pl.read_csv(csv_path)
    else:
        raise FileNotFoundError(f"Please run identify_premature_discontinuations.py first to generate {csv_path}")

def categorize_discontinuation_decisions(df: pl.DataFrame) -> pl.DataFrame:
    """
    Categorize premature discontinuations by likely clinical reasoning.
    """
    # Add categorization based on VA levels and timing
    df = df.with_columns([
        # Very good VA (>70 letters) - likely "patient doing too well" error
        pl.when(pl.col("current_va") > 70)
        .then(pl.lit("excellent_va_stop"))
        
        # Good VA (50-70 letters) at ~1 year - likely "course complete" error
        .when((pl.col("current_va").is_between(50, 70)) & 
              (pl.col("days_from_first_injection").is_between(300, 400)))
        .then(pl.lit("one_year_course_complete"))
        
        # Good VA (50-70 letters) early - likely "good enough" error
        .when((pl.col("current_va").is_between(50, 70)) & 
              (pl.col("days_from_first_injection") < 300))
        .then(pl.lit("early_good_enough"))
        
        # Moderate VA (35-50 letters) - likely "plateau" reasoning
        .when(pl.col("current_va").is_between(35, 50))
        .then(pl.lit("plateau_reasoning"))
        
        # Lower VA but >20 - unclear reasoning
        .otherwise(pl.lit("other_reasoning"))
        .alias("discontinuation_category")
    ])
    
    return df

def analyze_consequences_by_category(df: pl.DataFrame) -> dict:
    """
    Analyze VA outcomes by discontinuation category.
    """
    categories = df.select("discontinuation_category").unique().to_series().to_list()
    
    results = {}
    for category in categories:
        cat_data = df.filter(pl.col("discontinuation_category") == category)
        
        # Only analyze cases where we have VA change data
        cat_with_change = cat_data.filter(pl.col("va_change").is_not_null())
        
        if len(cat_with_change) > 0:
            results[category] = {
                "count": len(cat_data),
                "mean_va_at_stop": float(cat_data.select("current_va").mean().item()),
                "mean_interval_after": float(cat_data.select("next_interval").mean().item()),
                "mean_va_change": float(cat_with_change.select("va_change").mean().item()),
                "percent_losing_5_letters": len(cat_with_change.filter(pl.col("va_change") <= -5)) / len(cat_with_change) * 100,
                "percent_losing_10_letters": len(cat_with_change.filter(pl.col("va_change") <= -10)) / len(cat_with_change) * 100,
                "percent_losing_15_letters": len(cat_with_change.filter(pl.col("va_change") <= -15)) / len(cat_with_change) * 100
            }
        else:
            results[category] = {
                "count": len(cat_data),
                "mean_va_at_stop": float(cat_data.select("current_va").mean().item()),
                "mean_interval_after": float(cat_data.select("next_interval").mean().item()),
                "mean_va_change": None,
                "percent_losing_5_letters": None,
                "percent_losing_10_letters": None,
                "percent_losing_15_letters": None
            }
    
    return results

def identify_restart_patterns(df: pl.DataFrame) -> dict:
    """
    For patients who were prematurely discontinued, check if they restarted
    treatment and what triggered the restart.
    """
    # Load full interval data to trace what happened after discontinuation
    conn = connect_to_db()
    query = "SELECT * FROM interval_va_data"
    full_data = pl.read_database(query=query, connection=conn)
    conn.close()
    
    # Convert dates
    full_data = full_data.with_columns([
        pl.col("previous_date").str.to_datetime("%Y-%m-%d"),
        pl.col("current_date").str.to_datetime("%Y-%m-%d")
    ])
    
    restart_patterns = {
        "restarted": 0,
        "never_returned": 0,
        "va_at_restart": [],
        "time_to_restart": [],
        "va_loss_before_restart": []
    }
    
    # For each premature discontinuation, check subsequent history
    for row in df.iter_rows(named=True):
        patient_eye_id = row["patient_eye_id"]
        discontinuation_date = datetime.strptime(row["next_date"], "%Y-%m-%d")
        va_at_stop = row["current_va"]
        
        # Get all subsequent visits for this patient
        subsequent = full_data.filter(
            (pl.col("uuid") == row["uuid"]) & 
            (pl.col("eye") == row["eye"]) &
            (pl.col("current_date") > discontinuation_date)
        ).sort("current_date")
        
        if len(subsequent) > 0:
            # They restarted
            restart_patterns["restarted"] += 1
            
            # Get first visit after gap
            first_return = subsequent.row(0, named=True)
            va_at_restart = first_return["current_va"]
            days_to_restart = (first_return["current_date"] - discontinuation_date).days
            
            if va_at_restart is not None:
                restart_patterns["va_at_restart"].append(va_at_restart)
                restart_patterns["time_to_restart"].append(days_to_restart)
                restart_patterns["va_loss_before_restart"].append(va_at_restart - va_at_stop)
        else:
            restart_patterns["never_returned"] += 1
    
    return restart_patterns

def create_clinical_decision_visualizations(df: pl.DataFrame, category_results: dict, 
                                          restart_patterns: dict, output_dir: Path):
    """Create visualizations focused on clinical decision-making errors."""
    
    # 1. Distribution of discontinuation categories
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Category counts
    categories = list(category_results.keys())
    counts = [category_results[cat]["count"] for cat in categories]
    category_labels = [cat.replace("_", " ").title() for cat in categories]
    
    ax1.bar(category_labels, counts, color='steelblue', alpha=0.7)
    ax1.set_ylabel('Number of Cases')
    ax1.set_title('Types of Inappropriate Discontinuations')
    ax1.tick_params(axis='x', rotation=45)
    
    # Add count labels
    for i, (label, count) in enumerate(zip(category_labels, counts)):
        ax1.text(i, count + 1, str(count), ha='center')
    
    # 2. Mean VA at discontinuation by category
    mean_vas = [category_results[cat]["mean_va_at_stop"] for cat in categories]
    bars = ax2.bar(category_labels, mean_vas, color='green', alpha=0.7)
    ax2.set_ylabel('Mean VA at Stop (letters)')
    ax2.set_title('Vision Quality When Discontinued')
    ax2.tick_params(axis='x', rotation=45)
    ax2.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Driving standard')
    ax2.legend()
    
    # 3. VA outcomes by category
    mean_changes = [category_results[cat]["mean_va_change"] for cat in categories if category_results[cat]["mean_va_change"] is not None]
    valid_categories = [cat for cat in categories if category_results[cat]["mean_va_change"] is not None]
    valid_labels = [cat.replace("_", " ").title() for cat in valid_categories]
    
    if mean_changes:
        ax3.bar(valid_labels, mean_changes, color='red', alpha=0.7)
        ax3.set_ylabel('Mean VA Change (letters)')
        ax3.set_title('Vision Loss After Inappropriate Stop')
        ax3.tick_params(axis='x', rotation=45)
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    
    # 4. Restart patterns
    restart_data = ['Restarted\nTreatment', 'Never\nReturned']
    restart_counts = [restart_patterns["restarted"], restart_patterns["never_returned"]]
    
    ax4.pie(restart_counts, labels=restart_data, autopct='%1.1f%%', startangle=90)
    ax4.set_title('Patient Return After Inappropriate Stop')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'inappropriate_discontinuation_analysis.png', dpi=300)
    plt.close()
    
    # 2. Additional visualization: Time to restart vs VA loss
    if restart_patterns["time_to_restart"] and restart_patterns["va_loss_before_restart"]:
        plt.figure(figsize=(10, 6))
        plt.scatter(restart_patterns["time_to_restart"], 
                   restart_patterns["va_loss_before_restart"],
                   alpha=0.6, s=50)
        
        # Add trend line
        z = np.polyfit(restart_patterns["time_to_restart"], 
                      restart_patterns["va_loss_before_restart"], 1)
        p = np.poly1d(z)
        plt.plot(sorted(restart_patterns["time_to_restart"]), 
                p(sorted(restart_patterns["time_to_restart"])), 
                "r--", alpha=0.8)
        
        plt.xlabel('Days Until Treatment Restart')
        plt.ylabel('VA Loss Before Restart (letters)')
        plt.title('Vision Loss vs Time to Restart After Inappropriate Discontinuation')
        plt.grid(True, alpha=0.3)
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        plt.savefig(output_dir / 'restart_timing_va_loss.png', dpi=300)
        plt.close()

def create_clinical_guidance_summary(category_results: dict, restart_patterns: dict) -> dict:
    """
    Create a summary of findings to guide clinical education.
    """
    total_cases = sum(cat["count"] for cat in category_results.values())
    
    # Calculate restart statistics
    restart_rate = restart_patterns["restarted"] / (restart_patterns["restarted"] + 
                                                   restart_patterns["never_returned"]) * 100
    
    if restart_patterns["va_loss_before_restart"]:
        mean_va_loss_at_restart = np.mean(restart_patterns["va_loss_before_restart"])
        median_time_to_restart = np.median(restart_patterns["time_to_restart"])
    else:
        mean_va_loss_at_restart = None
        median_time_to_restart = None
    
    guidance = {
        "total_inappropriate_stops": total_cases,
        "clinical_error_patterns": {
            "excellent_va_stop": {
                "description": "Stopped because VA >70 letters ('too good to need treatment')",
                "frequency": category_results.get("excellent_va_stop", {}).get("count", 0),
                "mean_va_loss": category_results.get("excellent_va_stop", {}).get("mean_va_change", None),
                "key_message": "AMD requires ongoing treatment regardless of good vision"
            },
            "one_year_course_complete": {
                "description": "Stopped at ~1 year thinking 'course complete'",
                "frequency": category_results.get("one_year_course_complete", {}).get("count", 0),
                "mean_va_loss": category_results.get("one_year_course_complete", {}).get("mean_va_change", None),
                "key_message": "AMD is chronic - there is no 'course completion'"
            },
            "early_good_enough": {
                "description": "Stopped early with VA 50-70 letters ('good enough')",
                "frequency": category_results.get("early_good_enough", {}).get("count", 0),
                "mean_va_loss": category_results.get("early_good_enough", {}).get("mean_va_change", None),
                "key_message": "Stopping at 'good enough' vision leads to preventable loss"
            },
            "plateau_reasoning": {
                "description": "Stopped with moderate VA thinking 'plateau reached'",
                "frequency": category_results.get("plateau_reasoning", {}).get("count", 0),
                "mean_va_loss": category_results.get("plateau_reasoning", {}).get("mean_va_change", None),
                "key_message": "Plateaus require maintenance, not discontinuation"
            }
        },
        "patient_outcomes": {
            "restart_rate_percent": restart_rate,
            "never_returned_percent": 100 - restart_rate,
            "mean_va_loss_before_restart": mean_va_loss_at_restart,
            "median_days_to_restart": median_time_to_restart
        }
    }
    
    return guidance

def main():
    """Main analysis function."""
    print("Loading premature discontinuation data...")
    df = load_premature_discontinuation_data()
    
    print(f"Analyzing {len(df)} cases of premature discontinuation...")
    
    # Categorize discontinuations
    df = categorize_discontinuation_decisions(df)
    
    # Analyze consequences by category
    category_results = analyze_consequences_by_category(df)
    
    # Analyze restart patterns
    print("Analyzing restart patterns...")
    restart_patterns = identify_restart_patterns(df)
    
    # Create visualizations
    print("Creating visualizations...")
    create_clinical_decision_visualizations(df, category_results, restart_patterns, output_dir)
    
    # Create clinical guidance summary
    guidance = create_clinical_guidance_summary(category_results, restart_patterns)
    
    # Save results
    with open(output_dir / 'inappropriate_discontinuation_analysis.json', 'w') as f:
        json.dump({
            "category_results": category_results,
            "restart_patterns": {
                "restarted": restart_patterns["restarted"],
                "never_returned": restart_patterns["never_returned"],
                "restart_rate_percent": restart_patterns["restarted"] / 
                    (restart_patterns["restarted"] + restart_patterns["never_returned"]) * 100,
                "mean_va_at_restart": np.mean(restart_patterns["va_at_restart"]) if restart_patterns["va_at_restart"] else None,
                "mean_time_to_restart_days": np.mean(restart_patterns["time_to_restart"]) if restart_patterns["time_to_restart"] else None,
                "mean_va_loss_before_restart": np.mean(restart_patterns["va_loss_before_restart"]) if restart_patterns["va_loss_before_restart"] else None
            },
            "clinical_guidance": guidance
        }, f, indent=2)
    
    # Print summary
    print("\n=== Clinical Decision Error Analysis ===")
    print(f"Total inappropriate discontinuations: {len(df)}")
    print("\nBreakdown by clinical reasoning:")
    for category, results in category_results.items():
        print(f"\n{category.replace('_', ' ').title()}:")
        print(f"  - Count: {results['count']}")
        print(f"  - Mean VA at stop: {results['mean_va_at_stop']:.1f} letters")
        if results['mean_va_change'] is not None:
            print(f"  - Mean VA change: {results['mean_va_change']:.1f} letters")
    
    print(f"\n=== Patient Outcomes ===")
    print(f"Restarted treatment: {restart_patterns['restarted']} ({restart_patterns['restarted']/(restart_patterns['restarted']+restart_patterns['never_returned'])*100:.1f}%)")
    print(f"Never returned: {restart_patterns['never_returned']} ({restart_patterns['never_returned']/(restart_patterns['restarted']+restart_patterns['never_returned'])*100:.1f}%)")
    
    if restart_patterns["va_loss_before_restart"]:
        print(f"\nFor those who restarted:")
        print(f"  - Mean time to restart: {np.mean(restart_patterns['time_to_restart']):.0f} days")
        print(f"  - Mean VA loss before restart: {np.mean(restart_patterns['va_loss_before_restart']):.1f} letters")
    
    print("\nAnalysis complete. Results saved to:", output_dir)

if __name__ == "__main__":
    main()