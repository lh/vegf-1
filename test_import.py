import sys
print("Python path:", sys.path)

try:
    from simulation.config import SimulationConfig
    print("SimulationConfig imported successfully")
except ImportError as e:
    print(f"Failed to import SimulationConfig: {e}")

try:
    import treat_and_extend_abs
    print("treat_and_extend_abs imported successfully")
except ImportError as e:
    print(f"Failed to import treat_and_extend_abs: {e}")

try:
    import treat_and_extend_des
    print("treat_and_extend_des imported successfully")
except ImportError as e:
    print(f"Failed to import treat_and_extend_des: {e}")
