"""Script to check which workload analyzer implementation is being used in the app.

This script verifies:
1. Which version (original vs optimized) is imported
2. Whether caching is properly configured
3. File modification times
4. Import paths and dependencies
"""

import os
import sys
import importlib
import inspect
import datetime
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_file_info(filepath: str):
    """Check file existence and modification time."""
    path = Path(filepath)
    if path.exists():
        stat = path.stat()
        mod_time = datetime.datetime.fromtimestamp(stat.st_mtime)
        size = stat.st_size
        print(f"  ✓ Exists: {filepath}")
        print(f"    Modified: {mod_time}")
        print(f"    Size: {size:,} bytes")
        return True
    else:
        print(f"  ✗ NOT FOUND: {filepath}")
        return False


def check_imports():
    """Check which modules can be imported and their details."""
    print("\n" + "="*60)
    print("IMPORT CHECK")
    print("="*60)
    
    modules_to_check = [
        ("Original analyzer", "ape.components.treatment_patterns.workload_analyzer"),
        ("Optimized analyzer", "ape.components.treatment_patterns.workload_analyzer_optimized"),
        ("Visualizations", "ape.components.treatment_patterns.workload_visualizations"),
        ("Enhanced tab", "ape.components.treatment_patterns.enhanced_tab")
    ]
    
    imported_modules = {}
    
    for name, module_path in modules_to_check:
        print(f"\n{name} ({module_path}):")
        try:
            module = importlib.import_module(module_path)
            imported_modules[module_path] = module
            print(f"  ✓ Import successful")
            
            # Get file path
            if hasattr(module, '__file__'):
                print(f"  File: {module.__file__}")
                check_file_info(module.__file__)
            
            # List main functions
            functions = [item for item in dir(module) 
                        if not item.startswith('_') and callable(getattr(module, item))]
            print(f"  Functions: {', '.join(functions[:5])}{'...' if len(functions) > 5 else ''}")
            
        except ImportError as e:
            print(f"  ✗ Import failed: {e}")
    
    return imported_modules


def analyze_enhanced_tab_imports():
    """Analyze what the enhanced tab is actually importing."""
    print("\n" + "="*60)
    print("ENHANCED TAB IMPORT ANALYSIS")
    print("="*60)
    
    try:
        # Read the enhanced_tab.py file
        enhanced_tab_path = "ape/components/treatment_patterns/enhanced_tab.py"
        with open(enhanced_tab_path, 'r') as f:
            content = f.read()
        
        # Check for optimized imports
        if "workload_analyzer_optimized" in content:
            print("✓ Enhanced tab DOES import optimized analyzer")
            
            # Find the specific import lines
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "workload_analyzer_optimized" in line:
                    print(f"  Line {i+1}: {line.strip()}")
        else:
            print("✗ Enhanced tab does NOT import optimized analyzer")
        
        # Check for fallback mechanism
        if "try:" in content and "workload_analyzer_optimized" in content:
            print("✓ Enhanced tab has try/except fallback mechanism")
        
        # Check for caching decorators
        cache_count = content.count("@st.cache_data")
        print(f"\nCaching: Found {cache_count} @st.cache_data decorators")
        
    except FileNotFoundError:
        print(f"✗ Could not find {enhanced_tab_path}")


def check_function_signatures():
    """Compare function signatures between original and optimized versions."""
    print("\n" + "="*60)
    print("FUNCTION SIGNATURE COMPARISON")
    print("="*60)
    
    try:
        from ape.components.treatment_patterns import workload_analyzer_optimized as opt
        from ape.components.treatment_patterns import workload_analyzer as orig
        
        # Compare main function
        func_name = "calculate_clinical_workload_attribution"
        
        if hasattr(opt, func_name) and hasattr(orig, func_name):
            opt_func = getattr(opt, func_name)
            orig_func = getattr(orig, func_name)
            
            opt_sig = inspect.signature(opt_func)
            orig_sig = inspect.signature(orig_func)
            
            print(f"\n{func_name}:")
            print(f"  Original: {orig_sig}")
            print(f"  Optimized: {opt_sig}")
            
            if opt_sig == orig_sig:
                print("  ✓ Signatures match - drop-in replacement possible")
            else:
                print("  ✗ Signatures differ - may need code changes")
                
    except ImportError as e:
        print(f"Could not compare signatures: {e}")


