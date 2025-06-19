#!/usr/bin/env python3
"""Extract key data from aflibercept papers for literature review and simulation parameters."""

import PyPDF2
import re
import os

def extract_pdf_text(pdf_path, max_pages=None):
    """Extract text from PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            pages_to_read = min(len(reader.pages), max_pages) if max_pages else len(reader.pages)
            for i in range(pages_to_read):
                text += reader.pages[i].extract_text()
            return text
    except Exception as e:
        return f'Error reading {pdf_path}: {e}'

def extract_key_data(text, paper_name):
    """Extract key data points from paper text."""
    results = {
        'paper': paper_name,
        'sample_size': [],
        'follow_up_duration': [],
        'injection_numbers': [],
        'visual_acuity': [],
        'discontinuation': [],
        'atrophy_rates': [],
        'key_findings': []
    }
    
    # Sample size patterns
    sample_patterns = [
        r'(\d+)\s*(?:patients|eyes|participants)',
        r'n\s*=\s*(\d+)',
        r'enrolled\s+(\d+)',
        r'included\s+(\d+)'
    ]
    
    # Follow-up duration patterns
    duration_patterns = [
        r'(\d+)[\s-]*year',
        r'(\d+)[\s-]*month',
        r'follow[\s-]*up.*?(\d+).*?(?:year|month)'
    ]
    
    # Injection number patterns
    injection_patterns = [
        r'(\d+\.?\d*)\s*(?:±\s*\d+\.?\d*)?\s*injection[s]?.*?(?:year|month)',
        r'mean.*?(\d+\.?\d*)\s*injection',
        r'received\s*(\d+\.?\d*)\s*(?:±\s*\d+\.?\d*)?\s*injection'
    ]
    
    # Visual acuity patterns
    va_patterns = [
        r'(?:logMAR|BCVA|visual acuity).*?(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*(?:±\s*\d+\.?\d*)?\s*letters',
        r'gain.*?(\d+\.?\d*)\s*letters'
    ]
    
    # Extract data using patterns
    for pattern_list, key in [(sample_patterns, 'sample_size'), 
                               (duration_patterns, 'follow_up_duration'),
                               (injection_patterns, 'injection_numbers'),
                               (va_patterns, 'visual_acuity')]:
        for pattern in pattern_list:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                results[key].extend(matches[:5])  # Limit to first 5 matches
    
    return results

def main():
    """Process all aflibercept papers."""
    papers = [
        ('docs/literature/s41598-019-39995-5.pdf', 'Nishikawa 2019 - 4-year aflibercept'),
        ('docs/literature/41433_2020_Article_851.pdf', 'Kim 2020 - 5-year injection frequency'),
        ('docs/literature/1-s2.0-S0161642019321372.pdf', 'Gillies 2019 - FRB Registry'),
        ('docs/literature/s12886-021-02055-6.pdf', 'Veritti 2021 - Long-term real-life'),
        ('docs/literature/Clinical Exper Ophthalmology - 2025 - Spooner - Real‐World 10‐Year Outcomes of Anti‐VEGF Therapy for Neovascular.pdf', 'Spooner 2025 - 10-year meta-analysis')
    ]
    
    all_results = []
    
    for pdf_path, paper_name in papers:
        if os.path.exists(pdf_path):
            print(f"\nProcessing: {paper_name}")
            print("="*60)
            
            # Extract text
            text = extract_pdf_text(pdf_path, max_pages=20)
            
            if text.startswith('Error'):
                print(text)
                continue
            
            # Extract key data
            data = extract_key_data(text, paper_name)
            all_results.append(data)
            
            # Print summary
            print(f"Sample sizes found: {data['sample_size'][:3]}")
            print(f"Follow-up durations: {data['follow_up_duration'][:3]}")
            print(f"Injection numbers: {data['injection_numbers'][:3]}")
            print(f"Visual acuity data: {data['visual_acuity'][:3]}")
            
            # Extract specific passages for key findings
            if 'year' in text.lower():
                year_sentences = [s.strip() for s in text.split('.') if 'year' in s.lower() and 'injection' in s.lower()][:3]
                if year_sentences:
                    print("\nKey injection frequency findings:")
                    for s in year_sentences:
                        if len(s) < 200:  # Reasonable sentence length
                            print(f"- {s}")
        else:
            print(f"\nFile not found: {pdf_path}")
    
    return all_results

if __name__ == "__main__":
    results = main()