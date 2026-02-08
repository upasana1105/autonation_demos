#!/usr/bin/env python3
"""
Deploy all 3 AutoNation agents to Vertex AI Agent Engine.
Agents are defined inline to avoid import issues.
"""

import os
import sys
from google.cloud import aiplatform
from google.adk.sessions import InMemorySessionService
from google.adk.agents.llm_agent import Agent
from vertexai.agent_engines import AdkApp
import vertexai.agent_engines as vae
from typing import Dict, Any, List
import requests

# Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "uppdemos")
LOCATION = os.environ.get("GCP_REGION", "us-central1")
STAGING_BUCKET = os.environ.get("STAGING_BUCKET", "gs://autonation-staging-uppdemos")

print("="*70)
print("AutoNation Agent Deployment to Vertex AI Agent Engine")
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

# Common requirements for all agents
REQUIREMENTS = [
    "google-cloud-aiplatform==1.136.0",
    "google-adk==1.23.0",
    "vertexai==1.43.0",
    "google-genai==1.62.0",
    "cloudpickle==3.1.2",
    "pydantic==2.12.5",
    "requests==2.32.5"
]

deployed_agents = {}


def deploy_agent(agent, display_name, description):
    """Deploy a single agent to Agent Engine."""
    print(f"\n📦 Deploying {display_name}...")
    print(f"   Description: {description}")

    app = AdkApp(
        agent=agent,
        session_service_builder=lambda **kwargs: InMemorySessionService()
    )

    try:
        remote_agent = vae.create(
            agent_engine=app,
            display_name=display_name,
            description=description,
            requirements=REQUIREMENTS
        )

        print(f"   ✅ Deployed successfully!")
        print(f"   Resource: {remote_agent.resource_name}")

        agent_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/{remote_agent.resource_name}"
        print(f"   URL: {agent_url}")

        return {
            "name": display_name,
            "resource_name": remote_agent.resource_name,
            "url": agent_url
        }

    except Exception as e:
        print(f"   ❌ Deployment failed: {e}")
        return None


# ============================================================================
# AGENT 1: Market Intelligence
# ============================================================================

def vin_decoder_tool(vin: str) -> Dict[str, Any]:
    """
    Decodes a VIN using the NHTSA API.

    Args:
        vin: Vehicle Identification Number (17 characters)
    """
    if not vin or len(vin) != 17:
        return {"success": False, "error": "Invalid VIN format", "vin": vin}

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
            "full_data": vehicle_info
        }
    except Exception as e:
        return {"success": False, "error": str(e), "vin": vin}


def market_data_tool(vin: str, zip_code: str = "33130") -> Dict[str, Any]:
    """
    Retrieves market intelligence for a vehicle.

    Args:
        vin: Vehicle Identification Number
        zip_code: Zip code for regional pricing
    """
    # Mock market data
    mock_data = {
        "1HGBH41JXMN109186": {
            "kbb_instant_offer": 23800,
            "avg_price": 24640,
            "min_price": 24200,
            "max_price": 25100,
            "comparables": [
                {"source": "cargurus", "price": 24500, "mileage": 32000},
                {"source": "cargurus", "price": 24200, "mileage": 35000},
                {"source": "autotrader", "price": 25100, "mileage": 28000}
            ]
        }
    }

    data = mock_data.get(vin)
    if not data:
        return {"success": False, "error": f"No market data for VIN {vin}", "vin": vin}

    return {"success": True, "vin": vin, "zip_code": zip_code, **data}


market_intelligence_agent = Agent(
    name="MarketIntelligenceAgent",
    model="gemini-2.5-flash",
    description="Aggregates real-time vehicle market data from NHTSA and comparable listings",
    instruction="""You are a market intelligence specialist for vehicle appraisals.

When given a VIN:
1. Decode the VIN using vin_decoder_tool
2. Retrieve market data using market_data_tool
3. Provide a comprehensive market summary with pricing insights

Return your analysis concisely with vehicle specs, comparable prices, and market averages.""",
    tools=[vin_decoder_tool, market_data_tool]
)


# ============================================================================
# AGENT 2: Vision Analyst
# ============================================================================

def estimate_reconditioning_cost(detected_issues: List[str]) -> Dict[str, Any]:
    """
    Estimates reconditioning costs based on detected issues.

    Args:
        detected_issues: List of issue identifiers (e.g., ["scratches_bumper", "seat_wear"])
    """
    cost_map = {
        "scratches_bumper": {"category": "paint", "cost": 450, "description": "Bumper scratch repair"},
        "scratches_door": {"category": "paint", "cost": 400, "description": "Door scratch repair"},
        "dent_door": {"category": "bodywork", "cost": 350, "description": "Door dent removal"},
        "paint_fade": {"category": "paint", "cost": 800, "description": "Paint fade correction"},
        "rust_spots": {"category": "bodywork", "cost": 600, "description": "Rust repair"},
        "seat_wear": {"category": "interior", "cost": 250, "description": "Seat wear repair"},
        "seat_tear": {"category": "interior", "cost": 400, "description": "Seat tear repair"},
        "seat_stain": {"category": "interior", "cost": 200, "description": "Seat stain removal"},
        "dashboard_crack": {"category": "interior", "cost": 350, "description": "Dashboard crack repair"},
        "aftermarket_wheels": {"category": "aftermarket", "cost": -800, "description": "Aftermarket wheels (adds value)"},
        "aftermarket_audio": {"category": "aftermarket", "cost": -300, "description": "Aftermarket audio (adds value)"},
        "window_tint": {"category": "aftermarket", "cost": -150, "description": "Window tint (adds value)"}
    }

    breakdown = {}
    total_cost = 0
    aftermarket_value = 0

    for issue in detected_issues:
        issue_key = issue.lower().replace(" ", "_")
        if issue_key in cost_map:
            item = cost_map[issue_key]
            cost = item["cost"]

            if item["category"] == "aftermarket":
                aftermarket_value += abs(cost)
            else:
                breakdown[item["description"]] = cost
                total_cost += cost

    return {
        "status": "success",
        "total_reconditioning_cost": total_cost,
        "aftermarket_value_added": aftermarket_value,
        "net_adjustment": aftermarket_value - total_cost,
        "breakdown": breakdown
    }


