import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from workflow import app  # noqa: E402


def run_claim_workflow(*, user_id, property_id, check_out_path, check_in_path="", media_type="image"):
    workflow_input = {
        "property_id": property_id,
        "user_id": str(user_id),
        "media_type": media_type,
        "check_in_url": check_in_path,
        "check_out_url": check_out_path,
        "anamolies": [],
        "is_image_clear": False,
        "total_claim_value": 0,
        "status": "Starting pipeline from Django upload",
    }
    return app.invoke(workflow_input)
