#!/bin/bash

# Run baseline regression tests and save results
# This establishes our reference point before implementing memory architecture

echo "Running APE V2 Baseline Regression Tests"
echo "========================================"
echo ""
echo "This will establish baseline metrics for:"
echo "  - Existing functionality"
echo "  - Memory usage patterns"
echo "  - Performance characteristics"
echo ""

# Create results directory
mkdir -p tests/baseline_results

# Set timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="tests/baseline_results/baseline_${TIMESTAMP}.txt"

# Run tests and capture output
echo "Running regression tests..."
pytest tests/regression -v --tb=short -m "not slow" | tee "$RESULTS_FILE"

echo ""
echo "Running memory baseline tests..."
pytest tests/regression/test_memory_baseline.py -v -s | tee -a "$RESULTS_FILE"

echo ""
echo "Baseline results saved to: $RESULTS_FILE"
echo ""
echo "Summary:"
echo "--------"
grep -E "(PASSED|FAILED|ERROR)" "$RESULTS_FILE" | sort | uniq -c

echo ""
echo "Memory measurements:"
echo "-------------------"
grep -E "(Import overhead:|patients:|Memory)" "$RESULTS_FILE" | grep -v "test_"

echo ""
echo "Next steps:"
echo "1. Review baseline results"
echo "2. Implement memory architecture"
echo "3. Run tests again to ensure no regression"