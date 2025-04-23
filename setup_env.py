"""Environment setup script for the Macular Simulation project.

This script automates the installation of Python dependencies from a YAML
configuration file (requirements.yaml). It ensures all required packages
are installed before running the simulation or analysis code. It is supplied for use 
in cases where anaconda or conda are not available. 

Features
--------
- Reads dependencies from YAML configuration
- Installs packages using pip
- Provides feedback during installation
- Uses the same Python interpreter that runs the script

Configuration
-------------
The script expects a requirements.yaml file with this structure:
```yaml
dependencies:
  - package1
  - package2>=1.0.0
  - package3~=2.3.0
```

Usage
-----
Run directly from command line:
```bash
python setup_env.py
```

Or import and call programmatically:
```python
from setup_env import setup_environment
setup_environment()
```

Error Handling
-------------
- Raises subprocess.CalledProcessError if pip install fails
- Raises yaml.YAMLError for invalid YAML
- Raises FileNotFoundError if requirements.yaml is missing

Examples
--------
1. Basic usage:
```bash
python setup_env.py
```

2. Check installed packages:
```bash
pip list
```

See Also
--------
- pip documentation: https://pip.pypa.io/
- PyYAML documentation: https://pyyaml.org/
- Python subprocess module: https://docs.python.org/3/library/subprocess.html
"""

import yaml
import subprocess
import sys

def setup_environment():
    """Install project dependencies from requirements.yaml.
    
    Reads the dependencies list from requirements.yaml and installs each package
    using pip. Prints progress messages during installation.

    Raises
    ------
    FileNotFoundError
        If requirements.yaml doesn't exist
    yaml.YAMLError
        If requirements.yaml contains invalid YAML
    subprocess.CalledProcessError
        If any pip install command fails
    """
    with open('requirements.yaml') as f:
        config = yaml.safe_load(f)
    
    # Install dependencies using pip
    for dep in config['dependencies']:
        print(f"Installing {dep}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

if __name__ == "__main__":
    setup_environment()
