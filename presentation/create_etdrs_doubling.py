#!/usr/bin/env python3
"""
Create ETDRS chart showing the doubling principle
"""

import matplotlib.pyplot as plt
import numpy as np

# ETDRS letter set (Sloan letters)
SLOAN_LETTERS = ['N', 'C', 'K', 'Z', 'O', 'R', 'H', 'S', 'D', 'V']

def create_doubling_chart(filename='etdrs_doubling.pdf'):
    """Create chart showing ETDRS doubling principle"""
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Remove axes
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Title
    ax.text(50, 95, 'ETDRS Vision Doubling Principle', fontsize=22, weight='bold', 
            ha='center', va='top')
    ax.text(50, 91, 'Letter Size Doubles Every 3 Lines', fontsize=14, 
            ha='center', va='top', style='italic')
    
    # Define vision levels with proper doubling
    # Base size for 6/6 vision
    base_size = 6
    
    # Vision levels - we'll calculate y positions based on letter heights
    levels = [
        ('6/96', 20, 16),   # 16x larger than 6/6
        ('6/48', 35, 8),    # 8x larger
        ('6/24', 55, 4),    # 4x larger  
        ('6/12', 70, 2),    # 2x larger
        ('6/6', 85, 1),     # Normal size
    ]
    
    # Generate consistent letters for comparison
    test_letters = ['N', 'C', 'K', 'Z', 'O']
    
    # Calculate y positions based on letter heights
    y_position = 85  # Start from top
    
    for snellen, etdrs, size_mult in levels:
        # Calculate font size
        font_size = base_size * size_mult
        
        # Calculate spacing - tight but readable
        letter_spacing = font_size * 0.115
        total_width = (len(test_letters) - 1) * letter_spacing
        
        # Center the letters
        start_x = 50 - (total_width / 2)
        
        # Draw letters
        for i, letter in enumerate(test_letters):
            x_pos = start_x + (i * letter_spacing)
            ax.text(x_pos, y_position, letter, fontsize=font_size, weight='bold',
                   ha='center', va='center', fontname='Arial')
        
        # Add measurements on the right
        info_text = f"{snellen} (ETDRS {etdrs})"
        ax.text(85, y_position, info_text, fontsize=12, ha='left', va='center',
               weight='bold')
        
        # Add size indicator on the left
        size_text = f"{size_mult}x"
        ax.text(15, y_position, size_text, fontsize=14, ha='right', va='center',
               color='red', weight='bold')
        
        # Add invisible spacer text below this row for proper spacing
        # Spacer is half the size of the letters
        spacer_size = font_size * 0.5
        ax.text(50, y_position - font_size, 'X', fontsize=spacer_size, 
                ha='center', va='top', alpha=0)  # alpha=0 makes it invisible
        
        # Move to next row - letter height + spacer height
        y_position -= (font_size + spacer_size)
    
    
    
    # Save
    plt.tight_layout()
    plt.savefig(filename, format='pdf', bbox_inches='tight')
    plt.savefig(filename.replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
    
    print(f"Doubling chart saved as {filename}")
    print(f"PNG version saved as {filename.replace('.pdf', '.png')}")

if __name__ == "__main__":
    create_doubling_chart()