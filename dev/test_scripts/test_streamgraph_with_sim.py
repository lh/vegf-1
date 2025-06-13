"""Test streamgraph with actual simulation data."""

import matplotlib.pyplot as plt
from streamlit_app.streamgraph_discontinuation import generate_enhanced_discontinuation_streamgraph
from simulation.config import SimulationConfig
from treat_and_extend_abs_fixed import TreatAndExtendABS

# Create a small test simulation
config = SimulationConfig.from_yaml("test_simulation")
config.num_patients = 10
config.duration_days = 365  # 1 year

print("Running simulation...")
sim = TreatAndExtendABS(config)
patient_histories = sim.run()

print(f"Simulation complete. Generated {len(patient_histories)} patients")

# Create results structure similar to what the streamlit app creates
results = {
    "population_size": config.num_patients,
    "duration_years": config.duration_days / 365,
    "patient_histories": patient_histories,
    "discontinuation_counts": sim.stats.get("discontinuations", {}),
}

# Generate the streamgraph
print("Generating streamgraph...")
try:
    fig = generate_enhanced_discontinuation_streamgraph(results)
    fig.savefig("test_streamgraph_with_sim.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("Streamgraph saved to test_streamgraph_with_sim.png")
except ValueError as e:
    print(f"Error: {e}")
    # Let's check what's in patient_histories
    print(f"Patient histories type: {type(patient_histories)}")
    if patient_histories:
        print(f"First patient type: {type(patient_histories[0])}")
        if hasattr(patient_histories[0], 'visit_history'):
            print("Patient has visit_history attribute")
        elif hasattr(patient_histories[0], 'state'):
            print("Patient has state attribute")
            state = patient_histories[0].state
            print(f"State type: {type(state)}")
            if hasattr(state, 'visit_history'):
                print("State has visit_history attribute")
            elif isinstance(state, dict) and 'visit_history' in state:
                print("visit_history is in patient.state dict")
            else:
                print(f"State keys: {state.keys() if isinstance(state, dict) else 'Not a dict'}")
        else:
            print(f"Patient attributes: {dir(patient_histories[0])}")