"""
Module A containing a simple function to be imported.
"""

def greeting():
    """Return a simple greeting message."""
    return "Hello from module_a!"

class DataProcessor:
    """A simple class for data processing demonstrations."""
    
    def __init__(self, name="Default"):
        self.name = name
        
    def process(self, data):
        """Process the given data by adding the processor's name."""
        return f"{self.name} processed: {data}"