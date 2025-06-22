# Economic Analysis Specification v2.1

## Core Principles
1. **Track ACTUAL costs** - Never estimate, never fall back. If data is missing, ERROR.
2. **Show real workload patterns** - No smoothing. Show daily peaks and troughs.
3. **Use correct terminology** - Role-based (Injector, Decision Maker, etc.), not nurse/consultant.
4. **Educational tool** - For exploring different configurations and their impacts.
5. **Configurable Resources** - Roles and capacities defined in protocol files, not hardcoded.

## Style Guidelines
1. **NO EMOJIS** - Never use emoji icons (❌ "💰 Workload Analysis")
2. **Carbon Design System** - Use carbon buttons via `ape_button()` helper, not standard Streamlit buttons
3. **Tufte Principles** - Minimal chart junk, data-ink ratio, no unnecessary borders or backgrounds
4. **Semantic Colors Only** - All colors from central color system (`visualization.color_system`)
   - If new colors needed, add to central system first
   - Never define colors locally or use fallbacks
5. **Clean Visualizations** - No bounding boxes, minimal gridlines, focus on data

## Resource Configuration System

### Protocol Resource Definition
Add new section to protocol YAML files:

```yaml
# In protocol file or separate resource_config.yaml
resources:
  roles:
    injector:
      capacity_per_session: 14
      description: "Administers injections"
    
    injector_assistant:
      capacity_per_session: 14
      description: "Assists with injection procedure"
    
    vision_tester:
      capacity_per_session: 20
      description: "Performs visual acuity tests"
    
    oct_operator:
      capacity_per_session: 16
      description: "Operates OCT scanner"
    
    decision_maker:
      capacity_per_session: 12
      description: "Clinical decision making"
  
  visit_requirements:
    injection_only:
      roles_needed:
        - injector: 1
        - injector_assistant: 1
      duration_minutes: 15
    
    decision_with_injection:
      roles_needed:
        - vision_tester: 1
        - oct_operator: 1
        - decision_maker: 1
        - injector: 1
        - injector_assistant: 1
      duration_minutes: 30
    
    decision_only:
      roles_needed:
        - vision_tester: 1
        - oct_operator: 1
        - decision_maker: 1
      duration_minutes: 20

  session_parameters:
    session_duration_hours: 4
    sessions_per_day: 2  # morning and afternoon
    working_days: ["Mon", "Tue", "Wed", "Thu", "Fri"]
```

## New Page: Workload and Costs Analysis

### Layout
**Page Title:** "Workload and Economic Analysis" (no emoji)
**Page Icon:** Use Carbon icon if needed

### Section 1: Enhanced Workload Timeline
- **Chart Type:** Multi-series chart showing resource requirements by role
- **X-axis:** Days (with weekends using `SEMANTIC_COLORS['weekend']` or similar)
- **Y-axis:** Sessions needed per role
- **Data series (one per role):**
  - Injector sessions needed
  - Injector assistant sessions needed
  - Vision tester sessions needed
  - OCT operator sessions needed
  - Decision maker sessions needed
- **Calculation example:**
  ```
  Daily injector sessions = ceil(injection_visits / injector_capacity_per_session)
  Daily vision_tester sessions = ceil((decision_visits + injection_visits_needing_VA) / vision_tester_capacity)
  ```
- **Tufte styling:**
  - Remove all borders
  - Minimal gridlines (light gray, alpha 0.2)
  - Direct labeling where possible
  - No legend box - integrate labels into chart
- **Features:**
  - NO SMOOTHING - show actual daily variations
  - Show bottlenecks (which role hits capacity first)
  - Highlight days where any role exceeds available sessions
  - Option to view by role or aggregated
  - Show staffing requirements (e.g., "Need 3.5 injection sessions")

