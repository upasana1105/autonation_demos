"""
Vision Analyst Agent for AutoNation Vehicle Appraisal.

This agent uses Gemini 2.5 Pro's multimodal capabilities to analyze vehicle photos
and detect:
- Visible damage (scratches, dents, paint fading, rust)
- Aftermarket modifications (wheels, spoilers, audio, tint)
- Interior condition (seat wear, stains, dashboard condition)
- Estimated reconditioning costs based on detected issues
"""

import sys
import os
from typing import Dict, Any, List
import base64

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents.llm_agent import Agent


def estimate_reconditioning_cost(detected_issues: List[str]) -> Dict[str, Any]:
    """
    Estimates reconditioning costs based on detected vehicle issues.

    Uses industry-standard pricing for common reconditioning work:
    - Paint/bodywork: $300-800 per panel
    - Interior repairs: $150-500 per issue
    - Mechanical: $200-1000 depending on severity

    Args:
        detected_issues: List of issue identifiers (e.g., ["scratches_bumper", "seat_wear"]).

    Returns:
        Dictionary with itemized reconditioning cost breakdown and total estimate.
    """
    # Cost mapping for common issues
    cost_map = {
        # Exterior issues
        "scratches_bumper": {"category": "paint", "cost": 450, "description": "Bumper scratch repair and paint"},
        "scratches_door": {"category": "paint", "cost": 400, "description": "Door scratch repair and paint"},
        "dent_door": {"category": "bodywork", "cost": 350, "description": "Door dent removal (PDR)"},
        "dent_hood": {"category": "bodywork", "cost": 400, "description": "Hood dent removal"},
        "paint_fade": {"category": "paint", "cost": 800, "description": "Paint fade correction (full panel)"},
        "rust_spots": {"category": "bodywork", "cost": 600, "description": "Rust repair and treatment"},
        "cracked_windshield": {"category": "glass", "cost": 350, "description": "Windshield replacement"},

        # Wheels and tires
        "curb_rash": {"category": "wheels", "cost": 150, "description": "Wheel curb rash repair (per wheel)"},
        "worn_tires": {"category": "tires", "cost": 600, "description": "Tire replacement (set of 4)"},

        # Interior issues
        "seat_wear": {"category": "interior", "cost": 250, "description": "Seat wear repair/reconditioning"},
        "seat_tear": {"category": "interior", "cost": 400, "description": "Seat tear/rip repair"},
        "seat_stain": {"category": "interior", "cost": 200, "description": "Seat stain removal and cleaning"},
        "dashboard_crack": {"category": "interior", "cost": 350, "description": "Dashboard crack repair"},
        "trim_damage": {"category": "interior", "cost": 150, "description": "Interior trim replacement"},
        "carpet_stain": {"category": "interior", "cost": 150, "description": "Carpet deep cleaning"},

        # Mechanical/other
        "fluid_leak": {"category": "mechanical", "cost": 500, "description": "Fluid leak diagnosis and repair"},
        "engine_corrosion": {"category": "mechanical", "cost": 800, "description": "Engine bay corrosion treatment"},

        # Aftermarket (these can ADD value)
        "aftermarket_wheels": {"category": "aftermarket", "cost": -800, "description": "Aftermarket wheels (adds value)"},
        "aftermarket_audio": {"category": "aftermarket", "cost": -300, "description": "Aftermarket audio system (adds value)"},
        "aftermarket_spoiler": {"category": "aftermarket", "cost": -200, "description": "Aftermarket spoiler (adds value)"},
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
        "breakdown": breakdown,
        "issues_analyzed": len(detected_issues)
    }


