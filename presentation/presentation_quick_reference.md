# NAMD Presentation Quick Reference

## Key NHS Cost Data (Updated)
- **Total UK patients**: 700,000+ with AMD (39,800 new wet AMD cases/year)
- **Annual NHS budget**: £600-800 million for wet AMD (current estimate)
- **Drug costs alone**: £447 million (2015/16 figure)
- **Projected 2035 cost**: £1.2-1.5 billion (60% increase)

## Annual NHS Spending Comparison
- **Wet AMD treatment**: £600-800 million (700,000+ patients, ongoing)
- **Cataract surgery**: £320-480 million (400,000 procedures/year)
- **Hip replacement**: £500-700 million (100,000 procedures/year)

**Key insight**: 
- Cataract surgery: £1,964 per QALY (exceptional value)
- Hip replacement: £2,128 per QALY (strong value)  
- Wet AMD: £58,047 per QALY (nearly 3x NICE's £20,000 threshold)

## Current Drug Costs (2024 list prices before confidential discounts)
- **Aflibercept (Eylea)**: £816 per injection
- **Generic aflibercept**: Coming soon (expected 50% reduction)
- **Treatment frequency**: 8-10 injections year 1, then 4-5/year ongoing

## Cost Breakdown
- Drug costs: 42.5% of total
- Eye exams/monitoring: 28.3%
- Remainder: OCT scans, appointments, procedures

## Building the Presentation
```bash
cd workspace
pdflatex namd_presentation.tex
pdflatex namd_presentation.tex  # Run twice for references
```

## Presentation Flow (10 minutes)
1. Title & Acknowledgments (0:15)
2. What is NAMD? (0:45)
3. Biology of NAMD (0:45)
4. Revolutionary Treatment (0:45)
5. Cost Challenge (1:00)
6. Why Model? (1:00)
7. Two Approaches (1:00)
8. Our Solution (0:30)
9. Live Demo (2:30)
10. Key Insights (1:00)
11. Thank You (0:30)

## Screen Recording Plan
- Main interface tour
- Protocol loading
- Run simulation (1000 patients)
- Patient Explorer
- Calendar-time visualization
- Protocol comparison

## Key Messages
- NAMD causes central vision loss leading to legal blindness
- Anti-VEGF treatments work but need repeated injections
- Balancing cost vs effectiveness is critical
- Agent-based modeling provides better insights than simple Excel models
- Your tool enables evidence-based decision making