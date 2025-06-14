"""
Advanced import demonstration script.

This script shows various ways to import modules and specific components
from different package levels.
"""

# Import module with alias
import module_a as mod_a

# Import specific items from module
from module_a import greeting, DataProcessor

# Import from package
import package.module_b

# Import specific items from package
from package.module_b import advanced_function, AdvancedClass

# Import from subpackage
import package.subpackage.module_c

# Import specific items from subpackage
from package.subpackage.module_c import specialized_function, SpecializedProcessor

def main():
    """Main function to demonstrate various imports."""
    print("\n--- Basic Imports ---")
    print(f"Direct module function call: {mod_a.greeting()}")
    print(f"Imported function call: {greeting()}")
    
    basic_processor = DataProcessor("Basic Demo")
    print(f"Using imported class: {basic_processor.process('test data')}")
    
    print("\n--- Package Imports ---")
    print(f"Function from package: {advanced_function()}")
    
    adv_class = AdvancedClass({"level": "advanced", "debug": True})
    print(f"Class from package: {adv_class.execute('important task')}")
    
    print("\n--- Subpackage Imports ---")
    print(f"Function from subpackage: {specialized_function()}")
    
    spec_processor = SpecializedProcessor(
        "Special Processor", 
        {"level": "specialized", "optimization": "enabled"}
    )
    print(f"Subclass from subpackage: {spec_processor.execute('critical task')}")

if __name__ == "__main__":
    main()