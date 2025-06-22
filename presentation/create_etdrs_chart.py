#!/usr/bin/env python3
"""
Create a pyramid-shaped ETDRS chart
4 metre version with top letters = 6/60 Snellen
Going down to 6/6 (85 letters, LogMAR 0.0)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

# ETDRS letter set (Sloan letters)
SLOAN_LETTERS = ['N', 'C', 'K', 'Z', 'O', 'R', 'H', 'S', 'D', 'V']

# ETDRS chart structure - focused on key clinical thresholds
# Every 3 lines (15 letters) = doubling of visual angle
# Key clinical thresholds: 6/96 (lower threshold), 6/12 (treatment threshold), 6/6 (normal)
ETDRS_ROWS = [
    # (Snellen 6/x, LogMAR, ETDRS score, number of letters, letter height in mm at 4m)
    # Lower threshold for treatment
    (96, 1.2, 20, 5, 93.2),       # Row 1: 6/96 (ETDRS 20) - Lower treatment threshold
    (76, 1.1, 25, 5, 73.8),       # Row 2: 6/76 (ETDRS 25)
    (60, 1.0, 30, 5, 58.2),       # Row 3: 6/60 (ETDRS 30)
    (48, 0.9, 35, 5, 46.5),       # Row 4: 6/48 (ETDRS 35)
    (38, 0.8, 40, 5, 36.9),       # Row 5: 6/38 (ETDRS 40)
    # Doubling point
    (30, 0.7, 45, 5, 29.1),       # Row 6: 6/30 (ETDRS 45)
    (24, 0.6, 50, 5, 23.3),       # Row 7: 6/24 (ETDRS 50)
    (19, 0.5, 55, 5, 18.4),       # Row 8: 6/19 (ETDRS 55)
    (15, 0.4, 60, 5, 14.6),       # Row 9: 6/15 (ETDRS 60)
    (12, 0.3, 65, 5, 11.6),       # Row 10: 6/12 (ETDRS 65)
    # Treatment threshold
    (12, 0.3, 70, 5, 11.6),       # Row 11: 6/12 (ETDRS 70) - Treatment threshold
    (9.5, 0.2, 75, 5, 9.2),       # Row 12: 6/9.5 (ETDRS 75)
    (7.5, 0.1, 80, 5, 7.3),       # Row 13: 6/7.5 (ETDRS 80)
    # Normal vision
    (6, 0.0, 85, 5, 5.8),         # Row 14: 6/6 (ETDRS 85) - Normal vision
]

def generate_random_letters(n):
    """Generate n random Sloan letters"""
    return np.random.choice(SLOAN_LETTERS, n, replace=True)

def create_etdrs_chart(filename='etdrs_chart_extended.pdf'):
    """Create an extended ETDRS chart"""
    
    # Create figure with appropriate dimensions
    # A4 portrait orientation
    fig_width = 8.27  # inches
    fig_height = 11.69  # inches
    
    fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height))
    
    # Remove axes
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 170)
    ax.axis('off')
    
    # Title
    ax.text(50, 165, 'ETDRS Chart (4m)', fontsize=20, weight='bold', 
            ha='center', va='top')
    ax.text(50, 160, 'Extended Format: 0 to 85 Letters', fontsize=14, 
            ha='center', va='top')
    
    # Column headers
    ax.text(5, 155, 'LogMAR', fontsize=10, weight='bold', ha='left')
    ax.text(88, 155, 'ETDRS', fontsize=10, weight='bold', ha='right')
    ax.text(95, 155, 'Snellen', fontsize=10, weight='bold', ha='right')
    
    # Starting y position
    y_position = 150
    
    # Calculate total height needed
    total_rows = len(ETDRS_ROWS)
    available_height = 130  # from y=150 down to y=20
    
    # Draw each row
    for i, (snellen, logmar, etdrs_score, num_letters, letter_height_mm) in enumerate(ETDRS_ROWS):
        # Generate random letters for this row
        letters = generate_random_letters(num_letters)
        
        # Scale font size proportionally to create pyramid effect
        # Larger letters at top, progressively smaller
        scale_factor = 0.3 if i == 0 else 0.25  # Make top letter bigger
        font_size = letter_height_mm * scale_factor * (1 - i * 0.03)  # Progressive reduction
        
        # Calculate spacing between letters - uniform spacing
        # Standard spacing for all rows
        spacing_factor = 0.5
        letter_spacing = font_size * spacing_factor
        total_letter_width = (num_letters - 1) * letter_spacing
        start_x = 50 - (total_letter_width / 2)
        
        # Draw letters
        for j, letter in enumerate(letters):
            x_pos = start_x + (j * letter_spacing)
            ax.text(x_pos, y_position, letter, fontsize=font_size, 
                   weight='bold', ha='center', va='center',
                   fontname='Arial')
        
        # Add row information on the sides
        # Left side: LogMAR
        ax.text(5, y_position, f"{logmar:+.1f}", fontsize=8, ha='left', va='center')
        
        # Right side: Snellen and ETDRS score
        info_text = f"6/{snellen:.0f}" if snellen >= 10 else f"6/{snellen:.1f}"
        ax.text(95, y_position, info_text, fontsize=8, ha='right', va='center')
        ax.text(88, y_position, f"{etdrs_score}", fontsize=8, 
                ha='right', va='center', weight='bold')
        
        # Adjust y position for next row
        # Use proportional spacing that gets tighter as we go down
        base_spacing = 7.5  # Base spacing between rows
        y_spacing = base_spacing * (1 - i * 0.02)  # Slightly tighter as we go down
        y_position -= y_spacing
    
    # Add footer information
    ax.text(50, 10, 'Testing Distance: 4 metres', fontsize=10, 
            ha='center', va='bottom')
    ax.text(50, 7, '85 letters = 6/6 = LogMAR 0.0', fontsize=9, 
            ha='center', va='bottom', weight='bold')
    ax.text(50, 4, 'Extended format with 5 letters per row throughout', fontsize=8, 
            ha='center', va='bottom')
    
    # Add vertical line to emphasize pyramid
    for i in range(len(ETDRS_ROWS)):
        ax.axhline(y=y_position + i * 6, color='lightgray', linewidth=0.5, alpha=0.3)
    
    # Save as PDF
    plt.tight_layout()
    plt.savefig(filename, format='pdf', bbox_inches='tight')
    plt.savefig(filename.replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
    
    print(f"ETDRS chart saved as {filename}")
    print(f"PNG version saved as {filename.replace('.pdf', '.png')}")
    
    # Also create a simplified version showing the concept
    create_concept_diagram()

def create_concept_diagram():
    """Create a simplified diagram showing the concept"""
    fig, ax = plt.subplots(1, 1, figsize=(6, 8))
    
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Title
    ax.text(50, 95, 'ETDRS Chart Concept', fontsize=16, weight='bold', 
            ha='center', va='top')
    ax.text(50, 90, 'Progressive Letter Size Reduction', fontsize=12, 
            ha='center', va='top')
    
    # Show a few key rows matching our ETDRS table
    # 85 letters = 6/6, ETDRS 70 = 6/12 (not 6/6!)
    key_rows = [
        (85, 'N C K Z O', 30, '6/60 (ETDRS 20)', 'Legally Blind'),
        (70, 'R H S D V', 20, '6/24 (ETDRS 40)', 'Severe Impairment'),
        (55, 'N O Z K C', 15, '6/12 (ETDRS 55)', 'Driving Standard'),
        (40, 'D V H R S', 10, '6/12 (ETDRS 70)', 'Good Vision'),  # ETDRS 70 = 6/12!
        (25, 'K Z O', 7, '6/6 (ETDRS 85)', 'Excellent Vision'),  # 85 letters = 6/6!
        (10, 'N', 5, '6/1.2 (ETDRS 105)', 'Single Letter'),
    ]
    
    for y, letters, size, label, description in key_rows:
        # Draw letters
        ax.text(50, y, letters, fontsize=size, weight='bold', 
                ha='center', va='center', fontname='Arial')
        
        # Add labels
        ax.text(5, y, label, fontsize=8, ha='left', va='center')
        ax.text(95, y, description, fontsize=8, ha='right', va='center',
                style='italic', color='gray')
    
    # Add explanation
    ax.text(50, 5, 'Extended ETDRS allows measurement down to single letter recognition', 
            fontsize=10, ha='center', va='bottom', wrap=True)
    
    plt.tight_layout()
    plt.savefig('etdrs_concept.pdf', format='pdf', bbox_inches='tight')
    plt.savefig('etdrs_concept.png', format='png', dpi=300, bbox_inches='tight')
    
    print("Concept diagram saved as etdrs_concept.pdf and etdrs_concept.png")

if __name__ == "__main__":
    create_etdrs_chart()