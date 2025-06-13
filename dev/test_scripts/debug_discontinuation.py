from simulation.config import SimulationConfig
import yaml

# Load the configuration
config = SimulationConfig.from_yaml('eylea_literature_based')

# Get the discontinuation parameters
discontinuation_params = config.get_treatment_discontinuation_params()
print("Discontinuation params from config.get_treatment_discontinuation_params():")
print(discontinuation_params)

# Check if 'enabled' is in the parameters
print("\nIs 'enabled' in discontinuation_params?", 'enabled' in discontinuation_params)

# Load the discontinuation parameters file directly
with open('protocols/parameter_sets/eylea/discontinuation_parameters.yaml', 'r') as f:
    direct_params = yaml.safe_load(f)
    print("\nDirect load of discontinuation_parameters.yaml:")
    print(direct_params)

# Check the structure of the parameters
if 'discontinuation' in direct_params:
    print("\nFound 'discontinuation' key in direct_params")
    print("direct_params['discontinuation']['enabled'] =", direct_params['discontinuation'].get('enabled'))
else:
    print("\nNo 'discontinuation' key in direct_params")

# Check the structure we're passing to DiscontinuationManager
wrapped_params = {"discontinuation": discontinuation_params}
print("\nWrapped params that we're passing to DiscontinuationManager:")
print(wrapped_params)
print("wrapped_params['discontinuation'].get('enabled') =", wrapped_params['discontinuation'].get('enabled', 'Not found'))
