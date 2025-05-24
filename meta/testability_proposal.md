# Testability Enhancement Proposal for AMD Protocol Explorer

## Background

The AMD Protocol Explorer Streamlit application currently has challenges with automated testing. While there is some puppeteer integration in place, it's not consistently applied, making it difficult to reliably automate interactions with the application for testing and monitoring.

## Proposed Architecture: Comprehensive Testability Framework

This proposal outlines a layered, robust approach to make the Streamlit app fully testable while maintaining a clean separation of concerns between the application logic and test infrastructure.

### 1. Component Registry Pattern

Create a central registry of interactive components to decouple the testing interface from component implementation:

```python
# testability_registry.py
class ComponentRegistry:
    _registry = {}
    
    @classmethod
    def register(cls, component_id, component, interaction_type, selector=None):
        """Register a component with the testing framework"""
        cls._registry[component_id] = {
            'component': component,
            'type': interaction_type,  # button, slider, selectbox, etc.
            'selector': selector,      # DOM selector for direct access
            'timestamp': time.time()   # When the component was registered
        }
    
    @classmethod
    def get_component(cls, component_id):
        """Retrieve a component by ID"""
        return cls._registry.get(component_id)
    
    @classmethod
    def get_all_components(cls, component_type=None):
        """Get all components, optionally filtered by type"""
        if component_type:
            return {id: info for id, info in cls._registry.items() 
                   if info['type'] == component_type}
        return cls._registry
```

### 2. Explicit Testing JavaScript API

Add a JavaScript layer specifically for testing to provide a stable interface for automated tools:

```javascript
// test_api.js (injected during app initialization)
window.testAPI = {
    // Component registry
    components: {},
    
    // Action handlers
    actions: {
        navigate: function(pageName) {
            // Find and click navigation element by page name
            const navigationItems = Array.from(document.querySelectorAll('[data-testid="stRadio"] label'));
            const targetItem = navigationItems.find(item => item.textContent.includes(pageName));
            if (targetItem) targetItem.click();
            return !!targetItem;
        },
        
        setValue: function(componentId, value) {
            // Set value for sliders, inputs, etc.
            const component = document.querySelector(`[data-test-id="${componentId}"]`);
            if (!component) return false;
            
            // Handle different component types
            const type = component.getAttribute('data-test-type');
            if (type === 'slider') {
                // Position calculation logic for sliders
                this._setSliderValue(component, value);
            } else if (type === 'input') {
                // Set input value
                const input = component.querySelector('input');
                if (input) {
                    input.value = value;
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
            return true;
        },
        
        click: function(componentId) {
            // Click a button or other clickable element
            const component = document.querySelector(`[data-test-id="${componentId}"]`);
            if (!component) return false;
            
            // Find the actual clickable element
            const clickable = component.querySelector('button') || component;
            clickable.click();
            return true;
        },
        
        // Helper methods for specific component types
        _setSliderValue: function(sliderElement, value) {
            // Calculate position based on min/max/value
            const min = parseFloat(sliderElement.getAttribute('data-min') || '0');
            const max = parseFloat(sliderElement.getAttribute('data-max') || '100');
            const percent = (value - min) / (max - min);
            
            // Get bounding box
            const rect = sliderElement.getBoundingClientRect();
            const x = rect.left + rect.width * percent;
            const y = rect.top + rect.height / 2;
            
            // Simulate mouse interaction
            const mouseDown = new MouseEvent('mousedown', {
                bubbles: true, cancelable: true, clientX: x, clientY: y
            });
            const mouseUp = new MouseEvent('mouseup', {
                bubbles: true, cancelable: true, clientX: x, clientY: y
            });
            
            sliderElement.dispatchEvent(mouseDown);
            sliderElement.dispatchEvent(mouseUp);
        }
    },
    
    // Status tracking
    status: {
        isReady: false,
        pendingComponents: [],
        readyComponents: []
    },
    
    // Event system
    events: {
        listeners: {},
        on: function(event, callback) {
            if (!this.listeners[event]) this.listeners[event] = [];
            this.listeners[event].push(callback);
        },
        emit: function(event, data) {
            if (!this.listeners[event]) return;
            this.listeners[event].forEach(callback => callback(data));
        }
    },
    
    // Initialization
    init: function() {
        this.status.isReady = true;
        this.events.emit('ready');
        console.log('Test API initialized');
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    window.testAPI.init();
});
```

