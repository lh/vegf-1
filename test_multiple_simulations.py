import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from test_abs_simulation import run_test_simulation as run_abs
from test_des_simulation import run_test_des_simulation as run_des
from analysis.simulation_results import SimulationResults

def setup_database():
    """Create SQLite database and tables"""
    conn = sqlite3.connect('simulations.db')
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS simulation_runs
                 (run_id INTEGER PRIMARY KEY,
                  sim_type TEXT,
                  start_date TEXT,
                  end_date TEXT,
                  run_date TEXT)''')
                 
    c.execute('''CREATE TABLE IF NOT EXISTS patient_outcomes
                 (run_id INTEGER,
                  patient_id TEXT,
                  final_vision INTEGER,
                  vision_change INTEGER,
                  num_injections INTEGER,
                  num_visits INTEGER,
                  FOREIGN KEY(run_id) REFERENCES simulation_runs(run_id))''')
    
    conn.commit()
    return conn

def store_results(conn, run_id: int, sim_type: str, start_date: datetime, 
                 end_date: datetime, patient_histories: dict):
    """Store simulation results in database"""
    c = conn.cursor()
    
    # Store run info
    c.execute('''INSERT INTO simulation_runs 
                 (run_id, sim_type, start_date, end_date, run_date)
                 VALUES (?, ?, ?, ?, ?)''',
              (run_id, sim_type, start_date.isoformat(), 
               end_date.isoformat(), datetime.now().isoformat()))
    
    # Store patient outcomes
    for patient_id, history in patient_histories.items():
        # Calculate metrics
        visits = len(history)
        injections = sum(1 for v in history if 'injection' in v.get('actions', []))
        
        # Get vision values
        vision_values = [v['vision'] for v in history if 'vision' in v]
        if vision_values:
            final_vision = vision_values[-1]
            vision_change = final_vision - vision_values[0]
        else:
            final_vision = None
            vision_change = None
            
        c.execute('''INSERT INTO patient_outcomes
                     (run_id, patient_id, final_vision, vision_change, 
                      num_injections, num_visits)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (run_id, patient_id, final_vision, vision_change, 
                   injections, visits))
    
    conn.commit()

def analyze_results(conn):
    """Analyze and visualize results from multiple simulation runs"""
    # Load data into pandas
    runs_df = pd.read_sql_query("SELECT * FROM simulation_runs", conn)
    outcomes_df = pd.read_sql_query("SELECT * FROM patient_outcomes", conn)
    
    # Merge dataframes
    df = pd.merge(outcomes_df, runs_df, on='run_id')
    
    # Create comparative visualizations
    plt.figure(figsize=(15, 5))
    
    # Vision changes
    plt.subplot(131)
    df.boxplot(column='vision_change', by='sim_type')
    plt.title('Vision Changes by Simulation Type')
    plt.suptitle('')  # Remove automatic suptitle
    
    # Number of injections
    plt.subplot(132)
    df.boxplot(column='num_injections', by='sim_type')
    plt.title('Number of Injections by Simulation Type')
    
    # Number of visits
    plt.subplot(133)
    df.boxplot(column='num_visits', by='sim_type')
    plt.title('Number of Visits by Simulation Type')
    
    plt.tight_layout()
    plt.savefig('simulation_comparison.png')
    plt.close()
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("==================")
    for sim_type in df['sim_type'].unique():
        sim_data = df[df['sim_type'] == sim_type]
        print(f"\n{sim_type} Simulation:")
        print(f"Mean vision change: {sim_data['vision_change'].mean():.1f} letters")
        print(f"Mean injections: {sim_data['num_injections'].mean():.1f}")
        print(f"Mean visits: {sim_data['num_visits'].mean():.1f}")

def run_multiple_simulations(num_runs: int = 5):
    """Run multiple simulations of each type and analyze results"""
    conn = setup_database()
    
    start_date = datetime(2023, 1, 1)
    end_date = start_date + timedelta(days=365)
    
    # Run ABS simulations
    print("\nRunning Agent-Based Simulations...")
    for i in range(num_runs):
        print(f"Run {i+1}/{num_runs}")
        results = run_abs(verbose=False)
        store_results(conn, i, 'ABS', start_date, end_date, results)
        
    # Run DES simulations
    print("\nRunning Discrete Event Simulations...")
    for i in range(num_runs):
        print(f"Run {i+1}/{num_runs}")
        results = run_des(verbose=False)
        store_results(conn, i+num_runs, 'DES', start_date, end_date, results)
    
    # Analyze results
    analyze_results(conn)
    conn.close()

if __name__ == "__main__":
    run_multiple_simulations()
