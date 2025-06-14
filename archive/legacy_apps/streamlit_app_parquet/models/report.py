"""
Report data structures for the APE Streamlit application.

This module provides data models for report generation, supporting
both interactive Streamlit reports and static exports in various formats.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
import datetime
import os
from pathlib import Path
import json

from streamlit_app.models.simulation_results import SimulationResults


@dataclass
class ReportSection:
    """Section of a report."""
    
    title: str
    content: str
    order: int = 0
    visualizations: List[str] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    subsections: List['ReportSection'] = field(default_factory=list)
    
    def add_visualization(self, viz_path: str) -> None:
        """Add a visualization to the section.
        
        Parameters
        ----------
        viz_path : str
            Path to the visualization
        """
        self.visualizations.append(viz_path)
    
    def add_table(self, table_data: Dict[str, Any]) -> None:
        """Add a table to the section.
        
        Parameters
        ----------
        table_data : Dict[str, Any]
            Table data
        """
        self.tables.append(table_data)
    
    def add_subsection(self, subsection: 'ReportSection') -> None:
        """Add a subsection to the section.
        
        Parameters
        ----------
        subsection : ReportSection
            Subsection to add
        """
        self.subsections.append(subsection)
        
        # Sort subsections by order
        self.subsections.sort(key=lambda x: x.order)


@dataclass
class Report:
    """Report containing multiple sections."""
    
    title: str
    description: str
    author: str = "APE: AMD Protocol Explorer"
    simulation_id: Optional[str] = None
    date: datetime.datetime = field(default_factory=datetime.datetime.now)
    sections: List[ReportSection] = field(default_factory=list)
    visualizations: Dict[str, str] = field(default_factory=dict)
    data_tables: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_section(self, section: ReportSection) -> None:
        """Add a section to the report.
        
        Parameters
        ----------
        section : ReportSection
            Section to add
        """
        self.sections.append(section)
        
        # Sort sections by order
        self.sections.sort(key=lambda x: x.order)
    
    def add_visualization(self, viz_type: str, viz_path: str) -> None:
        """Add a visualization to the report.
        
        Parameters
        ----------
        viz_type : str
            Type of visualization
        viz_path : str
            Path to the visualization
        """
        self.visualizations[viz_type] = viz_path
    
    def add_data_table(self, table_name: str, table_data: Dict[str, Any]) -> None:
        """Add a data table to the report.
        
        Parameters
        ----------
        table_name : str
            Name of the table
        table_data : Dict[str, Any]
            Table data
        """
        self.data_tables[table_name] = table_data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary representation of the report
        """
        # Helper function to convert section to dict
        def section_to_dict(section: ReportSection) -> Dict[str, Any]:
            return {
                "title": section.title,
                "content": section.content,
                "order": section.order,
                "visualizations": section.visualizations,
                "tables": section.tables,
                "subsections": [section_to_dict(subsection) for subsection in section.subsections]
            }
        
        return {
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "simulation_id": self.simulation_id,
            "date": self.date.isoformat(),
            "sections": [section_to_dict(section) for section in self.sections],
            "visualizations": self.visualizations,
            "data_tables": self.data_tables,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Report':
        """Create a Report from a dictionary.
        
        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary representation of a report
        
        Returns
        -------
        Report
            Report instance
        """
        # Helper function to convert dict to section
        def dict_to_section(section_dict: Dict[str, Any]) -> ReportSection:
            section = ReportSection(
                title=section_dict["title"],
                content=section_dict["content"],
                order=section_dict.get("order", 0),
                visualizations=section_dict.get("visualizations", []),
                tables=section_dict.get("tables", [])
            )
            
            # Add subsections
            for subsection_dict in section_dict.get("subsections", []):
                section.add_subsection(dict_to_section(subsection_dict))
            
            return section
        
        # Parse date if provided
        date = datetime.datetime.now()
        if "date" in data:
            try:
                date = datetime.datetime.fromisoformat(data["date"])
            except ValueError:
                pass
        
        # Create report
        report = cls(
            title=data["title"],
            description=data["description"],
            author=data.get("author", "APE: AMD Protocol Explorer"),
            simulation_id=data.get("simulation_id"),
            date=date,
            visualizations=data.get("visualizations", {}),
            data_tables=data.get("data_tables", {}),
            metadata=data.get("metadata", {})
        )
        
        # Add sections
        for section_dict in data.get("sections", []):
            report.add_section(dict_to_section(section_dict))
        
        return report
    
    def save(self, file_path: str) -> None:
        """Save the report to a file.
        
        Parameters
        ----------
        file_path : str
            Path to save the report to
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Convert to dictionary
        report_dict = self.to_dict()
        
        # Save to file
        with open(file_path, "w") as f:
            json.dump(report_dict, f, indent=2)
    
    @classmethod
    def load(cls, file_path: str) -> 'Report':
        """Load a report from a file.
        
        Parameters
        ----------
        file_path : str
            Path to load the report from
        
        Returns
        -------
        Report
            Report instance
        """
        # Load from file
        with open(file_path, "r") as f:
            report_dict = json.load(f)
        
        # Convert to Report
        return cls.from_dict(report_dict)


class ReportGenerator:
    """Generator for reports from simulation results."""
    
    def __init__(self, 
                 output_dir: Optional[str] = None,
                 include_code: bool = False,
                 include_appendix: bool = True):
        """Initialize report generator.
        
        Parameters
        ----------
        output_dir : str, optional
            Directory to save reports to, by default None
        include_code : bool, optional
            Whether to include code in reports, by default False
        include_appendix : bool, optional
            Whether to include appendices in reports, by default True
        """
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "output", "reports"
        )
        self.include_code = include_code
        self.include_appendix = include_appendix
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_simulation_report(self, results: SimulationResults) -> Report:
        """Generate a report from simulation results.
        
        Parameters
        ----------
        results : SimulationResults
            Simulation results
        
        Returns
        -------
        Report
            Generated report
        """
        # Create report
        report = Report(
            title=f"{results.simulation_type} Simulation Report",
            description=f"Report for {results.simulation_type} simulation with {results.population_size} patients over {results.duration_years} years",
            simulation_id=results.simulation_id if hasattr(results, "simulation_id") else None,
            metadata={
                "simulation_type": results.simulation_type,
                "population_size": results.population_size,
                "duration_years": results.duration_years,
                "parameters": results.parameters
            }
        )
        
        # Create executive summary section
        summary_section = ReportSection(
            title="Executive Summary",
            content=(
                f"This report presents the results of a {results.simulation_type} simulation "
                f"with {results.population_size} patients over {results.duration_years} years. "
                f"The simulation models AMD treatment patterns and outcomes, including discontinuation events "
                f"and visual acuity changes over time."
            ),
            order=0
        )
        report.add_section(summary_section)
        
        # Create key metrics section
        metrics_section = ReportSection(
            title="Key Metrics",
            content="This section presents the key metrics from the simulation.",
            order=1
        )
        
        # Add metrics table
        metrics_table = {
            "headers": ["Metric", "Value"],
            "rows": [
                ["Simulation Type", results.simulation_type],
                ["Population Size", results.population_size],
                ["Duration (years)", results.duration_years],
                ["Total Injections", results.total_injections],
                ["Mean Injections per Patient", f"{results.mean_injections:.2f}"],
                ["Total Discontinuations", results.total_discontinuations],
                ["Discontinuation Rate", f"{results.discontinuation_rate:.2f}%"]
            ]
        }
        metrics_section.add_table(metrics_table)
        report.add_section(metrics_section)
        
        # Create discontinuation analysis section
        if results.discontinuation_counts:
            disc_section = ReportSection(
                title="Discontinuation Analysis",
                content="This section analyzes patient discontinuation patterns in the simulation.",
                order=2
            )
            
            # Add discontinuation table
            disc_counts = results.discontinuation_counts.as_dict()
            disc_table = {
                "headers": ["Discontinuation Type", "Count", "Percentage"],
                "rows": []
            }
            
            total_disc = sum(disc_counts.values())
            for disc_type, count in disc_counts.items():
                percentage = (count / total_disc * 100) if total_disc > 0 else 0
                disc_table["rows"].append([
                    disc_type,
                    count,
                    f"{percentage:.2f}%"
                ])
            
            disc_section.add_table(disc_table)
            report.add_section(disc_section)
        
        # Create visual acuity section
        if results.mean_va_data:
            va_section = ReportSection(
                title="Visual Acuity Over Time",
                content="This section presents visual acuity changes over the course of the simulation.",
                order=3
            )
            report.add_section(va_section)
        
        # Create appendix if requested
        if self.include_appendix:
            appendix = ReportSection(
                title="Appendix",
                content="Additional details and methodology information.",
                order=10
            )
            
            # Add simulation parameters subsection
            params_section = ReportSection(
                title="Simulation Parameters",
                content="Detailed list of simulation parameters used.",
                order=0
            )
            
            # Add parameters table
            params_table = {
                "headers": ["Parameter", "Value"],
                "rows": []
            }
            
            # Add parameters
            for param, value in results.parameters.items():
                params_table["rows"].append([param, str(value)])
            
            params_section.add_table(params_table)
            appendix.add_subsection(params_section)
            
            # Add methodology subsection
            method_section = ReportSection(
                title="Methodology",
                content=(
                    "This simulation uses a sophisticated model of treatment discontinuation and recurrence "
                    "in AMD treatment. The model includes multiple discontinuation types, type-specific "
                    "monitoring schedules, time-dependent recurrence probabilities, and clinician variation."
                ),
                order=1
            )
            appendix.add_subsection(method_section)
            
            report.add_section(appendix)
        
        return report
    
    def save_report(self, report: Report, format: str = "json") -> str:
        """Save a report to a file.
        
        Parameters
        ----------
        report : Report
            Report to save
        format : str, optional
            Format to save in, by default "json"
        
        Returns
        -------
        str
            Path to the saved report
        """
        # Create a filename based on title and date
        title_slug = report.title.lower().replace(" ", "_").replace(":", "")
        date_str = report.date.strftime("%Y%m%d_%H%M%S")
        filename = f"{title_slug}_{date_str}.{format}"
        
        # Create file path
        file_path = os.path.join(self.output_dir, filename)
        
        # Save report
        report.save(file_path)
        
        return file_path