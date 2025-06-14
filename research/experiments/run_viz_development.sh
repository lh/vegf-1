#!/bin/bash
# Run patient pathway visualization for actual simulation data

echo "🔀 Patient Pathway Visualization"
echo "================================"

# Check if there are any simulation results
if [ ! -d "../simulation_results" ] || [ -z "$(ls -A ../simulation_results 2>/dev/null)" ]; then
    echo "❌ No simulation results found!"
    echo ""
    echo "Please run a simulation first using the main Streamlit app:"
    echo "  cd .. && streamlit run APE.py"
    echo ""
    exit 1
fi

echo "✅ Found simulation results"
echo ""

# Optional: Run gap analysis on all simulations
read -p "Run gap analysis on simulations? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📊 Analyzing treatment gaps..."
    python detect_treatment_gaps.py
    echo ""
fi

echo "🚀 Starting visualization server..."
echo "   URL: http://localhost:8511"
echo ""
echo "   Select a simulation from the sidebar to visualize patient pathways"
echo ""

# Run visualization app
streamlit run visualize_simulation_pathways.py --server.port 8511