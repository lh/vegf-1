#!/bin/bash
# Test the R visualization integration

echo "Testing R visualization integration..."
cd "$(dirname "$0")"

# Run the test script
python streamlit_app/test_r_integration.py

# Add instructions for how to check logs
echo ""
echo "To check the logs, run:"
echo "  cat $(python -c 'import tempfile; print(tempfile.gettempdir() + "/streamlit_app.log")')"
echo ""
echo "To run the Streamlit app with enhanced R visualization:"
echo "  streamlit run streamlit_app/app_refactored.py"