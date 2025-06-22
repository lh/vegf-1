# Cost Tracking Data Requirements

## 1. Input Data Requirements

### 1.1 Cost Parameters (User Configurable)

#### Drug Costs
```yaml
drug_costs:
  eylea_2mg:
    default: 800  # GBP
    min: 350      # Biosimilar price
    max: 1200     # List price + markup
    source: "NHS Drug Tariff 2025"
    
  # Future drugs for expansion
  eylea_8mg: 1197.60
  lucentis: 613.20
  avastin: 50.00
  faricimab: 1028.40
```

#### Visit Component Costs
```yaml
component_costs:
  # Core procedures
  injection_administration:
    value: 150
    code: "HRG BZ86B"
    includes: ["nurse time", "consumables", "facility"]
    
  oct_scan:
    value: 75
    code: "HRG BZ88A"
    includes: ["technician time", "equipment use"]
    
  visual_acuity_test:
    value: 25
    code: "Local tariff"
    includes: ["technician time"]
    
  # Clinical review types
  consultant_review_f2f:
    value: 120
    code: "WF01B"
    includes: ["consultant time", "examination"]
    
  consultant_review_virtual:
    value: 50
    code: "WF01A"
    includes: ["consultant time", "remote review"]
    
  nurse_review:
    value: 40
    code: "N02AF"
    includes: ["specialist nurse time"]
```

### 1.2 Protocol-Specific Parameters

#### T&E Protocol Rules
```yaml
tae_visit_patterns:
  loading_phase:
    - visit: 1
      type: "initial_assessment"
      components: ["consultant_review_f2f", "oct_scan", "visual_acuity_test", "injection_administration"]
    - visit: 2-3
      type: "loading_injection"
      components: ["nurse_review", "injection_administration"]
    - visit: 4
      type: "loading_assessment"
      components: ["consultant_review_f2f", "oct_scan", "visual_acuity_test", "injection_administration"]
  
  maintenance_phase:
    default:
      type: "full_assessment"
      components: ["consultant_review_f2f", "oct_scan", "visual_acuity_test", "injection_administration"]
      decision_maker: true
```

#### T&T Protocol Rules
```yaml
tnt_visit_patterns:
  loading_phase:
    # Same as T&E
    
  maintenance_phase:
    injection_visits:
      type: "injection_only"
      components: ["nurse_review", "injection_administration"]
      decision_maker: false
      
    assessment_visits:
      frequency: "quarterly"  # Every 3rd visit
      type: "monitoring_assessment"
      components: ["consultant_review_f2f", "oct_scan", "visual_acuity_test"]
      decision_maker: true
```

### 1.3 NHS Reference Data

#### Workload Capacity Assumptions
```yaml
nhs_capacity:
  injections_per_nurse_day: 20
  assessments_per_consultant_day: 15
  oct_scans_per_technician_day: 30
  
  # Staff costs for capacity planning
  staff_costs:
    consultant_per_day: 800
    specialist_nurse_per_day: 300
    technician_per_day: 200
```

## 2. Simulation Output Data

### 2.1 Visit-Level Data
```python
# For each visit recorded
visit_data = {
    'patient_id': 'P0001',
    'visit_date': datetime(2025, 1, 15),
    'visit_number': 4,
    'visit_type': 'full_assessment',
    'protocol': 'tae',
    'disease_state': 'ACTIVE',
    'injection_given': True,
    'interval_days': 56,
    'components': {
        'drug_cost': 800,
        'injection_cost': 150,
        'oct_cost': 75,
        'va_test_cost': 25,
        'review_cost': 120,
        'total_cost': 1170
    },
    'workload': {
        'requires_injection': True,
        'requires_decision_maker': True,
        'requires_oct': True
    }
}
```

### 2.2 Patient-Level Aggregations
```python
patient_summary = {
    'patient_id': 'P0001',
    'enrollment_date': datetime(2025, 1, 1),
    'current_status': 'active',  # active/discontinued
    'discontinuation_date': None,
    'discontinuation_reason': None,
    
    # Cost totals
    'total_drug_cost': 12000,
    'total_procedure_cost': 4500,
    'total_cost': 16500,
    
    # Visit counts
    'total_visits': 15,
    'injection_visits': 13,
    'assessment_visits': 15,
    'monitoring_only_visits': 2,
    
    # Outcomes
    'baseline_vision': 55,
    'current_vision': 62,
    'best_vision': 65,
    'months_treated': 18,
    
    # Calculated metrics
    'cost_per_month': 916.67,
    'cost_per_letter_gained': 2357.14,
    'injections_per_year': 8.67
}
```

