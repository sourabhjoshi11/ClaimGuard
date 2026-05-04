from typing import List, TypedDict


class DamageReport(TypedDict, total=False):
    item: str
    issue: str
    severity: str
    estimated_cost: float


class ClaimState(TypedDict):
    property_id: str
    user_id: str
    media_type: str
    check_in_url: str
    check_out_url: str
    is_image_clear: bool
    anamolies: List[DamageReport]
    total_claim_value: float
    status: str
