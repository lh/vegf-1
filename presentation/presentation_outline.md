# NAMD Simulation Presentation Outline (10 minutes)

## Time Allocation
- Introduction & NAMD Education: 3 minutes
- Treatment Challenges & Costs: 2 minutes  
- Modeling Rationale: 2 minutes
- Application Demo: 2.5 minutes
- Conclusion: 0.5 minutes

## Slide Structure

### 1. Title Slide (0:00-0:15)
- Title: "Agent-Based Simulation for Neovascular AMD Treatment Planning"
- Your name, NHS Trust
- Acknowledgments: HSMA team, Finance/IT Directors, NHS England Pharmacy Team

### 2. What is Neovascular AMD? (0:15-1:00)
- Central vision loss → cannot read or recognize faces
- Legal blindness if untreated
- Visual example showing impact on vision

### 3. The Biology Behind NAMD (1:00-1:45)
- Aging eye environment
- Abnormal blood vessel growth, leakage, fibrosis, bleeding
- VEGF (Vascular Endothelial Growth Factor) mediates process
- Diagram showing normal vs NAMD eye

### 4. Revolutionary Treatment (1:45-2:15)
- Anti-VEGF antibodies bind and remove growth factor
- BUT: molecules are cleared over time
- Requires repeated injections
- Treatment frequency poorly understood

### 5. Real-World Treatment Challenges (2:15-2:45)
- Discontinuation reasons: mortality, frailty, treatment failure
- 10-15% drop out per year
- Only 50-60% remain on treatment by year 5
- Critical question: optimize for those who remain

### 6. The Cost Challenge (2:45-3:30)
- Annual NHS cost for NAMD treatment: £XXX million
- Cost per patient per year: £XXXX
- Compare: Cataract surgery ~£800 per patient (one-time)
- Balance: Too much treatment = expensive, Too little = ineffective

### 6. Why Model? (3:30-4:30)
- Treatment controversies need exploration
- Writing models clarifies outcome thinking
- Challenge: Limited real-world data

### 7. Two Modeling Approaches (4:30-5:00)
- Simple approach: Excel spreadsheet with "best guesses" (NHS England)
- Complex approach: Build from known parameters
- Agent-Based Simulation: Individual patients with probabilistic events

### 8. Real-World Complexity (5:00-5:30)
- Simple models: Same starting vision, perfect adherence, no delays
- Our simulation: Vision distribution, real discontinuation, treatment gaps
- Why it matters: NHS capacity, actual populations, realistic outcomes

### 9. Our Solution Architecture (5:30-6:00)
- [SWITCH TO SCREEN RECORDING]
- Four key modules:
  * Protocol management
  * Simulation engine
  * Analysis & visualization
  * Comparison tools
  * (Future: Cost calculator)

### 9. Live Demo (6:00-8:30)
- [SCREEN RECORDING CONTINUES]
- Load protocol
- Run simulation with 1000 patients
- Show patient journeys
- Visualize outcomes
- Compare protocols

### 10. Key Insights (8:30-9:30)
- [RETURN TO SLIDES]
- Model reveals treatment pattern impacts
- Enables evidence-based protocol comparison
- Supports commissioning decisions

### 11. Thank You (9:30-10:00)
- Questions?
- Contact information
- GitHub repository link

## Screen Recording Segments
1. Quick tour of main interface (30s)
2. Loading and editing a protocol (30s)
3. Running a simulation (30s)
4. Viewing patient explorer (30s)
5. Calendar-time analysis visualization (30s)

## Key Messages
- NAMD is serious but treatable
- Treatment optimization is critical for NHS resources
- Agent-based modeling provides insights unavailable from simple models
- Tool enables evidence-based decision making