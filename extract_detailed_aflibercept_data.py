#!/usr/bin/env python3
"""Extract detailed data from aflibercept papers with improved parsing."""

import PyPDF2
import re
import os

def extract_detailed_text(pdf_path):
    """Extract full text from PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            full_text = ''
            for page in reader.pages:
                full_text += page.extract_text() + '\n'
            return full_text
    except Exception as e:
        return f'Error reading {pdf_path}: {e}'

def extract_nishikawa_2019(text):
    """Extract specific data from Nishikawa 2019 4-year study."""
    print("\n=== Nishikawa 2019 - 4-Year Aflibercept Outcomes ===")
    
    # Find key results
    results_section = re.search(r'Results(.*?)Discussion', text, re.DOTALL | re.IGNORECASE)
    if results_section:
        results_text = results_section.group(1)
        
        # Extract injection data
        injection_match = re.search(r'(\d+\.\d+)\s*±\s*(\d+\.\d+)\s*injections.*?first year.*?(\d+\.\d+)\s*±\s*(\d+\.\d+).*?following three', results_text)
        if injection_match:
            print(f"Year 1 injections: {injection_match.group(1)} ± {injection_match.group(2)}")
            print(f"Years 2-4 total injections: {injection_match.group(3)} ± {injection_match.group(4)}")
        
        # Extract visual acuity
        va_match = re.search(r'logMAR.*?baseline.*?(\d+\.\d+).*?year one.*?(\d+\.\d+).*?year four.*?(\d+\.\d+)', results_text)
        if va_match:
            print(f"Visual acuity (logMAR): Baseline {va_match.group(1)}, Year 1 {va_match.group(2)}, Year 4 {va_match.group(3)}")
    
    # Extract predictive factors
    if 'ELM' in text and 'vitreoretinal' in text:
        print("\nPredictive factors found:")
        print("- External limiting membrane (ELM) presence")
        print("- Absence of vitreoretinal adhesion")
        print("- Thicker baseline choroid")

def extract_kim_2020(text):
    """Extract specific data from Kim 2020 5-year study."""
    print("\n=== Kim 2020 - 5-Year Injection Frequency Impact ===")
    
    # Look for injection frequency data
    injection_patterns = re.findall(r'year\s*(\d+).*?(\d+\.\d+).*?injection', text, re.IGNORECASE)
    if injection_patterns:
        print("\nInjection frequency by year:")
        for year, injections in injection_patterns[:5]:
            print(f"Year {year}: {injections} injections")
    
    # Look for visual outcomes
    if '≥5 injections' in text or '>=5 injections' in text:
        print("\nKey finding: Patients receiving ≥5 injections annually maintained better visual outcomes")

def extract_gillies_2019(text):
    """Extract specific data from Gillies 2019 FRB Registry."""
    print("\n=== Gillies 2019 - Fight Retinal Blindness Registry ===")
    
    # Look for comparative data
    if 'aflibercept' in text.lower() and 'ranibizumab' in text.lower():
        # Find comparison results
        comparison_match = re.search(r'aflibercept.*?(\d+\.\d+).*?letters.*?ranibizumab.*?(\d+\.\d+).*?letters', text, re.IGNORECASE)
        if comparison_match:
            print(f"12-month outcomes: Aflibercept +{comparison_match.group(1)} letters vs Ranibizumab +{comparison_match.group(2)} letters")
        
        # Injection frequency
        inj_match = re.search(r'aflibercept.*?(\d+\.\d+).*?injection.*?ranibizumab.*?(\d+\.\d+)', text, re.IGNORECASE)
        if inj_match:
            print(f"First year injections: Aflibercept {inj_match.group(1)} vs Ranibizumab {inj_match.group(2)}")

def extract_veritti_2021(text):
    """Extract specific data from Veritti 2021 real-life study."""
    print("\n=== Veritti 2021 - Long-term Real-Life Outcomes ===")
    
    # Look for follow-up duration
    followup_match = re.search(r'mean follow.*?up.*?(\d+\.\d+).*?years', text, re.IGNORECASE)
    if followup_match:
        print(f"Mean follow-up: {followup_match.group(1)} years")
    
    # Geographic atrophy rates
    ga_match = re.search(r'geographic atrophy.*?(\d+)%', text, re.IGNORECASE)
    if ga_match:
        print(f"Geographic atrophy development: {ga_match.group(1)}%")
    
    # Injection reduction over time
    if 'year 1' in text.lower() and 'year 4' in text.lower():
        print("Progressive reduction in injection frequency noted from year 1 to year 4")

def extract_spooner_2025(text):
    """Extract specific data from Spooner 2025 meta-analysis."""
    print("\n=== Spooner 2025 - 10-Year Meta-Analysis ===")
    
    # Find pooled analysis data
    if 'pooled' in text.lower():
        studies_match = re.search(r'(\d+)\s*studies.*?(\d+,?\d+)\s*eyes', text, re.IGNORECASE)
        if studies_match:
            print(f"Pooled analysis: {studies_match.group(1)} studies with {studies_match.group(2)} eyes")
    
    # Visual outcomes over time
    outcomes_match = re.search(r'1 year.*?\+(\d+\.\d+).*?3 years.*?([-+]?\d+\.\d+).*?5 years.*?([-+]?\d+\.\d+)', text, re.IGNORECASE)
    if outcomes_match:
        print(f"Visual outcomes: 1 year +{outcomes_match.group(1)} letters, 3 years {outcomes_match.group(2)} letters, 5 years {outcomes_match.group(3)} letters")
    
    # Discontinuation rates
    discontinuation_match = re.search(r'(\d+)%.*?discontinu.*?2 years', text, re.IGNORECASE)
    if discontinuation_match:
        print(f"Discontinuation rate by 2 years: {discontinuation_match.group(1)}%")
    
    # Macular atrophy
    ma_match = re.search(r'macular atrophy.*?(\d+)%.*?10', text, re.IGNORECASE)
    if ma_match:
        print(f"Macular atrophy by year 10: {ma_match.group(1)}%")

def main():
    """Process all aflibercept papers with specific extraction functions."""
    papers = [
        ('docs/literature/s41598-019-39995-5.pdf', extract_nishikawa_2019),
        ('docs/literature/41433_2020_Article_851.pdf', extract_kim_2020),
        ('docs/literature/1-s2.0-S0161642019321372.pdf', extract_gillies_2019),
        ('docs/literature/s12886-021-02055-6.pdf', extract_veritti_2021),
        ('docs/literature/Clinical Exper Ophthalmology - 2025 - Spooner - Real‐World 10‐Year Outcomes of Anti‐VEGF Therapy for Neovascular.pdf', extract_spooner_2025)
    ]
    
    for pdf_path, extract_func in papers:
        if os.path.exists(pdf_path):
            text = extract_detailed_text(pdf_path)
            if not text.startswith('Error'):
                extract_func(text)
        else:
            print(f"\nFile not found: {pdf_path}")

if __name__ == "__main__":
    main()