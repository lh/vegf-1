"""
Analyze COVID-Era Mortality Rates in Eylea Patient Data
======================================================

This script analyzes mortality rates during COVID-19 vs non-COVID periods
to identify any excess mortality and potential correlations with treatment disruptions.

Key Questions:
1. Was there excess mortality during the COVID period?
2. Did patients with treatment gaps have higher mortality?
3. What was the temporal pattern of mortality during COVID?

Usage:
------
python analyze_covid_mortality.py --data path/to/original_data.csv

The input CSV should contain columns:
- Current Age: Patient's current age
- Injection Date: Date of injection
- Age at Death: Age when patient died (if applicable)
- Deceased: Binary indicator (0/1)
- VA Letter Score at Injection: Visual acuity (if available)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
import argparse
import json
from scipy import stats
from typing import Dict, List, Tuple, Optional

# Define COVID period
COVID_START = pd.to_datetime('2020-03-01')
COVID_END = pd.to_datetime('2021-12-31')

# Define analysis periods
PERIODS = {
    'pre_covid': ('2018-01-01', '2020-02-29'),
    'covid_early': ('2020-03-01', '2020-08-31'),
    'covid_peak': ('2020-09-01', '2021-02-28'),
    'covid_late': ('2021-03-01', '2021-12-31'),
    'post_covid': ('2022-01-01', '2023-12-31')
}

class CovidMortalityAnalyzer:
    """Analyze mortality patterns during COVID-19 pandemic."""
    
    def __init__(self, data_path: str, output_dir: str = 'output/covid_mortality_analysis'):
        self.data_path = data_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.data = None
        self.mortality_stats = {}
        
    def load_data(self):
        """Load and preprocess the patient data."""
        print(f"Loading data from {self.data_path}...")
        # First, check which columns are available
        df_sample = pd.read_csv(self.data_path, nrows=5)
        print(f"Available columns: {list(df_sample.columns)[:10]}...")
        
        # Parse dates - only parse columns that exist
        date_cols = ['Injection Date']
        if 'Date of Death' in df_sample.columns:
            date_cols.append('Date of Death')
        if 'Date of 1st Injection' in df_sample.columns:
            date_cols.append('Date of 1st Injection')
            
        self.data = pd.read_csv(self.data_path, parse_dates=date_cols)
        
        # Add derived columns
        self.data['year'] = self.data['Injection Date'].dt.year
        self.data['month'] = self.data['Injection Date'].dt.to_period('M')
        self.data['is_covid_period'] = (
            (self.data['Injection Date'] >= COVID_START) & 
            (self.data['Injection Date'] <= COVID_END)
        )
        
        print(f"Loaded {len(self.data)} records for {self.data['UUID'].nunique()} patients")
        
        # Check death data availability
        if 'Deceased' in self.data.columns:
            deaths = self.data.groupby('UUID')['Deceased'].max().sum()
            print(f"Found {deaths} deceased patients")
            if 'Age at Death' in self.data.columns:
                avg_age_at_death = self.data[self.data['Deceased'] == 1]['Age at Death'].mean()
                print(f"Average age at death: {avg_age_at_death:.1f} years")
        else:
            print("No death data found in dataset")
        
    def calculate_mortality_rates(self) -> Dict:
        """Calculate mortality rates by period."""
        results = {}
        
        # Get unique patients per period
        for period_name, (start, end) in PERIODS.items():
            start_date = pd.to_datetime(start)
            end_date = pd.to_datetime(end)
            
            # Patients active in this period
            period_patients = self.data[
                (self.data['Injection Date'] >= start_date) & 
                (self.data['Injection Date'] <= end_date)
            ]['UUID'].unique()
            
            # Deaths in this period - we'll estimate based on last injection date
            # Since we don't have Date of Death, we'll use patients who:
            # 1. Are marked as deceased
            # 2. Had their last injection in this period
            deceased_patients = self.data[self.data['Deceased'] == 1]
            if not deceased_patients.empty:
                last_injections = deceased_patients.groupby('UUID')['Injection Date'].max()
                period_deaths = sum(
                    (last_injections >= start_date) & (last_injections <= end_date)
                )
            else:
                period_deaths = 0
            
            # Calculate rate
            mortality_rate = (period_deaths / len(period_patients) * 100) if len(period_patients) > 0 else 0
            
            results[period_name] = {
                'patients': len(period_patients),
                'deaths': period_deaths,
                'mortality_rate': mortality_rate,
                'start': start,
                'end': end
            }
            
        self.mortality_stats = results
        return results
    
    def analyze_treatment_gap_mortality(self) -> Dict:
        """Analyze mortality by treatment gap duration."""
        # Calculate intervals between injections for each patient
        gap_analysis = []
        
        for patient_id in self.data['UUID'].unique():
            patient_data = self.data[self.data['UUID'] == patient_id].sort_values('Injection Date')
            
            if len(patient_data) < 2:
                continue
                
            # Calculate gaps
            patient_data['days_since_last'] = patient_data['Injection Date'].diff().dt.days
            
            # Find maximum gap during COVID
            covid_data = patient_data[patient_data['is_covid_period']]
            if not covid_data.empty and 'days_since_last' in covid_data.columns:
                max_covid_gap = covid_data['days_since_last'].max()
            else:
                max_covid_gap = 0
                
            # Check if patient died
            is_deceased = patient_data['Deceased'].iloc[-1] if 'Deceased' in patient_data.columns else 0
            # Estimate death date as last injection date for deceased patients
            death_date = patient_data['Injection Date'].iloc[-1] if is_deceased else None
            
            gap_analysis.append({
                'patient_id': patient_id,
                'max_covid_gap': max_covid_gap,
                'is_deceased': is_deceased,
                'death_date': death_date,
                'last_injection': patient_data['Injection Date'].iloc[-1]
            })
            
        gap_df = pd.DataFrame(gap_analysis)
        
        # Categorize gaps
        gap_df['gap_category'] = pd.cut(
            gap_df['max_covid_gap'],
            bins=[0, 90, 180, 365, np.inf],
            labels=['Normal (<90d)', 'Short gap (90-180d)', 'Long gap (180-365d)', 'Discontinued (>365d)']
        )
        
        # Calculate mortality by gap category
        mortality_by_gap = gap_df.groupby('gap_category').agg({
            'is_deceased': ['count', 'sum', 'mean']
        }).round(3)
        
        mortality_by_gap.columns = ['total_patients', 'deaths', 'mortality_rate']
        mortality_by_gap['mortality_rate'] *= 100  # Convert to percentage
        
        return mortality_by_gap.to_dict('index')
    
    def plot_mortality_timeline(self):
        """Plot mortality rates over time."""
        # Monthly mortality rates
        monthly_stats = []
        
        for month in pd.date_range('2018-01', '2023-12', freq='ME'):
            month_start = month
            month_end = (month + pd.DateOffset(months=1)) - pd.Timedelta(days=1)
            
            # Active patients in month
            active_patients = self.data[
                (self.data['Injection Date'] >= month_start) & 
                (self.data['Injection Date'] <= month_end)
            ]['UUID'].unique()
            
            # Deaths in month - estimate based on last injection for deceased patients
            deceased_patients = self.data[self.data['Deceased'] == 1]
            if not deceased_patients.empty:
                last_injections = deceased_patients.groupby('UUID')['Injection Date'].max()
                deaths = sum(
                    (last_injections >= month_start) & (last_injections <= month_end)
                )
            else:
                deaths = 0
                
            monthly_stats.append({
                'month': month,
                'patients': len(active_patients),
                'deaths': deaths,
                'rate': (deaths / len(active_patients) * 100) if len(active_patients) > 0 else 0
            })
            
        monthly_df = pd.DataFrame(monthly_stats)
        
        # Plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        # Mortality rate
        ax1.plot(monthly_df['month'], monthly_df['rate'], 'b-', label='Monthly mortality rate')
        
        # Add COVID period shading
        ax1.axvspan(COVID_START, COVID_END, alpha=0.2, color='red', label='COVID period')
        
        # Add rolling average
        monthly_df['rate_ma'] = monthly_df['rate'].rolling(window=3, center=True).mean()
        ax1.plot(monthly_df['month'], monthly_df['rate_ma'], 'r--', label='3-month moving average')
        
        ax1.set_ylabel('Mortality Rate (%)')
        ax1.set_title('Monthly Mortality Rate in Eylea Patients')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Patient counts
        ax2.bar(monthly_df['month'], monthly_df['patients'], width=20, alpha=0.7, label='Active patients')
        ax2.bar(monthly_df['month'], monthly_df['deaths'], width=20, alpha=0.7, color='red', label='Deaths')
        ax2.set_ylabel('Count')
        ax2.set_xlabel('Date')
        ax2.set_title('Monthly Patient Counts and Deaths')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'mortality_timeline.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def generate_report(self):
        """Generate summary report of findings."""
        report = {
            'analysis_date': datetime.now().isoformat(),
            'data_summary': {
                'total_patients': self.data['UUID'].nunique(),
                'total_records': len(self.data),
                'date_range': {
                    'start': str(self.data['Injection Date'].min()),
                    'end': str(self.data['Injection Date'].max())
                },
                'total_deaths': self.data['Deceased'].sum() if 'Deceased' in self.data.columns else 'N/A'
            },
            'mortality_by_period': self.mortality_stats,
            'mortality_by_treatment_gap': self.analyze_treatment_gap_mortality()
        }
        
        # Calculate excess mortality
        if 'pre_covid' in self.mortality_stats and any(p in self.mortality_stats for p in ['covid_early', 'covid_peak', 'covid_late']):
            baseline_rate = self.mortality_stats['pre_covid']['mortality_rate']
            
            excess_mortality = {}
            for period in ['covid_early', 'covid_peak', 'covid_late']:
                if period in self.mortality_stats:
                    period_rate = self.mortality_stats[period]['mortality_rate']
                    excess = period_rate - baseline_rate
                    excess_mortality[period] = {
                        'rate': period_rate,
                        'excess': excess,
                        'relative_increase': (excess / baseline_rate * 100) if baseline_rate > 0 else 'N/A'
                    }
            
            report['excess_mortality'] = excess_mortality
            
        # Save report
        with open(self.output_dir / 'covid_mortality_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        # Create summary text
        summary = f"""