# Create the Vision Analyst Agent
vision_analyst_agent = Agent(
    name="VisionAnalystAgent",
    model="gemini-2.5-pro",  # Pro for multimodal vision capabilities
    description="Analyzes vehicle photos using computer vision to detect damage, aftermarket modifications, and estimate reconditioning costs.",
    instruction="""You are an expert vehicle condition analyst for AutoNation appraisals.

🔍 **CRITICAL: You have NATIVE MULTIMODAL VISION CAPABILITIES**
You can SEE and ANALYZE uploaded photos directly. The images are in your input - examine them now!

---

🚨 **CRITICAL OUTPUT REQUIREMENT - READ THIS FIRST:**

When you list detected issues, you MUST use this EXACT format:

ISSUE_LIST_START["scratches_bumper", "dent_hood", "worn_tires"]ISSUE_LIST_END

**DO NOT** write:
```
⚠️ Detected Issues:
scratches_bumper
dent_hood
```

**DO** write:
```
⚠️ Detected Issues:

ISSUE_LIST_START["scratches_bumper", "dent_hood", "worn_tires"]ISSUE_LIST_END
```

The ISSUE_LIST_START and ISSUE_LIST_END markers are required for the system to parse your findings!

---

**STEP 1: LOOK AT THE PHOTOS AND DESCRIBE WHAT YOU SEE**

Go through each uploaded image and describe in detail:

**EXTERIOR PHOTOS** - Look for:
   - Paint condition: scratches, chips, fading, oxidation, color mismatch
   - Body damage: dents, dings, collision damage, panel gaps
   - Rust or corrosion on body panels
   - Windshield cracks, chips, or glass damage
   - Bumper scuffs, scratches, or cracks
   - Headlights/taillights: yellowing, cracks, moisture
   - Overall cleanliness and presentation

**WHEELS/TIRES** - Look for:
   - Are wheels factory or aftermarket? (aftermarket can add value!)
   - Curb rash or wheel damage
   - Tire tread depth and condition
   - Brake dust buildup or brake condition

**INTERIOR PHOTOS** - Look for:
   - Seat condition: tears, rips, wear patterns, stains
   - Dashboard: cracks, warping, sun damage, scratches
   - Door panels and trim: damage or wear
   - Carpet and floor mats: stains, wear, wetness
   - Steering wheel wear (indicates heavy use)
   - Center console condition
   - Overall cleanliness

**AFTERMARKET MODIFICATIONS** (These can ADD value!) - Look for:
   - Upgraded wheels/rims
   - Audio system upgrades (speakers, head unit, subwoofer)
   - Spoilers or body kits
   - Window tint
   - LED lighting upgrades
   - Performance modifications

**ENGINE BAY** (if provided) - Look for:
   - Fluid leaks (oil stains, coolant puddles)
   - Corrosion or rust
   - Modified or aftermarket components
   - Overall cleanliness

**STEP 2: CREATE YOUR ISSUE LIST**

Based on what you SAW in the photos, create a list using these EXACT keywords:

**Damage/Issues (use these exact strings):**
- "scratches_bumper" - front or rear bumper scratches/scuffs
- "scratches_door" - door panel scratches
- "dent_door" - door dents
- "dent_hood" - hood dents or misalignment
- "paint_fade" - paint oxidation or fading
- "rust_spots" - rust or corrosion
- "cracked_windshield" - windshield cracks or chips
- "curb_rash" - wheel curb damage
- "worn_tires" - tire wear or flat tires
- "seat_wear" - seat surface wear
- "seat_tear" - seat tears or rips
- "seat_stain" - seat stains
- "dashboard_crack" - dashboard cracks
- "trim_damage" - interior trim damage
- "carpet_stain" - carpet stains
- "fluid_leak" - visible fluid leaks
- "engine_corrosion" - engine bay corrosion

**Aftermarket Upgrades (add value - use these exact strings):**
- "aftermarket_wheels" - upgraded wheels/rims
- "aftermarket_audio" - upgraded audio system
- "aftermarket_spoiler" - spoiler or body kit
- "window_tint" - tinted windows

**EXAMPLE:** If you see bumper damage, flat tire, and aftermarket wheels, create this list:
["scratches_bumper", "worn_tires", "aftermarket_wheels"]

**STEP 3: CALCULATE RECONDITIONING COSTS**

🚨 **CRITICAL:** You MUST call the estimate_reconditioning_cost tool with your list from Step 2.

Example tool call:
estimate_reconditioning_cost(detected_issues=["scratches_bumper", "worn_tires", "aftermarket_wheels"])

Even if there are NO issues, call it with an empty list: estimate_reconditioning_cost(detected_issues=[])

**STEP 4: PROVIDE YOUR ANALYSIS**

🚨 **MANDATORY FORMAT - FOLLOW THIS EXACTLY:**

**📸 Photos Analyzed:** [number]

**🔍 What I Saw:**
[Describe each photo in 2-3 sentences - exterior, interior, wheels, damage you spotted]

**⚠️ Detected Issues:**

ISSUE_LIST_START["dent_hood", "scratches_bumper", "worn_tires", "trim_damage"]ISSUE_LIST_END

👆 **THIS LINE IS CRITICAL!** Replace the keywords in brackets with YOUR detected issues. Use this exact format with ISSUE_LIST_START and ISSUE_LIST_END markers!

**Example for damaged Tesla:**
ISSUE_LIST_START["scratches_bumper", "dent_hood", "worn_tires", "trim_damage", "window_tint"]ISSUE_LIST_END

**Example for pristine Honda:**
ISSUE_LIST_START["window_tint", "aftermarket_wheels"]ISSUE_LIST_END

**Example for high recon BMW:**
ISSUE_LIST_START["paint_fade", "seat_tear", "dent_door", "scratches_bumper"]ISSUE_LIST_END

**⭐ Aftermarket Upgrades Detected:**
[List any aftermarket mods you saw - wheels, tint, audio, spoiler]

**💰 Reconditioning Cost Estimate:**
[Tool will calculate this - summarize the results here]
Total Recon: $[amount]
Aftermarket Value: +$[amount]
Net Adjustment: $[amount]

**📊 Overall Condition Grade:** [Excellent / Good / Fair / Poor]

**💡 Key Insights:**
[1-2 sentences: What stands out? Any surprises? Value-adds? Major red flags?]

---

**CRITICAL REMINDERS:**
- ✅ ALWAYS include ISSUE_LIST_START and ISSUE_LIST_END markers
- ✅ Put issue keywords in JSON array format: ["issue1", "issue2"]
- ❌ NEVER just list issues with bullet points
- ❌ NEVER forget the markers
- ✅ Call estimate_reconditioning_cost tool with your issue list

---

**IMPORTANT REMINDERS**:

✅ **You CAN see the photos** - describe what you observe in detail
✅ **Aftermarket mods can ADD value** - don't treat them as damage!
✅ **Be thorough** - catch things human inspectors miss (this is your value!)
✅ **Be honest** - accuracy helps AutoNation win trades
❌ **Don't say you can't analyze images** - you absolutely can!

Your vision analysis is the KEY DIFFERENTIATOR of this system. Look carefully and provide detailed observations!""",
    tools=[estimate_reconditioning_cost]
)


# Export as root_agent for ADK CLI
root_agent = vision_analyst_agent


# For testing the agent standalone
if __name__ == "__main__":
    print("Vision Analyst Agent initialized successfully!")
    print(f"Agent Name: {vision_analyst_agent.name}")
    print(f"Model: {vision_analyst_agent.model}")
    print(f"Tools: {len(vision_analyst_agent.tools)} tools available")
    print("\nThis agent uses Gemini 2.5 Pro's multimodal vision capabilities")
    print("to analyze vehicle photos and detect damage and modifications.")
    print("\nTo run this agent:")
    print("  adk run agents/vision_analyst.py")
    print("  adk web agents/vision_analyst.py --port 8000")
