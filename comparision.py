import os
import json
from state import ClaimState
from dotenv import load_dotenv
from backend.claims.services.media_service import media_to_base64_preview

try:
    from groq import Groq
except ImportError:
    Groq = None

load_dotenv()


def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ")
    return Groq(api_key=api_key) if Groq and api_key else None


IMAGE_PROMPT = """You are a damage assessment AI for an insurance company in India.

You are given TWO images:
  IMAGE 1 - BEFORE (original / undamaged state)
  IMAGE 2 - AFTER  (current / damaged state)

This could be anything: a vehicle, a room, furniture, electronics, flooring, walls,
machinery, appliances, a shop, a house, or any other insurable asset.

Your task:
1. Carefully compare Image 1 (before) with Image 2 (after).
2. Identify ONLY the NEW damage that appears in Image 2 but was NOT present in Image 1.
3. Ignore pre-existing damage already visible in Image 1.
4. For each new damage found, name the specific item/part affected and describe the damage.
5. Classify severity as Low / Medium / High:
     Low    : minor cosmetic damage (small scratches, scuffs, chips, stains)
     Medium : moderate damage (cracks, partial breakage, significant dents/tears)
     High   : severe damage (complete breakage, structural damage, total loss of function)
6. If no new damage is detected, return an empty damages array.

Return ONLY a valid JSON object - no markdown, no extra text:
{"damages": [{"item": "<affected item/part>", "issue": "<description of damage>", "severity": "Low|Medium|High"}]}"""

VIDEO_PROMPT = """You are a damage assessment AI for an insurance company in India.

Each uploaded image is a vertical strip of key frames sampled from a video.
  IMAGE 1 - BEFORE video frames (original / undamaged state)
  IMAGE 2 - AFTER  video frames (current / damaged state)

This could be anything: a vehicle, a room, furniture, electronics, flooring, walls,
machinery, appliances, a shop, a house, or any other insurable asset.

Compare the scenes across both strips and identify ONLY new damage visible in the AFTER frames
that was not present in the BEFORE frames. Classify each damage as Low / Medium / High severity.

Return ONLY a valid JSON object - no markdown, no extra text:
{"damages": [{"item": "<affected item/part>", "issue": "<description of damage>", "severity": "Low|Medium|High"}]}"""


def comparison_node(state: ClaimState):
    print("[ClaimGuard] Running damage comparison...")

    try:
        check_in_url  = state.get("check_in_url", "")
        check_out_url = state.get("check_out_url", "")

        if not check_in_url:
            return {"anamolies": [], "status": "No reference (before) image provided"}

        if not check_out_url:
            return {"anamolies": [], "status": "No damaged (after) image provided"}

        if Groq is None:
            return {"anamolies": [], "status": "Groq SDK not installed - run: pip install groq"}

        client = get_groq_client()
        if not client:
            return {"anamolies": [], "status": "GROQ_API_KEY missing - set it in backend/.env"}

        media_type = state.get("media_type", "image")
        before_b64  = media_to_base64_preview(check_in_url,  media_type)
        after_b64   = media_to_base64_preview(check_out_url, media_type)

        prompt = VIDEO_PROMPT if media_type == "video" else IMAGE_PROMPT

        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text",      "text": prompt},
                        {"type": "text",      "text": "IMAGE 1 - BEFORE (original undamaged state):"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{before_b64}"}},
                        {"type": "text",      "text": "IMAGE 2 - AFTER (current damaged state):"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{after_b64}"}},
                    ],
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        raw_content = completion.choices[0].message.content
        ai_data     = json.loads(raw_content)

        if isinstance(ai_data, dict) and "damages" in ai_data:
            anamolies = ai_data["damages"]
        elif isinstance(ai_data, list):
            anamolies = ai_data
        else:
            anamolies = []

        print(f"[ClaimGuard] Detected {len(anamolies)} damage item(s).")
        return {"anamolies": anamolies, "status": "Groq Comparison Done"}

    except json.JSONDecodeError as e:
        print(f"[ClaimGuard] JSON parse error: {e}")
        return {"anamolies": [], "status": f"Comparison failed - bad JSON from model: {e}"}
    except Exception as e:
        print(f"[ClaimGuard] Comparison error: {e}")
        return {"anamolies": [], "status": f"Comparison error: {e}"}
