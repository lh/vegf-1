"""
Compatibility module for runtime patching of discontinuation functionality.

This module provides functions to patch the discontinuation functionality
at runtime without requiring code changes. It can be imported into existing
code to automatically fix the discontinuation issues.

Example usage:
```python
# Import this at the top of your script
import simulation.discontinued_compat

# Rest of your code remains unchanged
from treat_and_extend_abs import TreatAndExtendABS
from treat_and_extend_des import TreatAndExtendDES

# The imports are automatically patched to use the fixed implementations
```
"""

import sys
import inspect
import logging
import importlib
from types import ModuleType
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flag to track if patching has been applied
_PATCHED = False

def _get_caller_module():
    """Get the module that imported this module."""
    frame = inspect.currentframe()
    try:
        # Go back two frames to get the caller of the caller (i.e., who imported this module)
        caller = frame.f_back.f_back
        if caller is not None:
            return inspect.getmodule(caller)
        return None
    finally:
        del frame  # Avoid reference cycles

def _patch_module_imports():
    """Patch the imports in the caller module."""
    global _PATCHED
    
    if _PATCHED:
        logger.info("Patching already applied, skipping...")
        return
    
    try:
        # Import the fixed implementations
        abs_fixed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "treat_and_extend_abs_fixed.py")
        des_fixed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "treat_and_extend_des_fixed.py")
        
        if not os.path.exists(abs_fixed_path) or not os.path.exists(des_fixed_path):
            logger.error("Fixed implementation files not found. Patching aborted.")
            return
        
        # Import the fixed modules using import machinery
        spec_abs = importlib.util.spec_from_file_location("treat_and_extend_abs_fixed", abs_fixed_path)
        fixed_abs_module = importlib.util.module_from_spec(spec_abs)
        spec_abs.loader.exec_module(fixed_abs_module)
        
        spec_des = importlib.util.spec_from_file_location("treat_and_extend_des_fixed", des_fixed_path)
        fixed_des_module = importlib.util.module_from_spec(spec_des)
        spec_des.loader.exec_module(fixed_des_module)
        
        # Get the fixed classes
        FixedABS = fixed_abs_module.TreatAndExtendABS
        FixedDES = fixed_des_module.TreatAndExtendDES
        
        # Replace the original modules in sys.modules
        if "treat_and_extend_abs" in sys.modules:
            sys.modules["treat_and_extend_abs"].TreatAndExtendABS = FixedABS
        
        if "treat_and_extend_des" in sys.modules:
            sys.modules["treat_and_extend_des"].TreatAndExtendDES = FixedDES
        
        # Also patch the caller's module if available
        caller_module = _get_caller_module()
        if caller_module:
            for name, obj in inspect.getmembers(caller_module):
                if name == "TreatAndExtendABS":
                    setattr(caller_module, name, FixedABS)
                elif name == "TreatAndExtendDES":
                    setattr(caller_module, name, FixedDES)
        
        # Set the patched flag
        _PATCHED = True
        logger.info("Successfully patched discontinuation implementation.")
    
    except Exception as e:
        logger.error(f"Error patching discontinuation implementation: {e}")

# Apply the patching when this module is imported
_patch_module_imports()