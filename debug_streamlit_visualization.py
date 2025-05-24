"""Debug the Streamlit visualization issue"""

import json
import matplotlib.pyplot as plt
import numpy as np

# Let's analyze the data structure from the JSON file we saved
with open("test_data_structure.json", "r") as f:
    data = json.load(f)

# Look at the patient histories
print("Patient histories sample:")
for patient_id, visits in data["patient_histories_sample"].items():
    print(f"\nPatient {patient_id}:")
    for i, visit in enumerate(visits):
        print(f"  Visit {i}: {visit}")

# Now let's create a simple scatter plot to see the issue
fig, ax = plt.subplots(figsize=(12, 6))

# Extract all visit times and visual acuities
all_times = []
all_vas = []

for patient_id, visits in data["patient_histories_sample"].items():
    for visit in visits:
        # Parse the date
        if "date" in visit:
            # Extract just the time component for now
            all_times.append(float(visit.get("time", 0)) / 30.44)  # Convert days to months
            all_vas.append(float(visit.get("vision", 0)))

# Plot the raw data
ax.scatter(all_times, all_vas, alpha=0.5, s=50)
ax.set_xlabel("Time (months)")
ax.set_ylabel("Visual Acuity")
ax.set_title("Raw Visit Data Distribution")
ax.grid(True, alpha=0.3)

plt.savefig("debug_visit_distribution.png")
plt.close()

# Now analyze the time distribution
print(f"\nTime distribution analysis:")
print(f"Unique times: {sorted(set(all_times))}")
print(f"Total visits: {len(all_times)}")

# Create histogram of visit times
fig, ax = plt.subplots(figsize=(12, 6))
ax.hist(all_times, bins=50, alpha=0.7)
ax.set_xlabel("Time (months)")
ax.set_ylabel("Count")
ax.set_title("Visit Time Distribution")

plt.savefig("debug_time_histogram.png")
plt.close()

print("\nDebug plots saved as debug_visit_distribution.png and debug_time_histogram.png")