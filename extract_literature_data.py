#!/usr/bin/env python3
"""
Extract clinical parameters from literature PDFs for aflibercept 2mg
Focus on disease transitions, vision outcomes, and treatment effects
"""

import PyPDF2
import re
import json
from pathlib import Path

def extract_text_from_pdf(pdf_path, max_pages=None):
    """Extract text from PDF with page tracking"""
    text = ""
    page_texts = {}
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            pages_to_read = min(total_pages, max_pages) if max_pages else total_pages
            
            print(f"Processing {pdf_path.name} ({pages_to_read} of {total_pages} pages)")
            
            for page_num in range(pages_to_read):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text + "\n\n"
                page_texts[page_num + 1] = page_text
                
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    
    return text, page_texts

def extract_vision_outcomes(text):
    """Extract vision change data from text"""
    vision_data = {
        'mean_gains': [],
        'mean_losses': [],
        'standard_deviations': [],
        'confidence_intervals': []
    }
    
    # Patterns for vision outcomes
    patterns = {
        'mean_gain': [
            r'mean\s+(?:gain|improvement).*?(\+?\d+\.?\d*)\s*(?:letters|ETDRS)',
            r'gained?\s+(?:a\s+)?mean\s+(?:of\s+)?(\+?\d+\.?\d*)\s*(?:letters|ETDRS)',
            r'(?:BCVA|VA)\s+(?:gain|improvement).*?(\+?\d+\.?\d*)\s*(?:letters|ETDRS)',
        ],
        'mean_loss': [
            r'mean\s+(?:loss|decline).*?(-?\d+\.?\d*)\s*(?:letters|ETDRS)',
            r'lost\s+(?:a\s+)?mean\s+(?:of\s+)?(-?\d+\.?\d*)\s*(?:letters|ETDRS)',
        ],
        'std_dev': [
            r'(?:SD|standard\s+deviation).*?(\d+\.?\d*)',
            r'±\s*(\d+\.?\d*)\s*(?:letters|ETDRS)',
        ],
        'confidence_interval': [
            r'(?:95%\s*)?CI[:\s]+(-?\d+\.?\d*)\s*(?:to|,|-)\s*(-?\d+\.?\d*)',
            r'\((-?\d+\.?\d*)\s*(?:to|,|-)\s*(-?\d+\.?\d*)\)',
        ]
    }
    
    # Search for patterns
    for pattern_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if pattern_type == 'mean_gain':
                    vision_data['mean_gains'].append(float(match))
                elif pattern_type == 'mean_loss':
                    vision_data['mean_losses'].append(float(match))
                elif pattern_type == 'std_dev':
                    vision_data['standard_deviations'].append(float(match))
                elif pattern_type == 'confidence_interval' and isinstance(match, tuple):
                    vision_data['confidence_intervals'].append((float(match[0]), float(match[1])))
    
    return vision_data

def extract_transition_data(text):
    """Extract disease state transition information"""
    transition_data = {
        'stable_rates': [],
        'progression_rates': [],
        'improvement_rates': [],
        'recurrence_rates': []
    }
    
    # Patterns for transitions
    patterns = {
        'stable': [
            r'(\d+\.?\d*)%?\s*(?:remained?|were|stayed?)\s*stable',
            r'stable\s+(?:disease|AMD|patients?).*?(\d+\.?\d*)%',
        ],
        'progression': [
            r'progress(?:ed|ion).*?(\d+\.?\d*)%',
            r'(\d+\.?\d*)%?\s*(?:progressed?|developed?)\s*(?:to\s+)?(?:active|worse)',
        ],
        'improvement': [
            r'improv(?:ed|ement).*?(\d+\.?\d*)%',
            r'(\d+\.?\d*)%?\s*(?:improved?|better)',
        ],
        'recurrence': [
            r'recurr(?:ed|ence).*?(\d+\.?\d*)%',
            r'(\d+\.?\d*)%?\s*(?:recurred?|reactivated?)',
        ]
    }
    
    for pattern_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                value = float(match)
                if value <= 100:  # Ensure it's a percentage
                    transition_data[f'{pattern_type}_rates'].append(value)
    
    return transition_data

def extract_treatment_intervals(text):
    """Extract treatment interval data"""
    interval_data = {
        'loading_doses': [],
        'maintenance_intervals': [],
        'extension_criteria': [],
        'maximum_intervals': []
    }
    
    # Loading phase patterns
    loading_patterns = [
        r'(?:initial|loading).*?(\d+)\s*(?:monthly\s*)?(?:injections?|doses?)',
        r'(\d+)\s*(?:consecutive\s*)?monthly\s*(?:injections?|doses?)',
    ]
    
    # Interval patterns
    interval_patterns = [
        r'(?:interval|between).*?(\d+)\s*(?:to|-)\s*(\d+)\s*weeks?',
        r'(?:every|q)(\d+)\s*weeks?',
        r'extended?\s+(?:to|by)\s*(\d+)\s*weeks?',
    ]
    
    for pattern in loading_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            interval_data['loading_doses'].append(int(match))
    
    for pattern in interval_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                interval_data['maintenance_intervals'].append((int(match[0]), int(match[1])))
            else:
                interval_data['maintenance_intervals'].append(int(match))
    
    return interval_data

