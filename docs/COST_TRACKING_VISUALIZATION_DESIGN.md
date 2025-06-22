# Cost Tracking Visualization Design

## Overview
This document describes the visualization components for cost tracking and workload analysis in the VEGF simulation.

## 1. Cost Configuration Panel (Sidebar)

### Layout
```
┌─────────────────────────────────┐
│ 💰 Cost Parameters              │
├─────────────────────────────────┤
│ Drug Costs                      │
│ ┌─────────────────────────────┐ │
│ │ Eylea 2mg (£)               │ │
│ │ [===|=======] 800           │ │
│ │  400        1200            │ │
│ └─────────────────────────────┘ │
│                                 │
│ Visit Cost Model                │
│ ┌─────────────────────────────┐ │
│ │ ▼ NHS Standard 2025         │ │
│ └─────────────────────────────┘ │
│                                 │
│ [?] Component Costs             │
│ • Injection: £150               │
│ • OCT Scan: £75                 │
│ • Clinical Review: £120         │
│ • VA Test: £25                  │
│                                 │
│ ☐ Include virtual clinics       │
│ ☐ Apply biosimilar pricing      │
└─────────────────────────────────┘
```

### Features
- Slider for drug cost adjustment
- Dropdown for cost model selection
- Expandable section showing component costs
- Checkboxes for cost scenarios

## 2. Main Dashboard Layout

### Tab Structure
```
┌─────────────┬──────────────┬─────────────────┬──────────────────┐
│ Simulation  │ Analysis     │ 💰 Economics    │ Patient Explorer │
└─────────────┴──────────────┴─────────────────┴──────────────────┘
```

## 3. Economics Tab Components

### 3.1 Summary Metrics (Top Row)
```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│ Total Cost      │ Active Patients │ Cost/Patient    │ Cost/Vision Yr  │
│ £2.4M          │ 245/300        │ £8,750         │ £15,200        │
│ ▲ 5.2%         │ 81.7%          │ ▼ 3.1%         │ ▼ 8.5%         │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

### 3.2 Workload Timeline (Main Chart)
```
┌──────────────────────────────────────────────────────────────────┐
│ Clinical Workload Over Time                                      │
│                                                                  │
│ 250 ┤                                    ╱╲                      │
│     │                                   ╱  ╲                     │
│ 200 ┤                     ╱────────────╯    ╲                   │
│     │                    ╱                    ╲___               │
│ 150 ┤        ╱──────────╯ [Injections]         ╲──────         │
│     │       ╱                                            ╲       │
│ 100 ┤ ─────╯  ┌─────────────────────────────────────────┐╲     │
│     │         │  Decision-maker visits                  │ ╲    │
│  50 ┤ ████████████████████████████████████████████████████████ │
│     │                                                          │
│   0 └──────────────────────────────────────────────────────────┘
│     0    6    12    18    24    30    36    42    48    54    60│
│                         Months from Start                        │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 Cost Breakdown (Left Column)
```
┌─────────────────────────────┐  ┌─────────────────────────────┐
│ Cost by Component          │  │ Cost by Year               │
│                            │  │                            │
│       Drug                 │  │ Year 1: £450K (38%)       │
│       65%  ╱─────╲         │  │ Year 2: £280K (23%)       │
│          ╱         ╲       │  │ Year 3: £210K (18%)       │
│        ╱             ╲     │  │ Year 4: £155K (13%)       │
│      │   Procedures   │    │  │ Year 5: £105K (9%)        │
│      │      20%       │    │  │                            │
│       ╲             ╱      │  │ ████████████████████ Y1    │
│ OCT 8% ╲─────────╱ Other  │  │ █████████████ Y2           │
│         Review 7%          │  │ ██████████ Y3              │
│                            │  │ ███████ Y4                 │
│ Total: £1,200,000         │  │ █████ Y5                   │
└─────────────────────────────┘  └─────────────────────────────┘
```

### 3.4 Protocol Comparison (Right Column)
```
┌──────────────────────────────────────────────────────────────┐
│ T&E vs T&T Comparison                                        │
├──────────────────────────────────────────────────────────────┤
│                        T&E          T&T         Difference   │
│ ─────────────────────────────────────────────────────────── │
│ Total Cost:         £1.2M        £1.4M         -£200K (-14%) │
│ Drug Cost:          £780K        £910K         -£130K (-14%) │
│ Visit Cost:         £420K        £490K         -£70K (-14%)  │
│                                                              │
│ Injections:         1,050        1,225         -175 (-14%)   │
│ Decision Visits:    1,050          350         +700 (+200%)  │
│                                                              │
│ Cost/Patient:       £8,750       £10,200       -£1,450       │
│ Cost/Vision Year:   £15,200      £14,800       +£400         │
└──────────────────────────────────────────────────────────────┘
```

