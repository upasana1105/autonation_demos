"""
AutoNation Vehicle Appraisal Workflow

Sequential workflow that orchestrates three specialized agents:
1. Market Intelligence Agent - Gathers market data and comparable vehicles
2. Vision Analyst Agent - Analyzes photos to detect condition and modifications
3. Pricing Strategist Agent - Generates optimal offer with transparent reasoning

This workflow provides end-to-end vehicle appraisal in under 10 seconds.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize Vertex AI
import vertexai
from dotenv import load_dotenv

load_dotenv()
vertexai.init(
    project=os.getenv("GCP_PROJECT_ID", "uppdemos"),
    location=os.getenv("GCP_REGION", "us-central1")
)

from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.llm_agent import Agent

# Import individual agents
from agents.market_intelligence import market_intelligence_agent
from agents.vision_analyst import vision_analyst_agent
from agents.pricing_strategist import pricing_strategist_agent


# Configure agents to store outputs in session state
market_agent_with_output = Agent(
    name="MarketIntelligenceAgent",
    model=market_intelligence_agent.model,
    description=market_intelligence_agent.description,
    instruction=market_intelligence_agent.instruction,
    tools=market_intelligence_agent.tools,
    output_key="market_intelligence_data"  # Store results in session state
)

vision_agent_with_output = Agent(
    name="VisionAnalystAgent",
    model=vision_analyst_agent.model,
    description=vision_analyst_agent.description,
    instruction=vision_analyst_agent.instruction + """

**IMPORTANT**: You will receive market intelligence data from a previous step:
{market_intelligence_data}

Use this context to understand the vehicle specifications when analyzing photos.""",
    tools=vision_analyst_agent.tools,
    output_key="condition_analysis_data"  # Store results in session state
)

pricing_agent_with_context = Agent(
    name="PricingStrategistAgent",
    model=pricing_strategist_agent.model,
    description=pricing_strategist_agent.description,
    instruction=pricing_strategist_agent.instruction + """

**IMPORTANT**: You have access to data from previous analysis steps:

**Market Intelligence Data**:
{market_intelligence_data}

**Condition Analysis Data**:
{condition_analysis_data}

Use ALL of this information to generate your pricing recommendation. Reference specific data points from both analyses in your reasoning.""",
    tools=pricing_strategist_agent.tools,
    output_key="pricing_recommendation"  # Final output
)


# Create the Sequential Workflow
appraisal_workflow = SequentialAgent(
    name="VehicleAppraisalWorkflow",
    sub_agents=[
        market_agent_with_output,      # Step 1: Market research
        vision_agent_with_output,      # Step 2: Condition analysis
        pricing_agent_with_context     # Step 3: Pricing strategy
    ]
)


# Export as root_agent for ADK CLI
root_agent = appraisal_workflow


# Helper function for programmatic execution
async def run_appraisal(vin: str, photos: list, zip_code: str = "33130", session_id: str = "demo-session"):
    """
    Execute the complete vehicle appraisal workflow.

    Args:
        vin: Vehicle Identification Number
        photos: List of photo file paths or base64 encoded images
        zip_code: Location for market comparables search
        session_id: Unique session identifier

    Returns:
        Complete appraisal results including market analysis, condition assessment,
        and pricing recommendation
    """
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    runner = Runner(
        app_name="autonation_appraisal",
        agent=appraisal_workflow,
        session_service=InMemorySessionService()
    )

    # Construct user message with VIN and photos
    user_message_parts = [
        types.Part(text=f"Please appraise this vehicle. VIN: {vin}, Location: {zip_code}")
    ]

    # Add photos to message
    for photo in photos:
        # Assuming photos are file paths - in production, handle base64 or URLs
        user_message_parts.append(
            types.Part(inline_data={"mime_type": "image/jpeg", "data": photo})
        )

    # Run workflow
    final_response = None
    async for event in runner.run_async(
        session_id=session_id,
        user_id="appraiser",
        new_message=types.Content(
            role="user",
            parts=user_message_parts
        )
    ):
        if event.is_final_response():
            final_response = event.content

    return final_response


# For testing the workflow standalone
if __name__ == "__main__":
    print("=" * 70)
    print("AutoNation Vehicle Appraisal Workflow")
    print("=" * 70)
    print("\nWorkflow Configuration:")
    print(f"  Name: {appraisal_workflow.name}")
    print(f"  Type: Sequential (3 agents)")
    print(f"\n  Agent Pipeline:")
    print(f"    1. Market Intelligence Agent (gemini-2.5-flash)")
    print(f"       └─ Decodes VIN, gathers market comparables")
    print(f"    2. Vision Analyst Agent (gemini-2.5-pro)")
    print(f"       └─ Analyzes photos, detects condition")
    print(f"    3. Pricing Strategist Agent (gemini-2.5-pro)")
    print(f"       └─ Generates offer with reasoning")
    print("\n" + "=" * 70)
    print("\nExpected Flow:")
    print("  User Input:")
    print("    - VIN: 1HGBH41JXMN109186")
    print("    - Photos: 4-8 vehicle images")
    print("    - Zip Code: 33130")
    print("\n  Agent 1 Output → Session State:")
    print("    market_intelligence_data: {...}")
    print("\n  Agent 2 Output → Session State:")
    print("    condition_analysis_data: {...}")
    print("\n  Agent 3 Output → Final Response:")
    print("    pricing_recommendation: {...}")
    print("=" * 70)
    print("\nTo run this workflow:")
    print("  adk run workflows/appraisal_workflow.py")
    print("  adk web workflows/appraisal_workflow.py --port 8000")
    print("=" * 70)
