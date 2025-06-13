"""
Simulation registry for tracking and managing saved simulations.

Provides a centralized index of all simulations with metadata for
quick browsing and loading.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import shutil


class SimulationRegistry:
    """Manage registry of saved simulations."""
    
    REGISTRY_FILE = "simulation_registry.json"
    MAX_SIMULATIONS = 50  # Maximum saved simulations
    
    def __init__(self, base_dir: Path):
        """
        Initialize registry.
        
        Args:
            base_dir: Base directory for simulation storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.base_dir / self.REGISTRY_FILE
        
        # Load or create registry
        self._registry = self._load_registry()
        
    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from disk or create new."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        else:
            return {
                'version': '1.0',
                'simulations': {},
                'last_updated': datetime.now().isoformat()
            }
            
    def _save_registry(self) -> None:
        """Save registry to disk."""
        self._registry['last_updated'] = datetime.now().isoformat()
        with open(self.registry_path, 'w') as f:
            json.dump(self._registry, f, indent=2)
            
    def register_simulation(
        self,
        sim_id: str,
        metadata: Dict[str, Any],
        size_mb: float
    ) -> None:
        """
        Register a new simulation.
        
        Args:
            sim_id: Simulation identifier
            metadata: Simulation metadata
            size_mb: Size in megabytes
        """
        # Add to registry
        self._registry['simulations'][sim_id] = {
            'metadata': metadata,
            'size_mb': size_mb,
            'created': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'access_count': 0
        }
        
        # Check if we need to clean up old simulations
        if len(self._registry['simulations']) > self.MAX_SIMULATIONS:
            self._cleanup_old_simulations()
            
        self._save_registry()
        
    def get_simulation_info(self, sim_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a simulation.
        
        Args:
            sim_id: Simulation identifier
            
        Returns:
            Simulation info or None if not found
        """
        if sim_id in self._registry['simulations']:
            # Update access info
            sim_info = self._registry['simulations'][sim_id]
            sim_info['last_accessed'] = datetime.now().isoformat()
            sim_info['access_count'] += 1
            self._save_registry()
            
            return sim_info
        return None
        
    def list_simulations(
        self,
        sort_by: str = 'created',
        descending: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List all simulations with sorting.
        
        Args:
            sort_by: Field to sort by ('created', 'last_accessed', 'size_mb')
            descending: Sort order
            limit: Maximum number to return
            
        Returns:
            List of simulation info dictionaries
        """
        simulations = []
        
        for sim_id, info in self._registry['simulations'].items():
            sim_data = {
                'sim_id': sim_id,
                **info,
                **info['metadata']
            }
            simulations.append(sim_data)
            
        # Sort
        if sort_by in ['created', 'last_accessed']:
            simulations.sort(
                key=lambda x: x[sort_by],
                reverse=descending
            )
        elif sort_by == 'size_mb':
            simulations.sort(
                key=lambda x: x['size_mb'],
                reverse=descending
            )
            
        # Limit
        if limit:
            simulations = simulations[:limit]
            
        return simulations
        
    def delete_simulation(self, sim_id: str) -> bool:
        """
        Delete a simulation and its data.
        
        Args:
            sim_id: Simulation identifier
            
        Returns:
            True if deleted successfully
        """
        if sim_id not in self._registry['simulations']:
            return False
            
        # Delete data directory
        sim_dir = self.base_dir / sim_id
        if sim_dir.exists():
            shutil.rmtree(sim_dir)
            
        # Remove from registry
        del self._registry['simulations'][sim_id]
        self._save_registry()
        
        return True
        
    def _cleanup_old_simulations(self) -> None:
        """Clean up oldest simulations when limit exceeded."""
        # Get simulations sorted by last access time
        simulations = self.list_simulations(
            sort_by='last_accessed',
            descending=False
        )
        
        # Delete oldest until under limit
        while len(self._registry['simulations']) > self.MAX_SIMULATIONS:
            oldest = simulations.pop(0)
            self.delete_simulation(oldest['sim_id'])
            
    def get_total_size_mb(self) -> float:
        """Get total size of all simulations."""
        total = 0
        for info in self._registry['simulations'].values():
            total += info['size_mb']
        return total
        
    def cleanup_orphaned_directories(self) -> int:
        """
        Clean up directories not in registry.
        
        Returns:
            Number of directories cleaned
        """
        cleaned = 0
        
        # Find all directories
        for path in self.base_dir.iterdir():
            if path.is_dir() and path.name not in self._registry['simulations']:
                # This is an orphaned directory
                shutil.rmtree(path)
                cleaned += 1
                
        return cleaned
        
    def export_summary(self) -> pd.DataFrame:
        """
        Export registry summary as DataFrame.
        
        Returns:
            DataFrame with simulation summaries
        """
        simulations = self.list_simulations()
        
        if not simulations:
            return pd.DataFrame()
            
        # Flatten the data
        records = []
        for sim in simulations:
            record = {
                'sim_id': sim['sim_id'],
                'protocol_name': sim.get('protocol_name', 'Unknown'),
                'n_patients': sim.get('n_patients', 0),
                'duration_years': sim.get('duration_years', 0),
                'size_mb': sim['size_mb'],
                'created': sim['created'],
                'last_accessed': sim['last_accessed'],
                'access_count': sim['access_count']
            }
            records.append(record)
            
        return pd.DataFrame(records)