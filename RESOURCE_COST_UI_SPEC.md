# Resource and Cost UI Specification

## Resources Page Design

### Page Layout
```
┌─────────────────────────────────────────────────────────────────┐
│  Resources  │ Vision | Patients | States | Intervals | [Costs] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Resource Utilization Timeline                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  [Stacked Area Chart]                                      │ │
│  │   - Staff hours (blue shades)                             │ │
│  │   - Equipment usage (green shades)                         │ │
│  │   - Drug vials (purple shades)                            │ │
│  │   - Facility hours (orange shades)                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Resource Category Breakdown                    Peak Usage      │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐ │
│  │ [Donut Chart]                │  │ Peak Time: Month 18      │ │
│  │ - Medical Staff: 45%         │  │ - Nurses: 12 concurrent  │ │
│  │ - Nursing Staff: 30%         │  │ - OCT Scans: 45/day      │ │
│  │ - Equipment: 15%             │  │ - Injection rooms: 98%   │ │
│  │ - Facilities: 10%            │  └──────────────────────────┘ │
│  └─────────────────────────────┘                                │
│                                                                 │
│  Weekly Resource Requirements Table                             │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Week │ Nurses │ OCT │ Injections │ Rooms │ Utilization  │ │
│  │   1  │   45   │ 120 │    180     │  85%  │     72%      │ │
│  │   2  │   48   │ 135 │    195     │  90%  │     78%      │ │
│  │  ...                                                       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  [Export CSV] [Export PDF] [Planning Mode]                      │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features
1. **Resource Timeline**: Interactive stacked area chart showing resource usage over time
2. **Category Breakdown**: Donut chart for current or selected time period
3. **Peak Usage Analysis**: Identify bottlenecks and capacity constraints
4. **Planning Table**: Exportable weekly/monthly resource requirements
5. **Interactive Tooltips**: Detailed breakdowns on hover
6. **Time Resolution Toggle**: Switch between daily/weekly/monthly views

## Costs Page Design

### Page Layout
```
┌─────────────────────────────────────────────────────────────────┐
│  Costs      │ Vision | Patients | States | Intervals | Resources│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Cost Summary Dashboard                                         │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │ Total Cost   │ Per Patient  │ Drug Costs   │ Visit Costs  │ │
│  │ £4,061,413   │ £2,031       │ £3,367,064   │ £694,349     │ │
│  │              │ (avg)        │ (82.9%)      │ (17.1%)      │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                 │
│  Cost Timeline                        Cost Breakdown            │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐ │
│  │ [Combined Line/Bar Chart]    │  │ [Sunburst Chart]         │ │
│  │ - Cumulative cost (line)     │  │ - Drugs                  │ │
│  │ - Monthly costs (bars)       │  │   - Aflibercept 2mg      │ │
│  │ - Budget line (dashed)       │  │   - Aflibercept 8mg      │ │
│  └─────────────────────────────┘  │ - Visits                 │ │
│                                    │   - Injection visits     │ │
│  Patient Cost Distribution         │   - Monitoring visits    │ │
│  ┌─────────────────────────────┐  └──────────────────────────┘ │
│  │ [Histogram + Box Plot]       │                               │
│  │ Shows cost per patient       │  Cost Drivers               │
│  │ with quintile markers        │  ┌────────────────────────┐ │
│  └─────────────────────────────┘  │ 1. Aflibercept 2mg 65% │ │
│                                    │ 2. Injection visits 12% │ │
│  Monthly Cost Table                │ 3. OCT scans 8%        │ │
│  ┌─────────────────────────────┐  │ 4. Monitoring 6%       │ │
│  │ Month │ Drugs │ Visits │ Total │ │ 5. Other 9%            │ │
│  │   1   │ £65k  │ £12k   │ £77k  │ └────────────────────────┘ │
│  │   2   │ £68k  │ £14k   │ £82k  │                            │
│  └─────────────────────────────┘  [Scenario Analysis]         │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features
1. **Cost Summary Cards**: High-level metrics with percentages
2. **Interactive Timeline**: Zoom and filter capabilities
3. **Hierarchical Breakdown**: Sunburst chart for drilling down
4. **Distribution Analysis**: Understand cost variation across patients
5. **Cost Drivers**: Ranked list with percentage contributions
6. **Scenario Analysis**: What-if modeling capabilities

## Compare Page Integration

### New Comparison Sections
```
┌─────────────────────────────────────────────────────────────────┐
│  Comparison: Simulation A vs Simulation B                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Existing comparison sections...]                              │
│                                                                 │
│  Resource Comparison                                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Resource Type    │ Simulation A │ Simulation B │ Difference │ │
│  │ Total Staff Hours│    12,450    │    10,230    │   -17.8%   │ │
│  │ Peak Nurses Req. │      15      │      12      │   -20.0%   │ │
│  │ OCT Scans Total  │    4,500     │    3,800     │   -15.6%   │ │
│  │ Injection Slots  │    6,200     │    5,100     │   -17.7%   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Cost Comparison                                                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ [Side-by-side bar charts]                                  │ │
│  │ Total Costs: A: £4.06M | B: £3.52M | Savings: £540K       │ │
│  │ Per Patient: A: £2,031 | B: £1,760 | Savings: £271        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Economic Analysis                                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Metric                  │ Simulation A │ Simulation B      │ │
│  │ Cost per vision-year    │    £425      │    £380           │ │
│  │ ICER (vs no treatment)  │   £12,500    │   £10,200         │ │
│  │ Budget impact (5 years) │   £20.3M     │   £17.6M          │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Interactive Features

### 1. Time-based Filtering
- Slider to focus on specific time periods
- Synchronized across all visualizations
- Show period-specific costs and resources

### 2. Drill-down Capabilities
- Click on chart segments for detailed breakdowns
- Patient-level cost exploration
- Resource usage by department/clinic

### 3. Export Options
- CSV exports for all tables
- PDF reports with visualizations
- PowerBI/Tableau compatible formats

### 4. What-if Scenarios
- Adjust drug prices
- Change treatment protocols
- Modify resource availability
- See immediate impact on costs

## Color Scheme
Following established pattern:
- Blues: Staff/human resources
- Greens: Equipment and procedures  
- Purples: Drugs and medications
- Oranges: Facilities and overhead
- Grays: Administrative and other

## Responsive Design
- Mobile-friendly tables with horizontal scroll
- Simplified visualizations for smaller screens
- Priority information shown first on mobile
- Export functionality maintained on all devices