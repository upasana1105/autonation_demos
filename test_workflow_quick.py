"""
Quick test of the appraisal workflow to verify it works before Streamlit testing.
"""

import asyncio
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import the workflow
from workflows.appraisal_workflow import appraisal_workflow


async def test_workflow():
    print("\n" + "="*70)
    print("Testing AutoNation Appraisal Workflow")
    print("="*70)

    # Create runner
    runner = Runner(
        app_name="test_workflow",
        agent=appraisal_workflow,
        session_service=InMemorySessionService()
    )

    # Create test message
    user_message = types.Content(
        role="user",
        parts=[types.Part(text="Appraise VIN 1HGBH41JXMN109186 in zip code 33130. The vehicle has minor scratches on the bumper and aftermarket wheels.")]
    )

    # Run workflow
    print("\n⏳ Running sequential workflow (3 agents)...\n")

    async for event in runner.run_async(
        session_id="test-session",
        user_id="tester",
        new_message=user_message
    ):
        # Show agent progress
        if hasattr(event, 'agent_name') and event.agent_name:
            print(f"  🤖 Agent active: {event.agent_name}")

        # Show final response
        if event.is_final_response():
            print("\n" + "="*70)
            print("✅ Workflow Complete!")
            print("="*70)
            print("\nFinal Response:")
            print(event.content.parts[0].text if event.content.parts else "No text response")

            # Check session state
            if hasattr(event, 'session') and event.session:
                print("\n📦 Session State Keys:")
                for key in event.session.state.keys():
                    print(f"  - {key}")

    print("\n" + "="*70)
    print("Test complete!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_workflow())
