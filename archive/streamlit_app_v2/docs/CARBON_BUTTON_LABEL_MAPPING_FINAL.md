# Carbon Button Label & Icon Mapping - Final Plan

## Available Carbon Icons (18 total)
- ADD, CHART_BAR, CLOSE, COPY, DELETE, DOCUMENT, DOWNLOAD, FILTER
- HELP, HOME, INFO, PLAY, SAVE, SEARCH, SETTINGS, SUCCESS, UPLOAD, WARNING

## Final Label & Icon Mappings

### Navigation Buttons

| Current Label | Final Carbon Label | Carbon Icon | Button Type |
|---------------|-------------------|-------------|-------------|
| 🦍 Home | Home | HOME | ghost or secondary |
| 📋 **Protocol Manager**<br>Browse, view... | Protocol Manager | DOCUMENT | secondary |
| 🚀 **Run Simulation**<br>Execute simulations... | Run Simulation | PLAY | secondary (primary on home) |
| 📊 **Analysis**<br>Visualize and compare... | Analysis Overview | CHART_BAR | secondary |

### Action Buttons

| Current Label | Final Carbon Label | Carbon Icon | Button Type |
|---------------|-------------------|-------------|-------------|
| 📤 Upload | Upload Protocol | UPLOAD | secondary |
| 📝 Duplicate | Duplicate | COPY | secondary |
| 📝 Create Duplicate | Create Copy | COPY | primary (in form) |
| 💾 Download | Download | DOWNLOAD | secondary |
| 🗑️ Delete | Delete | DELETE | danger |
| 🗑️ Confirm Delete | Delete Protocol | DELETE | danger |
| 🔄 Refresh | Refresh | (no icon) | secondary |
| ✅ Load into Simulation | Load Protocol | SAVE | primary |
| ✕ (dismiss) | (icon only) | CLOSE | ghost |

### Status/Helper Buttons

| Current | Final | Icon | Notes |
|---------|-------|------|-------|
| Deploy | Deploy | (none) | Streamlit system button |
| Settings | Settings | SETTINGS | If we add settings |
| Help | Help | HELP | If we add help |
| Info messages | (in alerts) | INFO | For information |
| Success states | (in alerts) | SUCCESS | For success messages |
| Warnings | (in alerts) | WARNING | For warnings |

## Icon Substitutions (Limited icon set)

Since we have limited icons, here are the compromises:
- **Run Simulation**: Use PLAY instead of ROCKET
- **Analysis**: Use CHART_BAR (no ANALYTICS icon)
- **Refresh**: No refresh icon, use text only
- **Load Protocol**: Use SAVE icon (since it's saving to simulation)
- **Delete confirmation**: Keep DELETE icon

## Button Implementation Examples

```python
# Navigation on home page
ape_button("Protocol Manager", key="nav_protocol", 
          icon=CarbonIcons.DOCUMENT, button_type="secondary")

ape_button("Run Simulation", key="nav_simulation",
          icon=CarbonIcons.PLAY, button_type="primary", is_primary_action=True)

# Top navigation
ape_button("Home", key="top_home",
          icon=CarbonIcons.HOME, button_type="ghost")

# Actions
ape_button("Upload Protocol", key="upload",
          icon=CarbonIcons.UPLOAD, button_type="secondary")

ape_button("Delete", key="delete",
          icon=CarbonIcons.DELETE, button_type="danger")

# Icon-only dismiss
ape_button("", key="dismiss", 
          icon=CarbonIcons.CLOSE, button_type="ghost",
          aria_label="Dismiss warning")
```

## Design Decisions Made

1. **No emojis** - All emojis replaced with Carbon icons or removed
2. **Simplified labels** - Multi-line descriptions removed, single line only
3. **Limited icon set** - Work within the 18 available icons
4. **Consistent types** - Primary for main actions, secondary for navigation, danger for delete
5. **Professional look** - Clean, enterprise-appropriate styling

## Migration Priority

### Phase 1 (Immediate)
1. Home page navigation buttons (3 buttons)
2. Top "Home" navigation on each page (3 instances)

### Phase 2 
3. Protocol Manager action buttons
4. Run Simulation button
5. Form buttons

### Phase 3
6. Delete confirmations
7. Miscellaneous buttons

## Questions Resolved

1. **Icon limitations**: We'll work with the 18 available icons
2. **Multi-line text**: Remove descriptions, use single-line labels
3. **Primary actions**: "Run Simulation" and "Load Protocol" are primary
4. **Ghost buttons**: Use for top navigation and dismiss buttons
5. **Missing icons**: Use text-only for actions without suitable icons