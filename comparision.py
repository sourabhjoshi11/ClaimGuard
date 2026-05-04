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

def comparison_node(state: ClaimState):
    print("comparision")

    try:
        if not state.get('check_in_url'):
            return {"anamolies": [], "status": "No reference image provided"}

        if Groq is None:
            return {"anamolies": [], "status": "Groq SDK missing"}

        client = get_groq_client()
        if not client:
            return {"anamolies": [], "status": "Groq API key missing. Set GROQ_API_KEY in backend/.env"}

        media_type = state.get("media_type", "image")
        check_in = media_to_base64_preview(state['check_in_url'], media_type)
        check_out = media_to_base64_preview(state['check_out_url'], media_type)
        comparison_prompt = (
            "Compare these before and after images. Return ONLY a JSON object in the form "
            "{\"damages\": [{\"item\": \"string\", \"issue\": \"string\", \"severity\": \"Low/Medium/High\"}]}"
        )
        if media_type == "video":
            comparison_prompt = (
                "Each uploaded image is a vertical strip of key frames from a before video and an after video. "
                "Compare the scenes and return ONLY a JSON object in the form "
                "{\"damages\": [{\"item\": \"string\", \"issue\": \"string\", \"severity\": \"Low/Medium/High\"}]}"
            )

        
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": comparison_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{check_in}"}
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{check_out}"}
                        }
                    ]
                }
            ],
            temperature=0.1, 
            response_format={"type": "json_object"}
        )

      
        raw_content = completion.choices[0].message.content
        
       
        ai_data = json.loads(raw_content)
        
        
        if isinstance(ai_data, dict) and "damages" in ai_data:
            anamolies = ai_data["damages"]
        else:
            anamolies = [ai_data] if ai_data else []

        print(f"detected {len(anamolies)} issues.")
        return {"anamolies": anamolies, "status": "Groq Comparison Done"}

  

    except Exception as e:
        print(f"Groq Error: {e}")
        return {"status": f"Error in Groq: {str(e)}", "anamolies": []}
