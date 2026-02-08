"""
NHTSA (National Highway Traffic Safety Administration) VIN Decoder API.
This is a FREE real API with no authentication required.
https://vpic.nhtsa.dot.gov/api/
"""

import requests
from typing import Dict, Any, Optional


def decode_vin(vin: str) -> Dict[str, Any]:
    """
    Decode a VIN using the free NHTSA API.

    Args:
        vin: Vehicle Identification Number (17 characters)

    Returns:
        Dictionary with vehicle specifications
    """
    if not vin or len(vin) != 17:
        return {
            "success": False,
            "error": "Invalid VIN format. VIN must be 17 characters.",
            "vin": vin
        }

    # NHTSA VIN Decoder API endpoint
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract key vehicle information
        results = data.get("Results", [])

        # Parse results into a clean dictionary
        vehicle_info = {}
        for item in results:
            variable = item.get("Variable", "")
            value = item.get("Value", "")

            # Only include non-null values
            if value and value not in ["", "Not Applicable"]:
                vehicle_info[variable] = value

        # Extract commonly used fields
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
            "plant_city": vehicle_info.get("Plant City", "Unknown"),
            "vehicle_type": vehicle_info.get("Vehicle Type", "Unknown"),
            "full_data": vehicle_info  # Include all decoded fields
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"API request failed: {str(e)}",
            "vin": vin
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to decode VIN: {str(e)}",
            "vin": vin
        }


def validate_vin(vin: str) -> Dict[str, Any]:
    """
    Validate a VIN and return basic vehicle info.

    Args:
        vin: Vehicle Identification Number

    Returns:
        Validation result with basic vehicle info
    """
    result = decode_vin(vin)

    if not result["success"]:
        return {
            "valid": False,
            "error": result.get("error", "Unknown error"),
            "vin": vin
        }

    # Check if we got valid vehicle data
    make = result.get("make", "Unknown")
    model = result.get("model", "Unknown")

    if make == "Unknown" or model == "Unknown":
        return {
            "valid": False,
            "error": "VIN decoded but vehicle details not found",
            "vin": vin
        }

    return {
        "valid": True,
        "vin": vin,
        "make": make,
        "model": model,
        "year": result.get("year", "Unknown"),
        "trim": result.get("trim", "Unknown")
    }


def get_vehicle_specs(vin: str) -> Dict[str, Any]:
    """
    Get detailed vehicle specifications from VIN.

    Args:
        vin: Vehicle Identification Number

    Returns:
        Detailed vehicle specifications
    """
    return decode_vin(vin)
