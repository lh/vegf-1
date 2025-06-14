"""
Module C inside a subpackage.
"""

from ..module_b import AdvancedClass

def specialized_function():
    """Return a message from the specialized function."""
    return "This is a specialized function from package.subpackage.module_c"

class SpecializedProcessor(AdvancedClass):
    """A specialized processor that inherits from AdvancedClass."""
    
    def __init__(self, name, config=None):
        super().__init__(config)
        self.name = name
        
    def execute(self, command):
        """Override execute to include the processor name."""
        base_result = super().execute(command)
        return f"{self.name}: {base_result}"