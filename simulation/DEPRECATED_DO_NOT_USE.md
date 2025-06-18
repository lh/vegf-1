# ⚠️ DEPRECATED - DO NOT USE ⚠️

## This entire directory contains the OLD simulation framework (v1)

### ❌ DO NOT USE THIS CODE FOR NEW DEVELOPMENT

**APE uses `simulation_v2/` exclusively.**

## Why is this here?

This legacy code is retained for:
- Historical reference
- Understanding how the old system worked
- Comparison with new implementation

## What should I use instead?

| Old (simulation/)          | New (simulation_v2/)                      |
|---------------------------|-------------------------------------------|
| `simulation.abs`          | `simulation_v2.engines.abs_engine`        |
| `simulation.des`          | `simulation_v2.engines.des_engine`        |
| `AgentBasedSimulation`    | `ABSEngine`                              |
| `DiscreteEventSimulation` | `DESEngine`                              |
| `SimulationConfig`        | `ProtocolSpecification`                  |

## For APE development:

Use the components in:
- `ape/` - APE-specific components
- `simulation_v2/` - Core simulation engines
- `protocols/v2/` - Protocol specifications

## If you see imports from this directory:

1. The code is likely outdated
2. Check if it's in `archive/` or `research/` (expected)
3. If in active code, it needs updating to use `simulation_v2`

## Key differences:

- **Architecture**: v2 has cleaner separation of engines, models, and specs
- **Configuration**: v2 uses `ProtocolSpecification` instead of `SimulationConfig`
- **Time-based models**: Only supported in v2
- **Performance**: v2 is optimized for large-scale simulations

---

**Last updated**: 2025-01-18
**Status**: Deprecated since 2024
**Replaced by**: simulation_v2/