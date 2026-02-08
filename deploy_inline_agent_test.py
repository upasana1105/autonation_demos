#!/usr/bin/env python3
"""
Test deployment with agent defined inline (no imports from agents package).
"""

import os
import sys
from google.cloud import aiplatform
from google.adk.sessions import InMemorySessionService
from google.adk.agents.llm_agent import Agent
from vertexai.agent_engines import AdkApp
import vertexai.agent_engines as vae
from typing import Dict, Any
import requests

# Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "uppdemos")
LOCATION = os.environ.get("GCP_REGION", "us-central1")
STAGING_BUCKET = os.environ.get("STAGING_BUCKET", "gs://autonation-staging-uppdemos")

print("="*70)
print("Testing Inline Agent Deployment")
print("="*70)
print(f"Project: {PROJECT_ID}")
print(f"Location: {LOCATION}")
print(f"Staging Bucket: {STAGING_BUCKET}")
print("="*70)

# Initialize Vertex AI
aiplatform.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET
)

# Define agent INLINE - no imports from agents package
def vin_decoder_tool(vin: str) -> Dict[str, Any]:
    """
    Decodes a VIN using the NHTSA API to get vehicle specifications.

    Args:
        vin: Vehicle Identification Number (17 characters)
    """
    if not vin or len(vin) != 17:
        return {
            "success": False,
            "error": "Invalid VIN format",
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
            "trim": vehicle_info.get("Trim", "Unknown")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "vin": vin
        }


def market_data_tool(vin: str, zip_code: str = "33130") -> Dict[str, Any]:
    """
    Retrieves market intelligence for a vehicle.

    Args:
        vin: Vehicle Identification Number
        zip_code: Zip code for regional pricing
    """
    # Mock data
    mock_data = {
        "1HGBH41JXMN109186": {
            "kbb_instant_offer": 23800,
            "avg_price": 24640,
            "comparables": 5
        }
    }

    data = mock_data.get(vin, {"error": "No data found"})
    return {"success": True, "vin": vin, **data}


# Create agent inline
root_agent = Agent(
    name="MarketIntelligenceAgent",
    model="gemini-2.5-flash",
    description="Test market intelligence agent",
    instruction="You decode VINs and provide market data. Use vin_decoder_tool to decode VINs and market_data_tool to get pricing.",
    tools=[vin_decoder_tool, market_data_tool]
)

# Required packages
requirements = [
    "google-cloud-aiplatform==1.136.0",
    "google-adk==1.23.0",
    "vertexai==1.43.0",
    "google-genai==1.62.0",
    "cloudpickle==3.1.2",
    "pydantic==2.12.5",
    "requests==2.32.5"
]

# Wrap agent in AdkApp
app = AdkApp(
    agent=root_agent,
    session_service_builder=lambda **kwargs: InMemorySessionService()
)

print("\n📦 Deploying inline agent...")

try:
    remote_agent = vae.create(
        agent_engine=app,
        display_name="autonation-inline-test",
        description="TEST: Inline agent with no external imports",
        requirements=requirements
    )

    print(f"\n✅ Deployment successful!")
    print(f"   Resource: {remote_agent.resource_name}")

    agent_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/{remote_agent.resource_name}"
    print(f"   URL: {agent_url}")

    print("\n🎯 SUCCESS! The inline agent deployment worked!")

except Exception as e:
    print(f"\n❌ Deployment failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
