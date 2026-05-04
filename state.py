from typing import List, TypedDict


class DamageReport(TypedDict, total=False):
    item: str
    issue: str
    severity: str
    estimated_cost: float
    action: str
    reasoning: str


class VehicleInfo(TypedDict, total=False):
    make: str
    model: str
    segment: str
    year: str
    variant: str


class AssetInfo(TypedDict, total=False):
    asset_type: str    # e.g. "Car", "Room", "Sofa", "Laptop", "Shop"
    description: str   # e.g. "2020 Maruti Alto LXI" or "3-seater leather sofa"
    year: str          # year of purchase / construction
    tier: str          # "Budget", "Standard", "Premium"


class ClaimState(TypedDict, total=False):
    property_id: str
    user_id: str
    media_type: str
    check_in_url: str       # BEFORE image (original / undamaged state)
    check_out_url: str      # AFTER image  (current / damaged state)
    is_image_clear: bool
    anamolies: List[DamageReport]
    total_claim_value: float
    currency: str
    status: str
    asset_info: AssetInfo       # generic: works for any insurable asset
    vehicle_info: VehicleInfo   # kept for backward compatibility
    damage_summary: str
