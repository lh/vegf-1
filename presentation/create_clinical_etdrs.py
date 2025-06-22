#!/usr/bin/env python3
"""
Create a simplified ETDRS chart focusing on key clinical thresholds
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

# ETDRS letter set (Sloan letters)
SLOAN_LETTERS = ['N', 'C', 'K', 'Z', 'O', 'R', 'H', 'S', 'D', 'V']

def generate_random_letters(n):
    """Generate n random Sloan letters"""
    return np.random.choice(SLOAN_LETTERS, n, replace=True)

def create_clinical_etdrs_chart(filename='etdrs_clinical_thresholds.pdf'):
    """Create a simplified ETDRS chart showing key clinical thresholds"""
    
    # Create figure
    fig_width = 10
    fig_height = 8
    
    fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height))
    
    # Remove axes
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Title
    ax.text(50, 95, 'ETDRS Clinical Thresholds', fontsize=24, weight='bold', 
            ha='center', va='top')
    ax.text(50, 90, 'Key Vision Levels for Treatment Decisions', fontsize=16, 
            ha='center', va='top')
    
    # Key thresholds to display
    # Letter size should double when visual angle doubles
    # 6/96 is 16x larger than 6/6, 6/48 is 8x, 6/24 is 4x, 6/12 is 2x
    base_size = 10  # Size for 6/6
    
    thresholds = [
        # (y_pos, Snellen, LogMAR, ETDRS, letters, size_multiplier, color, label)
        (70, 96, 1.2, 20, generate_random_letters(5), 16, '#d32f2f', 'Lower Treatment Threshold'),
        (55, 48, 0.9, 35, generate_random_letters(5), 8, '#ff6b35', '6/48'),
        (40, 24, 0.6, 55, generate_random_letters(5), 4, '#ff9800', '6/24'),
        (30, 12, 0.3, 70, generate_random_letters(5), 2, '#2196f3', 'Treatment Threshold'),
        (20, 6, 0.0, 85, generate_random_letters(5), 1, '#4caf50', 'Normal Vision'),
    ]
    
    # Draw each threshold
    for y_pos, snellen, logmar, etdrs, letters, size_mult, color, label in thresholds:
        # Calculate actual font size
        font_size = base_size * size_mult
        
        # Draw letters with proper spacing
        letter_spacing = font_size * 0.7
        total_width = (len(letters) - 1) * letter_spacing
        start_x = 50 - (total_width / 2)
        
        for i, letter in enumerate(letters):
            x_pos = start_x + (i * letter_spacing)
            ax.text(x_pos, y_pos, letter, fontsize=font_size, weight='bold',
                   ha='center', va='center', color=color, fontname='Arial')
        
        # Add labels
        info_y = y_pos
        
        # Left side: clinical significance
        ax.text(5, y_pos, label, fontsize=12, ha='left', va='center',
               weight='bold', color=color)
        
        # Right side: measurements
        measurements = f"6/{snellen} • ETDRS {etdrs} • LogMAR {logmar:.1f}"
        ax.text(95, y_pos, measurements, fontsize=10, ha='right', va='center')
    
    # Add explanation box
    box_y = 10
    box_props = dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.2)
    
    explanation = (
        "Visual Acuity Progression:\n"
        "• Every 3 lines (15 letters) = doubling of visual angle\n"
        "• 6/96 → 6/48 → 6/24 → 6/12 → 6/6\n"
        "• Treatment typically indicated between 6/96 and 6/12"
    )
    
    ax.text(50, box_y, explanation, fontsize=11, ha='center', va='center',
            bbox=box_props, linespacing=1.5)
    
    # Save
    plt.tight_layout()
    plt.savefig(filename, format='pdf', bbox_inches='tight')
    plt.savefig(filename.replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
    
    print(f"Clinical ETDRS chart saved as {filename}")
    print(f"PNG version saved as {filename.replace('.pdf', '.png')}")

if __name__ == "__main__":
    create_clinical_etdrs_chart()