# Button Inventory - Baseline Documentation

Generated: 2025-06-03

## Summary
Total buttons found across all pages: ~30-40 buttons (varies by state)

## Button Types by Page

### 1. Home Page (APE.py)
| Button | Type | Icon | Properties | Key |
|--------|------|------|------------|-----|
| Protocol Manager | Navigation | 📋 | Multi-line, full width | nav_protocol |
| Run Simulation | Navigation | 🚀 | Multi-line, full width | nav_simulation |
| Analysis | Navigation | 📊 | Multi-line, full width | nav_analysis |

### 2. Protocol Manager (pages/1_Protocol_Manager.py)
| Button | Type | Icon | Properties | Key |
|--------|------|------|------------|-----|
| Home | Navigation | 🦍 | Top navigation | top_home |
| Upload (popover trigger) | Action | 📤 | In column | - |
| Duplicate (popover trigger) | Action | 📝 | In column | - |
| Create Duplicate | Form | 📝 | Inside popover, full width | create_dup_btn |
| Download | Action | 💾 | Downloads YAML | - |
| Delete (popover trigger) | Danger | 🗑️ | Only for temp files | - |
| Confirm Delete | Danger | 🗑️ | Inside popover, secondary | delete_{name} |
| Refresh | Action | 🔄 | When file deleted | - |
| Load into Simulation | Primary | ✅ | Full width | load_protocol |
| Return to Home | Navigation | 🦍 | Fallback when no protocols | - |
| Dismiss Warning | Action | ✕ | Small dismiss button | dismiss_warning |

### 3. Run Simulation (pages/2_Run_Simulation.py)
| Button | Type | Icon | Properties | Key |
|--------|------|------|------------|-----|
| Home | Navigation | 🦍 | Top navigation | - |
| Run Simulation | Primary | 🚀 | Full width, primary action | run_simulation |
| View Results | Action | 📊 | After simulation | - |
| Reset Parameters | Action | 🔄 | Reset to defaults | - |

### 4. Analysis Overview (pages/3_Analysis_Overview.py)
| Button | Type | Icon | Properties | Key |
|--------|------|------|------------|-----|
| Home | Navigation | 🦍 | Top navigation | - |
| Deploy | System | - | Streamlit system button | - |
| Export buttons | Built-in | - | Part of Plotly charts | - |

### 5. Treatment Pattern Tabs (if loaded)
| Button | Type | Icon | Properties | Key |
|--------|------|------|------------|-----|
| Various export formats | Export | 📥 | In Plotly toolbar | - |

## System Buttons (Streamlit Default)
- Deploy button (appears in Streamlit Cloud)
- Sidebar toggle
- Settings/menu buttons
- Element toolbar buttons

## Button Characteristics

### Navigation Buttons
- Use emoji icons (🦍, 📋, 🚀, 📊)
- Multi-line text with descriptions on home page
- Simple text with icon on other pages
- Full width on home page
- Standard width in top navigation

### Action Buttons
- Primary actions use full width
- Secondary actions in columns
- Popover triggers for complex actions
- Form submit buttons inside popovers

### Danger Buttons
- Delete actions use 🗑️ icon
- Require confirmation
- Type="secondary" for confirm delete
- Only available for temporary files

### Special Patterns
- Popovers used for: Upload, Duplicate, Delete
- Multi-step workflows with state management
- Conditional visibility based on file type
- Success/error messages after actions

## Session State Usage
- `selected_protocol_name`: Maintains protocol selection
- `duplicate_success`: Shows success message
- `creating_duplicate`: Prevents double-clicks
- `dismissed_temp_warning`: Hides warning after dismiss
- `simulation_results`: Tracks if results available

## Migration Considerations
1. Multi-line button text needs special handling in Carbon
2. Popovers may need alternative UI pattern
3. Full-width buttons common for primary actions
4. Icon usage is extensive - need Carbon icon mapping
5. State management for multi-step workflows
6. Conditional button visibility based on context