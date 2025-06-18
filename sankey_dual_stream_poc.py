#!/usr/bin/env python3
"""
Proof of concept: Dual-stream Sankey diagram
Two separate flows in one diagram for proper scaling comparison
"""

import plotly.graph_objects as go
import plotly.io as pio

# Create a simple dual-stream Sankey
def create_dual_stream_sankey():
    """
    Create a Sankey with two separate streams:
    - Top stream: 3 → 2 + 1
    - Bottom stream: 3 → 1 + 2
    """
    
    # Define nodes for both streams
    # Top stream nodes (A): positions 0.7-0.9
    # Bottom stream nodes (B): positions 0.1-0.3
    
    nodes = [
        # Top stream (A) nodes
        "A: Start",      # 0
        "A: Path 1",     # 1  
        "A: Path 2",     # 2
        
        # Bottom stream (B) nodes  
        "B: Start",      # 3
        "B: Path 1",     # 4
        "B: Path 2",     # 5
    ]
    
    # Define node positions
    x_positions = [
        # Top stream
        0.1,  # A: Start
        0.9,  # A: Path 1
        0.9,  # A: Path 2
        
        # Bottom stream
        0.1,  # B: Start
        0.9,  # B: Path 1
        0.9,  # B: Path 2
    ]
    
    y_positions = [
        # Top stream (upper half)
        0.8,   # A: Start
        0.9,   # A: Path 1
        0.7,   # A: Path 2
        
        # Bottom stream (lower half)
        0.2,   # B: Start
        0.3,   # B: Path 1
        0.1,   # B: Path 2
    ]
    
    # Define colors
    node_colors = [
        # Top stream - blues
        "#1f77b4",  # A: Start
        "#4393c3",  # A: Path 1
        "#92c5de",  # A: Path 2
        
        # Bottom stream - greens
        "#2ca02c",  # B: Start
        "#7fbc41",  # B: Path 1
        "#c7e9b4",  # B: Path 2
    ]
    
    # Define links
    # Top stream: 3 → 2 + 1
    # Bottom stream: 3 → 1 + 2
    
    links = [
        # Top stream flows
        {"source": 0, "target": 1, "value": 2},  # A: Start → A: Path 1 (2)
        {"source": 0, "target": 2, "value": 1},  # A: Start → A: Path 2 (1)
        
        # Bottom stream flows
        {"source": 3, "target": 4, "value": 1},  # B: Start → B: Path 1 (1)
        {"source": 3, "target": 5, "value": 2},  # B: Start → B: Path 2 (2)
    ]
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        arrangement='fixed',  # Use our fixed positions
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes,
            color=node_colors,
            x=x_positions,
            y=y_positions,
        ),
        link=dict(
            source=[link["source"] for link in links],
            target=[link["target"] for link in links],
            value=[link["value"] for link in links],
            color=[
                "rgba(31, 119, 180, 0.4)",   # A flows - blue
                "rgba(31, 119, 180, 0.4)",
                "rgba(44, 160, 44, 0.4)",    # B flows - green
                "rgba(44, 160, 44, 0.4)",
            ]
        )
    )])
    
    # Add separator line
    fig.add_shape(
        type="line",
        x0=0, x1=1,
        y0=0.5, y1=0.5,
        line=dict(color="gray", width=2, dash="dash"),
        xref="paper", yref="paper"
    )
    
    # Add labels
    fig.add_annotation(
        text="Stream A: 3 → 2 + 1",
        xref="paper", yref="paper",
        x=0.5, y=0.95,
        showarrow=False,
        font=dict(size=14, color="blue")
    )
    
    fig.add_annotation(
        text="Stream B: 3 → 1 + 2", 
        xref="paper", yref="paper",
        x=0.5, y=0.05,
        showarrow=False,
        font=dict(size=14, color="green")
    )
    
    fig.update_layout(
        title="Dual-Stream Sankey Proof of Concept",
        height=600,
        width=800,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="white"
    )
    
    return fig

# Create and show the diagram
if __name__ == "__main__":
    fig = create_dual_stream_sankey()
    
    # Save as HTML for easy viewing
    fig.write_html("dual_stream_sankey_poc.html")
    print("Saved to dual_stream_sankey_poc.html")
    
    # Also save as image if kaleido is installed
    try:
        fig.write_image("dual_stream_sankey_poc.png")
        print("Saved to dual_stream_sankey_poc.png")
    except:
        print("Install kaleido to save as PNG: pip install kaleido")
    
    # Show in browser
    fig.show()