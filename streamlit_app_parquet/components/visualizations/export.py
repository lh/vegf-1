"""
Visualization export functionality for the APE Streamlit application.

This module provides functions to export visualizations to various formats
for use in reports, presentations, and publications. It works with the
visualization cache to avoid regenerating visualizations.
"""

import os
import base64
import logging
import tempfile
from typing import Dict, Any, Optional, List, Tuple, Union, BinaryIO
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image
import io

from streamlit_app.components.visualizations.cache import get_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default export directory
DEFAULT_EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 "output", "exports")

class VisualizationExporter:
    """Export visualizations to various formats."""
    
    def __init__(self, export_dir: Optional[str] = None):
        """Initialize the visualization exporter.
        
        Parameters
        ----------
        export_dir : str, optional
            Directory to export visualizations to, by default None
        """
        self.export_dir = export_dir or DEFAULT_EXPORT_DIR
        
        # Ensure export directory exists
        os.makedirs(self.export_dir, exist_ok=True)
        
        # Get visualization cache
        self.cache = get_cache()
    
    def export_visualization(
        self,
        viz_path: str,
        output_path: Optional[str] = None,
        format: Optional[str] = None,
        dpi: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> str:
        """Export a visualization to a file.
        
        Parameters
        ----------
        viz_path : str
            Path to the visualization
        output_path : str, optional
            Path to export to, by default None
        format : str, optional
            Format to export to, by default None
        dpi : int, optional
            Resolution in DPI, by default None
        width : int, optional
            Width in pixels, by default None
        height : int, optional
            Height in pixels, by default None
        
        Returns
        -------
        str
            Path to the exported visualization
        """
        # Check if the visualization exists
        if not os.path.exists(viz_path):
            logger.error(f"Visualization not found: {viz_path}")
            return ""
        
        # If no output path is provided, create one in the export directory
        if output_path is None:
            # Get original filename and extension
            viz_filename = os.path.basename(viz_path)
            viz_basename, viz_ext = os.path.splitext(viz_filename)
            
            # Use provided format or original format
            export_ext = f".{format.lower()}" if format else viz_ext
            
            # Create output path
            output_path = os.path.join(self.export_dir, f"{viz_basename}{export_ext}")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # Open the original image
            img = Image.open(viz_path)
            
            # Resize if width or height is provided
            if width or height:
                # Calculate new dimensions
                if width and height:
                    new_size = (width, height)
                elif width:
                    ratio = width / img.width
                    new_size = (width, int(img.height * ratio))
                else:  # height only
                    ratio = height / img.height
                    new_size = (int(img.width * ratio), height)
                
                # Resize image
                img = img.resize(new_size, Image.LANCZOS)
            
            # Save with specified format
            if format:
                format = format.upper()
                img.save(output_path, format=format, dpi=(dpi, dpi) if dpi else None)
            else:
                # Save with original format
                img.save(output_path, dpi=(dpi, dpi) if dpi else None)
            
            logger.info(f"Exported visualization to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error exporting visualization: {e}")
            return ""
    
    def export_matplotlib_figure(
        self,
        fig: plt.Figure,
        output_path: Optional[str] = None,
        format: str = "png",
        dpi: Optional[int] = None,
        transparent: bool = False,
        bbox_inches: str = 'tight'
    ) -> str:
        """Export a matplotlib figure to a file.
        
        Parameters
        ----------
        fig : plt.Figure
            Matplotlib figure to export
        output_path : str, optional
            Path to export to, by default None
        format : str, optional
            Format to export to, by default "png"
        dpi : int, optional
            Resolution in DPI, by default None
        transparent : bool, optional
            Whether to use a transparent background, by default False
        bbox_inches : str, optional
            Bounding box in inches, by default 'tight'
        
        Returns
        -------
        str
            Path to the exported figure
        """
        # If no output path is provided, create one in the export directory
        if output_path is None:
            # Create a unique filename
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            output_path = os.path.join(self.export_dir, f"figure_{unique_id}.{format.lower()}")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # Save figure
            fig.savefig(
                output_path,
                format=format,
                dpi=dpi,
                transparent=transparent,
                bbox_inches=bbox_inches
            )
            
            logger.info(f"Exported matplotlib figure to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error exporting matplotlib figure: {e}")
            return ""
    
    def export_for_report(
        self,
        simulation_id: str,
        output_dir: Optional[str] = None,
        format: str = "png",
        dpi: int = 300
    ) -> Dict[str, str]:
        """Export all visualizations for a simulation for use in a report.
        
        Parameters
        ----------
        simulation_id : str
            Simulation ID
        output_dir : str, optional
            Directory to export to, by default None
        format : str, optional
            Format to export to, by default "png"
        dpi : int, optional
            Resolution in DPI, by default 300
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping visualization types to file paths
        """
        # Get the export directory
        if output_dir is None:
            output_dir = os.path.join(self.export_dir, f"report_{simulation_id}")
        
        # Ensure export directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Get all visualizations for the simulation
        viz_paths = self.cache.get_visualizations_for_simulation(simulation_id)
        
        # Dictionary to store exported visualization paths
        exported_viz = {}
        
        # Export each visualization
        for viz_path in viz_paths:
            try:
                # Get visualization type from metadata
                viz_type = "unknown"
                for key, meta in self.cache.metadata.items():
                    if meta.file_path == viz_path:
                        viz_type = meta.viz_type
                        break
                
                # Create output path
                output_path = os.path.join(output_dir, f"{viz_type}.{format}")
                
                # Export visualization
                exported_path = self.export_visualization(
                    viz_path=viz_path,
                    output_path=output_path,
                    format=format,
                    dpi=dpi
                )
                
                if exported_path:
                    exported_viz[viz_type] = exported_path
            except Exception as e:
                logger.error(f"Error exporting visualization {viz_path}: {e}")
        
        return exported_viz
    
    def get_html_img_tag(
        self,
        viz_path: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        alt: str = "Visualization",
        style: str = ""
    ) -> str:
        """Get an HTML img tag for a visualization.
        
        Parameters
        ----------
        viz_path : str
            Path to the visualization
        width : int, optional
            Width in pixels, by default None
        height : int, optional
            Height in pixels, by default None
        alt : str, optional
            Alt text, by default "Visualization"
        style : str, optional
            CSS style, by default ""
        
        Returns
        -------
        str
            HTML img tag
        """
        # Check if the visualization exists
        if not os.path.exists(viz_path):
            logger.error(f"Visualization not found: {viz_path}")
            return f"<p>Image not found: {viz_path}</p>"
        
        try:
            # Read image
            with open(viz_path, "rb") as f:
                img_data = f.read()
            
            # Determine MIME type based on extension
            ext = os.path.splitext(viz_path)[1].lower()
            mime_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
                ".pdf": "application/pdf"
            }.get(ext, "image/png")
            
            # Encode as base64
            encoded = base64.b64encode(img_data).decode("utf-8")
            
            # Create data URL
            data_url = f"data:{mime_type};base64,{encoded}"
            
            # Create img tag
            width_attr = f'width="{width}" ' if width else ""
            height_attr = f'height="{height}" ' if height else ""
            style_attr = f'style="{style}" ' if style else ""
            
            return f'<img src="{data_url}" {width_attr}{height_attr}alt="{alt}" {style_attr}/>'
        except Exception as e:
            logger.error(f"Error creating HTML img tag: {e}")
            return f"<p>Error loading image: {str(e)}</p>"
    
    def embed_in_markdown(
        self,
        viz_path: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        alt: str = "Visualization",
        caption: Optional[str] = None
    ) -> str:
        """Embed a visualization in markdown.
        
        Parameters
        ----------
        viz_path : str
            Path to the visualization
        width : int, optional
            Width in pixels, by default None
        height : int, optional
            Height in pixels, by default None
        alt : str, optional
            Alt text, by default "Visualization"
        caption : str, optional
            Caption text, by default None
        
        Returns
        -------
        str
            Markdown with embedded visualization
        """
        # Get HTML img tag
        img_tag = self.get_html_img_tag(viz_path, width, height, alt)
        
        # Add caption if provided
        if caption:
            return f"<figure>\n{img_tag}\n<figcaption>{caption}</figcaption>\n</figure>"
        else:
            return img_tag


# Global instance for easy access
_exporter_instance = None

def get_exporter(reset: bool = False) -> VisualizationExporter:
    """Get the global visualization exporter instance.
    
    Parameters
    ----------
    reset : bool, optional
        Whether to reset the exporter, by default False
    
    Returns
    -------
    VisualizationExporter
        Global visualization exporter instance
    """
    global _exporter_instance
    
    if _exporter_instance is None or reset:
        _exporter_instance = VisualizationExporter()
    
    return _exporter_instance