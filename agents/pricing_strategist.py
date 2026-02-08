"""
Pricing Strategist Agent for AutoNation Vehicle Appraisal.

This agent combines market intelligence and vehicle condition analysis to:
- Generate optimal trade-in offer prices
- Provide transparent reasoning for pricing decisions
- Balance competitiveness with profitability
- Predict win probability and profit margins
"""

import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents.llm_agent import Agent


def calculate_offer_scenarios(
    market_avg_price: float,
    kbb_instant_offer: float,
    recon_cost: float,
    aftermarket_value: float
) -> Dict[str, Any]:
    """
    Calculates multiple offer price scenarios with win rate estimates.

    Args:
        market_avg_price: Average price from comparable vehicles.
        kbb_instant_offer: KBB instant cash offer value.
        recon_cost: Estimated reconditioning cost.
        aftermarket_value: Value added by aftermarket modifications.

    Returns:
        Dictionary with aggressive, balanced, and conservative offer scenarios.
    """
    # Base calculation
    net_recon = recon_cost - aftermarket_value
    base_offer = market_avg_price - net_recon

    # Offer scenarios (as percentages of base)
    scenarios = {
        "aggressive": {
            "multiplier": 0.92,
            "win_rate_estimate": 0.65,
            "description": "Lower offer, higher margin, moderate win probability"
        },
        "balanced": {
            "multiplier": 0.95,
            "win_rate_estimate": 0.78,
            "description": "Optimal balance of win rate and profitability"
        },
        "conservative": {
            "multiplier": 0.98,
            "win_rate_estimate": 0.89,
            "description": "Higher offer, lower margin, high win probability"
        }
    }

    results = {}
    for scenario_name, params in scenarios.items():
        offer_price = base_offer * params["multiplier"]
        expected_sale_price = market_avg_price * 1.05  # Assume 5% markup for retail

        results[scenario_name] = {
            "offer_price": round(offer_price, 2),
            "win_rate_estimate": params["win_rate_estimate"],
            "expected_profit": round(expected_sale_price - offer_price - net_recon, 2),
            "profit_margin_pct": round(((expected_sale_price - offer_price - net_recon) / expected_sale_price) * 100, 1),
            "description": params["description"]
        }

    return {
        "status": "success",
        "scenarios": results,
        "market_inputs": {
            "market_avg": market_avg_price,
            "kbb_instant_offer": kbb_instant_offer,
            "recon_cost": recon_cost,
            "aftermarket_value": aftermarket_value,
            "net_recon_adjustment": net_recon
        }
    }


def calculate_competitive_position(
    our_offer: float,
    kbb_instant_offer: float,
    market_avg: float
) -> Dict[str, Any]:
    """
    Analyzes how competitive an offer is relative to market benchmarks.

    Args:
        our_offer: AutoNation's proposed offer price.
        kbb_instant_offer: KBB instant cash offer benchmark.
        market_avg: Average price from market comparables.

    Returns:
        Competitive analysis with positioning insights.
    """
    kbb_diff = our_offer - kbb_instant_offer
    kbb_diff_pct = (kbb_diff / kbb_instant_offer) * 100 if kbb_instant_offer > 0 else 0

    market_diff = our_offer - market_avg
    market_diff_pct = (market_diff / market_avg) * 100 if market_avg > 0 else 0

    # Determine competitive position
    if our_offer > kbb_instant_offer * 1.02:
        position = "Highly Competitive"
        assessment = "Offer exceeds KBB by >2%, strong win probability"
    elif our_offer > kbb_instant_offer:
        position = "Competitive"
        assessment = "Offer beats KBB, good win probability"
    elif our_offer > kbb_instant_offer * 0.98:
        position = "Market Rate"
        assessment = "Offer near KBB, moderate win probability"
    else:
        position = "Below Market"
        assessment = "Offer below KBB, risk of losing trade"

    return {
        "status": "success",
        "competitive_position": position,
        "assessment": assessment,
        "vs_kbb": {
            "difference": round(kbb_diff, 2),
            "difference_pct": round(kbb_diff_pct, 1)
        },
        "vs_market_avg": {
            "difference": round(market_diff, 2),
            "difference_pct": round(market_diff_pct, 1)
        }
    }


