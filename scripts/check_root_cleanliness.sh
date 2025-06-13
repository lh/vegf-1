#!/bin/bash
# Check if root directory is getting cluttered

echo "🧹 Checking root directory cleanliness..."

# Count Python files in root (excluding APE.py)
PYTHON_COUNT=$(ls -1 *.py 2>/dev/null | grep -v "APE.py" | wc -l)

# Count data files in root  
DATA_COUNT=$(ls -1 *.csv *.json *.txt 2>/dev/null | grep -v "requirements" | wc -l)

# Count image files in root
IMAGE_COUNT=$(ls -1 *.png *.jpg *.pdf 2>/dev/null | wc -l)

# Total file count
TOTAL_FILES=$(ls -1 | wc -l)

# Check thresholds
ISSUES=0

if [ $PYTHON_COUNT -gt 2 ]; then
    echo "⚠️  Found $PYTHON_COUNT Python files in root (should be in dev/test_scripts/ or scripts/)"
    ls -1 *.py | grep -v "APE.py" | head -5
    ISSUES=$((ISSUES + 1))
fi

if [ $DATA_COUNT -gt 5 ]; then
    echo "⚠️  Found $DATA_COUNT data files in root (should be in output/data/)"
    ls -1 *.csv *.json *.txt 2>/dev/null | grep -v "requirements" | head -5
    ISSUES=$((ISSUES + 1))
fi

if [ $IMAGE_COUNT -gt 0 ]; then
    echo "⚠️  Found $IMAGE_COUNT image files in root (should be in output/plots/)"
    ls -1 *.png *.jpg *.pdf 2>/dev/null | head -5
    ISSUES=$((ISSUES + 1))
fi

if [ $TOTAL_FILES -gt 150 ]; then
    echo "⚠️  Total files in root: $TOTAL_FILES (getting cluttered!)"
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo "✅ Root directory is clean! ($TOTAL_FILES files)"
    echo "📁 Remember to use workspace/ for temporary work"
else
    echo ""
    echo "❌ Found $ISSUES cleanliness issues"
    echo "📖 See WHERE_TO_PUT_THINGS.md for the directory guide"
    echo "💡 Tip: Use workspace/ for temporary files!"
fi

exit $ISSUES