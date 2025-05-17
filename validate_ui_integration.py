#!/usr/bin/env python3
"""
Validate that the UI integration is working correctly by generating 
a static HTML preview of what the Streamlit app should display.
"""

import matplotlib.pyplot as plt
import base64
from io import BytesIO
import numpy as np
from collections import defaultdict

# Mock data generation
def generate_mock_data():
    """Generate mock simulation results."""
    # Generate patient data
    np.random.seed(42)
    patient_data = {}
    
    for i in range(100):
        visits = []
        current_va = np.random.normal(70, 10)
        for month in range(60):
            current_va += np.random.normal(-0.1, 2)  # Slight decline with noise
            current_va = np.clip(current_va, 0, 85)
            visits.append({
                'time': month,
                'vision': current_va
            })
        patient_data[f'patient_{i}'] = visits
    
    # Create mean_va_data
    time_va_map = defaultdict(list)
    for patient_id, visits in patient_data.items():
        for visit in visits:
            time_month = visit['time']
            time_va_map[time_month].append(visit['vision'])
    
    mean_va_data = []
    for time_month in sorted(time_va_map.keys()):
        va_values = time_va_map[time_month]
        mean_va_data.append({
            'time_months': time_month,
            'visual_acuity': np.mean(va_values),
            'std_error': np.std(va_values) / np.sqrt(len(va_values)),
            'sample_size': len(va_values)
        })
    
    return {
        'patient_data': patient_data,
        'mean_va_data': mean_va_data,
        'simulation_type': 'ABS',
        'population_size': 100,
        'duration_years': 5
    }

def fig_to_base64(fig):
    """Convert matplotlib figure to base64 string."""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{b64}"

# Import visualization functions
from streamlit_app.simulation_runner import (
    generate_va_over_time_thumbnail,
    generate_va_distribution_thumbnail,
    generate_va_over_time_plot,
    generate_va_distribution_plot
)

# Generate mock results
results = generate_mock_data()

# Generate all plots
try:
    thumb1 = generate_va_over_time_thumbnail(results)
    thumb1_b64 = fig_to_base64(thumb1)
except Exception as e:
    thumb1_b64 = f"Error: {e}"

try:
    thumb2 = generate_va_distribution_thumbnail(results)
    thumb2_b64 = fig_to_base64(thumb2)
except Exception as e:
    thumb2_b64 = f"Error: {e}"

try:
    plot1 = generate_va_over_time_plot(results)
    plot1_b64 = fig_to_base64(plot1)
except Exception as e:
    plot1_b64 = f"Error: {e}"

try:
    plot2 = generate_va_distribution_plot(results)
    plot2_b64 = fig_to_base64(plot2)
except Exception as e:
    plot2_b64 = f"Error: {e}"

# Create HTML preview
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>VA Visualization Integration Test</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .row {{ display: flex; margin: 20px 0; }}
        .col {{ flex: 1; text-align: center; padding: 10px; }}
        .thumbnail {{ border: 1px solid #ddd; padding: 10px; }}
        .full-plot {{ margin: 30px 0; }}
        img {{ max-width: 100%; height: auto; }}
        .caption {{ font-size: 14px; color: #666; margin-top: 5px; }}
        h2, h3 {{ text-align: center; }}
        .error {{ color: red; padding: 20px; background: #ffe0e0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Visual Acuity Over Time - Integration Test</h1>
        
        <h3>Quick Comparison</h3>
        <div class="row">
            <div class="col thumbnail">
                <img src="{thumb1_b64}" alt="Mean + 95% CI Thumbnail">
                <div class="caption">Mean + 95% CI</div>
            </div>
            <div class="col thumbnail">
                <img src="{thumb2_b64}" alt="Patient Distribution Thumbnail">
                <div class="caption">Patient Distribution</div>
            </div>
        </div>
        
        <div class="full-plot">
            <h3>Mean Visual Acuity with Confidence Intervals</h3>
            <img src="{plot1_b64}" alt="Full Mean + CI Plot">
        </div>
        
        <div class="full-plot">
            <h3>Distribution of Visual Acuity</h3>
            <img src="{plot2_b64}" alt="Full Distribution Plot">
        </div>
        
        <div style="margin-top: 40px; padding: 20px; background: #f0f0f0;">
            <h4>Integration Test Results</h4>
            <ul>
                <li>Thumbnail 1 (Mean + CI): {'✓ Success' if 'Error' not in str(thumb1_b64) else '✗ ' + str(thumb1_b64)}</li>
                <li>Thumbnail 2 (Distribution): {'✓ Success' if 'Error' not in str(thumb2_b64) else '✗ ' + str(thumb2_b64)}</li>
                <li>Full Plot 1 (Mean + CI): {'✓ Success' if 'Error' not in str(plot1_b64) else '✗ ' + str(plot1_b64)}</li>
                <li>Full Plot 2 (Distribution): {'✓ Success' if 'Error' not in str(plot2_b64) else '✗ ' + str(plot2_b64)}</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

# Save HTML file
with open('/Users/rose/Code/CC/ui_integration_test.html', 'w') as f:
    f.write(html_content)

print("UI integration test saved to: ui_integration_test.html")
print("Open this file in a browser to verify the layout.")

# Also create a simple status report
status = []
status.append("Thumbnail 1 (Mean + CI): " + ('✓ Success' if 'Error' not in str(thumb1_b64) else '✗ Failed'))
status.append("Thumbnail 2 (Distribution): " + ('✓ Success' if 'Error' not in str(thumb2_b64) else '✗ Failed'))
status.append("Full Plot 1 (Mean + CI): " + ('✓ Success' if 'Error' not in str(plot1_b64) else '✗ Failed'))
status.append("Full Plot 2 (Distribution): " + ('✓ Success' if 'Error' not in str(plot2_b64) else '✗ Failed'))

print("\nStatus Report:")
for s in status:
    print(s)