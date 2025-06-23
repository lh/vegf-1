"""
Financial Parameters PDF Report Generator

Generates human-readable PDF reports of financial/resource parameters
for NHS cost modeling including staff roles, visit costs, and drug prices.
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


def generate_financial_parameters_pdf(resource_config: Optional[Dict[str, Any]] = None,
                                    resource_config_path: Optional[Path] = None) -> bytes:
    """
    Generate a PDF report for financial/resource parameters.
    
    Args:
        resource_config: Resource configuration dictionary (takes precedence)
        resource_config_path: Path to resource configuration file
        
    Returns:
        PDF file as bytes
    """
    # Use provided config or load from file
    if resource_config is None:
        # Default path if not provided
        if resource_config_path is None:
            resource_config_path = Path("protocols/resources/nhs_standard_resources.yaml")
        
        # Load resource configuration
        try:
            with open(resource_config_path) as f:
                config = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Could not load resource configuration: {e}")
    else:
        config = resource_config
    
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
    elements.append(Paragraph("Financial Parameters Report", title_style))
    elements.append(Paragraph("NHS Economic Analysis Configuration", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Metadata
    metadata = [
        ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ["Configuration:", "NHS Standard Resources"],
        ["Purpose:", "Economic analysis of anti-VEGF treatment protocols"],
    ]
    
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
    
    # Staff Roles and Capacities
    elements.append(Paragraph("Staff Roles and Capacities", heading_style))
    elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 0.2*inch))
    
    if 'resources' in config and 'roles' in config['resources']:
        roles_data = []
        roles_data.append(["Role", "Capacity/Session", "Description"])
        
        for role_name, role_info in config['resources']['roles'].items():
            roles_data.append([
                role_name.replace('_', ' ').title(),
                str(role_info.get('capacity_per_session', 'N/A')),
                role_info.get('description', '')
            ])
        
        roles_table = Table(roles_data, colWidths=[1.8*inch, 1.3*inch, 3.4*inch])
        roles_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(roles_table)
    
    # Visit Types and Resource Requirements
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Visit Types and Resource Requirements", heading_style))
    elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 0.2*inch))
    
    if 'resources' in config and 'visit_requirements' in config['resources']:
        for visit_type, visit_info in config['resources']['visit_requirements'].items():
            elements.append(Paragraph(f"<b>{visit_type.replace('_', ' ').title()}</b>", subheading_style))
            
            if 'description' in visit_info:
                elements.append(Paragraph(visit_info['description'], normal_style))
            
            visit_data = []
            visit_data.append(["Duration:", f"{visit_info.get('duration_minutes', 'N/A')} minutes"])
            
            if 'roles_needed' in visit_info:
                visit_data.append(["", ""])  # Spacer
                visit_data.append(["Resources Required:", ""])
                for role, count in visit_info['roles_needed'].items():
                    visit_data.append([f"  {role.replace('_', ' ').title()}:", f"{count} staff"])
            
            visit_table = Table(visit_data, colWidths=[2*inch, 2*inch])
            visit_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('LEFTPADDING', (0, 2), (0, -1), 24),
            ]))
            elements.append(visit_table)
            elements.append(Spacer(1, 0.3*inch))
    
    # Cost Structure
    elements.append(PageBreak())
    elements.append(Paragraph("Cost Structure", heading_style))
    elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 0.2*inch))
    
    # Procedure Costs
    if 'costs' in config and 'procedures' in config['costs']:
        elements.append(Paragraph("Procedure Costs", subheading_style))
        
        proc_data = []
        proc_data.append(["Procedure", "HRG Code", "Unit Cost", "Description"])
        
        for proc_name, proc_info in config['costs']['procedures'].items():
            hrg_code = proc_info.get('hrg_code', '')
            # Truncate "Diagnostic imaging" to just "Imaging" for space
            if hrg_code == "Diagnostic imaging":
                hrg_code = "Imaging"
            
            proc_data.append([
                proc_name.replace('_', ' ').title(),
                hrg_code,
                f"£{proc_info.get('unit_cost', 0)}",
                proc_info.get('description', '')
            ])
        
        proc_table = Table(proc_data, colWidths=[1.5*inch, 0.8*inch, 0.7*inch, 3.5*inch])
        proc_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(proc_table)
    
    # Drug Costs
    if 'costs' in config and 'drugs' in config['costs']:
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("Drug Costs", subheading_style))
        
        drug_data = []
        drug_data.append(["Drug", "Unit Cost", "Generic/Biosimilar"])
        
        for drug_id, drug_info in config['costs']['drugs'].items():
            drug_data.append([
                drug_info.get('name', drug_id),
                f"£{drug_info.get('unit_cost', 0)}",
                f"£{drug_info.get('expected_generic_cost', 'TBD')}" if 'expected_generic_cost' in drug_info else "N/A"
            ])
        
        drug_table = Table(drug_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        drug_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ]))
        elements.append(drug_table)
    
    # Session Parameters
    if 'resources' in config and 'session_parameters' in config['resources']:
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("Session Parameters", subheading_style))
        
        session_params = config['resources']['session_parameters']
        session_data = []
        
        if 'session_duration_hours' in session_params:
            session_data.append(["Session Duration:", f"{session_params['session_duration_hours']} hours"])
        if 'sessions_per_day' in session_params:
            session_data.append(["Sessions per Day:", str(session_params['sessions_per_day'])])
        if 'working_days' in session_params:
            session_data.append(["Working Days:", ", ".join(session_params['working_days'])])
            
        if session_data:
            session_table = Table(session_data, colWidths=[2*inch, 3*inch])
            session_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            elements.append(session_table)
    
    # Capacity Constraints
    if 'capacity_constraints' in config:
        elements.append(PageBreak())
        elements.append(Paragraph("Capacity Constraints", heading_style))
        elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
        elements.append(Spacer(1, 0.2*inch))
        
        if 'max_per_session' in config['capacity_constraints']:
            cap_data = []
            cap_data.append(["Visit Type", "Max per Session"])
            
            for visit_type, max_count in config['capacity_constraints']['max_per_session'].items():
                cap_data.append([
                    visit_type.replace('_', ' ').title(),
                    str(max_count)
                ])
            
            cap_table = Table(cap_data, colWidths=[3*inch, 2*inch])
            cap_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ]))
            elements.append(cap_table)
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes