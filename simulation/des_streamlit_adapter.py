"""
DES to Streamlit adapter module for enhanced discontinuation model.

This module provides adapters to transform DES simulation results into the format
expected by the Streamlit visualization dashboard. It handles discontinuation data,
patient visit histories, and state transitions to ensure the enhanced DES output
is compatible with existing visualization components.

Functions:
---------
adapt_des_for_streamlit(des_results)
    Transforms DES simulation results into the expected Streamlit format
enhance_patient_histories(patient_histories)
    Enhances patient histories with additional metadata for visualization
format_discontinuation_counts(raw_discontinuation_stats)
    Formats discontinuation counts for the Streamlit dashboard
"""

from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def adapt_des_for_streamlit(des_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapts DES simulation results to the format expected by the Streamlit dashboard.
    
    This adapter function transforms enhanced DES simulation results into the format
    expected by the existing visualization components in the Streamlit dashboard.
    
    Parameters
    ----------
    des_results : Dict[str, Any]
        Raw DES simulation results with enhanced discontinuation data
    
    Returns
    -------
    Dict[str, Any]
        Transformed results suitable for Streamlit visualization
    """
    # Initialize the adapted results with core properties
    adapted_results = {
        "simulation_type": "DES",
        "population_size": des_results.get("population_size", 0),
        "duration_years": des_results.get("duration_years", 5)
    }
    
    # Extract raw statistics from the DES results
    raw_stats = des_results.get("statistics", {})
    disc_stats = raw_stats.get("discontinuation_stats", {})
    
    # Format discontinuation counts
    adapted_results["discontinuation_counts"] = format_discontinuation_counts(disc_stats)
    
    # Process recurrence data
    if "retreatment_stats" in raw_stats:
        retreat_stats = raw_stats.get("retreatment_stats", {})
        adapted_results["recurrences"] = {
            "total": retreat_stats.get("total_retreatments", 0),
            "by_type": retreat_stats.get("retreatments_by_type", {})
        }
    
    # Process patient histories if available
    if "patient_histories" in des_results:
        adapted_results["patient_histories"] = enhance_patient_histories(
            des_results["patient_histories"]
        )
    
    # Add additional metadata for visualization
    adapted_results["raw_discontinuation_stats"] = disc_stats
    
    return adapted_results

def enhance_patient_histories(patient_histories: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Enhances patient histories with additional metadata for visualization.
    
    This function processes DES patient visit histories to ensure they have the
    fields expected by the Streamlit visualizations, including discontinuation flags
    and standardized date/time fields.
    
    Parameters
    ----------
    patient_histories : Dict[str, List[Dict[str, Any]]]
        Dictionary mapping patient IDs to their visit histories
    
    Returns
    -------
    Dict[str, Dict[str, Any]]
        Enhanced patient histories in a format compatible with Streamlit visualizations
    """
    # The streamlit_app/streamgraph_actual_data.py expects a different structure
    # where patient_histories maps patient IDs to dictionaries with 'visits' key
    enhanced_histories = {}
    
    for patient_id, visits in patient_histories.items():
        enhanced_visits = []
        
        # Track discontinuation and retreatment state
        is_discontinued = False
        last_discontinuation_reason = None
        is_retreated = False
        prev_visit_active = True  # Track previous visit's active status
        
        # First pass - create chronologically sorted visit list
        sorted_visits = sorted(visits, key=lambda v: v.get('date', v.get('time', 0)))
        
        for i, visit in enumerate(sorted_visits):
            enhanced_visit = visit.copy()
            
            # Standardize date/time field
            if "date" in visit and "time" not in visit:
                enhanced_visit["time"] = visit["date"]
            
            # Set visit type if not present
            if "type" not in enhanced_visit:
                if "is_monitoring" in visit and visit["is_monitoring"]:
                    enhanced_visit["type"] = "monitoring_visit"
                else:
                    enhanced_visit["type"] = "regular_visit"
            
            # Check if this is a discontinuation visit
            # A discontinuation visit is when treatment becomes inactive
            current_active = visit.get("treatment_status", {}).get("active", True)
            
            # Add explicit discontinuation flag if not present
            if "is_discontinuation_visit" not in enhanced_visit:
                # A visit is a discontinuation visit if:
                # 1. The previous visit was active AND
                # 2. This visit is not active OR has a cessation_type
                if prev_visit_active and (
                    not current_active or 
                    "cessation_type" in visit.get("treatment_status", {})
                ):
                    enhanced_visit["is_discontinuation_visit"] = True
                    is_discontinued = True
                    
                    # Extract the discontinuation reason
                    if "treatment_status" in visit and "cessation_type" in visit["treatment_status"]:
                        discontinuation_reason = visit["treatment_status"]["cessation_type"]
                        enhanced_visit["discontinuation_reason"] = discontinuation_reason
                        last_discontinuation_reason = discontinuation_reason
                else:
                    enhanced_visit["is_discontinuation_visit"] = False
                    
                    # Special handling for monitoring visits
                    if enhanced_visit["type"] == "monitoring_visit":
                        enhanced_visit["is_discontinuation_visit"] = False
            
            # Add retreatment flag if not present
            if "is_retreatment" not in enhanced_visit:
                # A visit is a retreatment visit if:
                # 1. The patient was previously discontinued AND
                # 2. This visit has active treatment AND
                # 3. It's not a monitoring visit
                if is_discontinued and current_active and enhanced_visit["type"] == "regular_visit":
                    enhanced_visit["is_retreatment"] = True
                    enhanced_visit["retreatment_reason"] = last_discontinuation_reason
                    is_discontinued = False
                    is_retreated = True
                else:
                    enhanced_visit["is_retreatment"] = False
            
            enhanced_visits.append(enhanced_visit)
            prev_visit_active = current_active
        
        # Create patient entry with 'visits' field as expected by streamgraph_actual_data.py
        enhanced_histories[patient_id] = {
            "visits": enhanced_visits,
            "retreatment_count": sum(1 for v in enhanced_visits if v.get("is_retreatment", False)),
            "discontinuation_reasons": [v.get("discontinuation_reason") for v in enhanced_visits 
                                      if v.get("is_discontinuation_visit", False) and "discontinuation_reason" in v]
        }
    
    return enhanced_histories

def format_discontinuation_counts(raw_discontinuation_stats: Dict[str, Any]) -> Dict[str, int]:
    """
    Formats discontinuation counts for the Streamlit dashboard.
    
    This function transforms the raw discontinuation statistics from the DES
    simulation into the format expected by the Streamlit dashboard's
    discontinuation visualization components.
    
    Parameters
    ----------
    raw_discontinuation_stats : Dict[str, Any]
        Raw discontinuation statistics from DES simulation
    
    Returns
    -------
    Dict[str, int]
        Formatted discontinuation counts by type
    """
    # Initialize result with zeros to ensure all categories are present
    formatted_counts = {
        "Planned": 0,
        "Administrative": 0,
        "Not Renewed": 0,
        "Premature": 0
    }
    
    # Map from DES cessation types to Streamlit visualization categories
    mapping = {
        "stable_max_interval": "Planned",
        "random_administrative": "Administrative",
        "treatment_duration": "Not Renewed",
        "premature": "Premature"
    }
    
    # Fill in actual counts
    for des_type, streamlit_type in mapping.items():
        # Try different formats that might be in raw stats
        count = raw_discontinuation_stats.get(f"{des_type}_discontinuations", 0)
        if count == 0:
            # Try alternative key format
            count = raw_discontinuation_stats.get(des_type, 0)
        
        formatted_counts[streamlit_type] = count
    
    return formatted_counts