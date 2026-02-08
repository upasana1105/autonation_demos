#!/usr/bin/env python3
"""
Test deployment of a single standalone agent to verify Agent Engine deployment works.
"""

import os
import sys
from google.cloud import aiplatform
from google.adk.sessions import InMemorySessionService
from vertexai.agent_engines import AdkApp
import vertexai.agent_engines as vae

# Import the standalone agent
from agents.market_intelligence_standalone import root_agent

# Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "uppdemos")
LOCATION = os.environ.get("GCP_REGION", "us-central1")
STAGING_BUCKET = os.environ.get("STAGING_BUCKET", "gs://autonation-staging-uppdemos")

print("="*70)
print("Testing Agent Engine Deployment - Market Intelligence Agent")
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

# Required packages - pinned versions
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

print("\n📦 Deploying Market Intelligence Agent (standalone)...")
print(f"   Requirements: {len(requirements)} packages")

try:
    remote_agent = vae.create(
        agent_engine=app,
        display_name="autonation-market-intel-test",
        description="TEST: Market intelligence agent with inlined tools",
        requirements=requirements
    )

    print(f"\n✅ Deployment successful!")
    print(f"   Resource: {remote_agent.resource_name}")

    agent_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/{remote_agent.resource_name}"
    print(f"   URL: {agent_url}")

    print("\n🎯 Test this agent with:")
    print(f'   curl -X POST "{agent_url}:query" \\')
    print(f'     -H "Authorization: Bearer $(gcloud auth print-access-token)" \\')
    print(f'     -H "Content-Type: application/json" \\')
    print(f'     -d \'{{"message": "Analyze VIN 1HGBH41JXMN109186"}}\'')

except Exception as e:
    print(f"\n❌ Deployment failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
