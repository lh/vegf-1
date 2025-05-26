"""
Test runner for Streamlit UI tests.

This script manages starting the Streamlit app, running tests, and cleanup.
"""

import subprocess
import time
import sys
import signal
import requests
from pathlib import Path


class StreamlitTestRunner:
    """Manages Streamlit app lifecycle for testing."""
    
    def __init__(self, app_path="APE.py", port=8501):
        self.app_path = app_path
        self.port = port
        self.process = None
        
    def start_app(self):
        """Start the Streamlit app."""
        print(f"Starting Streamlit app on port {self.port}...")
        
        # Start Streamlit in subprocess
        self.process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", self.app_path, 
             "--server.port", str(self.port),
             "--server.headless", "true"],
            cwd=Path(__file__).parent.parent.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for app to be ready
        self._wait_for_app()
        print(f"✅ Streamlit app is running on http://localhost:{self.port}")
        
    def _wait_for_app(self, timeout=30):
        """Wait for Streamlit app to be ready."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"http://localhost:{self.port}")
                if response.status_code == 200:
                    return
            except requests.ConnectionError:
                pass
            time.sleep(0.5)
        
        raise TimeoutError(f"Streamlit app did not start within {timeout} seconds")
    
    def stop_app(self):
        """Stop the Streamlit app."""
        if self.process:
            print("Stopping Streamlit app...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            print("✅ Streamlit app stopped")
    
    def run_tests(self, test_args=None):
        """Run the UI tests."""
        print("\nRunning UI tests...")
        
        cmd = [sys.executable, "-m", "pytest", "tests/ui/test_streamlit_ui.py"]
        if test_args:
            cmd.extend(test_args)
        
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)
        return result.returncode
    
    def __enter__(self):
        """Context manager entry."""
        self.start_app()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_app()


def main():
    """Run UI tests with managed Streamlit app."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Streamlit UI tests")
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Increase test verbosity")
    parser.add_argument("--headed", action="store_true",
                        help="Run tests with visible browser")
    parser.add_argument("--port", type=int, default=8501,
                        help="Port to run Streamlit on")
    parser.add_argument("--keep-running", action="store_true",
                        help="Keep app running after tests")
    
    args = parser.parse_args()
    
    # Build pytest args
    pytest_args = []
    if args.verbose:
        pytest_args.append("-" + "v" * args.verbose)
    if args.headed:
        pytest_args.extend(["--headed", "-s"])
    
    # Run tests
    with StreamlitTestRunner(port=args.port) as runner:
        exit_code = runner.run_tests(pytest_args)
        
        if args.keep_running:
            print("\nApp is still running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()