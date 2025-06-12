"""Performance configuration for treatment pattern analysis."""

# Performance limits
MAX_PATIENTS_FOR_PRECALC = 50000  # Skip pre-calc for very large simulations
MAX_VISITS_FOR_PRECALC = 1000000  # Skip if too many visits
PRECALC_TIMEOUT_SECONDS = 10.0    # Maximum time to spend pre-calculating

# Feature flags
ENABLE_TREATMENT_PATTERN_PRECALC = True  # Master switch

def should_precalculate(results) -> bool:
    """Determine if we should pre-calculate for this simulation."""
    if not ENABLE_TREATMENT_PATTERN_PRECALC:
        return False
        
    try:
        n_patients = results.metadata.n_patients
        duration_years = results.metadata.duration_years
        
        # Estimate visits (rough approximation)
        estimated_visits = n_patients * duration_years * 12  # ~monthly visits
        
        if n_patients > MAX_PATIENTS_FOR_PRECALC:
            return False
        if estimated_visits > MAX_VISITS_FOR_PRECALC:
            return False
            
        return True
    except:
        return True  # Default to trying