def extract_discontinuation_criteria(text):
    """Extract discontinuation criteria and rates"""
    discontinuation_data = {
        'vision_thresholds': [],
        'no_improvement_periods': [],
        'discontinuation_rates': []
    }
    
    # Vision threshold patterns
    threshold_patterns = [
        r'discontinu.*?(?:if|when).*?(?:VA|vision|BCVA).*?(?:<|less\s+than)\s*(\d+)\s*letters',
        r'stop.*?treatment.*?(?:VA|vision|BCVA).*?(?:<|less\s+than)\s*(\d+)\s*letters',
    ]
    
    # Time period patterns
    period_patterns = [
        r'(?:no|without)\s+improvement.*?(\d+)\s*months?',
        r'after\s*(\d+)\s*months?.*?(?:no|without)\s+(?:improvement|response)',
    ]
    
    # Rate patterns
    rate_patterns = [
        r'discontinu.*?(\d+\.?\d*)%',
        r'(\d+\.?\d*)%.*?discontinu',
    ]
    
    for pattern in threshold_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            discontinuation_data['vision_thresholds'].append(int(match))
    
    for pattern in period_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            discontinuation_data['no_improvement_periods'].append(int(match))
    
    for pattern in rate_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            value = float(match)
            if value <= 100:
                discontinuation_data['discontinuation_rates'].append(value)
    
    return discontinuation_data

def main():
    """Extract data from all literature PDFs"""
    
    literature_dir = Path("docs/literature")
    results = {}
    
    pdf_files = list(literature_dir.glob("*.pdf"))
    
    for pdf_file in pdf_files:
        print(f"\n{'='*60}")
        print(f"Analyzing: {pdf_file.name}")
        print(f"{'='*60}")
        
        # Extract text (first 50 pages to save time)
        text, page_texts = extract_text_from_pdf(pdf_file, max_pages=50)
        
        # Extract different types of data
        vision_outcomes = extract_vision_outcomes(text)
        transition_data = extract_transition_data(text)
        interval_data = extract_treatment_intervals(text)
        discontinuation_data = extract_discontinuation_criteria(text)
        
        # Store results
        results[pdf_file.name] = {
            'vision_outcomes': vision_outcomes,
            'transition_data': transition_data,
            'interval_data': interval_data,
            'discontinuation_data': discontinuation_data
        }
        
        # Print summary
        print("\nVision Outcomes Found:")
        if vision_outcomes['mean_gains']:
            print(f"  Mean gains: {vision_outcomes['mean_gains']}")
        if vision_outcomes['mean_losses']:
            print(f"  Mean losses: {vision_outcomes['mean_losses']}")
        if vision_outcomes['standard_deviations']:
            print(f"  Standard deviations: {vision_outcomes['standard_deviations']}")
            
        print("\nTransition Data Found:")
        if transition_data['stable_rates']:
            print(f"  Stable rates: {transition_data['stable_rates']}%")
        if transition_data['progression_rates']:
            print(f"  Progression rates: {transition_data['progression_rates']}%")
            
        print("\nInterval Data Found:")
        if interval_data['loading_doses']:
            print(f"  Loading doses: {interval_data['loading_doses']}")
        if interval_data['maintenance_intervals']:
            print(f"  Maintenance intervals: {interval_data['maintenance_intervals']}")
            
        print("\nDiscontinuation Data Found:")
        if discontinuation_data['vision_thresholds']:
            print(f"  Vision thresholds: {discontinuation_data['vision_thresholds']} letters")
        if discontinuation_data['discontinuation_rates']:
            print(f"  Discontinuation rates: {discontinuation_data['discontinuation_rates']}%")
    
    # Save results
    output_file = Path('literature_extraction_results.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")
    
    # Create summary for protocol parameters
    create_parameter_summary(results)

def create_parameter_summary(results):
    """Create a summary of extracted parameters for protocol use"""
    
    summary = {
        'vision_outcomes': {
            'mean_gain_range': [],
            'mean_loss_range': [],
            'typical_std_dev': []
        },
        'transition_probabilities': {
            'stable_rate_range': [],
            'progression_rate_range': [],
            'improvement_rate_range': []
        },
        'treatment_protocol': {
            'loading_doses_consensus': [],
            'maintenance_interval_range': []
        },
        'discontinuation': {
            'vision_threshold_consensus': [],
            'typical_rates': []
        }
    }
    
    # Aggregate data across all documents
    for doc_name, doc_data in results.items():
        # Vision outcomes
        summary['vision_outcomes']['mean_gain_range'].extend(doc_data['vision_outcomes']['mean_gains'])
        summary['vision_outcomes']['mean_loss_range'].extend(doc_data['vision_outcomes']['mean_losses'])
        summary['vision_outcomes']['typical_std_dev'].extend(doc_data['vision_outcomes']['standard_deviations'])
        
        # Transitions
        summary['transition_probabilities']['stable_rate_range'].extend(doc_data['transition_data']['stable_rates'])
        summary['transition_probabilities']['progression_rate_range'].extend(doc_data['transition_data']['progression_rates'])
        
        # Intervals
        summary['treatment_protocol']['loading_doses_consensus'].extend(doc_data['interval_data']['loading_doses'])
        
        # Discontinuation
        summary['discontinuation']['vision_threshold_consensus'].extend(doc_data['discontinuation_data']['vision_thresholds'])
        summary['discontinuation']['typical_rates'].extend(doc_data['discontinuation_data']['discontinuation_rates'])
    
    # Calculate ranges and consensus
    for category in summary:
        for metric in summary[category]:
            if summary[category][metric]:
                values = summary[category][metric]
                if values:
                    summary[category][metric] = {
                        'min': min(values),
                        'max': max(values),
                        'mean': sum(values) / len(values),
                        'values': sorted(list(set(values)))  # Unique values
                    }
    
    # Save summary
    summary_file = Path('literature_parameter_summary.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nParameter summary saved to: {summary_file}")

if __name__ == "__main__":
    main()