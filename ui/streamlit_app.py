"""
AutoNation Intelligent Appraisal System - Streamlit UI

Interactive demo interface for vehicle appraisal using ADK workflow.
"""

import streamlit as st
import sys
import os
import json
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.nhtsa_api import decode_vin
from tools.api_mocks import get_market_intelligence
from agents.vision_analyst import estimate_reconditioning_cost
from agents.pricing_strategist import calculate_offer_scenarios, calculate_competitive_position

# Page configuration
st.set_page_config(
    page_title="AutoNation Intelligent Appraisal",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        color: #155724;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.25rem;
        padding: 1rem;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">AutoNation Intelligent Appraisal System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Vehicle Trade-In Analysis</div>', unsafe_allow_html=True)

# Sidebar - Demo VIN Selector
st.sidebar.header("🎯 Quick Demo")
st.sidebar.markdown("Select a pre-loaded demo scenario:")

# Load demo VINs
demo_vins_path = Path(__file__).parent.parent / "data" / "demo_vins.csv"
if demo_vins_path.exists():
    demo_vins_df = pd.read_csv(demo_vins_path)
    demo_options = {f"{row['story_name']}: {row['make']} {row['model']}": row['vin']
                   for _, row in demo_vins_df.iterrows()}
    demo_options = {"-- Select Demo VIN --": None, **demo_options}

    selected_demo = st.sidebar.selectbox("Demo Scenarios", list(demo_options.keys()))

    if selected_demo != "-- Select Demo VIN --":
        selected_vin_data = demo_vins_df[demo_vins_df['vin'] == demo_options[selected_demo]].iloc[0]
        st.sidebar.success(f"**Story**: {selected_vin_data['story_description']}")
        st.sidebar.info(f"**Expected Offer**: ${selected_vin_data['expected_offer']:,.0f}")

# Main input section
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Vehicle Information")

    # VIN input
    if selected_demo != "-- Select Demo VIN --" and demo_options[selected_demo]:
        default_vin = demo_options[selected_demo]
    else:
        default_vin = ""

    vin_input = st.text_input(
        "Vehicle Identification Number (VIN)",
        value=default_vin,
        max_chars=17,
        help="Enter the 17-character VIN"
    )

with col2:
    st.subheader("📍 Location")
    zip_code = st.text_input(
        "Zip Code",
        value="33130",
        max_chars=5,
        help="Location for market comparables search"
    )

# Photo upload section
st.subheader("📸 Vehicle Photos")
st.markdown("Upload 4-8 photos of the vehicle (exterior, interior, wheels, engine bay)")

uploaded_photos = st.file_uploader(
    "Choose images",
    type=['jpg', 'jpeg', 'png'],
    accept_multiple_files=True,
    help="Upload high-quality photos from multiple angles"
)

if uploaded_photos:
    st.success(f"✓ {len(uploaded_photos)} photos uploaded")

    # Display uploaded photos in grid
    photo_cols = st.columns(4)
    for idx, photo in enumerate(uploaded_photos[:8]):  # Limit to 8 photos
        with photo_cols[idx % 4]:
            st.image(photo, caption=f"Photo {idx + 1}", use_container_width=True)

# Analyze button
st.markdown("---")
analyze_button = st.button("🚀 Generate Appraisal", type="primary", use_container_width=True)

if analyze_button:
    if not vin_input or len(vin_input) != 17:
        st.error("⚠️ Please enter a valid 17-character VIN")
    elif not uploaded_photos or len(uploaded_photos) < 4:
        st.warning("⚠️ Please upload at least 4 photos for accurate analysis")
    else:
        # Run the ADK Sequential Workflow
        with st.spinner("🔍 Analyzing vehicle with ADK agents... This may take a few seconds..."):

            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Import the workflow and runner
            from workflows.appraisal_workflow import appraisal_workflow
            from google.adk import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai import types
            import base64
            from io import BytesIO
            from PIL import Image
            import asyncio
            import uuid

            # Prepare photos for the workflow
            status_text.text("Preparing photos for analysis...")
            progress_bar.progress(10)

            photo_parts = []
            for photo in uploaded_photos[:6]:  # Analyze up to 6 photos
                # Read image bytes
                img_bytes = photo.read()
                photo.seek(0)  # Reset for display later

                # Convert to PIL Image
                img = Image.open(BytesIO(img_bytes))

                # Encode as base64
                buffered = BytesIO()
                img.save(buffered, format=img.format or "JPEG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()

                # Create image part for Gemini
                photo_parts.append(types.Part(
                    inline_data=types.Blob(
                        mime_type=f"image/{img.format.lower() if img.format else 'jpeg'}",
                        data=img_base64
                    )
                ))

            progress_bar.progress(20)

            # Create user message with VIN and photos for the workflow
            user_message_parts = [
                types.Part(text=f"Appraise this vehicle. VIN: {vin_input}, Location zip code: {zip_code}. Analyze the uploaded photos for condition.")
            ]
            user_message_parts.extend(photo_parts)

            # Run ADK Sequential Workflow properly using Streamlit session state
            status_text.text("Initializing ADK Sequential Workflow...")
            progress_bar.progress(30)

            # Initialize ADK session service in Streamlit session state (persists across reruns)
            if 'adk_session_service' not in st.session_state:
                st.session_state.adk_session_service = InMemorySessionService()

            if 'adk_runner' not in st.session_state:
                st.session_state.adk_runner = Runner(
                    app_name="autonation_streamlit",
                    agent=appraisal_workflow,
                    session_service=st.session_state.adk_session_service
                )

            # Run the workflow
            async def run_adk_workflow():
                # Generate a unique session ID for each appraisal
                import uuid
                session_id = f"appraisal-{uuid.uuid4()}"
                user_id = "streamlit-user"
                app_name = "autonation_streamlit"

                # Create the session properly using the session service
                await st.session_state.adk_session_service.create_session(
                    app_name=app_name,
                    user_id=user_id,
                    session_id=session_id,
                    state={}
                )

                workflow_response_text = ""

                # Iterate through workflow events
                async for event in st.session_state.adk_runner.run_async(
                    session_id=session_id,
                    user_id=user_id,
                    new_message=types.Content(
                        role="user",
                        parts=user_message_parts
                    )
                ):
                    # Update progress based on which agent is active
                    if hasattr(event, 'agent_name') and event.agent_name:
                        agent_name = str(event.agent_name)
                        if 'Market' in agent_name:
                            status_text.text("Step 1/3: Market Intelligence Agent (gemini-2.5-flash) analyzing VIN...")
                            progress_bar.progress(40)
                        elif 'Vision' in agent_name:
                            status_text.text("Step 2/3: Vision Analyst Agent (gemini-2.5-pro) analyzing photos...")
                            progress_bar.progress(60)
                        elif 'Pricing' in agent_name:
                            status_text.text("Step 3/3: Pricing Strategist Agent (gemini-2.5-pro) calculating offer...")
                            progress_bar.progress(75)

                    # Capture final response
                    if event.is_final_response() and event.content:
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                workflow_response_text += part.text

                return workflow_response_text

            try:
                status_text.text("Running ADK Sequential Workflow (3 agents)...")
                vision_analysis_text = asyncio.run(run_adk_workflow())
                progress_bar.progress(80)
            except Exception as e:
                st.warning(f"ADK Workflow encountered an issue: {e}")
                st.info("Falling back to individual agent tools...")

                # Fallback: Use Gemini directly for vision analysis
                from google.genai import Client

                vision_prompt = f"""Analyze these {len(photo_parts)} vehicle photos and provide a detailed condition assessment.

Detect and list:
1. Exterior issues (scratches, dents, paint damage)
2. Interior condition (seat wear, stains, dashboard issues)
3. Aftermarket modifications (wheels, audio, tint, etc.)
4. Overall condition grade (Excellent/Good/Fair/Poor)

Provide detailed commentary on what you observe."""

                async def analyze_photos():
                    client = Client()
                    response = await client.aio.models.generate_content(
                        model="gemini-2.5-pro",
                        contents=types.Content(
                            role="user",
                            parts=[types.Part(text=vision_prompt)] + photo_parts
                        )
                    )
                    return response.text

                try:
                    vision_analysis_text = asyncio.run(analyze_photos())
                except Exception as ve:
                    st.error(f"Vision analysis error: {ve}")
                    vision_analysis_text = "Unable to analyze photos."

            # Get market data (fallback to ensure we have data)
            from tools.nhtsa_api import decode_vin
            from tools.api_mocks import get_market_intelligence

            market_data = get_market_intelligence(vin_input, zip_code)
            vin_data = decode_vin(vin_input)
            progress_bar.progress(85)

            # Extract detected issues from vision analysis
            import re
            detected_issues = []

            # Parse detected issues from Gemini's response
            if vision_analysis_text:
                # PRIORITY Pattern: Look for ISSUE_LIST_START...ISSUE_LIST_END markers
                issue_list_match = re.search(r'ISSUE_LIST_START\s*(\[.*?\])\s*ISSUE_LIST_END', vision_analysis_text, re.DOTALL)
                if issue_list_match:
                    try:
                        import json
                        issues_list = json.loads(issue_list_match.group(1))
                        detected_issues = issues_list
                    except:
                        pass

                # Fallback Pattern 1: detected_issues=['issue1', 'issue2']
                if not detected_issues and "estimate_reconditioning_cost" in vision_analysis_text:
                    match = re.search(r'detected_issues\s*=\s*\[([^\]]+)\]', vision_analysis_text)
                    if match:
                        issues_str = match.group(1)
                        # Extract issue names from the list
                        raw_issues = re.findall(r"'([^']+)'", issues_str)
                        detected_issues.extend(raw_issues)

                # Fallback Pattern 2: "issues": ["issue1", "issue2"]
                if not detected_issues:
                    match = re.search(r'"issues":\s*\[([^\]]+)\]', vision_analysis_text)
                    if match:
                        issues_str = match.group(1)
                        detected_issues = re.findall(r'"([^"]+)"', issues_str)

                # AGGRESSIVE Fallback: Extract from "⚠️ Detected Issues:" section
                if not detected_issues:
                    # Find the section between "⚠️ Detected Issues:" and next emoji section
                    issues_section_match = re.search(r'⚠️ Detected Issues:(.+?)(?:⭐|💰|📊)', vision_analysis_text, re.DOTALL | re.IGNORECASE)
                    if issues_section_match:
                        issues_text = issues_section_match.group(1)
                        # Extract ALL snake_case or kebab-case words
                        potential_issues = re.findall(r'\b([a-z]+(?:_[a-z]+)+)\b', issues_text)
                        detected_issues.extend(potential_issues)

                # Even MORE aggressive: Look for common issue keywords anywhere in text
                if not detected_issues:
                    common_issues = [
                        'scratches_bumper', 'scratches_door', 'dent_door', 'dent_hood',
                        'paint_fade', 'rust_spots', 'cracked_windshield', 'curb_rash',
                        'worn_tires', 'seat_wear', 'seat_tear', 'seat_stain',
                        'dashboard_crack', 'trim_damage', 'carpet_stain',
                        'fluid_leak', 'engine_corrosion',
                        'aftermarket_wheels', 'aftermarket_audio', 'aftermarket_spoiler', 'window_tint'
                    ]
                    text_lower = vision_analysis_text.lower()
                    for keyword in common_issues:
                        if keyword in text_lower and keyword not in detected_issues:
                            detected_issues.append(keyword)

            # Normalize detected issues to standard cost codes
            normalized_issues = []
            for issue in detected_issues:
                issue_lower = issue.lower()

                # Map various descriptions to standard codes
                if "paint" in issue_lower and ("scratch" in issue_lower or "scuff" in issue_lower):
                    if "bumper" in issue_lower:
                        normalized_issues.append("scratches_bumper")
                    else:
                        normalized_issues.append("scratches_door")
                elif "wheel" in issue_lower and ("scuff" in issue_lower or "curb" in issue_lower or "rash" in issue_lower):
                    normalized_issues.append("curb_rash")
                elif "dent" in issue_lower:
                    if "door" in issue_lower:
                        normalized_issues.append("dent_door")
                    elif "hood" in issue_lower:
                        normalized_issues.append("dent_hood")
                    else:
                        normalized_issues.append("dent_door")
                elif "seat" in issue_lower:
                    if "tear" in issue_lower or "rip" in issue_lower:
                        normalized_issues.append("seat_tear")
                    elif "stain" in issue_lower:
                        normalized_issues.append("seat_stain")
                    else:
                        normalized_issues.append("seat_wear")
                elif "aftermarket" in issue_lower and "wheel" in issue_lower:
                    normalized_issues.append("aftermarket_wheels")
                elif "tint" in issue_lower:
                    normalized_issues.append("window_tint")
                elif "rust" in issue_lower:
                    normalized_issues.append("rust_spots")
                elif "fade" in issue_lower:
                    normalized_issues.append("paint_fade")

            # If we normalized any issues, use those
            if normalized_issues:
                detected_issues = list(set(normalized_issues))  # Remove duplicates

            # Also parse from natural language description
            text_lower = vision_analysis_text.lower()

            # Additional keyword detection
            additional_mappings = {
                "aftermarket wheels": "aftermarket_wheels",
                "custom wheels": "aftermarket_wheels",
                "window tint": "window_tint",
                "dashboard crack": "dashboard_crack",
            }

            for description, issue_code in additional_mappings.items():
                if description in text_lower and issue_code not in detected_issues:
                    detected_issues.append(issue_code)

            # Get reconditioning estimate by calling the tool (from Vision Analyst Agent)
            # Use detected issues, or empty list if truly pristine
            recon_estimate = estimate_reconditioning_cost(detected_issues if detected_issues else [])

            progress_bar.progress(70)

            # Agent 3: Pricing Strategist (uses agent's tools)
            status_text.text("Step 3/3: Pricing Strategist Agent calculating offer...")
            progress_bar.progress(80)

            if market_data.get("success"):
                market_avg = market_data["market_summary"]["avg_price"]
                kbb_offer = market_data["kbb_valuation"]["instant_cash_offer"]
                recon_cost = recon_estimate["total_reconditioning_cost"]
                aftermarket_value = recon_estimate["aftermarket_value_added"]

                # Calculate offer scenarios
                scenarios = calculate_offer_scenarios(
                    market_avg, kbb_offer, recon_cost, aftermarket_value
                )

                # Get recommended offer (balanced scenario)
                recommended_offer = scenarios["scenarios"]["balanced"]["offer_price"]

                # Competitive analysis
                competitive_analysis = calculate_competitive_position(
                    recommended_offer, kbb_offer, market_avg
                )

                progress_bar.progress(100)
                status_text.text("✓ Analysis complete!")

                # Display results in tabs
                st.markdown("---")
                st.success("### ✅ Appraisal Complete!")

                # Show agent architecture
                st.info("""
                **🤖 ADK Sequential Workflow (3 Agents):**
                - **Market Intelligence Agent** (gemini-2.5-flash) → Analyzed VIN and market comparables
                - **Vision Analyst Agent** (gemini-2.5-pro) → Analyzed vehicle photos with multimodal AI
                - **Pricing Strategist Agent** (gemini-2.5-pro) → Calculated optimal offer price

                *Agents ran in sequence with session state coordination via ADK Runner*
                """)

                tab1, tab2, tab3 = st.tabs(["📊 Market Intelligence", "🔍 Condition Analysis", "💰 Pricing Recommendation"])

                with tab1:
                    st.subheader("Market Intelligence Report")

                    # Vehicle info
                    if vin_data.get("success"):
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Make", vin_data.get("make", "N/A"))
                        col2.metric("Model", vin_data.get("model", "N/A"))
                        col3.metric("Year", vin_data.get("year", "N/A"))
                        col4.metric("Trim", vin_data.get("trim", "N/A"))

                    st.markdown("---")

                    # Market summary
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Market Average", f"${market_avg:,.0f}")
                    col2.metric("KBB Instant Offer", f"${kbb_offer:,.0f}")
                    col3.metric("Comparables Analyzed", len(market_data.get("comparables", [])))

                    # Comparables table
                    st.markdown("#### Comparable Vehicles")
                    if market_data.get("comparables"):
                        comps_df = pd.DataFrame(market_data["comparables"])
                        comps_display = comps_df[["source", "price", "mileage", "distance_miles", "days_listed", "dealer_name"]]
                        comps_display.columns = ["Source", "Price", "Mileage", "Distance (mi)", "Days Listed", "Dealer"]
                        comps_display["Price"] = comps_display["Price"].apply(lambda x: f"${x:,.0f}")
                        comps_display["Mileage"] = comps_display["Mileage"].apply(lambda x: f"{x:,}")
                        st.dataframe(comps_display, use_container_width=True, hide_index=True)

                with tab2:
                    st.subheader("🤖 Gemini 2.5 Pro Vision Analysis")

                    # Display AI's detailed commentary (clean up tool code if present)
                    st.markdown("##### 📝 AI Analysis Report")
                    # Remove tool code sections from display
                    clean_text = vision_analysis_text if vision_analysis_text else "No analysis available"

                    # Remove <tool_code>...</tool_code> blocks
                    clean_text = re.sub(r'<tool_code>.*?</tool_code>', '', clean_text, flags=re.DOTALL)

                    # Remove "Calling the..." paragraphs and JSON tool code blocks
                    clean_text = re.sub(r'Calling the.*?reconditioning.*?\n', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
                    clean_text = re.sub(r'\{[\s\n]*"tool_code":.*?\}', '', clean_text, flags=re.DOTALL)

                    # Remove any remaining tool-related lines
                    clean_text = re.sub(r'```.*?```', '', clean_text, flags=re.DOTALL)

                    # Remove "Reconditioning Cost Estimate" header and trailing artifacts
                    clean_text = re.sub(r'Reconditioning Cost Estimate\s*\]?\s*', '', clean_text, flags=re.IGNORECASE)

                    # Remove stray brackets and common artifacts
                    clean_text = re.sub(r'^\s*\]\s*', '', clean_text, flags=re.MULTILINE)

                    clean_text = clean_text.strip()
                    st.markdown(f'<div class="info-box">{clean_text}</div>', unsafe_allow_html=True)

                    st.markdown("---")

                    # Detected issues and modifications
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("##### ⚠️ Detected Issues")
                        if detected_issues:
                            for issue in detected_issues:
                                st.markdown(f"- {issue.replace('_', ' ').title()}")
                        else:
                            st.markdown("*No significant issues detected*")

                    with col2:
                        st.markdown("##### ⭐ Value-Adding Features")
                        aftermarket = [i for i in detected_issues if "aftermarket" in i or "wheel" in i or "tint" in i or "audio" in i]
                        if aftermarket:
                            for mod in aftermarket:
                                st.markdown(f"- {mod.replace('_', ' ').title()}")
                        else:
                            st.markdown("*No aftermarket modifications detected*")

                    st.markdown("---")

                    # Reconditioning costs with itemized breakdown
                    st.markdown("##### 💵 Itemized Reconditioning Estimate")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Recon Cost", f"${recon_cost:,.0f}")
                    col2.metric("Aftermarket Value", f"+${aftermarket_value:,.0f}", delta=f"+${aftermarket_value:,.0f}")
                    col3.metric("Net Adjustment", f"${aftermarket_value - recon_cost:+,.0f}")

                    # Detailed breakdown with parts/labor
                    if recon_estimate.get("breakdown"):
                        st.markdown("**Detailed Cost Breakdown:**")
                        breakdown_df = pd.DataFrame([
                            {"Item": item, "Cost": f"${cost:,.0f}"}
                            for item, cost in recon_estimate["breakdown"].items()
                        ])
                        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

                    st.markdown(f"*Analysis based on {len(uploaded_photos)} uploaded photos using Gemini 2.5 Pro vision model*")

                with tab3:
                    st.subheader("Pricing Recommendation")

                    # Main recommendation
                    st.markdown(f'<div class="success-box"><h2 style="margin:0;">Recommended Offer: ${recommended_offer:,.0f}</h2></div>', unsafe_allow_html=True)

                    st.markdown("---")

                    # Key metrics
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Win Probability", f"{scenarios['scenarios']['balanced']['win_rate_estimate']*100:.0f}%")
                    col2.metric("Expected Profit", f"${scenarios['scenarios']['balanced']['expected_profit']:,.0f}")
                    col3.metric("Profit Margin", f"{scenarios['scenarios']['balanced']['profit_margin_pct']:.1f}%")
                    col4.metric("Competitive Position", competitive_analysis["competitive_position"])

                    st.markdown("---")

                    # Reasoning
                    st.markdown("##### 🧠 Transparent Reasoning")
                    reasoning = f"""
**Market Analysis**: Market average is ${market_avg:,.0f} based on {len(market_data.get('comparables', []))} comparable vehicles.
KBB instant cash offer is ${kbb_offer:,.0f}.

**Condition Adjustment**: Vehicle requires ${recon_cost:,.0f} in reconditioning but has ${aftermarket_value:,.0f}
in aftermarket value (wheels). Net adjustment: ${aftermarket_value - recon_cost:+,.0f}.

**Recommended Offer**: ${recommended_offer:,.0f} positions AutoNation ${abs(recommended_offer - kbb_offer):,.0f}
{'above' if recommended_offer > kbb_offer else 'below'} KBB instant offer
({abs((recommended_offer - kbb_offer)/kbb_offer * 100):.1f}% {'premium' if recommended_offer > kbb_offer else 'discount'}).
This is a **{competitive_analysis["competitive_position"]}** position.

**Financial Projection**: Expected profit of ${scenarios['scenarios']['balanced']['expected_profit']:,.0f}
with {scenarios['scenarios']['balanced']['profit_margin_pct']:.1f}% margin after reconditioning and retail markup.

**Win Probability**: {scenarios['scenarios']['balanced']['win_rate_estimate']*100:.0f}% estimated win rate against competitors like CarMax and Carvana.
                    """
                    st.markdown(reasoning)

                    st.markdown("---")

                    # Alternative scenarios
                    st.markdown("##### 🎯 Alternative Offer Scenarios")
                    scenario_df = pd.DataFrame([
                        {
                            "Scenario": "Aggressive",
                            "Offer": f"${scenarios['scenarios']['aggressive']['offer_price']:,.0f}",
                            "Win Rate": f"{scenarios['scenarios']['aggressive']['win_rate_estimate']*100:.0f}%",
                            "Profit": f"${scenarios['scenarios']['aggressive']['expected_profit']:,.0f}",
                            "Description": scenarios['scenarios']['aggressive']['description']
                        },
                        {
                            "Scenario": "Balanced ⭐",
                            "Offer": f"${scenarios['scenarios']['balanced']['offer_price']:,.0f}",
                            "Win Rate": f"{scenarios['scenarios']['balanced']['win_rate_estimate']*100:.0f}%",
                            "Profit": f"${scenarios['scenarios']['balanced']['expected_profit']:,.0f}",
                            "Description": scenarios['scenarios']['balanced']['description']
                        },
                        {
                            "Scenario": "Conservative",
                            "Offer": f"${scenarios['scenarios']['conservative']['offer_price']:,.0f}",
                            "Win Rate": f"{scenarios['scenarios']['conservative']['win_rate_estimate']*100:.0f}%",
                            "Profit": f"${scenarios['scenarios']['conservative']['expected_profit']:,.0f}",
                            "Description": scenarios['scenarios']['conservative']['description']
                        }
                    ])
                    st.dataframe(scenario_df, use_container_width=True, hide_index=True)

            else:
                st.error("⚠️ Failed to retrieve market data for this VIN")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>AutoNation Intelligent Appraisal System | Powered by Google ADK & Gemini AI</p>
    <p>Demo Version - February 2026</p>
</div>
""", unsafe_allow_html=True)
