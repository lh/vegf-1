# Resource and Cost Data Specification

## Cost Configuration Structure

### Enhanced YAML Configuration Format
```yaml
metadata:
  version: "2.0"
  currency: "GBP"
  effective_date: "2025-06-16"
  region: "England"
  trust: "Generic NHS Trust"

# Drug costs with net pricing after discounts
drug_costs:
  aflibercept_2mg:
    list_price: 816.00
    discount_rate: 0.44
    net_price: 457.00
    vat_rate: 0.20  # Non-recoverable for drug purchases
    nhs_cost_inc_vat: 548.40
    unit: "per_vial"
    typical_annual_usage: 6.9  # injections per year
    
  aflibercept_8mg:
    list_price: 998.00
    discount_rate: 0.66
    net_price: 339.00
    vat_rate: 0.20
    nhs_cost_inc_vat: 406.80
    unit: "per_vial"
    typical_annual_usage: 6.1
    
  ranibizumab:
    list_price: 742.00
    discount_rate: 0.30
    net_price: 519.00
    vat_rate: 0.20
    nhs_cost_inc_vat: 622.80
    unit: "per_vial"
    
  bevacizumab_compounded:
    list_price: 50.00
    discount_rate: 0.00
    net_price: 50.00
    vat_rate: 0.20
    nhs_cost_inc_vat: 60.00
    unit: "per_vial"

# Visit component costs
visit_components:
  # Staff costs per hour
  consultant_ophthalmologist: 147.00
  specialist_nurse: 54.00
  healthcare_assistant: 29.00
  admin_staff: 25.00
  
  # Procedure costs
  oct_scan: 45.00
  visual_acuity_test: 15.00
  slit_lamp_exam: 25.00
  fundus_photography: 35.00
  
  # Facility costs per slot
  injection_room_30min: 50.00
  consultation_room_20min: 30.00
  
  # Consumables
  injection_consumables: 15.00  # needles, swabs, drapes, etc.
  
# Visit type definitions
visit_types:
  injection_visit:
    duration_minutes: 30
    components:
      - specialist_nurse
      - injection_room_30min
      - injection_consumables
      - visual_acuity_test
    staff_time:
      specialist_nurse: 0.5  # 30 minutes
      
  monitoring_visit:
    duration_minutes: 20
    components:
      - healthcare_assistant
      - consultation_room_20min
      - visual_acuity_test
      - oct_scan
    staff_time:
      healthcare_assistant: 0.33  # 20 minutes
      
  initial_assessment:
    duration_minutes: 45
    components:
      - consultant_ophthalmologist
      - consultation_room_20min
      - visual_acuity_test
      - oct_scan
      - slit_lamp_exam
      - fundus_photography
    staff_time:
      consultant_ophthalmologist: 0.75  # 45 minutes
      
  follow_up_consultation:
    duration_minutes: 20
    components:
      - consultant_ophthalmologist
      - consultation_room_20min
      - slit_lamp_exam
    staff_time:
      consultant_ophthalmologist: 0.33  # 20 minutes

# Special events and procedures
special_events:
  adverse_event_mild: 150.00
  adverse_event_severe: 500.00
  treatment_switch_admin: 50.00
  
# Time-based cost variations
time_variations:
  biosimilar_entry:
    date: "2025-06-16"
    changes:
      aflibercept_biosimilar:
        list_price: 400.00
        discount_rate: 0.43
        net_price: 228.00
        vat_rate: 0.20
        nhs_cost_inc_vat: 273.60
```

## Resource Categories and Tracking

### 1. Human Resources
```yaml
staff_resources:
  consultant_ophthalmologist:
    category: "medical_staff"
    unit: "hours"
    availability: 
      weekly_hours: 40
      clinic_allocation: 0.6  # 60% of time in clinic
      
  specialist_nurse:
    category: "nursing_staff"  
    unit: "hours"
    availability:
      weekly_hours: 37.5
      clinic_allocation: 0.8  # 80% of time in clinic
      
  healthcare_assistant:
    category: "support_staff"
    unit: "hours"
    availability:
      weekly_hours: 37.5
      clinic_allocation: 1.0  # 100% in clinic
```

### 2. Equipment Resources
```yaml
equipment_resources:
  oct_scanner:
    category: "diagnostic_equipment"
    unit: "scans"
    capacity:
      scans_per_hour: 6
      maintenance_downtime: 0.05  # 5% downtime
      
  injection_chair:
    category: "treatment_equipment"
    unit: "slots"
    capacity:
      slots_per_day: 16  # 30-min slots
      
  visual_acuity_chart:
    category: "basic_equipment"
    unit: "tests"
    capacity:
      tests_per_hour: 12
```

### 3. Facility Resources
```yaml
facility_resources:
  injection_room:
    category: "treatment_space"
    unit: "room_hours"
    capacity:
      hours_per_day: 8
      rooms_available: 2
      
  consultation_room:
    category: "consultation_space"
    unit: "room_hours"
    capacity:
      hours_per_day: 8
      rooms_available: 4
```

## Resource Usage Patterns

### Per Visit Resource Requirements
```yaml
resource_requirements:
  injection_visit:
    staff:
      specialist_nurse: 0.5  # hours
    equipment:
      injection_chair: 1  # slot
      visual_acuity_chart: 1  # test
    facility:
      injection_room: 0.5  # hours
    consumables:
      injection_pack: 1
      
  monitoring_visit:
    staff:
      healthcare_assistant: 0.33  # hours
    equipment:
      oct_scanner: 1  # scan
      visual_acuity_chart: 1  # test
    facility:
      consultation_room: 0.33  # hours
```

## Cost Calculation Rules

### 1. Drug Cost Calculations
- Base cost = net_price × quantity
- Include wastage factor for partial vials
- Apply time-based variations (e.g., biosimilar entry)

### 2. Visit Cost Calculations
- Sum all component costs
- Apply staff time multipliers
- Include facility overhead allocation

### 3. Total Patient Cost
- Sum all drug costs over treatment period
- Sum all visit costs
- Add special event costs if applicable
- Apply any bundle discounts

## Reporting Metrics

### Resource Utilization Metrics
- Peak concurrent resource usage
- Average utilization percentage
- Bottleneck identification
- Capacity planning requirements

### Cost Analysis Metrics
- Cost per patient per year
- Cost per injection
- Cost breakdown by category
- Cost variation analysis
- Budget impact projection

### Efficiency Metrics
- Cost per vision year saved
- Resource efficiency ratios
- Comparative effectiveness
- Value for money indicators