#!/usr/bin/env python3
"""
Simple ETDRS doubling demonstration
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_simple_doubling(filename='etdrs_simple_doubling.pdf'):
    """Create a simple chart showing letter size halving"""
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))
    
    # Remove axes
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Title
    ax.text(50, 95, 'ETDRS Vision Doubling Principle', fontsize=20, weight='bold', 
            ha='center', va='top')
    
    # Starting parameters
    y_position = 85
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
    
    for snellen, etdrs in levels:
        # Draw the letters as a single string (natural spacing)
        ax.text(50, y_position, letters, fontsize=font_size, weight='bold',
               ha='center', va='center', fontname='monospace')
        
        # Add labels
        ax.text(10, y_position, snellen, fontsize=12, ha='left', va='center')
        ax.text(90, y_position, etdrs, fontsize=12, ha='right', va='center')
        
        # Move down by 1.5x current font size (letter height + half line space)
        y_position -= (font_size * 1.5)
        
        # Halve the font size for next row
        font_size = font_size / 2
    
    # Save
    plt.tight_layout()
    plt.savefig(filename, format='pdf', bbox_inches='tight')
    plt.savefig(filename.replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
    
    print(f"Simple doubling chart saved as {filename}")

if __name__ == "__main__":
    create_simple_doubling()