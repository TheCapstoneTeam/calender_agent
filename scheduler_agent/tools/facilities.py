import json
from ..data_manager import get_data_manager

def find_facility(capacity: int = 0, amenities: str = "") -> str:
    """
    Finds facilities matching criteria.
    Args:
        capacity: Minimum number of people.
        amenities: Comma-separated list of required amenities (e.g. "Projector, Whiteboard").
    Returns:
        JSON string of matching facilities.
    """
    dm = get_data_manager()
    amenity_list = [a.strip() for a in amenities.split(",")] if amenities else []
    facilities = dm.find_facility(capacity=capacity, amenities=amenity_list)
    
    if not facilities:
        return "No matching facilities found."
    
    # Return simplified info to save tokens
    return json.dumps([{
        "name": f['name'],
        "capacity": f['capacity'],
        "amenities": f['amenities']
    } for f in facilities])

def get_facility_info(facility_name: str) -> str:
    """
    Returns details for a specific facility.
    """
    dm = get_data_manager()
    info = dm.get_facility_info(facility_name)
    if info:
        return json.dumps(info)
    return "Facility not found."
