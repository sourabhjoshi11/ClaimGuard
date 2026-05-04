import json
import os
from dotenv import load_dotenv
from state import ClaimState

load_dotenv()

try:
    from groq import Groq as _Groq
except ImportError:
    _Groq = None


def _get_groq_client():
    if _Groq is None:
        raise RuntimeError("Groq SDK not installed - run: pip install groq")
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set - add it to backend/.env")
    return _Groq(api_key=api_key)


INDIA_PRICING_CONTEXT = """
You are an insurance claim cost estimator for ClaimGuard AI operating in INDIA.
You handle ALL types of insurance claims - vehicles, property, furniture, electronics,
appliances, machinery, shops, homes, and any other insurable asset.

INDIAN REPAIR / REPLACEMENT MARKET RATES (2024, INR, labor included):

--- VEHICLES ---
- Windshield replacement (hatchback): 8000 - 18000
- Windshield replacement (sedan/SUV): 15000 - 35000
- Side/rear window glass: 3000 - 15000
- Hood/bonnet repair: 5000 - 12000 | replacement: 15000 - 30000
- Door panel repair: 5000 - 15000 | replacement: 12000 - 28000
- Bumper repair: 3000 - 8000 | replacement: 5000 - 25000
- Fender repair: 4000 - 10000 | replacement: 8000 - 18000
- Headlight assembly: 4000 - 35000 | Tail light: 3000 - 10000
- Tyre replacement (per unit): 4000 - 12000
- Radiator: 8000 - 20000 | Suspension (per side): 5000 - 15000
Vehicle segment multipliers: hatchback x1.0, sedan x1.3, compact SUV x1.6, full SUV x2.0, luxury x2.5

--- PROPERTY / CIVIL ---
- Wall replastering (per sq ft): 25 - 60
- Wall painting (per sq ft): 15 - 40
- Floor tile replacement (per sq ft): 80 - 300
- Wooden flooring repair (per sq ft): 150 - 500
- Door replacement (wooden): 5000 - 20000 | (metal): 8000 - 25000
- Window frame + glass replacement: 4000 - 15000
- Ceiling repair (per sq ft): 50 - 150
- Roof sheet replacement: 200 - 600 per sq ft
- Electrical wiring repair (per point): 500 - 2000
- Plumbing repair (per point): 500 - 3000

--- FURNITURE ---
- Sofa repair/reupholstering: 3000 - 15000
- Sofa replacement: 15000 - 80000
- Wooden chair/table repair: 1000 - 5000 | replacement: 3000 - 20000
- Wardrobe repair: 3000 - 10000 | replacement: 15000 - 60000
- Bed frame repair: 2000 - 8000 | replacement: 10000 - 50000
- Mattress replacement: 5000 - 30000
- Glass tabletop replacement: 2000 - 8000

--- ELECTRONICS & APPLIANCES ---
- Smartphone screen replacement: 2000 - 15000
- Laptop screen replacement: 4000 - 18000
- TV panel replacement (32-55 inch): 8000 - 35000
- Refrigerator compressor repair: 4000 - 12000 | full replacement: 15000 - 60000
- Washing machine repair: 2000 - 8000 | replacement: 15000 - 45000
- AC unit repair: 2000 - 10000 | replacement: 25000 - 80000
- Microwave repair: 1500 - 5000 | replacement: 5000 - 20000
- Water heater/geyser replacement: 5000 - 20000

--- SHOP / COMMERCIAL ---
- Glass shutter replacement: 8000 - 25000
- Display rack repair: 2000 - 8000 | replacement: 5000 - 20000
- Counter/cabinet repair: 3000 - 10000 | replacement: 10000 - 40000
- Signage replacement: 5000 - 30000
- CCTV camera replacement: 2000 - 10000

SEVERITY PRICING GUIDELINES:
- Low: cosmetic/minor damage -> lower end of range
- Medium: moderate damage, partial repair/replacement -> mid range
- High: severe damage, full replacement needed -> upper end of range
"""


