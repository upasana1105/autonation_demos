"""
Market Intelligence Agent for AutoNation Vehicle Appraisal (Standalone for Deployment).
All dependencies inlined to avoid module import issues.
"""

from google.adk.agents.llm_agent import Agent
from typing import Dict, Any
import requests
import json


# Inlined NHTSA API tool
def decode_vin(vin: str) -> Dict[str, Any]:
    """Decode a VIN using the free NHTSA API."""
    if not vin or len(vin) != 17:
        return {
            "success": False,
            "error": "Invalid VIN format. VIN must be 17 characters.",
            "vin": vin
        }

    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get("Results", [])

        vehicle_info = {}
        for item in results:
            variable = item.get("Variable", "")
            value = item.get("Value", "")
            if value and value not in ["", "Not Applicable"]:
                vehicle_info[variable] = value

        return {
            "success": True,
            "vin": vin,
            "make": vehicle_info.get("Make", "Unknown"),
            "model": vehicle_info.get("Model", "Unknown"),
            "year": vehicle_info.get("Model Year", "Unknown"),
            "trim": vehicle_info.get("Trim", "Unknown"),
            "body_class": vehicle_info.get("Body Class", "Unknown"),
            "engine": vehicle_info.get("Engine Model", "Unknown"),
            "fuel_type": vehicle_info.get("Fuel Type - Primary", "Unknown"),
            "manufacturer": vehicle_info.get("Manufacturer Name", "Unknown"),
            "full_data": vehicle_info
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to decode VIN: {str(e)}",
            "vin": vin
        }


# Inlined mock market data tool
MOCK_MARKET_DATA = {
    "1HGBH41JXMN109186": {
        "vehicle_info": {
            "make": "Honda",
            "model": "Accord",
            "year": 2022,
            "trim": "EX-L"
        },
        "kbb_data": {
            "instant_cash_offer": 23800,
            "trade_in_low": 23000,
            "trade_in_high": 25000
        },
        "comparables": [
            {"source": "cargurus", "price": 24500, "mileage": 32000, "distance_miles": 8},
            {"source": "cargurus", "price": 24200, "mileage": 35000, "distance_miles": 12},
            {"source": "autotrader", "price": 25100, "mileage": 28000, "distance_miles": 15},
            {"source": "carfax", "price": 24800, "mileage": 30000, "distance_miles": 10},
            {"source": "cargurus", "price": 24600, "mileage": 33000, "distance_miles": 9}
        ],
        "market_summary": {
            "avg_price": 24640,
            "min_price": 24200,
            "max_price": 25100,
            "days_on_market_avg": 18
        }
    }
}


def get_market_intelligence(vin: str, zip_code: str = "33130") -> Dict[str, Any]:
    """Get mock market intelligence data for a VIN."""
    data = MOCK_MARKET_DATA.get(vin)
    if not data:
        return {
            "success": False,
            "error": f"No market data found for VIN {vin}",
            "vin": vin
        }

    return {
        "success": True,
        "vin": vin,
        "zip_code": zip_code,
        **data
    }


# Tool wrappers for ADK
def vin_decoder_tool(vin: str) -> Dict[str, Any]:
    """
    Decodes a VIN using the NHTSA API to get vehicle specifications.

    Args:
        vin: Vehicle Identification Number (17 characters)
    """
    return decode_vin(vin)


def market_data_tool(vin: str, zip_code: str = "33130") -> Dict[str, Any]:
    """
    Retrieves comprehensive market intelligence for a vehicle.

    Args:
        vin: Vehicle Identification Number
        zip_code: Zip code for regional pricing (default: Miami 33130)
    """
    return get_market_intelligence(vin, zip_code)


# Create the agent
root_agent = Agent(
    name="MarketIntelligenceAgent",
    model="gemini-2.5-flash",
    description="Aggregates real-time vehicle market data from NHTSA and comparable listings",
    instruction="""You are a market intelligence specialist for vehicle appraisals.

When given a VIN, follow these steps:

1. **Decode the VIN** using vin_decoder_tool to get accurate vehicle specifications
2. **Retrieve market data** using market_data_tool to get comparable listings
3. **Analyze the data** to provide a comprehensive market summary

Return your analysis with:
- Vehicle specifications (make, model, year, trim)
- 5-10 comparable vehicles with prices and locations
- Average market price calculation
- Price range (min/max from comparables)
- KBB Instant Cash Offer value
- Regional market insights

Be concise and data-focused. Format prices as currency ($XX,XXX).
""",
    tools=[vin_decoder_tool, market_data_tool]
)
