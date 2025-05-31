#!/usr/bin/env python3
"""Extract discontinuation criteria from clinical guidance PDFs."""

import PyPDF2
import re
import json
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page.extract_text()
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text

def find_discontinuation_criteria(text):
    """Search for discontinuation-related content in text."""
    criteria = {
        "vision_thresholds": [],
        "poor_response_criteria": [],
        "number_of_assessments": [],
        "other_stopping_criteria": [],
        "retreatment_criteria": []
    }
    
    # Split text into lines for context
    lines = text.split('\n')
    
    # Keywords to search for
    keywords = [
        r'discontinu',
        r'stop\s+treatment',
        r'cessation',
        r'treatment\s+failure',
        r'poor\s+response',
        r'non-response',
        r'futility',
        r'criteria',
        r'threshold',
        r'visual\s+acuity',
        r'VA\s+<',
        r'VA\s+less',
        r'letters',
        r'logMAR',
        r'retreatment',
        r'resume\s+treatment'
    ]
    
    # Search for each keyword and extract surrounding context
    for i, line in enumerate(lines):
        for keyword in keywords:
            if re.search(keyword, line, re.IGNORECASE):
                # Get context (2 lines before and after)
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context = '\n'.join(lines[start:end])
                
                # Categorize based on content
                if re.search(r'(VA|visual\s+acuity|letters|logMAR)', context, re.IGNORECASE):
                    if re.search(r'(\d+\s*letters|logMAR\s*[\d.]+|<\s*\d+)', context):
                        criteria["vision_thresholds"].append(context.strip())
                
                if re.search(r'(poor\s+response|non-response|failure)', context, re.IGNORECASE):
                    criteria["poor_response_criteria"].append(context.strip())
                
                if re.search(r'(\d+\s*(visits?|assessments?|injections?))', context, re.IGNORECASE):
                    criteria["number_of_assessments"].append(context.strip())
                
                if re.search(r'(discontinu|stop|cessation)', context, re.IGNORECASE):
                    criteria["other_stopping_criteria"].append(context.strip())
                
                if re.search(r'(retreatment|resume)', context, re.IGNORECASE):
                    criteria["retreatment_criteria"].append(context.strip())
    
    # Remove duplicates
    for key in criteria:
        criteria[key] = list(set(criteria[key]))
    
    return criteria

def main():
    """Main function to process PDFs and extract discontinuation criteria."""
    docs_dir = Path("/Users/rose/Code/CC/docs/literature")
    pdf_files = list(docs_dir.glob("*.pdf"))
    
    all_results = {}
    
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")
        print("=" * 60)
        
        # Extract text
        text = extract_text_from_pdf(pdf_file)
        
        # Find criteria
        criteria = find_discontinuation_criteria(text)
        
        # Print results
        print(f"\nFound in {pdf_file.name}:")
        for category, items in criteria.items():
            if items:
                print(f"\n{category.replace('_', ' ').title()}:")
                for item in items[:5]:  # Show first 5 of each category
                    print(f"  - {item[:200]}...")
        
        all_results[pdf_file.name] = criteria
    
    # Save results to JSON
    output_file = Path("/Users/rose/Code/CC/output/discontinuation_criteria_extracted.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()