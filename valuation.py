import json
from groq import Groq
from state import ClaimState

client = Groq()

INDIA_PRICING_CONTEXT = """
You are an insurance claim cost estimator for ClaimGuard AI operating in INDIA.

INDIAN AUTO REPAIR MARKET RATES (2024, INR ₹, labor included):

GLASS:
- Windshield replacement (small hatchback): ₹8,000 – ₹18,000
- Windshield replacement (sedan/SUV): ₹15,000 – ₹35,000
- Side window glass: ₹3,000 – ₹8,000
- Rear windshield: ₹6,000 – ₹15,000

BODY PANELS:
- Hood/bonnet repair (dented): ₹5,000 – ₹12,000
- Hood/bonnet replacement: ₹15,000 – ₹30,000
- Door panel repair (dented): ₹5,000 – ₹15,000
- Door panel replacement: ₹12,000 – ₹28,000
- Roof repair: ₹8,000 – ₹20,000
- Fender repair: ₹4,000 – ₹10,000
- Fender replacement: ₹8,000 – ₹18,000

BUMPERS:
- Front bumper repair: ₹3,000 – ₹8,000
- Front bumper replacement (small car): ₹5,000 – ₹12,000
- Front bumper replacement (SUV): ₹10,000 – ₹25,000
- Rear bumper repair: ₹3,000 – ₹7,000
- Rear bumper replacement: ₹5,000 – ₹15,000

LIGHTS:
- Headlight assembly (small car): ₹4,000 – ₹12,000
- Headlight assembly (LED/projector): ₹12,000 – ₹35,000
- Tail light assembly: ₹3,000 – ₹10,000
- Fog lamp: ₹1,500 – ₹5,000

MECHANICAL:
- Radiator repair/replacement: ₹8,000 – ₹20,000
- AC condenser: ₹6,000 – ₹15,000
- Engine hood latch/support: ₹2,000 – ₹6,000
- Suspension repair (per side): ₹5,000 – ₹15,000
- Wheel/tyre replacement: ₹4,000 – ₹12,000 per unit

VEHICLE SEGMENT MULTIPLIERS:
- Small hatchback (Alto, Wagon R, Celerio): base price × 1.0
- Premium hatchback (i20, Baleno, Altroz): base price × 1.4
- Sedan (Dzire, Amaze, Tigor): base price × 1.3
- Compact SUV (Brezza, Venue, Nexon): base price × 1.6
- Full SUV (Creta, Seltos, XUV700): base price × 2.0
- Luxury (Fortuner, Innova Crysta): base price × 2.5

SEVERITY PRICING GUIDELINES:
- Low: cosmetic scratches, minor dents, small chips → lower end of range
- Medium: moderate damage, partial replacement needed → mid range
- High: severe damage, full replacement needed → upper end of range
- Critical: structural damage, safety-critical parts → upper end × 1.3
"""


def predict_costs_batch(issues: list, vehicle_info: dict) -> list:
    vehicle_context = f"""
VEHICLE IN THIS CLAIM:
- Make/Model: {vehicle_info.get('make', 'Unknown')} {vehicle_info.get('model', 'Unknown')}
- Segment: {vehicle_info.get('segment', 'Small hatchback')}
- Year: {vehicle_info.get('year', 'Unknown')}
- Variant: {vehicle_info.get('variant', 'Base')}
"""

    prompt = f"""{INDIA_PRICING_CONTEXT}

{vehicle_context}

ANOMALIES TO ESTIMATE:
{json.dumps(issues, indent=2)}

INSTRUCTIONS:
- Apply the correct vehicle segment multiplier
- Use severity to pick position within price range  
- All amounts must be in INR (₹)
- Be realistic — these estimates go into official insurance claims

Respond ONLY with a valid JSON array. No markdown, no explanation.
Each object must follow this exact format:
{{"index": <int>, "estimated_cost": <float>, "part": "<part name>", "action": "repair|replace", "reasoning": "<one line>"}}

Return one entry per anomaly in the same order as input."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,  # very low for consistent pricing
        max_tokens=1024,
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())


def valuation_node(state: ClaimState):
    print("🔍 CLAIMGUARD AI — CALCULATING COSTS (India Market)")

    fallback_map = {
        "Low": 5000.0,
        "Medium": 12000.0,
        "High": 25000.0,
        "Critical": 40000.0,
    }

    anomalies = state["anamolies"]

    # Pull vehicle info from state if available, else default to Alto
    vehicle_info = state.get("vehicle_info", {
        "make": "Maruti Suzuki",
        "model": "Alto",
        "segment": "Small hatchback",
        "year": "2020",
        "variant": "LXI",
    })

    total = 0.0
    updated_items = []

    try:
        predictions = predict_costs_batch(anomalies, vehicle_info)
        cost_lookup = {p["index"]: p for p in predictions}

        for i, issue in enumerate(anomalies):
            prediction = cost_lookup.get(i)
            if prediction is None:
                raise ValueError(f"Missing prediction for anomaly index {i}")

            issue["estimated_cost"] = round(float(prediction["estimated_cost"]), 2)
            issue["action"] = prediction.get("action", "repair")
            issue["reasoning"] = prediction.get("reasoning", "")
            total += issue["estimated_cost"]
            updated_items.append(issue)

        print(f"✅ AI Valuation complete — Total: ₹{round(total, 2):,.2f}")

    except Exception as e:
        print(f"⚠️  Groq prediction failed: {e} — falling back to rule-based pricing")
        for issue in anomalies:
            severity = issue.get("severity", "").strip().title()
            cost = fallback_map.get(severity, 5000.0)
            issue["estimated_cost"] = cost
            issue["action"] = "repair"
            issue["reasoning"] = "Fallback: rule-based estimate"
            updated_items.append(issue)
            total += cost

    return {
        "anamolies": updated_items,
        "total_claim_value": round(total, 2),
        "currency": "INR",
        "status": "Estimate Complete",
    }