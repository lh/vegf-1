import yaml
import subprocess
import sys

def setup_environment():
    with open('requirements.yaml') as f:
        config = yaml.safe_load(f)
    
    # Install dependencies using pip
    for dep in config['dependencies']:
        print(f"Installing {dep}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

if __name__ == "__main__":
    setup_environment()
