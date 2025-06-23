"""
Protocol PDF Report Generator

Generates human-readable PDF reports of protocol specifications including
all parameters, transitions, and configuration details.
"""

from pathlib import Path
from datetime import datetime
import yaml
from typing import Dict, Any, List, Tuple, Optional
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import KeepTogether, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class HRFlowable(Flowable):
    """A horizontal line flowable."""
    def __init__(self, width, thickness=1, color=colors.black):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color
        self.height = thickness
        
    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)
        
    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)


def load_parameter_file(spec, file_attr: str, base_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Safely load a parameter file referenced in the spec."""
    if not hasattr(spec, file_attr):
        return None
        
    file_path = getattr(spec, file_attr)
    if not file_path:
        return None
        
    # Determine base path
    if base_path is None:
        if hasattr(spec, 'source_file') and spec.source_file:
            base_path = Path(spec.source_file).parent
        else:
            base_path = Path.cwd()
    
    # Resolve the full path
    param_file = base_path / file_path
    
    # Check if file exists
    if not param_file.exists():
        return None
        
    try:
        with open(param_file) as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def generate_protocol_pdf(spec, is_time_based: bool) -> bytes:
    """
    Generate a PDF report for a protocol specification.
    
    Args:
        spec: Protocol specification object
        is_time_based: Whether this is a time-based protocol
        
    Returns:
        PDF file as bytes
    """
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#374151'),
        spaceAfter=12,
        spaceBefore=24
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=6,
        spaceBefore=12
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 14
    
    # Title page
    elements.append(Paragraph(f"Protocol Report", title_style))
    elements.append(Paragraph(f"{spec.name}", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Metadata
    metadata = [
        ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ["Protocol Type:", "Time-Based" if is_time_based else "Visit-Based"],
        ["Version:", spec.version],
        ["Author:", getattr(spec, 'author', 'Not specified')],
        ["Created:", getattr(spec, 'created_date', 'Not specified')],
    ]
    
    if hasattr(spec, 'description') and spec.description:
        # Handle multi-line description
        desc_para = Paragraph(spec.description, normal_style)
        metadata.append(["Description:", desc_para])
    
    if hasattr(spec, 'protocol_type'):
        metadata.append(["Treatment Type:", spec.protocol_type.replace('_', ' ').title()])
    
    meta_table = Table(metadata, colWidths=[2*inch, 4*inch])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('RIGHTPADDING', (0, 0), (0, -1), 12),
    ]))
    elements.append(meta_table)
    elements.append(PageBreak())
    
    # Treatment Protocol Overview
    elements.append(Paragraph("Treatment Protocol Overview", heading_style))
    elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 0.2*inch))
    
    if is_time_based:
        # Time-based protocol details
        timing_data = []
        
        # Loading phase
        if hasattr(spec, 'loading_dose_injections'):
            timing_data.append(["Loading Phase:", f"{spec.loading_dose_injections} injections"])
        if hasattr(spec, 'loading_dose_interval_days'):
            timing_data.append(["Loading Interval:", f"{spec.loading_dose_interval_days} days ({spec.loading_dose_interval_days/7:.1f} weeks)"])
            
        # Regular treatment intervals
        if hasattr(spec, 'min_interval_days'):
            timing_data.append(["Minimum Interval:", f"{spec.min_interval_days} days ({spec.min_interval_days/7:.1f} weeks)"])
        if hasattr(spec, 'max_interval_days'):
            timing_data.append(["Maximum Interval:", f"{spec.max_interval_days} days ({spec.max_interval_days/7:.1f} weeks)"])
            
        # Extension/shortening rules
        if hasattr(spec, 'extension_days'):
            timing_data.append(["Extension Step:", f"{spec.extension_days} days ({spec.extension_days/7:.1f} weeks)"])
        if hasattr(spec, 'shortening_days'):
            timing_data.append(["Shortening Step:", f"{spec.shortening_days} days ({spec.shortening_days/7:.1f} weeks)"])
            
        # Model update frequency
        if hasattr(spec, 'update_interval_days'):
            timing_data.append(["Disease Update:", f"Every {spec.update_interval_days} days"])
        if hasattr(spec, 'transition_model'):
            timing_data.append(["Transition Model:", spec.transition_model.title()])
        
        if timing_data:
            timing_table = Table(timing_data, colWidths=[2.5*inch, 3.5*inch])
            timing_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(timing_table)
    else:
        # Visit-based protocol details
        elements.append(Paragraph("Visit-based protocol parameters", normal_style))
    
    elements.append(Spacer(1, 0.5*inch))
    
    # Population Settings
    elements.append(Paragraph("Population Settings", heading_style))
    elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 0.2*inch))
    
    # Handle both dict and object forms of baseline_vision_distribution
    if hasattr(spec, 'baseline_vision_distribution'):
        dist = spec.baseline_vision_distribution
        
        # If it's a dict (time-based protocols)
        if isinstance(dist, dict):
            dist_type = dist.get('type', 'unknown')
            elements.append(Paragraph(f"<b>Distribution Type:</b> {dist_type.replace('_', ' ').title()}", normal_style))
            
            dist_params = []
            
            # Common parameters
            if 'mean' in dist:
                dist_params.append(["Mean:", f"{dist['mean']:.1f} letters"])
            elif hasattr(spec, 'baseline_vision_mean'):
                dist_params.append(["Mean:", f"{spec.baseline_vision_mean:.1f} letters"])
                
            if 'std' in dist:
                dist_params.append(["Standard Deviation:", f"{dist['std']:.1f} letters"])
            elif hasattr(spec, 'baseline_vision_std'):
                dist_params.append(["Standard Deviation:", f"{spec.baseline_vision_std:.1f} letters"])
                
            # Distribution-specific parameters
            if 'alpha' in dist:
                dist_params.append(["Alpha:", f"{dist['alpha']:.2f}"])
            if 'beta' in dist:
                dist_params.append(["Beta:", f"{dist['beta']:.2f}"])
                
            # Range parameters
            if 'min' in dist:
                dist_params.append(["Minimum:", f"{dist['min']} letters"])
            elif hasattr(spec, 'baseline_vision_min'):
                dist_params.append(["Minimum:", f"{spec.baseline_vision_min} letters"])
                
            if 'max' in dist:
                dist_params.append(["Maximum:", f"{dist['max']} letters"])
            elif hasattr(spec, 'baseline_vision_max'):
                dist_params.append(["Maximum:", f"{spec.baseline_vision_max} letters"])
                
            if 'threshold' in dist:
                dist_params.append(["Threshold:", f"{dist['threshold']} letters"])
                
        else:
            # Object form (older protocols)
            if hasattr(dist, 'name'):
                elements.append(Paragraph(f"<b>Distribution Type:</b> {dist.name}", normal_style))
            
            dist_params = []
            if hasattr(dist, 'mean') and hasattr(dist, 'std'):
                dist_params.append(["Mean:", f"{dist.mean:.1f} letters"])
                dist_params.append(["Standard Deviation:", f"{dist.std:.1f} letters"])
            elif hasattr(dist, 'alpha') and hasattr(dist, 'beta'):
                dist_params.append(["Alpha:", f"{dist.alpha:.2f}"])
                dist_params.append(["Beta:", f"{dist.beta:.2f}"])
            
            if hasattr(dist, 'min_value'):
                dist_params.append(["Minimum:", f"{dist.min_value} letters"])
            if hasattr(dist, 'max_value'):
                dist_params.append(["Maximum:", f"{dist.max_value} letters"])
            if hasattr(dist, 'threshold'):
                dist_params.append(["Threshold:", f"{dist.threshold} letters"])
            
        if dist_params:
            dist_table = Table(dist_params, colWidths=[2*inch, 3*inch])
            dist_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('LEFTPADDING', (0, 0), (-1, -1), 24),
            ]))
            elements.append(dist_table)
    
    # Parameter Files (for time-based protocols)
    if is_time_based and hasattr(spec, 'disease_transitions_file'):
        elements.append(PageBreak())
        elements.append(Paragraph("Model Parameters", heading_style))
        elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
        elements.append(Spacer(1, 0.2*inch))
        
        param_files = []
        if hasattr(spec, 'disease_transitions_file'):
            param_files.append(["Disease Transitions:", spec.disease_transitions_file])
        if hasattr(spec, 'treatment_effect_file'):
            param_files.append(["Treatment Effects:", spec.treatment_effect_file])
        if hasattr(spec, 'vision_parameters_file'):
            param_files.append(["Vision Model:", spec.vision_parameters_file])
        if hasattr(spec, 'discontinuation_parameters_file'):
            param_files.append(["Discontinuation Rules:", spec.discontinuation_parameters_file])
            
        if param_files:
            param_table = Table(param_files, colWidths=[2*inch, 4*inch])
            param_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(param_table)
            
        # Try to load and display disease transitions
        disease_data = load_parameter_file(spec, 'disease_transitions_file')
        if disease_data and 'fortnightly_transitions' in disease_data:
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph("Disease State Transitions (Fortnightly)", subheading_style))
            
            transitions = disease_data['fortnightly_transitions']
            states = ['NAIVE', 'STABLE', 'ACTIVE', 'HIGHLY_ACTIVE']
            
            # Create transition matrix table
            table_data = [['From \\ To'] + states]
            
            for from_state in states:
                row = [from_state]
                for to_state in states:
                    prob = transitions.get(from_state, {}).get(to_state, 0.0)
                    row.append(f"{prob:.3f}")
                table_data.append(row)
            
            trans_table = Table(table_data, colWidths=[1.3*inch] + [1.3*inch]*4)
            trans_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#e5e7eb')),
            ]))
            elements.append(trans_table)
    
    # Discontinuation Rules
    if hasattr(spec, 'discontinuation_rules'):
        elements.append(PageBreak())
        elements.append(Paragraph("Discontinuation Rules", heading_style))
        elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
        elements.append(Spacer(1, 0.2*inch))
        
        rules = spec.discontinuation_rules
        if hasattr(rules, 'poor_response_criteria'):
            elements.append(Paragraph("<b>Poor Response Criteria:</b>", subheading_style))
            criteria = rules.poor_response_criteria
            criteria_data = []
            if hasattr(criteria, 'months_to_check'):
                criteria_data.append(["Check at:", f"{criteria.months_to_check} months"])
            if hasattr(criteria, 'va_loss_threshold'):
                criteria_data.append(["VA Loss Threshold:", f"{criteria.va_loss_threshold} letters"])
                
            if criteria_data:
                criteria_table = Table(criteria_data, colWidths=[2*inch, 3*inch])
                criteria_table.setStyle(TableStyle([
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('LEFTPADDING', (0, 0), (-1, -1), 24),
                ]))
                elements.append(criteria_table)
    
    # Weekend Working Settings
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("Weekend Working Policy", subheading_style))
    
    weekend_data = []
    if hasattr(spec, 'allow_saturday_visits'):
        weekend_data.append(["Saturday Visits:", "Allowed" if spec.allow_saturday_visits else "Not Allowed"])
    if hasattr(spec, 'allow_sunday_visits'):
        weekend_data.append(["Sunday Visits:", "Allowed" if spec.allow_sunday_visits else "Not Allowed"])
    if hasattr(spec, 'prefer_weekday_for_first_visit'):
        weekend_data.append(["First Visit Preference:", "Weekday Preferred" if spec.prefer_weekday_for_first_visit else "Any Day"])
        
    if weekend_data:
        weekend_table = Table(weekend_data, colWidths=[2.5*inch, 3*inch])
        weekend_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 24),
        ]))
        elements.append(weekend_table)
    else:
        elements.append(Paragraph("Weekday visits only (standard policy)", normal_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes