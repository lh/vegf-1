"""
Main script that imports functionality from module_a.
"""

# Import the greeting function and DataProcessor class from module_a
from module_a import greeting, DataProcessor

def main():
    """Main function to demonstrate imports."""
    # Use the imported function
    message = greeting()
    print(message)
    
    # Create and use an instance of the imported class
    processor = DataProcessor("Main Processor")
    processed_data = processor.process("sample data")
    print(processed_data)

if __name__ == "__main__":
    main()