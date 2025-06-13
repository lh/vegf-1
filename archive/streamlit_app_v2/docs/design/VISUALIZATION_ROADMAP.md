# V2 Visualization Roadmap

## Design Principles

### Tufte + Zoom Optimization
1. **Maximize Data-Ink Ratio** - Remove unnecessary elements
2. **Large, Clear Labels** - Minimum 14pt for Zoom readability  
3. **High Contrast Colors** - Survive video compression
4. **Thick Lines** - 2.5pt minimum for data lines
5. **Strategic Annotations** - Bold text with white backgrounds
6. **Clean Backgrounds** - Pure white for screen sharing

## Phase 1: Enhanced Visualizations (Priority)

### 1.1 Streamgraph Visualization
**Purpose**: Show patient state transitions over time
**Zoom Considerations**:
- Large state labels directly on the streams
- High contrast colors between states
- Thick boundaries between streams
- Interactive tooltips with large text

```python
# Key features
- Stacked area chart showing patient counts
- States: NAIVE, STABLE, ACTIVE, HIGHLY_ACTIVE
- Clear color coding with legend
- Month markers on x-axis (0, 12, 24, 36...)
```

### 1.2 Protocol Comparison View
**Purpose**: Side-by-side protocol comparison
**Layout**: 2x2 grid optimized for screen sharing
- Top Left: Injection frequency comparison
- Top Right: Vision outcomes
- Bottom Left: Cost analysis
- Bottom Right: Key metrics table

**Zoom Features**:
- Each panel self-contained
- Large titles on each panel
- Consistent y-axis scales
- Bold difference indicators

### 1.3 Cohort Analysis Tools
**Purpose**: Analyze patient subgroups
**Visualizations**:
- Stratified outcomes by baseline vision
- Response patterns by initial disease state
- Time to discontinuation curves

## Phase 2: Batch Operations

### 2.1 Batch Simulation Runner
```python
# Features
- Queue multiple protocol runs
- Progress indicator with ETA
- Parallel execution option
- Results aggregation
```

### 2.2 Parameter Sensitivity Analysis
**Tornado Diagram** (Zoom-optimized):
- Horizontal bars showing parameter impact
- Large parameter names on y-axis
- Clear positive/negative coloring
- Value labels on bars

### 2.3 Results Comparison Matrix
**Heatmap Design**:
- Large cells with values
- Color gradient for quick scanning
- Row/column labels outside plot area
- Interactive cell details on hover

## Phase 3: Export Features

### 3.1 Report Generation
**PDF/HTML Reports**:
- Executive summary page
- Method section with protocol details
- Results with all visualizations
- Statistical appendix
- Reproducibility section

**Zoom Presentation Mode**:
- One visualization per page
- Landscape orientation
- Large margins for annotations
- Page numbers for reference

### 3.2 Excel Export
**Multi-sheet Structure**:
1. Summary - Key metrics dashboard
2. Patient_Data - Individual outcomes
3. Visit_Details - All visits
4. Protocol_Params - Full specification
5. Audit_Trail - Complete log

### 3.3 Reproducibility Package
**Contents**:
- Protocol YAML file
- Simulation script
- Results data
- Visualization code
- Environment specification
- README with instructions

## Phase 4: Protocol Tools

### 4.1 Protocol Editor
**Features**:
- YAML syntax highlighting
- Real-time validation
- Parameter documentation
- Save with version increment

**UI Design** (Zoom-friendly):
- Large font in editor
- Clear error messages
- Collapsible sections
- Preview panel

### 4.2 Protocol Templates
**Available Templates**:
1. Standard Treat-and-Extend
2. Intensive Loading + T&E
3. PRN (As-Needed)
4. Fixed Interval
5. Hybrid Protocols

**Template Features**:
- Pre-filled with typical values
- Extensive comments
- Literature references
- Validation rules

### 4.3 Version Diff Viewer
**Side-by-side Comparison**:
- Changed parameters highlighted
- Large diff markers (+/-)
- Collapsible unchanged sections
- Export diff report

## Implementation Priority

### Immediate (Week 1)
1. Streamgraph visualization
2. Basic protocol comparison
3. Zoom-optimized style guide

### Short-term (Week 2-3)
1. Batch simulation runner
2. Excel export
3. Basic report generation

### Medium-term (Week 4-6)
1. Parameter sensitivity analysis
2. Protocol templates
3. Cohort analysis tools

### Long-term (Week 7+)
1. Full protocol editor
2. Advanced statistical tools
3. Publication-ready exports

## Technical Implementation Notes

### Streamlit Components
```python
# Custom components needed
- StreamgraphComponent (React/D3.js)
- ProtocolEditor (CodeMirror)
- InteractiveHeatmap (Plotly)
- BatchProgressTracker
```

### Performance Considerations
- Cache comparison results
- Lazy load large visualizations
- Progressive rendering for reports
- Background job queue for batch ops

### Zoom Presentation Features
1. **Presentation Mode Toggle**
   - Increases all font sizes by 20%
   - Simplifies visualizations
   - Adds slide numbers
   - High contrast mode

2. **Screen Share Optimizer**
   - Reduces animation
   - Increases line weights
   - Enlarges click targets
   - Simplifies interactions

3. **Export Presets**
   - "Zoom Presentation" (1280x720)
   - "HD Display" (1920x1080)
   - "Print Quality" (300 DPI)
   - "Email Attachment" (compressed)

## Success Metrics

1. **Readability**: All text legible at 720p Zoom quality
2. **Performance**: <2s load time for visualizations
3. **Usability**: One-click export for common formats
4. **Reproducibility**: 100% parameter capture
5. **Accessibility**: WCAG AA compliance

## Next Steps

1. Implement Zoom-Tufte style guide ✓
2. Create streamgraph component
3. Build protocol comparison view
4. Add batch simulation capability
5. Implement basic export features