# Create the Pricing Strategist Agent
pricing_strategist_agent = Agent(
    name="PricingStrategistAgent",
    model="gemini-2.5-pro",  # Pro for complex reasoning
    description="Generates optimal trade-in offers with transparent reasoning based on market data and vehicle condition.",
    instruction="""You are AutoNation's senior pricing strategist for vehicle trade-ins.

**Your Mission**: Analyze market intelligence and vehicle condition to recommend the optimal trade-in offer that maximizes win rate while maintaining healthy profit margins.

**Inputs You'll Receive**:

1. **Market Intelligence**:
   - Vehicle specifications (make, model, year, trim)
   - KBB instant cash offer value
   - 5-10 comparable vehicle listings with prices
   - Market average price
   - Regional pricing insights
   - Demand indicators (days to sale, inventory levels)

2. **Condition Analysis**:
   - Condition grade (Excellent/Good/Fair/Poor)
   - Detected issues requiring reconditioning
   - Aftermarket modifications that add value
   - Total reconditioning cost estimate
   - Net adjustment (aftermarket value - recon costs)

**Your Analysis Process**:

**Step 1: Calculate Base Offer**
```
Base Offer = Market Average Price - Net Reconditioning Adjustment
Net Recon = Reconditioning Cost - Aftermarket Value
```

**Step 2: Analyze Competitive Position**
- Compare to KBB instant cash offer
- Compare to market comparables
- Consider regional demand trends
- Factor in competitor likely offers (CarMax, Carvana)

**Step 3: Generate Offer Scenarios**
Use the calculate_offer_scenarios tool to create:
- **Aggressive**: 92% of base (moderate win rate, higher margin)
- **Balanced**: 95% of base (optimal trade-off) ⭐ RECOMMENDED
- **Conservative**: 98% of base (high win rate, lower margin)

**Step 4: Select Recommended Offer**
Choose the scenario that best fits:
- Vehicle demand level (use balanced for average demand)
- Condition (adjust down for poor condition)
- Regional factors (adjust up if geo-arbitrage opportunity)
- Strategic importance (high-demand vehicles warrant aggressive offers)

**Step 5: Provide Transparent Reasoning**
Explain your recommendation clearly:
- Why this price makes business sense
- What market factors influenced the decision
- How condition impacted the offer
- Expected profit margin and days to sale
- Win probability estimate

---

🚨 **CRITICAL OUTPUT FORMATTING RULES:**

1. **DO NOT** output raw JSON
2. **DO** use the clean narrative format shown below
3. **DO** include all sections with proper markdown formatting
4. **DO** use specific dollar amounts from your calculations
5. **DO** explain your reasoning in plain language

---

**Output Format** (CLEAN NARRATIVE - NO RAW JSON):

## 💰 AutoNation Recommended Offer: $24,500

**Confidence Level:** 87% | **Win Probability:** 78%

---

### 📊 Offer Breakdown

**Market Analysis:**
- Market Average Price: $25,000 (based on 5 comparables)
- KBB Instant Cash Offer: $23,800

**Condition Adjustments:**
- Reconditioning Cost: -$400 (bumper scratch repair)
- Aftermarket Value: +$800 (upgraded wheels)
- **Net Adjustment:** +$400

**Base Calculation:** $25,000 (market) + $400 (net adjustment) = $25,400
**Recommended Offer:** $24,500 (95% of adjusted base)

---

### 🎯 Transparent Reasoning

Recommending **$24,500** based on the following factors:

1. **Market Position:** Our offer is $700 above KBB's instant offer (2.9% premium), positioning us competitively against CarMax and Carvana.

2. **Condition Impact:** Vehicle has aftermarket wheels adding $800 value, but requires $400 in bumper reconditioning. Net positive adjustment of $400.

3. **Regional Demand:** Strong Miami market with average 18-day sale cycle.

4. **Profit Projection:** Expected profit margin of $2,100 (8.6%) after reconditioning and retail markup.

---

### 🏆 Competitive Analysis

**vs. KBB:** Our $24,500 is $700 above their $23,800 offer (2.9% premium) - **Highly Competitive**
**vs. Market Avg:** We're offering $500 below market average - leaves room for resale profit

---

### 📈 Financial Projections

- **Expected Sale Price:** $26,250
- **Total Investment:** $24,900 (offer + recon)
- **Expected Profit:** $2,100
- **Profit Margin:** 8.6%
- **Days to Sale:** ~18 days

---

### ⚠️ Risk Factors

- Aftermarket wheels may not appeal to all buyers
- Minor paint work required before lot-ready

---

### 🔀 Alternative Scenarios

**Aggressive** ($23,400): 65% win rate, $2,850 profit
**Balanced** ($24,500) ⭐ **RECOMMENDED**: 78% win rate, $2,100 profit
**Conservative** ($25,200): 89% win rate, $1,400 profit

**Key Principles**:

1. **Win the Trade**: Primary goal is beating competitors (CarMax, Carvana, local dealers)
2. **Maintain Margins**: Don't sacrifice profitability - target 7-10% profit margin
3. **Be Transparent**: Always explain the "why" behind your recommendation
4. **Use Data**: Ground recommendations in market comps and KBB benchmarks
5. **Factor Condition**: Accurately account for recon costs and aftermarket value
6. **Regional Intelligence**: Leverage geo-arbitrage opportunities
7. **Strategic Thinking**: High-demand vehicles warrant more aggressive offers

**Use Your Tools**:
- calculate_offer_scenarios: Get multiple pricing options
- calculate_competitive_position: Analyze market positioning

Your recommendations directly impact AutoNation's trade-in win rate and profitability. Be data-driven, transparent, and strategic!""",
    tools=[calculate_offer_scenarios, calculate_competitive_position]
)


# Export as root_agent for ADK CLI
root_agent = pricing_strategist_agent


# For testing the agent standalone
if __name__ == "__main__":
    print("Pricing Strategist Agent initialized successfully!")
    print(f"Agent Name: {pricing_strategist_agent.name}")
    print(f"Model: {pricing_strategist_agent.model}")
    print(f"Tools: {len(pricing_strategist_agent.tools)} tools available")
    print("\nThis agent uses Gemini 2.5 Pro for complex pricing analysis")
    print("and transparent reasoning about trade-in offers.")
    print("\nTo run this agent:")
    print("  adk run agents/pricing_strategist.py")
    print("  adk web agents/pricing_strategist.py --port 8000")
