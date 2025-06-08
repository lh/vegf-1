#!/usr/bin/env python3
"""
Price Calculator Utility
Loads list prices and discounts to calculate net prices dynamically
"""

import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple

class DrugPriceCalculator:
    """Calculate drug prices from list prices and discount rates."""
    
    def __init__(self, pricing_dir: Path = None):
        """Initialize with pricing directory."""
        if pricing_dir is None:
            pricing_dir = Path(__file__).parent
        
        self.pricing_dir = pricing_dir
        self.list_prices = self._load_yaml('list_prices.yaml')
        self.discounts = self._load_yaml('nhs_discounts.yaml')
        
    def _load_yaml(self, filename: str) -> Dict:
        """Load a YAML file from the pricing directory."""
        filepath = self.pricing_dir / filename
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    
    def get_net_price(self, drug_category: str, drug_name: str) -> Tuple[float, float, float]:
        """
        Get net price for a drug.
        
        Returns:
            Tuple of (list_price, discount_rate, net_price)
        """
        # Get list price
        if drug_category in self.list_prices and drug_name in self.list_prices[drug_category]:
            drug_info = self.list_prices[drug_category][drug_name]
            if isinstance(drug_info, dict) and 'list_price' in drug_info:
                list_price = drug_info['list_price']
            else:
                # Handle entries like biosimilar with estimated_list_price
                if 'estimated_list_price' in self.list_prices.get(drug_name, {}):
                    list_price = self.list_prices[drug_name]['estimated_list_price']
                else:
                    raise ValueError(f"No list price found for {drug_category}/{drug_name}")
        else:
            raise ValueError(f"No list price found for {drug_category}/{drug_name}")
        
        # Get discount rate
        if (drug_category in self.discounts['discount_rates'] and 
            drug_name in self.discounts['discount_rates'][drug_category]):
            discount_info = self.discounts['discount_rates'][drug_category][drug_name]
            discount_rate = discount_info['discount']
            net_percentage = discount_info['net_percentage']
        else:
            # No discount available
            discount_rate = 0.0
            net_percentage = 1.0
        
        # Calculate net price
        net_price = list_price * net_percentage
        
        return list_price, discount_rate, net_price
    
    def compare_drugs(self, comparisons: list) -> None:
        """
        Compare multiple drugs.
        
        Args:
            comparisons: List of (category, name) tuples
        """
        print("\nDRUG PRICE COMPARISON")
        print("=" * 80)
        print(f"{'Drug':<30} {'List Price':<15} {'Discount':<15} {'Net Price':<15}")
        print("-" * 80)
        
        for category, name in comparisons:
            try:
                list_price, discount, net_price = self.get_net_price(category, name)
                print(f"{name:<30} £{list_price:<14.0f} {discount*100:<14.0f}% £{net_price:<14.0f}")
            except ValueError as e:
                print(f"{name:<30} {str(e)}")
    
    def calculate_annual_cost(self, drug_category: str, drug_name: str, 
                            injections_per_year: float) -> Dict[str, float]:
        """Calculate annual drug cost."""
        list_price, discount, net_price = self.get_net_price(drug_category, drug_name)
        
        return {
            'drug': drug_name,
            'list_price_per_injection': list_price,
            'net_price_per_injection': net_price,
            'injections_per_year': injections_per_year,
            'annual_list_cost': list_price * injections_per_year,
            'annual_net_cost': net_price * injections_per_year,
            'annual_savings': (list_price - net_price) * injections_per_year
        }


def main():
    """Demonstrate price calculations."""
    calc = DrugPriceCalculator()
    
    # Compare key drugs
    print("\nKEY ANTI-VEGF DRUG PRICING")
    comparisons = [
        ('aflibercept', 'eylea_2mg'),
        ('aflibercept', 'eylea_8mg'),
        ('ranibizumab', 'lucentis'),
        ('faricimab', 'vabysmo'),
        ('bevacizumab', 'avastin_compounded'),
    ]
    
    calc.compare_drugs(comparisons)
    
    # Annual cost comparison
    print("\n\nANNUAL COST ANALYSIS")
    print("=" * 80)
    
    drugs_to_analyze = [
        ('aflibercept', 'eylea_2mg', 6.9),    # T&E typical
        ('aflibercept', 'eylea_8mg', 6.1),    # Extended intervals
    ]
    
    for category, name, injections in drugs_to_analyze:
        costs = calc.calculate_annual_cost(category, name, injections)
        print(f"\n{costs['drug']} ({costs['injections_per_year']} injections/year):")
        print(f"  List cost: £{costs['annual_list_cost']:,.0f}")
        print(f"  Net cost:  £{costs['annual_net_cost']:,.0f}")
        print(f"  Savings:   £{costs['annual_savings']:,.0f}")
    
    # Key finding
    print("\n" + "="*80)
    print("KEY FINDING: Aflibercept 8mg is CHEAPER than 2mg due to 66% discount!")
    print("="*80)


if __name__ == "__main__":
    main()