def test_performance_difference():
    """Quick performance test between implementations."""
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)
    
    try:
        import pandas as pd
        import numpy as np
        import time
        
        # Create test data
        print("\nCreating test data (1000 patients)...")
        visits = []
        for i in range(1000):
            num_visits = np.random.randint(5, 15)
            current_time = 0
            for j in range(num_visits):
                visits.append({
                    'patient_id': i,
                    'time_days': current_time,
                    'visit_number': j
                })
                if j < num_visits - 1:
                    current_time += np.random.randint(30, 90)
        
        visits_df = pd.DataFrame(visits)
        print(f"Created {len(visits_df)} visits")
        
        # Test optimized version
        try:
            from ape.components.treatment_patterns.workload_analyzer_optimized import calculate_clinical_workload_attribution as calc_opt
            
            start = time.time()
            result_opt = calc_opt(visits_df)
            time_opt = time.time() - start
            print(f"\n✓ Optimized version: {time_opt:.3f} seconds")
        except ImportError:
            print("\n✗ Could not test optimized version")
            time_opt = None
        
        # Test original version
        try:
            from ape.components.treatment_patterns.workload_analyzer import calculate_clinical_workload_attribution as calc_orig
            
            start = time.time()
            result_orig = calc_orig(visits_df)
            time_orig = time.time() - start
            print(f"✓ Original version: {time_orig:.3f} seconds")
        except ImportError:
            print("✗ Could not test original version")
            time_orig = None
        
        # Compare
        if time_opt and time_orig:
            speedup = time_orig / time_opt
            print(f"\nSpeedup: {speedup:.1f}x")
            if speedup > 2:
                print("✓ Significant performance improvement detected")
            else:
                print("⚠ Limited performance improvement")
                
    except Exception as e:
        print(f"Performance test failed: {e}")


def check_visualization_performance():
    """Check visualization creation performance."""
    print("\n" + "="*60)
    print("VISUALIZATION PERFORMANCE CHECK")
    print("="*60)
    
    try:
        from ape.components.treatment_patterns.workload_visualizations import (
            create_dual_bar_chart,
            create_impact_pyramid,
            create_bubble_chart
        )
        import time
        
        # Create dummy workload data
        workload_data = {
            'summary_stats': {
                'Intensive': {
                    'patient_count': 100,
                    'patient_percentage': 10.0,
                    'visit_count': 500,
                    'visit_percentage': 25.0,
                    'visits_per_patient': 5.0,
                    'workload_intensity': 2.5
                },
                'Regular': {
                    'patient_count': 500,
                    'patient_percentage': 50.0,
                    'visit_count': 1000,
                    'visit_percentage': 50.0,
                    'visits_per_patient': 2.0,
                    'workload_intensity': 1.0
                },
                'Extended': {
                    'patient_count': 400,
                    'patient_percentage': 40.0,
                    'visit_count': 500,
                    'visit_percentage': 25.0,
                    'visits_per_patient': 1.25,
                    'workload_intensity': 0.625
                }
            },
            'total_patients': 1000,
            'total_visits': 2000,
            'category_definitions': {
                'Intensive': {'color': '#6B9DC7'},
                'Regular': {'color': '#8FC15C'},
                'Extended': {'color': '#6F9649'}
            }
        }
        
        viz_funcs = [
            ("Dual Bar Chart", create_dual_bar_chart),
            ("Impact Pyramid", create_impact_pyramid),
            ("Bubble Chart", create_bubble_chart)
        ]
        
        for name, func in viz_funcs:
            start = time.time()
            fig = func(workload_data, tufte_mode=True)
            elapsed = time.time() - start
            
            # Check figure size
            fig_json = fig.to_json()
            size_kb = len(fig_json) / 1024
            
            print(f"\n{name}:")
            print(f"  Creation time: {elapsed:.3f} seconds")
            print(f"  JSON size: {size_kb:.1f} KB")
            
            if elapsed > 0.5:
                print("  ⚠ Slow visualization creation")
            else:
                print("  ✓ Fast visualization creation")
                
    except Exception as e:
        print(f"Visualization test failed: {e}")


def main():
    """Run all checks."""
    print("CLINICAL WORKLOAD IMPLEMENTATION CHECK")
    print("=" * 60)
    print(f"Timestamp: {datetime.datetime.now()}")
    
    # Check file structure
    print("\n" + "="*60)
    print("FILE STRUCTURE CHECK")
    print("="*60)
    
    files_to_check = [
        "ape/components/treatment_patterns/workload_analyzer.py",
        "ape/components/treatment_patterns/workload_analyzer_optimized.py",
        "ape/components/treatment_patterns/workload_visualizations.py",
        "ape/components/treatment_patterns/enhanced_tab.py"
    ]
    
    for filepath in files_to_check:
        check_file_info(filepath)
    
    # Check imports
    imported_modules = check_imports()
    
    # Analyze enhanced tab
    analyze_enhanced_tab_imports()
    
    # Compare functions
    check_function_signatures()
    
    # Performance tests
    test_performance_difference()
    check_visualization_performance()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    print("\nKey findings:")
    print("1. Check if the optimized analyzer is being imported in enhanced_tab.py")
    print("2. Verify Streamlit caching decorators are present and working")
    print("3. Monitor visualization creation times")
    print("4. Consider implementing additional caching layers")
    
    print("\nNext steps:")
    print("1. Run profile_workload_performance.py for detailed profiling")
    print("2. Check Streamlit's own performance monitoring")
    print("3. Test with actual simulation data files")
    print("4. Monitor browser developer tools for rendering bottlenecks")


if __name__ == "__main__":
    main()