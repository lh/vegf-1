"""
Module B inside a package.
"""

def advanced_function():
    """Return a message from the advanced function."""
    return "This is an advanced function from package.module_b"

class AdvancedClass:
    """A more advanced class demonstration."""
    
    def __init__(self, config=None):
        self.config = config or {"default": True}
        
    def execute(self, command):
        """Execute a command with the current configuration."""
        return f"Executing '{command}' with config: {self.config}"