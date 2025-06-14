"""
Debug the t=0 discontinuation issue.
"""

import numpy as np

def sigmoid(x, steepness=10, midpoint=0.5):
    """Sigmoid function for smooth transitions."""
    return 1 / (1 + np.exp(-steepness * (x - midpoint)))

def stepped_curve(x, steps=4):
    """Create a stepped curve for certain events."""
    return np.floor(x * steps) / steps + (x * steps % 1) * 0.2

# Test what happens at t=0 for each curve type
print("=== Curve values at t=0 ===")

t = 0.0

# Planned - sigmoid with midpoint at 0.7
planned_progress = sigmoid(t, steepness=6, midpoint=0.7)
print(f"Planned (sigmoid, midpoint=0.7): {planned_progress:.6f}")

# Administrative - linear
admin_progress = t
print(f"Administrative (linear): {admin_progress:.6f}")

# Not Renewed - stepped curve
not_renewed_progress = stepped_curve(t, steps=3)
print(f"Not Renewed (stepped): {not_renewed_progress:.6f}")

# Premature - sigmoid with midpoint at 0.4
premature_progress = sigmoid(t, steepness=6, midpoint=0.4)
print(f"Premature (sigmoid, midpoint=0.4): {premature_progress:.6f}")

# Test sigmoid behavior near 0
print("\n=== Sigmoid behavior near t=0 ===")
for t_test in [0.0, 0.01, 0.05, 0.1]:
    sig_0_7 = sigmoid(t_test, steepness=6, midpoint=0.7)
    sig_0_4 = sigmoid(t_test, steepness=6, midpoint=0.4)
    print(f"t={t_test}: sigmoid(midpoint=0.7)={sig_0_7:.6f}, sigmoid(midpoint=0.4)={sig_0_4:.6f}")

# Test with example counts
print("\n=== Example with discontinuation counts ===")
disc_counts = {
    "Planned": 136,
    "Administrative": 11,
    "Not Renewed": 134,
    "Premature": 537
}

for disc_type, count in disc_counts.items():
    if disc_type == "Planned":
        progress = sigmoid(0, steepness=6, midpoint=0.7)
    elif disc_type == "Administrative":
        progress = 0  # Linear
    elif disc_type == "Not Renewed":
        progress = stepped_curve(0, steps=3)
    elif disc_type == "Premature":
        progress = sigmoid(0, steepness=6, midpoint=0.4)
    
    target_at_t0 = count * progress
    print(f"{disc_type}: {count} * {progress:.6f} = {target_at_t0:.2f} discontinuations at t=0")