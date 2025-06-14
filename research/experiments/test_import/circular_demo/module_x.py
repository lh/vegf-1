"""
Module X that demonstrates handling of circular imports.
"""

# We'll import module_y, but in a way that avoids circular import issues
print("Initializing module_x")

# Module-level variable for demonstration
x_value = "Value from module_x"

def get_x_value():
    """Return the value defined in module_x."""
    return x_value

def use_y_function():
    """Use a function from module_y.
    
    Note: We import y inside the function to avoid circular imports.
    """
    # Import inside function to avoid circular import problems
    import circular_demo.module_y as module_y
    return f"module_x using module_y: {module_y.get_y_value()}"