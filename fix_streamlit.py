"""
Direct streamlit metrics fix for discontinuations

This module fixes the displayed metrics in the streamlit app by
directly modifying the app.py file.
"""

import os
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Find streamlit app.py
project_root = os.path.dirname(os.path.abspath(__file__))
streamlit_app_path = os.path.join(project_root, "streamlit_app", "app.py")

# Check if app.py exists
if not os.path.exists(streamlit_app_path):
    logger.error(f"Could not find streamlit_app/app.py at {streamlit_app_path}")
    raise FileNotFoundError(f"streamlit_app/app.py not found at {streamlit_app_path}")

# Read the app.py file
with open(streamlit_app_path, 'r') as f:
    app_code = f.read()

# Define a regex pattern for finding the discontinuation rate calculation
disc_rate_pattern = r'(disc_rate\s*=\s*)(results\.get\([\'"]total_discontinuations[\'"]\s*,\s*0\)\s*/\s*results\.get\([\'"]patient_count[\'"]\s*,\s*1\))'

# Define a replacement with a cap at 100%
disc_rate_replacement = r'\1min(1.0, \2)'

# Apply the replacement
fixed_app_code = re.sub(disc_rate_pattern, disc_rate_replacement, app_code)

# Define a regex pattern for finding the discontinued patients count display
disc_count_pattern = r'(discontinued_patients\s*=\s*)(f[\'"]{\s*int\(disc_rate\s*\*\s*100\)\s*}%[\'"])'

# Define a replacement for showing "capped at 100%"
disc_count_replacement = r'\1f"{min(100, int(disc_rate * 100))}%" + (" (capped at 100%)" if disc_rate > 1.0 else "")'

# Apply the replacement
fixed_app_code = re.sub(disc_count_pattern, disc_count_replacement, fixed_app_code)

# Define a regex pattern for finding the discontinued patients count display
# Let's add a debug annotation to the streamlit app
metrics_pattern = r'(st\.metric\(\s*[\'"]Patients Discontinued[\'"],\s*discontinued_patients,\s*disc_count\s*\))'

# Define a replacement that adds debug info
# Replace with a container that includes debug information
metrics_replacement = r"""col1, col2 = st.columns(2)
                with col1:
                    st.metric("Patients Discontinued", discontinued_patients, disc_count)
                    
                    # Add debug information about discontinuations
                    if disc_rate > 1.0:
                        st.warning(f"⚠️ Actual discontinuation rate ({int(disc_rate * 100)}%) exceeds 100%, capped at 100%")
                        st.info("This means some patients were discontinued multiple times")
                        
                        # Calculate unique patients
                        raw_count = results.get('total_discontinuations', 0)
                        unique_count = results.get('unique_patient_discontinuations', raw_count)
                        patient_count = results.get('patient_count', 1)
                        
                        if unique_count < raw_count:
                            st.success(f"Unique patients discontinued: {unique_count} ({int((unique_count/patient_count)*100)}% of patients)")"""

# Apply the replacement
fixed_app_code = re.sub(metrics_pattern, metrics_replacement, fixed_app_code)

# Write the fixed app.py file
with open(streamlit_app_path, 'w') as f:
    f.write(fixed_app_code)

logger.info(f"Successfully fixed streamlit app display at {streamlit_app_path}")
print(f"✅ Applied fixes to streamlit discontinuation display")