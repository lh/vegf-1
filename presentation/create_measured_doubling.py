#!/usr/bin/env python3
"""
ETDRS doubling demonstration with measured text heights
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import sys

def create_measured_doubling(filename='etdrs_measured_doubling.pdf', spacing_multiplier=0.65):
    """Create chart with properly measured spacing"""
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))
    
    # Remove axes
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # No title - just the letters
    
    # Starting parameters - start lower since we're cropping
    y_position = 80
    font_size = 48  # Start big
    
    # Vision levels
    levels = [
        ('6/96', 'ETDRS 20'),
        ('6/48', 'ETDRS 35'),
        ('6/24', 'ETDRS 55'),
        ('6/12', 'ETDRS 70'),
        ('6/6', 'ETDRS 85'),
    ]
    
    # Standard letters
    letters = 'NCKZO'
    
    # Need to draw the figure first to get renderer
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    
    for snellen, etdrs in levels:
        # Draw the letters
        text_obj = ax.text(50, y_position, letters, fontsize=font_size, weight='bold',
                           ha='center', va='center', fontname='monospace')
        
        # Get the actual bounding box of the text
        bbox = text_obj.get_window_extent(renderer=renderer)
        # Transform to data coordinates
        bbox_data = bbox.transformed(ax.transData.inverted())
        
        # Get actual height in data coordinates
        text_height = bbox_data.height
        
        # Add labels
        ax.text(10, y_position, snellen, fontsize=12, ha='left', va='center')
        ax.text(90, y_position, etdrs, fontsize=12, ha='right', va='center')
        
        # Move down by less than expected - measured spacing is off
        # Using configurable multiplier for spacing
        y_position -= (text_height * spacing_multiplier)
        
        # Halve the font size for next row
        font_size = font_size / 2
        
        # Redraw to update renderer
        fig.canvas.draw()
    
    # Save with tight cropping
    plt.tight_layout()
    
    # Get the bounding box of all the text elements to crop tightly
    # We'll set specific limits based on where the content actually is
    # Leave full page height but keep horizontal crop
    ax.set_xlim(5, 95)  # From left labels to right labels
    ax.set_ylim(0, 100)  # Full page height
    
    plt.savefig(filename, format='pdf', bbox_inches='tight', pad_inches=0.05)
    plt.savefig(filename.replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight', pad_inches=0.05)
    
    print(f"Measured doubling chart saved as {filename} (spacing multiplier: {spacing_multiplier})")

if __name__ == "__main__":
    # Check if spacing multiplier provided as command line argument
    if len(sys.argv) > 1:
        try:
            multiplier = float(sys.argv[1])
            print(f"Using spacing multiplier: {multiplier}")
            create_measured_doubling(spacing_multiplier=multiplier)
        except ValueError:
            print("Invalid multiplier. Usage: python create_measured_doubling.py [multiplier]")
            print("Example: python create_measured_doubling.py 0.7")
    else:
        create_measured_doubling()