### 3.5 Resource Utilization Heatmap
```
┌──────────────────────────────────────────────────────────────┐
│ Monthly Resource Utilization                                 │
├──────────────────────────────────────────────────────────────┤
│        Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec      │
│ 2025   ███ ███ ███ ███ ██  ██  ██  ██  ██  ██  ██  ██       │
│ 2026   ██  ██  ██  ██  ██  █   █   █   █   █   █   █        │
│ 2027   █   █   █   █   █   █   █   █   █   █   █   █        │
│ 2028   █   █   █   █   █   █   █   █   █   █   ░   ░        │
│ 2029   ░   ░   ░   ░   ░   ░   ░   ░   ░   ░   ░   ░        │
│                                                              │
│ ███ >200 visits  ██ 100-200  █ 50-100  ░ <50 visits        │
└──────────────────────────────────────────────────────────────┘
```

## 4. Interactive Features

### 4.1 Hover Information
- **Workload Timeline**: Show exact counts on hover
- **Cost Breakdown**: Display amounts and percentages
- **Comparison Table**: Highlight differences

### 4.2 Filtering Options
```
Time Period: [All Time ▼] [Custom Range]
Patient Group: [All Patients ▼] [Active Only] [Discontinued]
Protocol: [Both ▼] [T&E Only] [T&T Only]
```

### 4.3 Export Options
```
┌─────────────────────────────────────┐
│ 📊 Export Options                   │
├─────────────────────────────────────┤
│ [Download Cost Report (PDF)]        │
│ [Export Data (CSV)]                 │
│ [Save Charts (PNG)]                 │
│ [Generate NICE Format]              │
└─────────────────────────────────────┘
```

## 5. Detailed Views

### 5.1 Patient-Level Cost View
```
┌──────────────────────────────────────────────────────────────┐
│ Patient Cost Distribution                                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  40 ┤                    ╱╲                                   │
│     │                   ╱  ╲                                  │
│  30 ┤                  ╱    ╲                                 │
│     │                 ╱      ╲                                │
│  20 ┤                ╱        ╲                               │
│     │               ╱          ╲                              │
│  10 ┤          ____╱            ╲____                         │
│     │     ____╱                      ╲____                    │
│   0 └──────────────────────────────────────────────────────┘
│     £0    £5K   £10K  £15K  £20K  £25K  £30K  £35K  £40K   │
│                      Cost per Patient                        │
│                                                              │
│ Mean: £12,450  |  Median: £11,200  |  SD: £5,670           │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Time-to-Event Cost Analysis
```
┌──────────────────────────────────────────────────────────────┐
│ Cumulative Cost by Patient Outcome                          │
├──────────────────────────────────────────────────────────────┤
│ £25K ┤                                    _____ Discontinued │
│      │                               ____╱                    │
│ £20K ┤                          ____╱   _____ Still Active   │
│      │                     ____╱  ____╱                      │
│ £15K ┤                ____╱  ____╱                           │
│      │           ____╱  ____╱                                │
│ £10K ┤      ____╱  ____╱ _____ Vision Maintained            │
│      │ ____╱  ____╱ ____╱                                    │
│  £5K ┤╱  ____╱ ____╱                                         │
│      │__╱ ____╱                                              │
│   £0 └──────────────────────────────────────────────────────┘
│      0    12    24    36    48    60    72    84    96      │
│                    Months in Treatment                       │
└──────────────────────────────────────────────────────────────┘
```

## 6. Mobile/Responsive Design

### Tablet View (768px)
- Stack cost breakdown and comparison vertically
- Maintain workload timeline full width
- Collapse detailed metrics into expandable cards

### Mobile View (480px)
- Single column layout
- Swipeable metric cards
- Simplified charts with essential data only
- Bottom navigation for tab switching

## 7. Color Scheme

### Primary Colors
- **Injections**: `#1f77b4` (Blue)
- **Decision Visits**: `#ff7f0e` (Orange)
- **Drug Costs**: `#2ca02c` (Green)
- **Procedure Costs**: `#d62728` (Red)
- **Other Costs**: `#9467bd` (Purple)

### Status Colors
- **Success/Savings**: `#28a745` (Green)
- **Warning/Increase**: `#ffc107` (Amber)
- **Alert/High Cost**: `#dc3545` (Red)
- **Neutral**: `#6c757d` (Gray)

## 8. Accessibility

### Features
- High contrast mode toggle
- Colorblind-friendly palette option
- Screen reader descriptions for all charts
- Keyboard navigation support
- Data tables as alternative to visualizations

### ARIA Labels
```html
<div role="img" aria-label="Workload timeline showing 150 injections 
     and 50 decision visits in January 2025">
  <!-- Chart content -->
</div>
```

## 9. Performance Considerations

### Data Aggregation
- Pre-calculate monthly summaries
- Cache cost calculations
- Lazy load detailed patient data
- Progressive chart rendering

### Update Strategy
- Real-time updates during simulation
- Batch updates every 100ms
- Debounce slider inputs
- Virtualize large data tables