### Section 2: Cost Summary
- **Display using metrics with clean styling**
- **Total Simulation Cost:** Sum of all patient costs
- **Average Cost per Patient:** Total cost / (sum of daily patient count / days)
- **Cost Breakdown:**
  - Drug costs (with slider to adjust drug price)
  - Injection visit costs
  - Decision visit costs
  - OCT costs
- **Controls:** Use Carbon-styled components

### Section 3: Resource Utilization Dashboard
- **Role-based view:**
  ```
  Role: Injector
  Peak daily demand: 45 procedures
  Sessions needed: 4 (3.2 actual)
  Utilization: 80%
  
  Role: Decision Maker
  Peak daily demand: 28 assessments
  Sessions needed: 3 (2.3 actual)
  Utilization: 77%
  ```
- **Bottleneck Analysis:**
  - Identify constraining resources
  - Show impact of capacity changes

### Section 4: Staffing Requirements
- **Summary table:**
  ```
  Role               | Average Sessions/Day | Peak Sessions | Staff Needed (Peak)
  Injector          | 2.5                  | 4            | 2
  Injector Assistant| 2.5                  | 4            | 2
  Vision Tester     | 3.1                  | 5            | 3
  OCT Operator      | 2.8                  | 4            | 2
  Decision Maker    | 1.8                  | 3            | 2
  ```

### Section 5: Cost Effectiveness (if possible)
- **Cost per vision year saved**
- **Cost per patient maintaining vision**
- **Simple, clear presentation**

## Enhanced Comparison Page

Add new section: "Economic Comparison"

### Workload Comparison (Priority #1)
- Side-by-side daily workload charts for selected protocols
- Use small multiples approach (Tufte)
- Consistent scales for comparison
- Difference chart showing T&E vs T&T workload
- Peak staffing requirements comparison

### Resource Comparison
- Compare staffing needs between protocols:
  ```
  T&E vs T&T Resource Requirements:
  
  Role            | T&E Sessions | T&T Sessions | Difference
  Decision Maker  | 125         | 45          | -64%
  Injector       | 125         | 132         | +6%
  ```

### Cost Comparison
- Total cost per patient for each protocol
- Drug cost impact (biosimilar vs originator) - Priority #1
- Year 1 vs Year 2 breakdown - Priority #2
- **Visual style:** Clean bar charts or dot plots, no 3D effects

## Calendar Time Analysis Integration

Add new tab or section:
- **Monthly cost accumulation chart** - Clean line chart
- **Workload heatmap** - Using semantic color gradients
- **Resource planning view** - Data-focused table

## Implementation Architecture

### Role-Based Tracking
```python
class ResourceTracker:
    def __init__(self, resource_config):
        self.roles = resource_config['roles']
        self.visit_requirements = resource_config['visit_requirements']
        self.daily_usage = defaultdict(lambda: defaultdict(int))
    
    def track_visit(self, date, visit_type):
        """Track resource usage for a visit"""
        requirements = self.visit_requirements[visit_type]['roles_needed']
        for role, count in requirements.items():
            self.daily_usage[date][role] += count
    
    def calculate_sessions_needed(self, date, role):
        """Calculate sessions needed for a role on a date"""
        daily_count = self.daily_usage[date][role]
        capacity = self.roles[role]['capacity_per_session']
        return math.ceil(daily_count / capacity)
```

## UI Components

### Buttons
```python
# Use carbon button helpers
from ape.utils.carbon_button_helpers import ape_button

# Instead of st.button()
if ape_button("Export Report", variant="primary"):
    # handle export
```

### Color Usage
```python
from visualization.color_system import SEMANTIC_COLORS, ALPHAS

# For all chart colors
injection_color = SEMANTIC_COLORS['injection_visits']
decision_color = SEMANTIC_COLORS['decision_visits']

# If new colors needed, first add to color_system.py:
# SEMANTIC_COLORS['workload_peak'] = '#FF6B6B'
```