### 3. Streamlit Component Wrappers

Create enhanced versions of Streamlit components that automatically register with the test framework:

```python
# testable_components.py
import streamlit as st
import uuid
from testability_registry import ComponentRegistry

def testable_button(label, on_click=None, key=None, test_id=None, **kwargs):
    """Create a button that's registered with the test framework"""
    # Generate a test ID if not provided
    if test_id is None:
        test_id = f"button-{key or label.lower().replace(' ', '-')}-{str(uuid.uuid4())[:8]}"
    
    # Add a marker element for testers to find
    st.markdown(f'<div data-test-id="{test_id}" data-test-type="button"></div>', 
                unsafe_allow_html=True)
    
    # Create the button
    result = st.button(label, on_click=on_click, key=key, **kwargs)
    
    # Register with the testability framework
    ComponentRegistry.register(test_id, "button", key)
    
    return result

def testable_slider(label, min_value, max_value, value=None, key=None, test_id=None, **kwargs):
    """Create a slider that's registered with the test framework"""
    # Generate a test ID if not provided
    if test_id is None:
        test_id = f"slider-{key or label.lower().replace(' ', '-')}-{str(uuid.uuid4())[:8]}"
    
    # Add a marker element with min/max attributes
    st.markdown(f'''
    <div data-test-id="{test_id}" 
         data-test-type="slider"
         data-min="{min_value}" 
         data-max="{max_value}"
         data-default="{value or min_value}"></div>
    ''', unsafe_allow_html=True)
    
    # Create the slider
    result = st.slider(label, min_value, max_value, value, key=key, **kwargs)
    
    # Register with the testability framework
    ComponentRegistry.register(
        test_id, 
        "slider", 
        key, 
        {"min": min_value, "max": max_value, "default": value or min_value}
    )
    
    return result

# Create wrappers for all Streamlit components
def testable_selectbox(label, options, index=0, key=None, test_id=None, **kwargs):
    # Implementation similar to button and slider
    pass

def testable_radio(label, options, index=0, key=None, test_id=None, **kwargs):
    # Implementation similar to button and slider
    pass

# And so on for other components...
```

### 4. Test Mode Integration

Add a special test mode that can be activated via URL parameters:

```python
# In app.py initialization

# Check for test mode
test_params = st.experimental_get_query_params()
test_mode = test_params.get('test_mode', ['false'])[0].lower() == 'true'

if test_mode:
    st.session_state['test_mode'] = True
    
    # Add marker class to body for test scripts to detect
    st.markdown("""
    <style>
    body {
        position: relative;
    }
    body:after {
        content: 'TEST MODE';
        position: fixed;
        bottom: 10px;
        right: 10px;
        background: rgba(255, 0, 0, 0.7);
        color: white;
        padding: 5px 10px;
        font-size: 12px;
        border-radius: 3px;
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Inject test API script
    with open(os.path.join(os.path.dirname(__file__), 'test_api.js'), 'r') as f:
        test_api_script = f.read()
        st.markdown(f"<script>{test_api_script}</script>", unsafe_allow_html=True)
```

### 5. Command Protocol for Testing

Define a standard protocol for test commands to provide a consistent interface:

```javascript
// Example command format
{
  "command": "interact",      // Command type (navigate, interact, verify, etc.)
  "target": "run-simulation-btn",  // Target component
  "action": "click",          // Action to perform
  "params": {},               // Additional parameters
  "expectedState": {          // Expected app state after action
    "page": "Run Simulation",
    "simulationRunning": true
  },
  "waitFor": {                // Elements to wait for
    "selector": ".stSuccess",
    "timeout": 60000          // 60 seconds
  }
}
```

### 6. Synchronization Helpers

