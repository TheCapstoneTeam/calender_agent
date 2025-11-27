"""
Test script to verify timezone awareness in calendar_tools.py
This demonstrates how the system now handles timezones.
"""
import sys
from datetime import datetime, timezone
from scheduler_agent.calendar_tools import (
    get_local_timezone,
    parse_date,
    parse_time,
    to_iso
)

def test_timezone_detection():
    """Test automatic timezone detection"""
    print("=" * 60)
    print("TEST 1: Timezone Detection")
    print("=" * 60)
    
    local_tz = get_local_timezone()
    print(f"✓ Detected local timezone: {local_tz}")
    print(f"  Type: {type(local_tz)}")
    print()

def test_time_conversion():
    """Test conversion from local time to UTC"""
    print("=" * 60)
    print("TEST 2: Time Conversion (Local → UTC)")
    print("=" * 60)
    
    # Example: Tomorrow at 2:00 PM local time
    date_str = "2025-11-27"
    time_str = "14:00"
    
    date_obj = parse_date(date_str)
    time_obj = parse_time(time_str)
    
    print(f"Input (naive):")
    print(f"  Date: {date_str}")
    print(f"  Time: {time_str}")
    print()
    
    # Convert to UTC ISO format
    utc_iso = to_iso(date_obj, time_obj)
    
    print(f"Output (UTC):")
    print(f"  ISO format: {utc_iso}")
    print(f"  ✓ Timezone-aware: {'+' in utc_iso or 'Z' in utc_iso}")
    print()

def test_duration_handling():
    """Test duration-based end times"""
    print("=" * 60)
    print("TEST 3: Duration Handling")
    print("=" * 60)
    
    from datetime import timedelta
    
    date_str = "2025-11-27"
    start_time = "09:00"
    duration = "2hr"
    
    date_obj = parse_date(date_str)
    start_t = parse_time(start_time)
    duration_t = parse_time(duration)
    
    print(f"Meeting scheduled for:")
    print(f"  Start: {start_time} local time")
    print(f"  Duration: {duration}")
    print()
    
    # Calculate end time
    from datetime import datetime as dt
    dt_start = dt.combine(date_obj, start_t)
    dt_end = dt_start + duration_t
    end_t = dt_end.time()
    
    start_utc = to_iso(date_obj, start_t)
    end_utc = to_iso(date_obj, end_t)
    
    print(f"Converted to UTC:")
    print(f"  Start: {start_utc}")
    print(f"  End:   {end_utc}")
    print()

def demonstrate_google_calendar_behavior():
    """Explain how Google Calendar handles timezones"""
    print("=" * 60)
    print("EXPLANATION: How Google Calendar Displays Events")
    print("=" * 60)
    print()
    print("When you create an event in UTC:")
    print("  • Google Calendar stores it with UTC timezone")
    print("  • Each attendee sees it converted to THEIR local timezone")
    print("  • No additional code needed from your side!")
    print()
    print("Example:")
    print("  Event created: 2025-11-27T14:00:00+00:00 (UTC)")
    print("  → User in Singapore (UTC+8) sees: Nov 27, 10:00 PM")
    print("  → User in New York (UTC-5) sees: Nov 27, 9:00 AM")
    print("  → User in London (UTC+0) sees: Nov 27, 2:00 PM")
    print()

if __name__ == "__main__":
    print("\n" + "🔧 TIMEZONE AWARENESS VERIFICATION" + "\n")
    print(f"Current system time: {datetime.now()}")
    print(f"Current UTC time: {datetime.now(timezone.utc)}")
    print()
    
    try:
        test_timezone_detection()
        test_time_conversion()
        test_duration_handling()
        demonstrate_google_calendar_behavior()
        
        print("=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Run your calendar agent")
        print("  2. Create an event using natural language")
        print("  3. Verify it appears at correct time in Google Calendar")
        print()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
