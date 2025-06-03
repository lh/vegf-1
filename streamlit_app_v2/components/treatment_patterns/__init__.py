"""Treatment pattern analysis components."""

from .pattern_analyzer import (
    extract_treatment_patterns_vectorized,
    determine_treatment_state_vectorized,
    TREATMENT_STATE_COLORS
)
from .sankey_builder import (
    create_treatment_pattern_sankey,
    create_enhanced_sankey_with_colored_streams,
    create_gradient_sankey
)
from .interval_analyzer import (
    create_interval_distribution_chart,
    create_gap_analysis_chart_tufte,
    calculate_interval_statistics
)

__all__ = [
    'extract_treatment_patterns_vectorized',
    'determine_treatment_state_vectorized',
    'TREATMENT_STATE_COLORS',
    'create_treatment_pattern_sankey',
    'create_enhanced_sankey_with_colored_streams',
    'create_gradient_sankey',
    'create_interval_distribution_chart',
    'create_gap_analysis_chart_tufte',
    'calculate_interval_statistics'
]

# Try to import enhanced features
try:
    from .pattern_analyzer_enhanced import extract_treatment_patterns_with_terminals
    from .sankey_builder_enhanced import (
        create_enhanced_sankey_with_terminals,
        create_enhanced_sankey_with_terminals_destination_colored
    )
    __all__.extend([
        'extract_treatment_patterns_with_terminals', 
        'create_enhanced_sankey_with_terminals',
        'create_enhanced_sankey_with_terminals_destination_colored'
    ])
except ImportError:
    pass