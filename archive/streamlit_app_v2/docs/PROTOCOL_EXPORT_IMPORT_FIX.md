# Protocol Export/Import Fix Summary

## Date: 2025-01-07

### Issue
- KeyError: 'spec' in treatment patterns tab when accessing imported simulations
- Protocol specification not being saved in export packages
- Only basic metadata (name, version) was being saved, not full clinical parameters

### Root Cause
We were thinking backwards - trying to search for protocol data during export instead of saving it when creating simulations.

### Solution
1. **Save protocol at simulation creation time**: Modified `MemoryAwareSimulationRunner` to save the full protocol specification as `protocol.yaml` when creating new simulations using the `to_yaml_dict()` method.

2. **Simplified export process**: The package export now just copies the existing `protocol.yaml` file instead of trying to reconstruct it.

3. **Updated loader**: Modified `simulation_loader.py` to properly instantiate `ProtocolSpecification` from the saved YAML using `from_yaml()` method.

4. **Fail-fast approach**: Removed graceful fallbacks - if protocol spec is missing, we fail immediately with a clear error message.

### Code Changes

#### core/simulation_adapter.py
```python
# Save the full protocol specification with results
protocol_path = results.data_path / "protocol.yaml"
try:
    import yaml
    protocol_dict = self.protocol_spec.to_yaml_dict()
    with open(protocol_path, 'w') as f:
        yaml.dump(protocol_dict, f, default_flow_style=False, sort_keys=False)
    print(f"✅ Saved full protocol specification to {protocol_path}")
except Exception as e:
    print(f"Warning: Could not save full protocol spec: {e}")
```

#### utils/simulation_loader.py
```python
# Load protocol spec from YAML properly
if 'min_interval_days' in protocol_data and 'disease_transitions' in protocol_data:
    from simulation_v2.protocols.protocol_spec import ProtocolSpecification
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(protocol_data, f, default_flow_style=False, sort_keys=False)
        temp_path = Path(f.name)
    
    try:
        protocol_spec = ProtocolSpecification.from_yaml(temp_path)
        protocol_info['spec'] = protocol_spec
        logger.info(f"Loaded full protocol specification for {sim_id}")
    finally:
        temp_path.unlink()  # Clean up temp file
else:
    raise ValueError("Full protocol specification required but not found")
```

### Testing
Created comprehensive test script that verifies:
1. New simulations save the full protocol specification
2. Export packages contain the complete protocol.yaml
3. Imported simulations can access protocol['spec'] in the treatment patterns tab
4. The full export/import workflow works correctly

### Key Principles Applied
1. **Forward-thinking data flow**: Save data when creating it, not search backwards
2. **Fail-fast**: No graceful fallbacks that hide missing data
3. **Data integrity**: Ensure all protocol clinical parameters are preserved
4. **Transparency**: Save protocol in a format that can handle future structure changes

### Result
✅ Full protocol specifications are now properly saved and loaded through the export/import cycle
✅ Treatment patterns tab can access protocol['spec'] for imported simulations
✅ No more KeyError: 'spec' issues