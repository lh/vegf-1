"""
Save baseline test results for future comparison.

Run this before implementing memory architecture changes.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import platform
import psutil


def get_system_info():
    """Get system information for baseline context."""
    return {
        'platform': platform.platform(),
        'python_version': sys.version,
        'cpu_count': psutil.cpu_count(),
        'total_memory_gb': psutil.virtual_memory().total / (1024**3),
        'timestamp': datetime.now().isoformat()
    }


def run_tests_and_capture():
    """Run all baseline tests and capture results."""
    results = {
        'system_info': get_system_info(),
        'test_results': {},
        'memory_measurements': {},
        'performance_baselines': {}
    }
    
    # Run regression tests
    print("Running regression tests...")
    try:
        output = subprocess.run(
            [sys.executable, '-m', 'pytest', 'tests/regression', '-v', '--tb=short', '-m', 'not slow'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        results['test_results']['regression'] = {
            'return_code': output.returncode,
            'stdout': output.stdout,
            'stderr': output.stderr
        }
    except Exception as e:
        results['test_results']['regression'] = {'error': str(e)}
    
    # Run memory baseline tests with output capture
    print("Running memory baseline tests...")
    try:
        output = subprocess.run(
            [sys.executable, '-m', 'pytest', 'tests/regression/test_memory_baseline.py', '-v', '-s'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        results['test_results']['memory'] = {
            'return_code': output.returncode,
            'stdout': output.stdout,
            'stderr': output.stderr
        }
        
        # Parse memory measurements from output
        for line in output.stdout.split('\n'):
            if 'Import overhead:' in line:
                results['memory_measurements']['import_overhead_mb'] = float(line.split(':')[1].strip().split()[0])
            elif 'patients:' in line and 'MB' in line:
                # Extract patient count and memory
                parts = line.strip().split()
                if len(parts) >= 4:
                    try:
                        patients = int(parts[0])
                        memory = float(parts[2])
                        results['memory_measurements'][f'{patients}_patients_mb'] = memory
                    except (ValueError, IndexError):
                        pass
                        
    except Exception as e:
        results['test_results']['memory'] = {'error': str(e)}
    
    return results


def save_baseline(results):
    """Save baseline results to file."""
    baseline_dir = Path(__file__).parent / 'baseline_results'
    baseline_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save full results as JSON
    json_file = baseline_dir / f'baseline_{timestamp}.json'
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save summary as markdown
    md_file = baseline_dir / f'baseline_{timestamp}.md'
    with open(md_file, 'w') as f:
        f.write(f"# Baseline Test Results\n\n")
        f.write(f"Generated: {results['system_info']['timestamp']}\n\n")
        f.write(f"## System Information\n\n")
        f.write(f"- Platform: {results['system_info']['platform']}\n")
        f.write(f"- Python: {results['system_info']['python_version'].split()[0]}\n")
        f.write(f"- CPUs: {results['system_info']['cpu_count']}\n")
        f.write(f"- Memory: {results['system_info']['total_memory_gb']:.1f} GB\n\n")
        
        f.write(f"## Test Results\n\n")
        for test_type, result in results['test_results'].items():
            if 'error' not in result:
                f.write(f"### {test_type.title()} Tests\n")
                f.write(f"- Return code: {result['return_code']}\n")
                
                # Count passed/failed
                stdout = result['stdout']
                passed = stdout.count('PASSED')
                failed = stdout.count('FAILED')
                f.write(f"- Passed: {passed}\n")
                f.write(f"- Failed: {failed}\n\n")
        
        f.write(f"## Memory Measurements\n\n")
        for key, value in sorted(results['memory_measurements'].items()):
            f.write(f"- {key}: {value:.1f} MB\n")
    
    # Create a "latest" symlink
    latest_json = baseline_dir / 'baseline_latest.json'
    latest_md = baseline_dir / 'baseline_latest.md'
    
    # Remove old symlinks if they exist
    for link in [latest_json, latest_md]:
        if link.exists() or link.is_symlink():
            link.unlink()
    
    # Create new symlinks (on Unix-like systems)
    if hasattr(Path, 'symlink_to'):
        try:
            latest_json.symlink_to(json_file.name)
            latest_md.symlink_to(md_file.name)
        except:
            # Copy instead if symlinks fail
            import shutil
            shutil.copy2(json_file, latest_json)
            shutil.copy2(md_file, latest_md)
    
    return json_file, md_file


def main():
    """Run baseline tests and save results."""
    print("APE V2 Baseline Test Runner")
    print("===========================\n")
    
    print("This will establish baseline metrics for:")
    print("  - Existing functionality")
    print("  - Memory usage patterns")
    print("  - Performance characteristics\n")
    
    results = run_tests_and_capture()
    json_file, md_file = save_baseline(results)
    
    print(f"\nBaseline results saved:")
    print(f"  - JSON: {json_file}")
    print(f"  - Summary: {md_file}")
    
    # Print summary
    print("\nSummary:")
    print("--------")
    
    for test_type, result in results['test_results'].items():
        if 'error' not in result:
            stdout = result['stdout']
            passed = stdout.count('PASSED')
            failed = stdout.count('FAILED')
            print(f"{test_type}: {passed} passed, {failed} failed")
    
    print("\nMemory measurements:")
    for key, value in sorted(results['memory_measurements'].items()):
        print(f"  {key}: {value:.1f} MB")


if __name__ == '__main__':
    main()