from datetime import datetime, time
from typing import Optional
import os

# Try to import GoogleSearchTool, handle if missing
try:
    from google.adk.tools.google_search_tool import GoogleSearchTool
    # Only instantiate if API keys are present to avoid errors on import
    if os.environ.get("GOOGLE_API_KEY") and os.environ.get("GOOGLE_CSE_ID"):
        _search_tool = GoogleSearchTool()
    else:
        _search_tool = None
except ImportError:
    _search_tool = None

from .search import get_user_details
from ..datetime_utils import parse_date, parse_time

_holiday_cache = {}

def is_holiday(date_str: str, country: str) -> bool:
    """
    Checks if a date is a public holiday in a specific country using Google Search.
    """
    if not country or not _search_tool:
        return False
        
    # Normalize date
    try:
        dt = parse_date(date_str)
        formatted_date = dt.strftime("%Y-%m-%d")
    except:
        formatted_date = date_str
        
    key = f"{country}:{formatted_date}"
    if key in _holiday_cache:
        return _holiday_cache[key]
        
    query = f"Is {formatted_date} a public holiday in {country}?"
    try:
        # Search returns a string summary
        results = _search_tool.search(query)
        lower_res = results.lower()
        
        # Heuristic check for holiday confirmation
        is_hol = (
            "public holiday" in lower_res or 
            "national holiday" in lower_res or 
            "bank holiday" in lower_res or
            "federal holiday" in lower_res
        )
        
        # Negative check
        if "not a public holiday" in lower_res or "not a holiday" in lower_res:
            is_hol = False
            
        _holiday_cache[key] = is_hol
        return is_hol
    except Exception as e:
        print(f"Holiday check error: {e}")
        return False

def is_working_time(date_str: str, start_time_str: str, end_time_str: str, user_email: str) -> dict:
    """
    Checks if the specified time falls within the user's working hours and days.
    Also checks for holidays if the user doesn't work on them.
    
    Returns:
        {
            "is_working": bool,
            "reason": str (if not working)
        }
    """
    user = get_user_details(user_email)
    if not user:
        return {"is_working": True, "reason": ""}
        
    prefs = user.get("preferences", {})
    if not prefs:
        return {"is_working": True, "reason": ""}
        
    # Parse inputs
    try:
        date_obj = parse_date(date_str)
        day_name = date_obj.strftime("%A")
    except:
        return {"is_working": True, "reason": "Invalid date"}
        
    # 1. Check Vacation Dates
    vacation_dates = prefs.get("vacation_dates", [])
    if vacation_dates:
        try:
            # Normalize input date
            dt = parse_date(date_str)
            formatted_date = dt.strftime("%Y-%m-%d")
            if formatted_date in vacation_dates:
                return {"is_working": False, "reason": "User is on Vacation"}
        except:
            pass

    # 2. Check Working Days
    working_days = prefs.get("working_days", [])
    if working_days and day_name not in working_days:
        return {"is_working": False, "reason": f"Non-working day ({day_name})"}
        
    # 3. Check Holidays
    work_on_holidays = prefs.get("work_on_holidays", False)
    if not work_on_holidays:
        country = user.get("country")
        if country and is_holiday(date_str, country):
            return {"is_working": False, "reason": f"Public Holiday in {country}"}
            
    # 4. Check Working Hours
    working_hours = prefs.get("working_hours", {})
    if working_hours:
        try:
            start_pref = datetime.strptime(working_hours["start"], "%H:%M").time()
            end_pref = datetime.strptime(working_hours["end"], "%H:%M").time()
            
            meeting_start = parse_time(start_time_str)
            if isinstance(meeting_start, time):
                 if meeting_start < start_pref or meeting_start >= end_pref:
                     return {"is_working": False, "reason": f"Outside working hours ({working_hours['start']}-{working_hours['end']})"}
        except:
            pass # Ignore parsing errors for preferences
            
    return {"is_working": True, "reason": ""}
