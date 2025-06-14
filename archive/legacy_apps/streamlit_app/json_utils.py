"""
JSON Utilities for APE: AMD Protocol Explorer

This module provides utilities for handling JSON serialization of complex Python objects,
particularly NumPy arrays, datetime objects, and custom classes in simulation results.
"""

import json
import numpy as np
from datetime import datetime, date
from typing import Any, Dict, List, Union, Optional


class APEJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles:
    - NumPy types (int32, int64, float32, float64, arrays)
    - Datetime objects
    - Object arrays
    - Lists with mixed types
    - Sets
    - Custom objects with to_dict method
    """
    
    def default(self, obj: Any) -> Any:
        """
        Convert objects to JSON-serializable types.
        
        Parameters
        ----------
        obj : Any
            The object to serialize
            
        Returns
        -------
        Any
            A JSON-serializable form of the object
        """
        # Handle NumPy types
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
            
        # Handle datetime objects
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()  # ISO format for consistent serialization
            
        # Handle sets by converting to lists
        elif isinstance(obj, set):
            return list(obj)
            
        # Handle custom objects with to_dict method
        elif hasattr(obj, 'to_dict') and callable(obj.to_dict):
            return obj.to_dict()
            
        # Handle any other array-like objects
        elif hasattr(obj, 'tolist') and callable(obj.tolist):
            return obj.tolist()
        
        # Default behavior
        return super().default(obj)


def serialize(obj: Any) -> str:
    """
    Serialize any object to JSON string.
    
    Parameters
    ----------
    obj : Any
        The object to serialize
        
    Returns
    -------
    str
        JSON string representation
    """
    return json.dumps(obj, cls=APEJSONEncoder)


def deserialize(json_str: str) -> Any:
    """
    Deserialize a JSON string to Python objects.
    
    Parameters
    ----------
    json_str : str
        JSON string to deserialize
        
    Returns
    -------
    Any
        Python object from JSON
    """
    return json.loads(json_str)


def save_json(obj: Any, file_path: str, indent: Optional[int] = 2) -> None:
    """
    Save object to JSON file.
    
    Parameters
    ----------
    obj : Any
        Object to serialize
    file_path : str
        Path to save JSON file
    indent : Optional[int]
        Indentation level for pretty printing, default 2
    """
    with open(file_path, 'w') as f:
        json.dump(obj, f, cls=APEJSONEncoder, indent=indent)


def load_json(file_path: str) -> Any:
    """
    Load object from JSON file.
    
    Parameters
    ----------
    file_path : str
        Path to JSON file
        
    Returns
    -------
    Any
        Deserialized object
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def convert_datetimes_in_dict(data: Dict) -> Dict:
    """
    Convert ISO format datetime strings back to datetime objects in a dictionary.
    
    Parameters
    ----------
    data : Dict
        Dictionary potentially containing datetime strings
        
    Returns
    -------
    Dict
        Dictionary with datetime strings converted to datetime objects
    """
    if not isinstance(data, dict):
        return data
        
    result = {}
    for key, value in data.items():
        if isinstance(value, str) and len(value) > 10:
            # Try to parse as ISO format datetime
            try:
                result[key] = datetime.fromisoformat(value)
            except ValueError:
                result[key] = value
        elif isinstance(value, dict):
            result[key] = convert_datetimes_in_dict(value)
        elif isinstance(value, list):
            result[key] = [
                convert_datetimes_in_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
            
    return result