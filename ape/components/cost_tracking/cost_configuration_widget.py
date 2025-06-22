"""
Cost configuration widget for Streamlit UI.

This module provides UI components for:
- Drug type selection (biosimilar/originator/custom)
- Cost display and adjustment
- Protocol cost comparison
"""

import streamlit as st
from typing import Dict, Optional, Tuple
from pathlib import Path
import yaml

from simulation_v2.economics.cost_config import CostConfig


class CostConfigurationWidget:
    """Widget for configuring cost parameters in Streamlit."""
    
    def __init__(self, default_config_path: str = "protocols/cost_configs/nhs_hrg_aligned_2025.yaml"):
        """
        Initialize cost configuration widget.
        
        Args:
            default_config_path: Path to default cost configuration
        """
        self.default_config_path = Path(default_config_path)
        self.load_default_config()
        
    def load_default_config(self) -> None:
        """Load the default NHS cost configuration."""
        if self.default_config_path.exists():
            self.default_config = CostConfig.from_yaml(self.default_config_path)
        else:
            st.error(f"Default cost configuration not found: {self.default_config_path}")
            self.default_config = None
            
    def render(self) -> Tuple[str, float, Optional[CostConfig]]:
        """
        Render the cost configuration widget.
        
        Returns:
            Tuple of (drug_type, drug_cost, cost_config)
        """
        st.subheader("💰 Cost Configuration")
        
        if not self.default_config:
            st.error("No cost configuration available")
            return "eylea_2mg_biosimilar", 355.0, None
            
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Drug selection
            drug_options = {
                "Eylea Biosimilar (£355)": ("eylea_2mg_biosimilar", 355),
                "Eylea Originator (£979)": ("eylea_2mg_originator", 979),
                "Eylea HD 8mg (£1,198)": ("eylea_8mg", 1198),
                "Lucentis Biosimilar (£628)": ("lucentis_biosimilar", 628),
                "Lucentis Originator (£613)": ("lucentis_originator", 613),
                "Faricimab/Vabysmo (£1,028)": ("faricimab", 1028),
                "Avastin (£50)": ("avastin", 50),
                "Custom": ("custom", 0)
            }
            
            selected_option = st.selectbox(
                "Select Drug",
                options=list(drug_options.keys()),
                index=0,  # Default to biosimilar
                help="Choose the anti-VEGF drug for cost calculations"
            )
            
            drug_type, default_cost = drug_options[selected_option]
            
            # Custom cost input
            if drug_type == "custom":
                drug_cost = st.number_input(
                    "Enter custom drug cost (£)",
                    min_value=0.0,
                    max_value=5000.0,
                    value=500.0,
                    step=10.0,
                    help="Enter the cost per injection for your custom drug"
                )
            else:
                # Show cost with adjustment slider
                drug_cost = st.slider(
                    f"Adjust {selected_option.split('(')[0].strip()} cost (£)",
                    min_value=int(default_cost * 0.5),
                    max_value=int(default_cost * 1.5),
                    value=int(default_cost),
                    step=5,
                    help="Adjust drug cost to reflect local pricing or discounts"
                )
                
        with col2:
            # Cost summary
            st.metric("Drug Cost per Injection", f"£{drug_cost:,.0f}")
            
            # Show cost reduction for biosimilar
            if drug_type == "eylea_2mg_biosimilar":
                originator_cost = self.default_config.get_drug_cost("eylea_2mg_originator")
                reduction = (1 - drug_cost/originator_cost) * 100
                st.metric("Cost Reduction vs Originator", f"{reduction:.0f}%")
                
        # Visit cost information
        with st.expander("Visit Cost Breakdown", expanded=False):
            st.write("**NHS HRG Cost Components:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Procedures:**")
                st.write(f"- Injection administration: £{self.default_config.get_component_cost('injection_administration')}")
                st.write(f"- OCT scan: £{self.default_config.get_component_cost('oct_scan')}")
                st.write(f"- Consultant first visit: £{self.default_config.get_component_cost('consultant_first')}")
                st.write(f"- Consultant follow-up: £{self.default_config.get_component_cost('consultant_followup')}")
                
            with col2:
                st.write("**Other Services:**")
                st.write(f"- Virtual review: £{self.default_config.get_component_cost('virtual_review')}")
                st.write(f"- Nurse review: £{self.default_config.get_component_cost('nurse_review')}")
                st.write(f"- Annual review: £{self.default_config.get_special_event_cost('annual_review')}")
                
        # Protocol cost comparison preview
        st.subheader("📊 Protocol Cost Implications")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # T&E costs
            tae_visit_cost = self.default_config.get_visit_cost("tae_assessment")
            tae_episode_cost = drug_cost + tae_visit_cost
            
            st.metric(
                "T&E Cost per Episode",
                f"£{tae_episode_cost:,.0f}",
                help=f"Drug (£{drug_cost}) + Visit (£{tae_visit_cost})"
            )
            
        with col2:
            # T&T costs
            tnt_injection_cost = self.default_config.get_visit_cost("tnt_injection_only")
            tnt_episode_cost = drug_cost + tnt_injection_cost
            
            st.metric(
                "T&T Injection Cost",
                f"£{tnt_episode_cost:,.0f}",
                help=f"Drug (£{drug_cost}) + Nurse visit (£{tnt_injection_cost})"
            )
            
        with col3:
            # Difference
            cost_diff = tae_episode_cost - tnt_episode_cost
            st.metric(
                "T&E vs T&T Difference",
                f"£{cost_diff:,.0f}",
                help="Additional cost per T&E visit due to full assessment"
            )
            
        # Year 1 cost estimates
        st.write("**Estimated Year 1 Costs (per patient):**")
        
        # Get expected injection counts from config
        tae_year1_injections = self.default_config.metadata.get('validation_targets', {}).get('injections_per_year', {}).get('tae', {}).get('year1', 6)
        tnt_year1_injections = self.default_config.metadata.get('validation_targets', {}).get('injections_per_year', {}).get('tnt', {}).get('year1', 7.5)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # T&E Year 1
            tae_drug_cost = drug_cost * tae_year1_injections
            tae_visit_cost_total = tae_visit_cost * tae_year1_injections
            tae_total = tae_drug_cost + tae_visit_cost_total
            
            st.info(f"""
            **T&E Protocol (~{tae_year1_injections} injections)**
            - Drug costs: £{tae_drug_cost:,.0f}
            - Visit costs: £{tae_visit_cost_total:,.0f}
            - Total: £{tae_total:,.0f}
            """)
            
        with col2:
            # T&T Year 1 (assuming 3 full assessments + rest nurse-led)
            tnt_assessments = 3  # Initial + 2 annual
            tnt_nurse_visits = tnt_year1_injections - tnt_assessments
            
            tnt_drug_cost = drug_cost * tnt_year1_injections
            tnt_assessment_cost = self.default_config.get_visit_cost("tae_assessment") * tnt_assessments
            tnt_nurse_cost = tnt_injection_cost * tnt_nurse_visits
            tnt_total = tnt_drug_cost + tnt_assessment_cost + tnt_nurse_cost
            
            st.info(f"""
            **T&T Protocol (~{tnt_year1_injections} injections)**
            - Drug costs: £{tnt_drug_cost:,.0f}
            - Assessment costs: £{tnt_assessment_cost:,.0f}
            - Nurse visit costs: £{tnt_nurse_cost:,.0f}
            - Total: £{tnt_total:,.0f}
            """)
            
        # Return configuration
        return drug_type, drug_cost, self.default_config
        
    def get_custom_config(self, drug_type: str, drug_cost: float) -> CostConfig:
        """
        Create a custom cost configuration with adjusted drug price.
        
        Args:
            drug_type: Selected drug type
            drug_cost: Custom drug cost
            
        Returns:
            Modified CostConfig instance
        """
        if not self.default_config:
            return None
            
        # Create a copy of the default config data
        config_data = {
            'metadata': dict(self.default_config.metadata),
            'drug_costs': dict(self.default_config.drug_costs),
            'visit_components': dict(self.default_config.visit_components),
            'visit_types': dict(self.default_config.visit_types),
            'special_events': dict(self.default_config.special_events)
        }
        
        # Update the selected drug cost
        if drug_type != "custom":
            config_data['drug_costs'][drug_type] = drug_cost
        else:
            # Add custom drug entry
            config_data['drug_costs']['custom_drug'] = drug_cost
            
        # Create new config instance
        return CostConfig(
            metadata=config_data['metadata'],
            drug_costs=config_data['drug_costs'],
            visit_components=config_data['visit_components'],
            visit_types=config_data['visit_types'],
            special_events=config_data['special_events']
        )