COVID-19 Mortality Analysis Summary
===================================
Analysis Date: {datetime.now().strftime('%Y-%m-%d')}

Data Summary:
- Total patients analyzed: {report['data_summary']['total_patients']}
- Date range: {report['data_summary']['date_range']['start']} to {report['data_summary']['date_range']['end']}
- Total deaths recorded: {report['data_summary']['total_deaths']}

Mortality Rates by Period:
"""
        
        for period, stats in self.mortality_stats.items():
            summary += f"\n{period.replace('_', ' ').title()}:"
            summary += f"\n  - Patients: {stats['patients']}"
            summary += f"\n  - Deaths: {stats['deaths']}"
            summary += f"\n  - Mortality rate: {stats['mortality_rate']:.2f}%"
            
        if 'excess_mortality' in report:
            summary += "\n\nExcess Mortality During COVID:"
            for period, stats in report['excess_mortality'].items():
                summary += f"\n{period.replace('_', ' ').title()}:"
                summary += f"\n  - Excess mortality: {stats['excess']:.2f}%"
                if isinstance(stats['relative_increase'], float):
                    summary += f"\n  - Relative increase: {stats['relative_increase']:.1f}%"
                    
        with open(self.output_dir / 'mortality_summary.txt', 'w') as f:
            f.write(summary)
            
        print(summary)
        
    def run_analysis(self):
        """Run complete mortality analysis."""
        self.load_data()
        self.calculate_mortality_rates()
        self.plot_mortality_timeline()
        self.generate_report()
        
        print(f"\nAnalysis complete. Results saved to {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Analyze COVID mortality in Eylea patients')
    parser.add_argument('--data', type=str, required=True, help='Path to CSV file with patient data')
    parser.add_argument('--output', type=str, default='output/covid_mortality_analysis',
                        help='Directory for output files')
    
    args = parser.parse_args()
    
    analyzer = CovidMortalityAnalyzer(args.data, args.output)
    analyzer.run_analysis()


if __name__ == "__main__":
    main()