### Chart Styling
```python
# Tufte-style configuration
fig.update_layout(
    showlegend=False,  # Use direct labeling instead
    plot_bgcolor='white',
    paper_bgcolor='white',
    margin=dict(l=40, r=20, t=30, b=40),
    xaxis=dict(
        showgrid=False,
        zeroline=False,
        showline=True,
        linewidth=1,
        linecolor='gray',
        mirror=False
    ),
    yaxis=dict(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='gray'
    )
)
```

## Data Structure Requirements

### Per Visit Tracking
```yaml
visit:
  date: 2024-01-15
  patient_id: P001
  visit_type: "injection_only" | "decision_with_injection" | "decision_only"
  injection_given: true/false
  oct_performed: true/false
  costs:
    drug: 355  # if injection given
    injection_procedure: 134
    decision_consultation: 75  # if decision visit
    oct_scan: 110  # if performed
  resources_used:  # Based on visit_requirements
    injector: 1
    injector_assistant: 1
    vision_tester: 1  # if applicable
    oct_operator: 1   # if applicable
    decision_maker: 1 # if applicable
```

### Visit Type Rules
- **T&E:** Visits 1-3 are injection+decision, then ALL visits are injection+decision
- **T&T:** 
  - Visits 1-3: injection only
  - Visit 4: decision (assessment after loading)
  - Then: injection only, except annual decision visits

## Configuration Management

### Default Resource Configuration
- Ship with sensible defaults in `protocols/resource_configs/nhs_standard_resources.yaml`
- Allow protocol-specific overrides
- Make it easy to create variations (e.g., "high_efficiency_clinic.yaml")

### UI for Resource Configuration
- Advanced section in settings to adjust:
  - Role capacities
  - Visit requirements
  - Session parameters
- Save custom configurations for reuse

## Export Requirements

### PDF Reports
- **Clean, professional layout**
- **No decorative elements**
- **Data tables with minimal borders**
- **Charts follow same Tufte principles**

### Sections:
1. **Executive Summary**
   - Total patients treated
   - Total cost
   - Average cost per patient
   - Peak staffing requirements by role

2. **Detailed Workload Report**
   - Daily workload table by role
   - Monthly summaries
   - Staffing projections
   - Resource utilization rates

3. **Cost Breakdown**
   - By component (drug, procedure, etc.)
   - By time period
   - Per patient averages

4. **Resource Analysis**
   - Sessions needed by role
   - Bottleneck identification
   - Capacity utilization

## Critical Implementation Notes

1. **No Fallbacks:** If visit data is incomplete, FAIL with clear error
2. **Actual Tracking:** Count actual visits as they occur in simulation
3. **Weekday Only:** Workload calculations assume Mon-Fri operation
4. **Variable Patient Numbers:** Must handle patients entering/leaving study correctly
5. **Cost Flexibility:** Drug costs adjustable post-simulation via UI
6. **Style Consistency:** Every visual element must use central style system
7. **Resource Tracking:** Every visit must track resources used based on configuration

## Benefits of This Approach

1. **Flexibility:** Easy to model different clinic configurations
2. **Transparency:** Clear what assumptions are being made
3. **Adaptability:** Can update as roles/responsibilities change
4. **Realism:** Models actual clinic constraints
5. **Planning Tool:** Helps identify optimal staff mix

## Success Criteria

1. Can see daily workload patterns without smoothing
2. Can calculate staffing needs in sessions by role
3. Shows true cost per patient (accounting for variable enrollment)
4. Enables comparison of protocols for workload planning
5. Integrates with existing Calendar Time Analysis
6. Exports comprehensive PDF reports
7. All UI elements follow design system (Carbon buttons, semantic colors, Tufte charts)
8. No emojis or decorative elements anywhere
9. Resource requirements are configurable, not hardcoded
10. Can identify bottlenecks and capacity constraints

## Additional Notes

- Resource configurations are versioned with protocols
- Can run "what-if" scenarios by adjusting capacities
- Export includes resource assumptions for full transparency
- Validation ensures visit requirements are feasible