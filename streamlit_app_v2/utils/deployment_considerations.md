# Carbon Icons: Deployment Considerations

## Streamlit Community Cloud Deployment ☁️

### ✅ Embedded SVGs (Recommended)
```python
class CarbonIcons:
    UPLOAD = '''<svg>...</svg>'''  # Works everywhere!
```

**Pros:**
- Zero configuration needed
- No `requirements.txt` changes
- Instant deployment
- No external dependencies
- Works offline
- Typically faster (no network requests)

**File size impact:**
- Each icon: ~200-500 bytes
- 20 icons = ~10KB total
- Negligible impact on app size

### ❌ NPM Package Approach (Not Recommended)
```javascript
npm install @carbon/icons
```

**Why this doesn't work well:**
- Streamlit Cloud is Python-only
- No Node.js runtime
- No npm build step
- Would need complex workarounds
- Adds unnecessary complexity

## Best Practice for Production

1. **Download only what you need**
   - 10-20 icons typical for most apps
   - Each icon is tiny (~300 bytes)

2. **Organize by feature**
   ```python
   class CarbonIcons:
       # Navigation
       HOME = '''<svg>...</svg>'''
       
       # Actions  
       UPLOAD = '''<svg>...</svg>'''
       DOWNLOAD = '''<svg>...</svg>'''
       
       # Status
       SUCCESS = '''<svg>...</svg>'''
       WARNING = '''<svg>...</svg>'''
   ```

3. **Consider licensing**
   - Carbon icons are Apache 2.0 licensed
   - Free for commercial use
   - Include attribution in your about page

## Quick Start for Your App

1. Visit https://carbondesignsystem.com/elements/icons/library/
2. Download these essential icons:
   - upload, download, copy, play--filled
   - document, home, chart--bar
   - warning, information, checkmark
   
3. Add to `carbon_button.py`:
   ```python
   class CarbonIcons:
       UPLOAD = '''[paste SVG here]'''
   ```

4. Deploy to Streamlit Cloud - it just works!

## Alternative: Icon Fonts

If you need many icons, consider icon fonts:
```python
st.markdown('''
<link href="https://unpkg.com/carbon-components/css/carbon-components.min.css" rel="stylesheet">
''', unsafe_allow_html=True)
```

But embedded SVGs are still recommended for:
- Better performance
- No external dependencies  
- Guaranteed availability
- Easier customization