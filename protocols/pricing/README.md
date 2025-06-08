# NHS Drug Pricing Structure

This directory contains a modular pricing system that separates list prices, discounts, and net prices for transparency and flexibility.

## File Structure

### 1. `list_prices.yaml`
- Official NHS Drug Tariff prices (before any discounts)
- Source: BNF/NHS Drug Tariff
- Updated: January 2025
- Contains all anti-VEGF drugs used in ophthalmology

### 2. `nhs_discounts.yaml`  
- Discount rates from list prices (Commercial in Confidence)
- Based on market intelligence
- Expressed as both discount % and net payment %
- Includes confidence levels and notes

### 3. `nhs_net_prices.yaml`
- Calculated net prices (list × discount)
- Annual cost calculations
- Cost rankings
- Strategic pricing insights

### 4. `price_calculator.py`
- Python utility to dynamically calculate prices
- Combines list prices and discounts
- Enables "what-if" analysis for different discount scenarios

## Key Findings

### Aflibercept Pricing Strategy
- **Eylea 2mg**: £816 list → £457 net (44% discount)
- **Eylea 8mg**: £998 list → £339 net (66% discount)
- **8mg is £118 CHEAPER per injection than 2mg**

### Why This Matters
1. Strategic discounting before biosimilar entry
2. Complete reversal of expected economics
3. 8mg now cost-saving, not premium option

## Usage

### In Protocols
```yaml
# Reference the pricing files
drug_costs:
  source: "protocols/pricing/list_prices.yaml"
  discount_source: "protocols/pricing/nhs_discounts.yaml"
```

### For Analysis
```python
from protocols.pricing.price_calculator import DrugPriceCalculator

calc = DrugPriceCalculator()
list_price, discount, net_price = calc.get_net_price('aflibercept', 'eylea_8mg')
```

### Updating Prices
1. Update `list_prices.yaml` when NHS Drug Tariff changes
2. Update `nhs_discounts.yaml` when discount intelligence changes
3. Net prices automatically recalculate

## Important Notes

1. **Confidentiality**: Actual NHS discounts are commercial in confidence
2. **Estimates**: These reflect market intelligence, not confirmed rates
3. **Variability**: Individual trusts may negotiate different rates
4. **Volume discounts**: High-volume centers may get additional discounts

## Future Considerations

- Biosimilar entry will disrupt pricing
- 8mg discount may reduce after market capture
- Need to monitor and update regularly