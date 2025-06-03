# Carbon Button Label & Icon Mapping Plan

## Design Principles
1. **No emojis** - Use proper Carbon icons instead
2. **Clear, concise labels** - Single line where possible
3. **Professional appearance** - Consistent with enterprise applications
4. **Semantic icons** - Icons should clearly represent the action

## Label Mappings

### Navigation Buttons

| Current Label | Proposed Carbon Label | Carbon Icon | Notes |
|---------------|----------------------|-------------|--------|
| 🦍 Home | Home | CarbonIcons.HOME | Clean, standard navigation |
| 📋 **Protocol Manager**<br>Browse, view, and validate treatment protocols | Protocol Manager | CarbonIcons.DOCUMENT | Simplified to single line |
| 🚀 **Run Simulation**<br>Execute simulations with selected protocols | Run Simulation | CarbonIcons.PLAY or CarbonIcons.ROCKET | Play might be clearer |
| 📊 **Analysis**<br>Visualize and compare simulation results | Analysis Overview | CarbonIcons.ANALYTICS or CarbonIcons.CHART_BAR | Either works well |

### Action Buttons

| Current Label | Proposed Carbon Label | Carbon Icon | Notes |
|---------------|----------------------|-------------|--------|
| 📤 Upload | Upload Protocol | CarbonIcons.UPLOAD | Standard upload icon |
| 📝 Duplicate | Duplicate | CarbonIcons.COPY | Copy is clearer than document |
| 📝 Create Duplicate | Create Copy | CarbonIcons.COPY | Consistent with above |
| 💾 Download | Download | CarbonIcons.DOWNLOAD | Standard download icon |
| 🗑️ Delete | Delete | CarbonIcons.DELETE or CarbonIcons.TRASH_CAN | Either works |
| 🗑️ Confirm Delete | Delete Protocol | CarbonIcons.DELETE | More explicit |
| 🔄 Refresh | Refresh | CarbonIcons.RENEW or CarbonIcons.RESET | Renew for data refresh |
| ✅ Load into Simulation | Load Protocol | CarbonIcons.CHECKMARK or CarbonIcons.ARROW_RIGHT | Checkmark for confirmation |
| ✕ (dismiss) | (icon only) | CarbonIcons.CLOSE | Standard close/dismiss |

### Export Buttons (if we implement separate buttons)

| Current | Proposed | Carbon Icon | Notes |
|----------|----------|-------------|--------|
| 📥 PNG | Export PNG | CarbonIcons.DOWNLOAD | Could use generic download |
| 📥 SVG | Export SVG | CarbonIcons.DOWNLOAD | Or specific format icons if available |
| 📥 JPEG | Export JPEG | CarbonIcons.DOWNLOAD | Keep consistent |
| 📥 WebP | Export WebP | CarbonIcons.DOWNLOAD | Keep consistent |

## Icon Selection Rationale

### Primary Navigation
- **HOME**: Universal home icon
- **DOCUMENT**: Protocols are documents/specifications
- **PLAY**: Simulation execution (alternative: ROCKET for launch metaphor)
- **ANALYTICS**: Data analysis and visualization

### File Operations
- **UPLOAD/DOWNLOAD**: Standard file transfer metaphors
- **COPY**: Clearer than "duplicate" 
- **DELETE/TRASH_CAN**: Standard deletion icons

### Actions
- **RENEW/RESET**: For refresh operations
- **CHECKMARK**: For confirmations
- **CLOSE**: For dismissing dialogs/warnings

## Button Type Recommendations

### Primary Actions (button_type="primary")
- Run Simulation
- Load Protocol
- Create Copy (when in form)

### Secondary Actions (button_type="secondary")
- Protocol Manager, Analysis (on home)
- Upload, Download, Duplicate

### Danger Actions (button_type="danger")
- Delete
- Delete Protocol (confirmation)

### Ghost Actions (button_type="ghost")
- Home navigation links
- Export format buttons
- Refresh

## Questions for Design Discussion

1. **Navigation style**: Should top "Home" buttons be ghost buttons or standard secondary?
2. **Icon positioning**: Left of text (standard) or icon-only buttons for some actions?
3. **Primary action**: Should "Run Simulation" on home be primary (teal-shadow) or secondary?
4. **Popover replacement**: Carbon doesn't have popovers - use modals or inline forms?
5. **Multi-line support**: If needed, how to handle in Carbon buttons?

## Implementation Priority

1. **High Priority** (Day 1-2):
   - Home page navigation buttons
   - Top navigation "Home" buttons
   
2. **Medium Priority** (Day 3-4):
   - Protocol Manager actions
   - Run Simulation button
   
3. **Lower Priority** (Day 5+):
   - Export buttons (may stay in Plotly)
   - Delete confirmations
   - Popover replacements