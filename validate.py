import os

from state import ClaimState
from backend.claims.services.media_service import is_supported_media

def input_validation_node(state:ClaimState):
    image_paths = [state.get('check_out_url'), state.get('check_in_url')]
    media_type = state.get("media_type", "image")

    for path in image_paths:
        if not path:
            continue
        try:
            if not is_supported_media(path, media_type):
                raise ValueError("unsupported media type")
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            if os.path.getsize(path) == 0:
                raise ValueError("empty media file")
            print(f"validation successful for: {path}")
        except Exception:
            print("Validation Fail")
            return {"is_image_clear":False,"status":"invalid image"}

    return {"is_image_clear":True,"status":"Valid image Detected"}