Add utilities to help test scripts synchronize with application state:

```javascript
// In test_api.js
waitForElement: async function(selector, options = {}) {
    const timeout = options.timeout || 10000;
    const interval = options.interval || 100;
    const start = Date.now();
    
    while (Date.now() - start < timeout) {
        const element = document.querySelector(selector);
        if (element) return element;
        await new Promise(r => setTimeout(r, interval));
    }
    
    throw new Error(`Timeout waiting for element: ${selector}`);
},

waitForCondition: async function(predicate, options = {}) {
    const timeout = options.timeout || 10000;
    const interval = options.interval || 100;
    const start = Date.now();
    
    while (Date.now() - start < timeout) {
        if (await predicate()) return true;
        await new Promise(r => setTimeout(r, interval));
    }
    
    throw new Error('Timeout waiting for condition');
}
```

### 7. Diagnostic Channel

Add a WebSocket-based diagnostic channel for real-time monitoring and debugging:

```python
# diagnostic_server.py
import asyncio
import websockets
import json
import time
import threading

class DiagnosticServer:
    def __init__(self, host='127.0.0.1', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.events = []
        self.max_events = 1000
        self.server = None
        self.thread = None
        
    async def handler(self, websocket, path):
        """Handle new WebSocket connections"""
        self.clients.add(websocket)
        try:
            # Send event history
            await websocket.send(json.dumps({
                'type': 'history',
                'events': self.events
            }))
            
            # Keep connection alive
            while True:
                await asyncio.sleep(30)
                await websocket.ping()
        except Exception as e:
            print(f"Diagnostic connection error: {e}")
        finally:
            self.clients.remove(websocket)
    
    async def broadcast(self, message):
        """Send message to all connected clients"""
        if not self.clients:
            return
            
        for client in self.clients:
            try:
                await client.send(message)
            except Exception:
                pass
    
    def report_event(self, event_type, data):
        """Report a new diagnostic event"""
        event = {
            'timestamp': time.time(),
            'type': event_type,
            'data': data
        }
        
        # Add to history
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
            
        # Broadcast to clients
        message = json.dumps(event)
        asyncio.run(self.broadcast(message))
    
    def start(self):
        """Start the diagnostic server in a background thread"""
        if self.thread and self.thread.is_alive():
            return
            
        def run_server():
            asyncio.set_event_loop(asyncio.new_event_loop())
            self.server = websockets.serve(self.handler, self.host, self.port)
            asyncio.get_event_loop().run_until_complete(self.server)
            asyncio.get_event_loop().run_forever()
        
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the diagnostic server"""
        if self.server:
            self.server.close()
```

## Implementation Strategy

The implementation would be phased to minimize disruption:

### Phase 1: Foundation
- Add test API JavaScript
- Create the component registry
- Develop basic testable component wrappers
- Implement test mode

### Phase 2: Enhanced Components
- Replace standard Streamlit components with testable versions
- Add diagnostic WebSocket server
- Implement component lifecycle events

### Phase 3: Test Tooling
- Create Puppeteer helpers that use the test API
- Develop automated test suites
- Add visual regression testing

## Benefits

This architecture provides several significant benefits:

1. **Resilience to UI Changes**: By decoupling testing from the specific DOM structure, tests remain stable even as the UI evolves
2. **Better Timing Control**: Explicit sync points and waitFor utilities prevent flaky tests by eliminating timing issues
3. **Improved Debugging**: The diagnostic channel and test mode make it easier to identify and fix test failures
4. **Comprehensive Coverage**: The approach works for all aspects of the application, not just simple UI elements
5. **Separation of Concerns**: Testing code is separate from application code, leading to cleaner implementation

## Conclusion

This comprehensive testability framework would significantly improve the AMD Protocol Explorer's automated testing capabilities. It provides a robust foundation for reliable UI testing while maintaining a clean separation between the application and test code.

With this framework in place, we would be able to:
- Run automated tests reliably as part of CI/CD pipelines
- Monitor application health in production environments
- Validate new features without regression
- Support AI assistant integration for application monitoring and testing