### 2.3 Cohort-Level Metrics
```python
cohort_metrics = {
    'simulation_id': 'SIM_20250621_001',
    'protocol': 'tae',
    'total_patients': 300,
    'active_patients': 245,
    'discontinued_patients': 55,
    
    # Cost metrics
    'total_cost': 4950000,
    'mean_cost_per_patient': 16500,
    'median_cost_per_patient': 15200,
    'cost_percentiles': {
        '25': 8500,
        '75': 22000,
        '95': 35000
    },
    
    # Workload metrics by month
    'monthly_workload': [
        {
            'month': '2025-01',
            'injections': 250,
            'decision_visits': 250,
            'oct_scans': 250,
            'total_visits': 250
        },
        # ... more months
    ],
    
    # Outcome metrics
    'patients_maintaining_vision': 220,
    'mean_vision_change': 3.5,
    'vision_years_saved': 612.5
}
```

## 3. Calculated Metrics

### 3.1 Cost-Effectiveness Metrics
```python
cost_effectiveness = {
    # Primary outcomes
    'cost_per_patient_treated': 16500,
    'cost_per_patient_maintaining_vision': 22500,
    'cost_per_letter_gained': 4714,
    'cost_per_vision_year_saved': 8082,
    
    # Comparative metrics
    'incremental_cost_vs_comparator': -2500,
    'incremental_effect_vs_comparator': 0.5,
    'icer': -5000,  # Incremental cost-effectiveness ratio
    
    # Budget impact
    'annual_budget_impact': 1650000,
    'cost_per_10000_population': 165000
}
```

### 3.2 Resource Utilization Metrics
```python
resource_metrics = {
    # Peak utilization
    'peak_monthly_injections': 250,
    'peak_monthly_assessments': 250,
    'peak_month': '2025-01',
    
    # Average utilization
    'mean_monthly_injections': 87.5,
    'mean_monthly_assessments': 87.5,
    
    # Capacity requirements
    'injection_nurse_days_required': 12.5,
    'consultant_days_required': 16.7,
    'oct_technician_days_required': 8.3,
    
    # Efficiency metrics
    'injections_per_assessment': 1.0,  # T&E
    'visits_per_patient_year': 8.7
}
```

## 4. Data Export Formats

### 4.1 Patient-Level Export (CSV)
```csv
patient_id,enrollment_date,status,months_treated,total_cost,drug_cost,procedure_cost,injections,baseline_va,final_va,va_change
P0001,2025-01-01,active,18,16500,12000,4500,13,55,62,7
P0002,2025-01-01,discontinued,12,11000,8000,3000,9,48,45,-3
...
```

### 4.2 Visit-Level Export (CSV)
```csv
patient_id,visit_date,visit_type,injection,drug_cost,procedure_cost,total_cost,decision_maker
P0001,2025-01-01,initial_assessment,1,800,370,1170,1
P0001,2025-01-29,loading_injection,1,800,190,990,0
...
```

### 4.3 Summary Report (JSON)
```json
{
  "simulation": {
    "id": "SIM_20250621_001",
    "date": "2025-06-21",
    "protocol": "tae",
    "patients": 300,
    "duration_years": 5
  },
  "costs": {
    "total": 4950000,
    "breakdown": {
      "drug": 3217500,
      "procedures": 1732500
    },
    "per_patient": {
      "mean": 16500,
      "median": 15200,
      "range": [5000, 45000]
    }
  },
  "workload": {
    "total_injections": 2625,
    "total_assessments": 2625,
    "peak_month": {
      "date": "2025-01",
      "injections": 250,
      "assessments": 250
    }
  },
  "outcomes": {
    "vision_maintained": 220,
    "mean_va_change": 3.5,
    "cost_per_vision_year": 8082
  }
}
```

## 5. Data Validation Rules

### 5.1 Cost Validation
- All costs must be non-negative
- Drug costs must be within configured min/max ranges
- Total visit cost must equal sum of components
- Currency must be consistent (GBP)

### 5.2 Workload Validation
- Injection count ≤ total visits
- Decision visits ≤ total visits
- Monthly totals must sum to cohort totals
- No negative workload values

### 5.3 Outcome Validation
- Vision values between 0-100
- Vision change = final - baseline
- Months treated ≥ 0
- Discontinued patients have discontinuation date

## 6. Performance Requirements

### 6.1 Real-Time Updates
- Cost calculations < 10ms per visit
- Aggregations < 100ms per 1000 patients
- Chart updates < 200ms

### 6.2 Memory Efficiency
- Store aggregated data, not all visit details
- Use incremental updates for running totals
- Limit historical data to configurable window

### 6.3 Scalability
- Support up to 10,000 patients
- Handle 5-year simulations
- Export datasets up to 100MB