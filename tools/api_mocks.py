"""
Mock API tools for KBB, CarGurus, and other third-party services.
Uses pre-cached demo data for fast, reliable demos.
"""

import json
import os
from typing import Dict, Any, Optional


def load_mock_market_data() -> Dict[str, Any]:
    """Load mock market comparables from JSON file."""
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "mock_market_comps.json"
    )
    with open(data_path, 'r') as f:
        return json.load(f)


def get_kbb_instant_cash_offer(vin: str) -> Dict[str, Any]:
    """
    Mock KBB Instant Cash Offer API.

    Args:
        vin: Vehicle Identification Number

    Returns:
        Dictionary with KBB valuation data
    """
    mock_data = load_mock_market_data()

    if vin in mock_data:
        return {
            "success": True,
            "vin": vin,
            "data": mock_data[vin]["kbb_data"]
        }

    # Fallback for unknown VINs
    return {
        "success": False,
        "error": "VIN not found in demo data",
        "vin": vin
    }


def get_cargurus_comparables(
    vin: str,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    zip_code: str = "33130"
) -> Dict[str, Any]:
    """
    Mock CarGurus comparable listings API.

    Args:
        vin: Vehicle Identification Number
        make: Vehicle make (optional, for fallback)
        model: Vehicle model (optional, for fallback)
        year: Vehicle year (optional, for fallback)
        zip_code: Search location zip code

    Returns:
        Dictionary with comparable vehicle listings
    """
    mock_data = load_mock_market_data()

    if vin in mock_data:
        vehicle_data = mock_data[vin]
        return {
            "success": True,
            "vin": vin,
            "vehicle_info": vehicle_data["vehicle_info"],
            "comparables": vehicle_data["comparables"],
            "market_summary": vehicle_data["market_summary"],
            "search_params": {
                "zip_code": zip_code,
                "radius_miles": 25
            }
        }

    # Fallback for unknown VINs
    return {
        "success": False,
        "error": "VIN not found in demo data",
        "vin": vin,
        "note": "For production, would search by make/model/year"
    }


def get_market_intelligence(vin: str, zip_code: str = "33130") -> Dict[str, Any]:
    """
    Combined market intelligence from multiple sources.

    Args:
        vin: Vehicle Identification Number
        zip_code: Search location

    Returns:
        Comprehensive market data combining KBB, CarGurus, and other sources
    """
    mock_data = load_mock_market_data()

    if vin not in mock_data:
        return {
            "success": False,
            "error": "VIN not found in demo data",
            "vin": vin
        }

    vehicle_data = mock_data[vin]

    # Compile comprehensive market intelligence
    response = {
        "success": True,
        "vin": vin,
        "vehicle_info": vehicle_data["vehicle_info"],
        "kbb_valuation": vehicle_data["kbb_data"],
        "comparables": vehicle_data["comparables"],
        "market_summary": vehicle_data["market_summary"]
    }

    # Add regional data if available
    if "regional_data" in vehicle_data:
        response["regional_insights"] = vehicle_data["regional_data"]

    # Add demand insights if available
    if "demand_insights" in vehicle_data:
        response["demand_insights"] = vehicle_data["demand_insights"]

    return response


def filter_outliers(comparables: list, std_dev_threshold: float = 2.0) -> Dict[str, Any]:
    """
    Filter outlier listings from comparable vehicles.

    Args:
        comparables: List of comparable vehicle dictionaries
        std_dev_threshold: Number of standard deviations for outlier detection

    Returns:
        Filtered comparables and statistics
    """
    if not comparables:
        return {
            "filtered_comparables": [],
            "outliers_removed": 0,
            "avg_price": 0
        }

    import statistics

    prices = [comp["price"] for comp in comparables]

    if len(prices) < 3:
        # Not enough data for outlier detection
        return {
            "filtered_comparables": comparables,
            "outliers_removed": 0,
            "avg_price": statistics.mean(prices)
        }

    mean_price = statistics.mean(prices)
    std_dev = statistics.stdev(prices)

    # Filter outliers
    filtered = [
        comp for comp in comparables
        if abs(comp["price"] - mean_price) <= (std_dev_threshold * std_dev)
    ]

    outliers_removed = len(comparables) - len(filtered)
    new_avg = statistics.mean([c["price"] for c in filtered]) if filtered else 0

    return {
        "filtered_comparables": filtered,
        "outliers_removed": outliers_removed,
        "avg_price": new_avg,
        "original_avg": mean_price,
        "std_dev": std_dev
    }