vision_analyst_agent = Agent(
    name="VisionAnalystAgent",
    model="gemini-2.5-pro",
    description="Analyzes vehicle photos to detect damage and aftermarket modifications",
    instruction="""You are an expert vehicle condition analyst using computer vision.

Analyze vehicle photos to detect:
1. Exterior damage (scratches, dents, paint issues)
2. Interior condition (seat wear, stains, dashboard cracks)
3. Aftermarket modifications (wheels, audio, tint)

Use estimate_reconditioning_cost tool to calculate repair costs.

Return a detailed analysis with condition grade, detected issues, and cost breakdown.""",
    tools=[estimate_reconditioning_cost]
)


# ============================================================================
# AGENT 3: Pricing Strategist
# ============================================================================

def calculate_offer_scenarios(market_avg_price: float, kbb_instant_offer: float,
                             recon_cost: float, aftermarket_value: float) -> Dict[str, Any]:
    """
    Calculates offer scenarios based on market data and vehicle condition.

    Args:
        market_avg_price: Average market price from comparables
        kbb_instant_offer: KBB Instant Cash Offer value
        recon_cost: Total reconditioning cost estimate
        aftermarket_value: Value added by aftermarket modifications
    """
    scenarios = {
        "aggressive": {"multiplier": 0.92, "win_rate": 0.65, "label": "Aggressive (Win Focused)"},
        "balanced": {"multiplier": 0.95, "win_rate": 0.78, "label": "Balanced (Recommended)"},
        "conservative": {"multiplier": 0.98, "win_rate": 0.89, "label": "Conservative (Profit Focused)"}
    }

    net_market_value = market_avg_price - recon_cost + aftermarket_value

    results = {}
    for strategy, params in scenarios.items():
        offer_price = net_market_value * params["multiplier"]
        expected_profit = market_avg_price - offer_price - recon_cost

        results[strategy] = {
            "label": params["label"],
            "offer_price": round(offer_price, 2),
            "win_rate_estimate": params["win_rate"],
            "expected_profit": round(expected_profit, 2),
            "margin_pct": round((expected_profit / offer_price) * 100, 1)
        }

    return {
        "status": "success",
        "scenarios": results,
        "market_inputs": {
            "market_avg": market_avg_price,
            "kbb_offer": kbb_instant_offer,
            "recon_cost": recon_cost,
            "aftermarket_value": aftermarket_value
        }
    }


pricing_strategist_agent = Agent(
    name="PricingStrategistAgent",
    model="gemini-2.5-pro",
    description="Generates optimal trade-in offers with transparent reasoning",
    instruction="""You are a pricing strategist for vehicle trade-ins.

Given market data and vehicle condition:
1. Use calculate_offer_scenarios to generate pricing strategies
2. Recommend the best offer based on win rate goals
3. Provide transparent reasoning for the recommendation

Return a clear recommendation with offer price, win probability, and justification.""",
    tools=[calculate_offer_scenarios]
)


# ============================================================================
# Deploy All Agents
# ============================================================================

print("\n" + "="*70)
print("STARTING DEPLOYMENT")
print("="*70)

# Deploy Agent 1
result = deploy_agent(
    market_intelligence_agent,
    "autonation-market-intelligence",
    "Aggregates real-time vehicle market data from NHTSA and comparable listings"
)
if result:
    deployed_agents["market_intelligence"] = result

# Deploy Agent 2
result = deploy_agent(
    vision_analyst_agent,
    "autonation-vision-analyst",
    "Analyzes vehicle photos to detect damage and aftermarket modifications"
)
if result:
    deployed_agents["vision_analyst"] = result

# Deploy Agent 3
result = deploy_agent(
    pricing_strategist_agent,
    "autonation-pricing-strategist",
    "Generates optimal trade-in offers with transparent reasoning"
)
if result:
    deployed_agents["pricing_strategist"] = result

# Summary
print("\n" + "="*70)
print("DEPLOYMENT SUMMARY")
print("="*70)

if len(deployed_agents) == 3:
    print("✅ All 3 agents deployed successfully!\n")

    for key, agent_info in deployed_agents.items():
        print(f"📌 {agent_info['name']}")
        print(f"   Resource: {agent_info['resource_name']}")
        print(f"   URL: {agent_info['url']}\n")

    # Save agent URLs
    with open(".env.deployed", "w") as f:
        f.write("# Deployed Agent URLs\n")
        f.write(f"MARKET_INTELLIGENCE_URL={deployed_agents['market_intelligence']['url']}\n")
        f.write(f"VISION_ANALYST_URL={deployed_agents['vision_analyst']['url']}\n")
        f.write(f"PRICING_STRATEGIST_URL={deployed_agents['pricing_strategist']['url']}\n")

    print("💾 Agent URLs saved to .env.deployed")
    print("\n📋 Next Steps:")
    print("1. Deploy Streamlit UI to Cloud Run")
    print("2. Configure UI to use deployed agent URLs")
    print("3. Test end-to-end appraisal workflow")

else:
    print(f"⚠️  Only {len(deployed_agents)}/3 agents deployed successfully")
    print("Check errors above and retry failed deployments")

print("="*70)
