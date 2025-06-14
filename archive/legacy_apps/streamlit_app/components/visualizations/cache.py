"""
Visualization caching system for the APE Streamlit application.

This module provides functionality to cache visualizations to disk,
allowing them to be reused across sessions and in reports without
regeneration, which is particularly important for expensive R-based
visualizations.
"""

import os
import json
import time
import hashlib
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default cache directory
DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                "output", "visualization_cache")

@dataclass
class VisualizationMetadata:
    """Metadata for cached visualizations."""
    
    viz_type: str
    created_at: float  # Unix timestamp
    simulation_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    data_hash: Optional[str] = None
    file_path: Optional[str] = None
    format: str = "png"
    width: int = 10
    height: int = 5
    dpi: int = 120
    
    @property
    def age_seconds(self) -> float:
        """Get the age of the visualization in seconds."""
        return time.time() - self.created_at


class VisualizationCache:
    """Cache for visualizations to avoid regeneration."""
    
    def __init__(self, cache_dir: Optional[str] = None, max_cache_age_days: int = 7):
        """Initialize the visualization cache.
        
        Parameters
        ----------
        cache_dir : str, optional
            Directory to store cached visualizations, by default None
        max_cache_age_days : int, optional
            Maximum age of cached items in days, by default 7
        """
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.max_cache_age_seconds = max_cache_age_days * 24 * 60 * 60
        self.metadata_file = os.path.join(self.cache_dir, "metadata.json")
        self.metadata: Dict[str, VisualizationMetadata] = {}
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load existing metadata
        self._load_metadata()
        
        # Clean up old cache entries
        self._cleanup_cache()
    
    def _load_metadata(self) -> None:
        """Load metadata from disk."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    metadata_dict = json.load(f)
                
                # Convert to VisualizationMetadata objects
                for key, data in metadata_dict.items():
                    self.metadata[key] = VisualizationMetadata(
                        viz_type=data.get("viz_type", "unknown"),
                        created_at=data.get("created_at", 0),
                        simulation_id=data.get("simulation_id"),
                        parameters=data.get("parameters", {}),
                        data_hash=data.get("data_hash"),
                        file_path=data.get("file_path"),
                        format=data.get("format", "png"),
                        width=data.get("width", 10),
                        height=data.get("height", 5),
                        dpi=data.get("dpi", 120)
                    )
                
                logger.info(f"Loaded {len(self.metadata)} visualization cache entries")
            except Exception as e:
                logger.error(f"Error loading visualization cache metadata: {e}")
                self.metadata = {}
    
    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        try:
            # Convert to dictionary format
            metadata_dict = {}
            for key, meta in self.metadata.items():
                metadata_dict[key] = {
                    "viz_type": meta.viz_type,
                    "created_at": meta.created_at,
                    "simulation_id": meta.simulation_id,
                    "parameters": meta.parameters,
                    "data_hash": meta.data_hash,
                    "file_path": meta.file_path,
                    "format": meta.format,
                    "width": meta.width,
                    "height": meta.height,
                    "dpi": meta.dpi
                }
            
            # Save to file
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata_dict, f, indent=2)
            
            logger.info(f"Saved {len(self.metadata)} visualization cache entries")
        except Exception as e:
            logger.error(f"Error saving visualization cache metadata: {e}")
    
    def _cleanup_cache(self) -> None:
        """Clean up old cache entries."""
        # Get current time
        now = time.time()
        
        # Find old entries
        old_keys = []
        missing_files = []
        
        for key, meta in self.metadata.items():
            # Check age
            if now - meta.created_at > self.max_cache_age_seconds:
                old_keys.append(key)
            
            # Check if file exists
            if meta.file_path and not os.path.exists(meta.file_path):
                missing_files.append(key)
        
        # Remove old entries
        for key in old_keys:
            self._remove_cache_entry(key)
        
        # Remove entries with missing files
        for key in missing_files:
            if key not in old_keys:  # Avoid double removal
                self._remove_cache_entry(key)
        
        if old_keys or missing_files:
            logger.info(f"Cleaned up {len(old_keys)} old and {len(missing_files)} missing cache entries")
            self._save_metadata()
    
    def _remove_cache_entry(self, key: str) -> None:
        """Remove a cache entry.
        
        Parameters
        ----------
        key : str
            Cache entry key
        """
        if key in self.metadata:
            # Delete file if it exists
            if self.metadata[key].file_path and os.path.exists(self.metadata[key].file_path):
                try:
                    os.remove(self.metadata[key].file_path)
                except Exception as e:
                    logger.error(f"Error removing cached file: {e}")
            
            # Remove from metadata
            del self.metadata[key]
    
    def _hash_data(self, data: Any) -> str:
        """Create a hash of data for caching.
        
        Parameters
        ----------
        data : Any
            Data to hash
        
        Returns
        -------
        str
            Hash of the data
        """
        try:
            # Serialize data
            if isinstance(data, pd.DataFrame):
                data_bytes = pickle.dumps(data.reset_index(drop=True))
            else:
                data_bytes = pickle.dumps(data)
            
            # Create hash
            return hashlib.md5(data_bytes).hexdigest()
        except Exception as e:
            logger.error(f"Error hashing data: {e}")
            # Use timestamp as fallback
            return f"unhashable_{int(time.time())}"
    
    def _generate_cache_key(self, viz_type: str, data_hash: str, parameters: Dict[str, Any]) -> str:
        """Generate a cache key.
        
        Parameters
        ----------
        viz_type : str
            Type of visualization
        data_hash : str
            Hash of the data
        parameters : Dict[str, Any]
            Visualization parameters
        
        Returns
        -------
        str
            Cache key
        """
        # Hash parameters
        params_str = json.dumps(parameters, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        
        # Combine with visualization type and data hash
        return f"{viz_type}_{data_hash}_{params_hash}"
    
    def get_cached_visualization(
        self, 
        viz_type: str, 
        data: Any, 
        parameters: Dict[str, Any] = None,
        simulation_id: Optional[str] = None
    ) -> Optional[str]:
        """Get a cached visualization if available.
        
        Parameters
        ----------
        viz_type : str
            Type of visualization
        data : Any
            Data used to create the visualization
        parameters : Dict[str, Any], optional
            Visualization parameters, by default None
        simulation_id : str, optional
            Simulation ID for the visualization, by default None
        
        Returns
        -------
        Optional[str]
            Path to the cached visualization if available, None otherwise
        """
        # Default parameters
        parameters = parameters or {}
        
        # Hash the data
        data_hash = self._hash_data(data)
        
        # Generate cache key
        cache_key = self._generate_cache_key(viz_type, data_hash, parameters)
        
        # Check if we have a cached version
        if cache_key in self.metadata:
            meta = self.metadata[cache_key]
            
            # Check if the file exists
            if meta.file_path and os.path.exists(meta.file_path):
                logger.info(f"Found cached visualization: {meta.file_path}")
                return meta.file_path
        
        return None
    
    def cache_visualization(
        self,
        viz_type: str,
        data: Any,
        file_path: str,
        parameters: Dict[str, Any] = None,
        simulation_id: Optional[str] = None,
        format: str = "png",
        width: int = 10,
        height: int = 5,
        dpi: int = 120
    ) -> str:
        """Cache a visualization.
        
        Parameters
        ----------
        viz_type : str
            Type of visualization
        data : Any
            Data used to create the visualization
        file_path : str
            Path to the visualization file
        parameters : Dict[str, Any], optional
            Visualization parameters, by default None
        simulation_id : str, optional
            Simulation ID for the visualization, by default None
        format : str, optional
            File format, by default "png"
        width : int, optional
            Width of the visualization in inches, by default 10
        height : int, optional
            Height of the visualization in inches, by default 5
        dpi : int, optional
            Resolution of the visualization in DPI, by default 120
        
        Returns
        -------
        str
            Path to the cached visualization
        """
        # Default parameters
        parameters = parameters or {}
        
        # Hash the data
        data_hash = self._hash_data(data)
        
        # Generate cache key
        cache_key = self._generate_cache_key(viz_type, data_hash, parameters)
        
        # Create cached file name
        filename = f"{cache_key}.{format}"
        cached_path = os.path.join(self.cache_dir, filename)
        
        # If file_path is different from cached_path, copy the file
        if file_path != cached_path and os.path.exists(file_path):
            # Copy file to cache directory
            import shutil
            try:
                shutil.copy2(file_path, cached_path)
            except Exception as e:
                logger.error(f"Error copying visualization to cache: {e}")
                # Use original path if copy fails
                cached_path = file_path
        
        # Update metadata
        self.metadata[cache_key] = VisualizationMetadata(
            viz_type=viz_type,
            created_at=time.time(),
            simulation_id=simulation_id,
            parameters=parameters,
            data_hash=data_hash,
            file_path=cached_path,
            format=format,
            width=width,
            height=height,
            dpi=dpi
        )
        
        # Save metadata
        self._save_metadata()
        
        logger.info(f"Cached visualization: {cached_path}")
        return cached_path
    
    def cache_matplotlib_figure(
        self,
        viz_type: str,
        fig: plt.Figure,
        data: Any,
        parameters: Dict[str, Any] = None,
        simulation_id: Optional[str] = None,
        format: str = "png",
        dpi: Optional[int] = None
    ) -> str:
        """Cache a matplotlib figure.
        
        Parameters
        ----------
        viz_type : str
            Type of visualization
        fig : plt.Figure
            Matplotlib figure to cache
        data : Any
            Data used to create the visualization
        parameters : Dict[str, Any], optional
            Visualization parameters, by default None
        simulation_id : str, optional
            Simulation ID for the visualization, by default None
        format : str, optional
            File format, by default "png"
        dpi : int, optional
            Resolution of the visualization in DPI, by default None
        
        Returns
        -------
        str
            Path to the cached visualization
        """
        # Default parameters
        parameters = parameters or {}
        
        # Hash the data
        data_hash = self._hash_data(data)
        
        # Generate cache key
        cache_key = self._generate_cache_key(viz_type, data_hash, parameters)
        
        # Create cached file name
        filename = f"{cache_key}.{format}"
        cached_path = os.path.join(self.cache_dir, filename)
        
        # Get figure size
        fig_width, fig_height = fig.get_size_inches()
        
        # Save figure to cache
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(cached_path), exist_ok=True)
            
            # Save figure
            fig.savefig(cached_path, format=format, dpi=dpi, bbox_inches='tight')
            
            # Update metadata
            self.metadata[cache_key] = VisualizationMetadata(
                viz_type=viz_type,
                created_at=time.time(),
                simulation_id=simulation_id,
                parameters=parameters,
                data_hash=data_hash,
                file_path=cached_path,
                format=format,
                width=fig_width,
                height=fig_height,
                dpi=dpi or fig.dpi
            )
            
            # Save metadata
            self._save_metadata()
            
            logger.info(f"Cached matplotlib figure: {cached_path}")
            return cached_path
        except Exception as e:
            logger.error(f"Error caching matplotlib figure: {e}")
            return ""
    
    def get_visualizations_for_simulation(self, simulation_id: str) -> List[str]:
        """Get all visualizations for a simulation.
        
        Parameters
        ----------
        simulation_id : str
            Simulation ID
        
        Returns
        -------
        List[str]
            List of paths to visualizations
        """
        viz_paths = []
        
        for key, meta in self.metadata.items():
            if meta.simulation_id == simulation_id and meta.file_path and os.path.exists(meta.file_path):
                viz_paths.append(meta.file_path)
        
        return viz_paths
    
    def clear_cache(self) -> None:
        """Clear the entire cache."""
        # Remove all files
        for key, meta in self.metadata.items():
            if meta.file_path and os.path.exists(meta.file_path):
                try:
                    os.remove(meta.file_path)
                except Exception as e:
                    logger.error(f"Error removing cached file: {e}")
        
        # Clear metadata
        self.metadata = {}
        
        # Save empty metadata
        self._save_metadata()
        
        logger.info("Cleared visualization cache")


# Global instance for easy access
_cache_instance = None

def get_cache(reset: bool = False) -> VisualizationCache:
    """Get the global visualization cache instance.
    
    Parameters
    ----------
    reset : bool, optional
        Whether to reset the cache, by default False
    
    Returns
    -------
    VisualizationCache
        Global visualization cache instance
    """
    global _cache_instance
    
    if _cache_instance is None or reset:
        _cache_instance = VisualizationCache()
    
    return _cache_instance