Visit Types Configuration
========================

This document describes the visit_types.yaml configuration file which defines the different types of visits in the simulation.

File Location
------------
protocols/visit_types.yaml

Purpose
-------
Defines the different visit types used in the simulation, including:
- Injection visits
- Monitoring visits
- Special visits

File Structure
-------------
The YAML file contains a mapping of visit type names to their properties:

.. code-block:: yaml

    visit_type_name:
      description: Human-readable description
      is_injection: Boolean indicating if this is an injection visit
      is_monitoring: Boolean indicating if this is a monitoring visit
      default_interval: Default weeks between visits of this type
