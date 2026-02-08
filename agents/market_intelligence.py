"""
Market Intelligence Agent for AutoNation Vehicle Appraisal.

This agent aggregates real-time vehicle market data by:
1. Decoding VINs using the free NHTSA API
2. Retrieving comparable vehicle listings from mock data sources
3. Providing comprehensive market analysis with pricing insights
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents.llm_agent import Agent
from tools.nhtsa_api import decode_vin, validate_vin
from tools.api_mocks import get_market_intelligence
from typing import Dict, Any


# Tool wrapper functions with proper ADK signatures
def vin_decoder_tool(vin: str) -> Dict[str, Any]:
    """
    Decodes a VIN using the NHTSA API to get vehicle specifications.

    This uses the free NHTSA Vehicle API to retrieve accurate make, model,
    year, trim, and other vehicle details from a 17-character VIN.

    Args:
        vin: Vehicle Identification Number (17 characters).

    Returns:
        Dictionary containing vehicle specifications including make, model,
        year, trim, engine, fuel type, and manufacturer information.
    """
    return decode_vin(vin)


def market_data_tool(vin: str, zip_code: str = "33130") -> Dict[str, Any]:
    """
    Retrieves comprehensive market intelligence for a vehicle.

    Aggregates data from multiple sources including KBB instant cash offers
    and comparable vehicle listings from CarGurus and AutoTrader.

    Args:
        vin: Vehicle Identification Number to research.
        zip_code: Location zip code for comparable listings (default: 33130 Miami).

    Returns:
        Dictionary containing:
        - vehicle_info: Make, model, year, trim, mileage
        - kbb_valuation: Instant cash offer and trade-in range
        - comparables: List of 5-10 similar vehicles with prices
        - market_summary: Average price, min/max range, outliers removed
        - regional_insights: Geo-arbitrage opportunities (if available)
        - demand_insights: Days to sale, inventory levels (if available)
    """
    return get_market_intelligence(vin, zip_code)


# Create the Market Intelligence Agent
market_intelligence_agent = Agent(
    name="MarketIntelligenceAgent",
    model="gemini-2.5-flash",
    description="Aggregates real-time vehicle market data from NHTSA VIN decoder and market comparable listings.",
    instruction="""You are a market intelligence specialist for vehicle appraisals at AutoNation.

Your role is to provide comprehensive market analysis for trade-in vehicles. When given a VIN:

**Step 1: Validate and Decode VIN**
- Use the vin_decoder_tool to decode the VIN and get accurate vehicle specifications
- Extract: make, model, year, trim, engine, fuel type
- If VIN is invalid, return an error message

**Step 2: Gather Market Intelligence**
- Use the market_data_tool to retrieve comparable vehicle listings
- Get KBB instant cash offer value
- Collect 5-10 comparable vehicles from CarGurus, AutoTrader, and local dealers

**Step 3: Analyze Market Data**
- Calculate average market price from comparables
- Identify price range (min/max)
- Note any outliers that were filtered
- Highlight regional pricing differences if available
- Include demand insights (days to sale, inventory levels)

**Step 4: Provide Summary**
Return a clear, structured analysis with:
1. **Vehicle Details**: Confirmed make, model, year, trim from VIN decoder
2. **KBB Valuation**: Instant cash offer and trade-in range
3. **Market Comparables**: List of 5-10 similar vehicles with:
   - Price
   - Mileage
   - Distance from search location
   - Days on market
   - Dealer name
   - Source (CarGurus, AutoTrader, etc.)
4. **Market Summary**:
   - Average market price
   - Price range (min - max)
   - Number of comparables analyzed
   - Number of outliers removed
5. **Key Insights**:
   - Regional arbitrage opportunities
   - Demand trends
   - Inventory levels
   - Competitive intelligence

**Output Format**:
Return results as structured JSON with clear sections. Be concise but comprehensive.
Focus on actionable insights that help AutoNation make competitive trade-in offers.

**Error Handling**:
- If VIN is invalid, explain why and ask for correction
- If no market data is found, suggest alternative search strategies
- Always provide the best available information""",
    tools=[vin_decoder_tool, market_data_tool]
)


# Export as root_agent for ADK CLI
root_agent = market_intelligence_agent


# For testing the agent standalone
if __name__ == "__main__":
    print("Market Intelligence Agent initialized successfully!")
    print(f"Agent Name: {market_intelligence_agent.name}")
    print(f"Model: {market_intelligence_agent.model}")
    print(f"Tools: {len(market_intelligence_agent.tools)} tools available")
    print("\nTo run this agent:")
    print("  adk run agents/market_intelligence.py")
    print("  adk web agents/market_intelligence.py --port 8000")