def predict_costs_batch(issues: list, asset_info: dict) -> list:
    client = _get_groq_client()

    asset_context = (
        "ASSET IN THIS CLAIM:\n"
        f"- Type: {asset_info.get('asset_type', 'Unknown')}\n"
        f"- Description: {asset_info.get('description', 'Not provided')}\n"
        f"- Age/Year: {asset_info.get('year', 'Unknown')}\n"
        f"- Quality/Tier: {asset_info.get('tier', 'Standard')}\n"
    )

    prompt = (
        INDIA_PRICING_CONTEXT
        + "\n" + asset_context
        + "\nDAMAGES TO ESTIMATE:\n"
        + json.dumps(issues, indent=2)
        + """

INSTRUCTIONS:
- Identify what type of asset is damaged from the item names and context
- Apply appropriate rates from the pricing table above
- Use severity to pick position within price range
- All amounts must be in INR
- Be realistic - these estimates go into official insurance claims

Respond ONLY with a valid JSON array. No markdown, no explanation.
Each object must follow this exact format:
{"index": <int>, "estimated_cost": <float>, "part": "<item/part name>", "action": "repair|replace", "reasoning": "<one line>"}

Return one entry per damage in the same order as input."""
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1024,
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())


def valuation_node(state: ClaimState):
    print("[ClaimGuard] Calculating repair costs (India market)...")

    fallback_map = {
        "Low": 3000.0,
        "Medium": 10000.0,
        "High": 25000.0,
        "Critical": 50000.0,
    }

    anomalies = state.get("anamolies", [])

    if not anomalies:
        return {
            "anamolies": [],
            "total_claim_value": 0.0,
            "currency": "INR",
            "damage_summary": "No damage detected - claim value is 0 INR.",
            "status": "Estimate Complete",
        }

    # Support both vehicle_info (old) and asset_info (new generic key)
    asset_info = (
        state.get("asset_info")
        or state.get("vehicle_info")
        or {
            "asset_type": "Unknown asset",
            "description": "Not provided",
            "year": "Unknown",
            "tier": "Standard",
        }
    )

    total = 0.0
    updated_items = []
    used_fallback = False

    try:
        predictions = predict_costs_batch(anomalies, asset_info)
        cost_lookup = {p["index"]: p for p in predictions}

        for i, issue in enumerate(anomalies):
            prediction = cost_lookup.get(i)
            if prediction is None:
                raise ValueError(f"Missing prediction for damage index {i}")

            issue["estimated_cost"] = round(float(prediction["estimated_cost"]), 2)
            issue["action"]         = prediction.get("action", "repair")
            issue["reasoning"]      = prediction.get("reasoning", "")
            total += issue["estimated_cost"]
            updated_items.append(issue)

        print(f"[ClaimGuard] AI valuation complete - Total: {round(total, 2):,.2f} INR")

    except Exception as e:
        print(f"[ClaimGuard] AI pricing failed ({e}) - using rule-based fallback")
        used_fallback = True
        for issue in anomalies:
            severity = issue.get("severity", "").strip().title()
            cost = fallback_map.get(severity, 3000.0)
            issue["estimated_cost"] = cost
            issue["action"]         = "repair"
            issue["reasoning"]      = "Fallback: rule-based estimate"
            updated_items.append(issue)
            total += cost

    item_lines = ", ".join(
        f"{d.get('item', 'Unknown')} ({d.get('severity', '?')}) - {d['estimated_cost']:,.0f} INR"
        for d in updated_items
    )
    note = " [rule-based fallback]" if used_fallback else ""
    damage_summary = (
        f"{len(updated_items)} damage item(s) found{note}: {item_lines}. "
        f"Total claim value: {round(total, 2):,.2f} INR."
    )

    return {
        "anamolies":         updated_items,
        "total_claim_value": round(total, 2),
        "currency":          "INR",
        "damage_summary":    damage_summary,
        "status":            "Estimate Complete",
    }
