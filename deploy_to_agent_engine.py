#!/usr/bin/env python3
"""
Deploy AutoNation Appraisal Agents to Vertex AI Agent Engine

This script deploys the 3 ADK agents to Agent Engine for production use.
"""

import os
import sys
from google.cloud import aiplatform
from vertexai.agent_engines import AdkApp
from google.adk.sessions import InMemorySessionService
import vertexai.agent_engines as vae

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import agents
from agents.market_intelligence import market_intelligence_agent
from agents.vision_analyst import vision_analyst_agent
from agents.pricing_strategist import pricing_strategist_agent

# Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "uppdemos")
LOCATION = os.environ.get("GCP_REGION", "us-central1")
STAGING_BUCKET = os.environ.get("STAGING_BUCKET", "gs://uppdemos-staging")

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

def deploy_agent(agent, display_name, description, env_vars=None):
    """Deploy a single agent to Agent Engine."""

    print(f"\n📦 Deploying {display_name}...")
    print(f"   Description: {description}")

    # Required packages - pinned versions for reproducible builds
    requirements = [
        "google-cloud-aiplatform==1.136.0",
        "google-adk==1.23.0",
        "vertexai==1.43.0",
        "google-genai==1.62.0",
        "cloudpickle==3.1.2",
        "pydantic==2.12.5",
        "google-cloud-bigquery==3.40.0",
        "google-cloud-storage==3.9.0",
        "requests==2.32.5",
        "pandas==2.2.0"
    ]

    # Wrap agent in AdkApp with InMemorySessionService
    app = AdkApp(
        agent=agent,
        session_service_builder=lambda **kwargs: InMemorySessionService()
    )

    try:
        remote_agent = vae.create(
            agent_engine=app,
            display_name=display_name,
            description=description,
            requirements=requirements
        )

        print(f"   ✅ Deployed successfully!")
        print(f"   Resource: {remote_agent.resource_name}")

        # Get agent URL
        agent_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/{remote_agent.resource_name}"
        print(f"   URL: {agent_url}")

        return {
            "name": display_name,
            "resource_name": remote_agent.resource_name,
            "url": agent_url,
            "remote_agent": remote_agent
        }

    except Exception as e:
        print(f"   ❌ Deployment failed: {e}")
        return None


def main():
    """Deploy all three AutoNation agents."""

    deployed_agents = {}

    # 1. Deploy Market Intelligence Agent
    market_agent = deploy_agent(
        agent=market_intelligence_agent,
        display_name="autonation-market-intelligence",
        description="Aggregates real-time vehicle market data from NHTSA and comparable listings",
        env_vars={
            "GCP_PROJECT_ID": PROJECT_ID,
            "BIGQUERY_DATASET": "autonation_demo"
        }
    )
    if market_agent:
        deployed_agents["market_intelligence"] = market_agent

    # 2. Deploy Vision Analyst Agent
    vision_agent = deploy_agent(
        agent=vision_analyst_agent,
        display_name="autonation-vision-analyst",
        description="Analyzes vehicle photos to detect damage and aftermarket modifications",
        env_vars={
            "GCP_PROJECT_ID": PROJECT_ID
        }
    )
    if vision_agent:
        deployed_agents["vision_analyst"] = vision_agent

    # 3. Deploy Pricing Strategist Agent
    pricing_agent = deploy_agent(
        agent=pricing_strategist_agent,
        display_name="autonation-pricing-strategist",
        description="Generates optimal trade-in offers with transparent reasoning",
        env_vars={
            "GCP_PROJECT_ID": PROJECT_ID,
            "BIGQUERY_DATASET": "autonation_demo"
        }
    )
    if pricing_agent:
        deployed_agents["pricing_strategist"] = pricing_agent

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

        # Save agent URLs to environment file
        with open(".env.deployed", "w") as f:
            f.write("# Deployed Agent URLs\n")
            f.write(f"MARKET_INTELLIGENCE_URL={deployed_agents['market_intelligence']['url']}\n")
            f.write(f"VISION_ANALYST_URL={deployed_agents['vision_analyst']['url']}\n")
            f.write(f"PRICING_STRATEGIST_URL={deployed_agents['pricing_strategist']['url']}\n")

        print("💾 Agent URLs saved to .env.deployed")
        print("\n📋 Next Steps:")
        print("1. Test agents with: python test_deployed_agents.py")
        print("2. Deploy Streamlit UI to Cloud Run")
        print("3. Configure UI to use deployed agent URLs")

    else:
        print(f"⚠️  Only {len(deployed_agents)}/3 agents deployed successfully")
        print("Check errors above and retry failed deployments")

    print("="*70)


if __name__ == "__main__":
    # Check prerequisites
    if not os.environ.get("GCP_PROJECT_ID"):
        print("⚠️  Warning: GCP_PROJECT_ID not set, using default: uppdemos")

    if not os.environ.get("STAGING_BUCKET"):
        print("⚠️  Warning: STAGING_BUCKET not set")
        print("Please create a GCS bucket and set:")
        print("  export STAGING_BUCKET=gs://your-bucket-name")
        sys.exit(1)

    main()
