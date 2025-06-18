"""
Distribution presets management for protocol editing.

Provides functionality to load, save, and manage baseline vision distribution presets.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


class DistributionPresets:
    """Manage baseline vision distribution presets."""
    
    def __init__(self, presets_dir: Optional[Path] = None):
        """Initialize distribution presets manager."""
        if presets_dir is None:
            self.presets_dir = Path(__file__).parent.parent.parent / "protocols" / "distributions"
        else:
            self.presets_dir = presets_dir
        
        # Ensure directory exists
        self.presets_dir.mkdir(parents=True, exist_ok=True)
    
    def get_available_presets(self) -> List[Dict[str, Any]]:
        """Get list of available distribution presets."""
        presets = []
        
        for preset_file in self.presets_dir.glob("*.yaml"):
            try:
                with open(preset_file, 'r') as f:
                    preset_data = yaml.safe_load(f)
                
                # Add file metadata
                preset_data['filename'] = preset_file.name
                preset_data['filepath'] = str(preset_file)
                
                presets.append(preset_data)
            except Exception as e:
                print(f"Warning: Could not load preset {preset_file}: {e}")
        
        # Sort by name for consistent ordering
        presets.sort(key=lambda x: x.get('name', ''))
        
        return presets
    
    def load_preset(self, filename: str) -> Dict[str, Any]:
        """Load a specific distribution preset."""
        preset_path = self.presets_dir / filename
        
        if not preset_path.exists():
            raise FileNotFoundError(f"Preset not found: {filename}")
        
        with open(preset_path, 'r') as f:
            return yaml.safe_load(f)
    
    def save_preset(self, distribution_config: Dict[str, Any], name: str, 
                   description: str = "", source: str = "User defined") -> str:
        """Save a distribution configuration as a new preset."""
        # Create safe filename
        safe_name = name.lower().replace(' ', '_').replace('-', '_')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')
        filename = f"{safe_name}.yaml"
        
        preset_data = {
            'name': name,
            'description': description,
            'source': source,
            **{k: v for k, v in distribution_config.items() if k not in ['name', 'description', 'source']}
        }
        
        preset_path = self.presets_dir / filename
        
        with open(preset_path, 'w') as f:
            yaml.dump(preset_data, f, default_flow_style=False, sort_keys=False)
        
        return filename
    
    def delete_preset(self, filename: str) -> bool:
        """Delete a distribution preset."""
        preset_path = self.presets_dir / filename
        
        if not preset_path.exists():
            return False
        
        preset_path.unlink()
        return True
    
    def preset_to_distribution_config(self, preset: Dict[str, Any]) -> Dict[str, Any]:
        """Convert preset data to baseline_vision_distribution format."""
        # Remove metadata fields
        config = {k: v for k, v in preset.items() 
                 if k not in ['name', 'description', 'source', 'filename', 'filepath']}
        
        return config
    
    def get_preset_summary(self, preset: Dict[str, Any]) -> str:
        """Get a human-readable summary of a preset."""
        dist_type = preset.get('type', 'unknown')
        
        if dist_type == 'normal':
            return f"Normal (μ={preset.get('mean', '?')}, σ={preset.get('std', '?')}, range {preset.get('min', '?')}-{preset.get('max', '?')})"
        elif dist_type == 'beta_with_threshold':
            return f"Beta with threshold (α={preset.get('alpha', '?')}, β={preset.get('beta', '?')}, threshold={preset.get('threshold', '?')})"
        elif dist_type == 'uniform':
            return f"Uniform (range {preset.get('min', '?')}-{preset.get('max', '?')})"
        else:
            return f"Type: {dist_type}"


def get_distribution_presets() -> DistributionPresets:
    """Get the default distribution presets manager."""
    return DistributionPresets()