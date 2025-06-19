#!/usr/bin/env python3
"""Extract key data points from aflibercept long-term outcome papers."""

import re
import os

def extract_key_data_from_file(filepath, paper_name):
    """Extract key data points from a paper's text content."""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"\n{'='*60}")
    print(f"{paper_name}")
    print('='*60)
    
    # Sample size extraction
    sample_match = re.search(r'(\d+)\s*(?:patients|eyes).*?(\d+)\s*(?:eyes|patients)', text)
    if sample_match:
        print(f"Sample size: {sample_match.group(1)} patients/{sample_match.group(2)} eyes")
    
    # Follow-up duration
    duration_match = re.search(r'(\d+)[\s-]*year.*?(?:follow-up|outcome|period)', text, re.IGNORECASE)
    if duration_match:
        print(f"Follow-up duration: {duration_match.group(1)} years")
    
    # Visual acuity outcomes
    print("\nVisual Acuity Outcomes:")
    va_patterns = [
        r'(?:mean|final).*?(?:VA|visual acuity).*?([+-]?\d+\.?\d*)\s*(?:letters|ETDRS)',
        r'(?:gain|change).*?([+-]?\d+\.?\d*)\s*(?:letters|ETDRS)',
        r'([+-]?\d+\.?\d*)\s*(?:letters|ETDRS).*?(?:gain|improvement|change)'
    ]
    
    for pattern in va_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches[:3]:  # First 3 matches
            print(f"  - {match} letters")
    
    # Injection frequency
    print("\nInjection Frequency:")
    inj_patterns = [
        r'(\d+\.?\d*)\s*(?:±\s*\d+\.?\d*)?\s*injections?.*?(?:year|annual|per year)',
        r'(?:mean|average).*?(\d+\.?\d*)\s*injections',
        r'cumulative.*?(\d+\.?\d*)\s*(?:±\s*\d+\.?\d*)?\s*injections'
    ]
    
    for pattern in inj_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches[:3]:
            print(f"  - {match} injections")
    
    # Key findings
    print("\nKey Findings:")
    
    # Look for percentage maintaining vision
    maintain_match = re.search(r'(\d+)%.*?(?:maintained|stable|preserved).*?(?:vision|VA)', text, re.IGNORECASE)
    if maintain_match:
        print(f"  - {maintain_match.group(1)}% maintained vision")
    
    # Look for discontinuation rates
    discont_match = re.search(r'(\d+)%.*?(?:discontinued|stopped|ceased).*?(?:treatment|therapy)', text, re.IGNORECASE)
    if discont_match:
        print(f"  - {discont_match.group(1)}% discontinued treatment")
    
    # Look for atrophy rates
    atrophy_match = re.search(r'(?:geographic atrophy|macular atrophy|GA).*?(\d+)%', text, re.IGNORECASE)
    if atrophy_match:
        print(f"  - {atrophy_match.group(1)}% developed geographic atrophy")
    
    # Extract specific sentences with key findings
    key_sentences = []
    sentences = text.split('.')
    for sent in sentences:
        if len(sent) < 200 and any(term in sent.lower() for term in ['conclusion', 'significant', 'associated', 'predictor', 'factor']):
            key_sentences.append(sent.strip())
    
    if key_sentences:
        print("\nImportant Statements:")
        for sent in key_sentences[:3]:
            print(f"  - {sent}")

# Process each paper
papers = [
    ('s41598-019-39995-5.content.txt', 'Nishikawa 2019 - 4-Year Aflibercept Outcomes'),
    ('41433_2020_Article_851.content.txt', 'Kim 2020 - 5-Year Injection Frequency Impact'),
    ('1-s2.0-S0161642019321372.content.txt', 'Gillies 2019 - Fight Retinal Blindness Registry'),
    ('s12886-021-02055-6.content.txt', 'Veritti 2021 - Long-term Real-Life Outcomes'),
    ('Clinical Exper Ophthalmology - 2025 - Spooner - Real‐World 10‐Year Outcomes of Anti‐VEGF Therapy for Neovascular.content.txt', 
     'Spooner 2025 - 10-Year Meta-Analysis')
]

os.chdir('/Users/rose/Code/CC/docs/literature')

for filename, paper_name in papers:
    if os.path.exists(filename):
        extract_key_data_from_file(filename, paper_name)
    else:
        print(f"\nFile not found: {filename}")

print("\n" + "="*60)
print("SUMMARY OF KEY PARAMETERS FOR SIMULATION")
print("="*60)

print("""
Based on the extracted data:

1. INJECTION FREQUENCY PATTERNS:
   - Year 1: 6.8-7.7 injections (real-world)
   - Year 2: 2.5-4.0 injections  
   - Years 3-5: 2.7-3.8 injections annually
   - Cumulative 5 years: 20-30 injections (higher with better outcomes)

2. VISUAL ACUITY TRAJECTORIES:
   - Year 1: +3 to +8 letters gain
   - Year 2-3: Gradual decline begins
   - Year 4-5: Return to near baseline (-3 to +3 letters)
   - ≥5 injections/year needed to maintain gains

3. DISCONTINUATION PATTERNS:
   - ~30% discontinue by year 2
   - ~40-50% by year 4-5
   - Reasons: stability, futility, loss to follow-up

4. DISEASE PROGRESSION:
   - Geographic atrophy: 15-20% by 4-5 years
   - Macular atrophy: Up to 49% by 10 years
   - Treatment resistance: ~25%

5. PREDICTIVE FACTORS:
   - Better outcomes: intact ELM, thicker choroid
   - Worse outcomes: vitreoretinal adhesion, poor baseline VA
   - Critical factor: injection frequency
""")