"""
Data Normalization Module

This module provides data normalization utilities for the simulation system,
ensuring consistent data types throughout the application.
"""

from datetime import datetime
import pandas as pd
from typing import Any, Dict, List, Union


class DataNormalizer:
    """Handles data type conversions at system boundaries."""
    
    @staticmethod
    def normalize_patient_histories(patient_histories: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize patient history data structure.
        
        Ensures all dates are datetime objects and validates required fields.
        
        Parameters
        ----------
        patient_histories : Dict[str, Any]
            Raw patient history data from simulation
            
        Returns
        -------
        Dict[str, Any]
            Normalized patient history data
            
        Raises
        ------
        ValueError
            If required fields are missing or invalid
        """
        normalized = {}
        
        for patient_id, patient_data in patient_histories.items():
            if isinstance(patient_data, list):
                # List of visits
                normalized[patient_id] = DataNormalizer._normalize_visit_list(patient_data, patient_id)
            elif isinstance(patient_data, dict):
                # Dictionary with various fields
                normalized[patient_id] = DataNormalizer._normalize_patient_dict(patient_data, patient_id)
            else:
                # Unknown structure - pass through
                normalized[patient_id] = patient_data
                
        return normalized
    
    @staticmethod
    def _normalize_visit_list(visits: List[Dict], patient_id: str) -> List[Dict]:
        """Normalize a list of visit records."""
        normalized_visits = []
        
        for i, visit in enumerate(visits):
            if not isinstance(visit, dict):
                raise ValueError(f"Visit {i} for patient {patient_id} is not a dictionary")
                
            # Normalize the visit
            normalized_visit = visit.copy()
            
            # Ensure date/time field exists and is normalized
            # Try different field names that might contain time information
            time_field = None
            for field_name in ['date', 'time', 'timestamp']:
                if field_name in normalized_visit:
                    time_field = field_name
                    break
            
            if time_field:
                # Normalize the time field to 'date' for consistency
                normalized_visit['date'] = DataNormalizer._to_datetime(
                    normalized_visit[time_field], 
                    f"visit {i} of patient {patient_id}"
                )
                # Keep original field too
                if time_field != 'date':
                    normalized_visit[time_field] = normalized_visit['date']
            else:
                # No time field found - this is okay, some visits might not have timestamps
                pass
            
            normalized_visits.append(normalized_visit)
            
        return normalized_visits
    
    @staticmethod
    def _normalize_patient_dict(patient_data: Dict, patient_id: str) -> Dict:
        """Normalize a patient dictionary structure."""
        normalized = patient_data.copy()
        
        # If there's a visit_history field, normalize it
        if 'visit_history' in normalized and isinstance(normalized['visit_history'], list):
            normalized['visit_history'] = DataNormalizer._normalize_visit_list(
                normalized['visit_history'], 
                patient_id
            )
            
        # If there's an acuity_history field, normalize its dates
        if 'acuity_history' in normalized and isinstance(normalized['acuity_history'], list):
            for i, entry in enumerate(normalized['acuity_history']):
                if isinstance(entry, dict) and 'date' in entry:
                    entry['date'] = DataNormalizer._to_datetime(
                        entry['date'],
                        f"acuity entry {i} of patient {patient_id}"
                    )
                    
        return normalized
    
    @staticmethod
    def _to_datetime(date_value: Any, context: str = "") -> datetime:
        """
        Convert various date formats to datetime objects.
        
        Parameters
        ----------
        date_value : Any
            The date value to convert
        context : str
            Context for error messages
            
        Returns
        -------
        datetime
            Normalized datetime object
            
        Raises
        ------
        ValueError
            If the date format is not supported
        """
        if isinstance(date_value, pd.Timestamp):
            return date_value.to_pydatetime()
        elif isinstance(date_value, datetime):
            return date_value
        elif isinstance(date_value, str):
            try:
                return pd.to_datetime(date_value).to_pydatetime()
            except Exception as e:
                raise ValueError(f"Cannot parse date string '{date_value}' {context}: {e}")
        elif isinstance(date_value, (int, float)):
            try:
                return datetime.fromtimestamp(date_value)
            except Exception as e:
                raise ValueError(f"Cannot convert numeric date {date_value} {context}: {e}")
        else:
            raise ValueError(
                f"Unsupported date type {type(date_value)} for value '{date_value}' {context}"
            )
    
    @staticmethod
    def validate_normalized_data(patient_histories: Dict[str, Any]) -> bool:
        """
        Validate that data has been properly normalized.
        
        Parameters
        ----------
        patient_histories : Dict[str, Any]
            Patient history data to validate
            
        Returns
        -------
        bool
            True if all dates are datetime objects
            
        Raises
        ------
        ValueError
            If validation fails with details about the issue
        """
        for patient_id, patient_data in patient_histories.items():
            if isinstance(patient_data, list):
                for i, visit in enumerate(patient_data):
                    if isinstance(visit, dict) and 'date' in visit:
                        if not isinstance(visit['date'], datetime):
                            raise ValueError(
                                f"Visit {i} for patient {patient_id} has non-datetime date: "
                                f"{type(visit['date'])}"
                            )
            elif isinstance(patient_data, dict):
                if 'visit_history' in patient_data:
                    for i, visit in enumerate(patient_data['visit_history']):
                        if isinstance(visit, dict) and 'date' in visit:
                            if not isinstance(visit['date'], datetime):
                                raise ValueError(
                                    f"Visit {i} in visit_history for patient {patient_id} "
                                    f"has non-datetime date: {type(visit['date'])}"
                                )
                                
        return True