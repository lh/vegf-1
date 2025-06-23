"""
Workload Results PDF Report Generator

Generates PDF reports of actual workload and cost results from simulations
including daily patterns, resource utilization, bottlenecks, and cost breakdowns.
"""

from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any, List, Optional
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


def generate_workload_results_pdf(
    simulation_info: Dict[str, Any],
    workload_summary: Dict[str, Any],
    total_costs: Dict[str, Any],
    utilization_data: List[Dict[str, Any]],
    staffing_data: List[Dict[str, Any]],
    bottlenecks: List[Dict[str, Any]] = None,
    patient_outcomes: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Generate a PDF report for workload and cost results.
    
    Args:
        simulation_info: Basic simulation parameters
        workload_summary: Summary statistics from ResourceTracker
        total_costs: Cost breakdown by category
        utilization_data: Resource utilization statistics
        staffing_data: Staffing requirements analysis
        bottlenecks: List of capacity bottlenecks (optional)
        
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
    elements.append(Paragraph("Workload & Economic Analysis Results", title_style))
    elements.append(Paragraph(f"{simulation_info['protocol']} Protocol", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Simulation metadata
    metadata = [
        ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ["Protocol:", simulation_info['protocol']],
        ["Total Patients:", f"{simulation_info['n_patients']:,}"],
        ["Duration:", f"{simulation_info['duration_years']} years"],
        ["Engine:", simulation_info.get('engine', 'ABS').upper()],
        ["Seed:", str(simulation_info.get('seed', 'Random'))],
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
    
    # Executive Summary
    elements.append(Paragraph("Executive Summary", heading_style))
    elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 0.2*inch))
    
    # Key metrics
    summary_data = [
        ["Metric", "Value"],
        ["Total Visits", f"{workload_summary['total_visits']:,}"],
        ["Total Cost", f"£{total_costs['total']:,.0f}"],
        ["Cost per Patient", f"£{total_costs['total'] / simulation_info['n_patients']:,.0f}"],
        ["Cost per Visit", f"£{total_costs['total'] / workload_summary['total_visits']:.0f}" if workload_summary['total_visits'] > 0 else "N/A"],
    ]
    
    # Add patient outcome metrics if available
    if patient_outcomes:
        if 'active_patients' in patient_outcomes and patient_outcomes['active_patients'] > 0:
            summary_data.append(["Cost per Active Patient", f"£{total_costs['total'] / patient_outcomes['active_patients']:,.0f}"])
        if 'vision_maintained' in patient_outcomes and patient_outcomes['vision_maintained'] > 0:
            summary_data.append(["Cost per Vision Maintained", f"£{total_costs['total'] / patient_outcomes['vision_maintained']:,.0f}"])
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
    ]))
    elements.append(summary_table)
    
    # Cost Breakdown
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Cost Breakdown", heading_style))
    elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 0.2*inch))
    
    cost_data = [["Category", "Cost", "Percentage"]]
    total_cost = total_costs['total']
    
    # Add cost categories
    cost_categories = [
        ('Drug Costs', 'drug'),
        ('Injection Procedures', 'injection_procedure'),
        ('Consultations', 'consultation'),
        ('OCT Scans', 'oct_scan')
    ]
    
    for label, key in cost_categories:
        if key in total_costs and total_costs[key] > 0:
            cost = total_costs[key]
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0
            cost_data.append([label, f"£{cost:,.0f}", f"{percentage:.1f}%"])
    
    cost_table = Table(cost_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
    cost_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(cost_table)
    
    # Resource Utilization
    elements.append(PageBreak())
    elements.append(Paragraph("Resource Utilization", heading_style))
    elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 0.2*inch))
    
    if utilization_data:
        util_table_data = [["Role", "Avg Daily", "Peak Daily", "Utilization %", "Total Sessions"]]
        
        for util in utilization_data:
            util_table_data.append([
                util['Role'],
                util['Average Daily Demand'],
                str(util['Peak Daily Demand']),
                util['Utilization %'],
                str(util['Total Sessions'])
            ])
        
        util_table = Table(util_table_data, colWidths=[1.8*inch, 1*inch, 1*inch, 1.2*inch, 1.2*inch])
        util_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ]))
        elements.append(util_table)
    
    # Staffing Requirements
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Staffing Requirements", heading_style))
    elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 0.2*inch))
    
    if staffing_data:
        staff_table_data = [["Role", "Avg Sessions/Day", "Peak Sessions", "Staff (Avg)", "Staff (Peak)"]]
        
        for staff in staffing_data:
            staff_table_data.append([
                staff['Role'],
                staff['Average Sessions/Day'],
                staff['Peak Sessions'],
                staff['Staff Needed (Average)'],
                str(staff['Staff Needed (Peak)'])
            ])
        
        staff_table = Table(staff_table_data, colWidths=[1.8*inch, 1.3*inch, 1.2*inch, 1*inch, 1*inch])
        staff_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ]))
        elements.append(staff_table)
    
    # Bottleneck Analysis
    if bottlenecks and len(bottlenecks) > 0:
        elements.append(PageBreak())
        elements.append(Paragraph("Bottleneck Analysis", heading_style))
        elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph(f"Found {len(bottlenecks)} days where capacity was exceeded", normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Group by role
        from collections import defaultdict
        role_bottlenecks = defaultdict(list)
        for b in bottlenecks:
            role_bottlenecks[b['role']].append(b)
        
        for role, incidents in role_bottlenecks.items():
            elements.append(Paragraph(f"<b>{role} ({len(incidents)} days)</b>", subheading_style))
            
            # Show top 5 worst cases
            worst_cases = sorted(incidents, key=lambda x: x['overflow'], reverse=True)[:5]
            
            bottleneck_data = [["Date", "Needed", "Available", "Overflow"]]
            for case in worst_cases:
                bottleneck_data.append([
                    case['date'],
                    f"{case['sessions_needed']:.1f}",
                    str(case['sessions_available']),
                    f"{case['overflow']:.1f}"
                ])
            
            bottleneck_table = Table(bottleneck_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
            bottleneck_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ]))
            elements.append(bottleneck_table)
            elements.append(Spacer(1, 0.3*inch))
    
    # Patient Outcomes (if available)
    if patient_outcomes:
        elements.append(PageBreak())
        elements.append(Paragraph("Patient Outcomes & Cost-Effectiveness", heading_style))
        elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
        elements.append(Spacer(1, 0.2*inch))
        
        outcomes_data = [
            ["Outcome Measure", "Count", "Percentage", "Cost per Patient"],
            ["Patients Still Active", 
             f"{patient_outcomes.get('active_patients', 0):,}",
             f"{patient_outcomes.get('retention_rate', 0):.1f}%",
             f"£{total_costs['total'] / patient_outcomes['active_patients']:,.0f}" if patient_outcomes.get('active_patients', 0) > 0 else "N/A"],
            ["Vision Maintained (≥ baseline - 10)", 
             f"{patient_outcomes.get('vision_maintained', 0):,} of {patient_outcomes.get('active_patients', 0):,}",
             f"{patient_outcomes.get('vision_maintenance_rate', 0):.1f}% of active",
             f"£{total_costs['total'] / patient_outcomes['vision_maintained']:,.0f}" if patient_outcomes.get('vision_maintained', 0) > 0 else "N/A"],
        ]
        
        outcomes_table = Table(outcomes_data, colWidths=[2.5*inch, 1*inch, 1.2*inch, 1.5*inch])
        outcomes_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ]))
        elements.append(outcomes_table)
        
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(
            "<i>Vision Maintained: Patients whose final visual acuity is no worse than 10 letters below their baseline.</i>",
            normal_style
        ))
    
    # Peak Demand Summary
    elements.append(PageBreak())
    elements.append(Paragraph("Peak Demand Analysis", heading_style))
    elements.append(HRFlowable(6.5*inch, thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 0.2*inch))
    
    peak_data = [["Role", "Peak Daily Demand", "Average Daily Demand", "Peak:Avg Ratio"]]
    
    for role, peak in workload_summary['peak_daily_demand'].items():
        avg = workload_summary['average_daily_demand'].get(role, 0)
        ratio = peak / avg if avg > 0 else 0
        peak_data.append([
            role,
            str(peak),
            f"{avg:.1f}",
            f"{ratio:.2f}"
        ])
    
    peak_table = Table(peak_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    peak_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
    ]))
    elements.append(peak_table)
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes