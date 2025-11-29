"""
Individual availability checker sub-agent.

This sub-agent checks the availability of a single attendee asynchronously,
allowing for parallel execution when checking multiple attendees.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from ..auth import get_calendar_service
from ..datetime_utils import parse_date, parse_time, to_iso, get_local_timezone


class AvailabilityCheckerAgent:
    """
    Sub-agent that checks calendar availability for a single attendee.
    
    Designed to be run in parallel with other instances to speed up
    multi-attendee availability checking.
    
    Usage:
        agent = AvailabilityCheckerAgent()
        result = await agent.check_availability(
            email="alice@example.com",
            date="2025-11-29",
            start_time="14:00",
            end_time="15:00"
        )
    """
    
    def __init__(self, timeout_seconds: int = 3):
        """
        Initialize the availability checker sub-agent.
        
        Args:
            timeout_seconds: Maximum time to wait for API response
        """
        self.timeout_seconds = timeout_seconds
        self.service = None
    
    def _get_service(self):
        """Lazy load calendar service"""
        if self.service is None:
            self.service = get_calendar_service()
        return self.service
    
    async def check_availability(
        self,
        email: str,
        date: str,
        start_time: str,
        end_time: str,
        timezone: str = None
    ) -> Dict[str, Any]:
        """
        Check if a single attendee is available during the specified time.
        
        Args:
            email: Attendee's email address
            date: Date string (DD-MM-YYYY or YYYY-MM-DD)
            start_time: Start time "HH:MM"
            end_time: End time "HH:MM" or duration "2hr"
            timezone: Timezone name (e.g., 'Asia/Singapore'). If None, uses system timezone
        
        Returns:
            {
                "email": str,
                "available": bool,
                "conflicts": [{"start": str, "end": str}],
                "error": str | None,
                "execution_time": float
            }
        """
        start_exec = datetime.now()
        
        try:
            # Run the check with timeout
            result = await asyncio.wait_for(
                self._check_availability_impl(email, date, start_time, end_time, timezone),
                timeout=self.timeout_seconds
            )
            
            execution_time = (datetime.now() - start_exec).total_seconds()
            result["execution_time"] = execution_time
            return result
            
        except asyncio.TimeoutError:
            return {
                "email": email,
                "available": False,
                "conflicts": [],
                "error": f"Timeout after {self.timeout_seconds} seconds",
                "execution_time": self.timeout_seconds
            }
        except Exception as e:
            execution_time = (datetime.now() - start_exec).total_seconds()
            return {
                "email": email,
                "available": False,
                "conflicts": [],
                "error": str(e),
                "execution_time": execution_time
            }
    
    async def _check_availability_impl(
        self,
        email: str,
        date: str,
        start_time: str,
        end_time: str,
        timezone: str = None
    ) -> Dict[str, Any]:
        """
        Internal implementation of availability checking.
        
        This is wrapped by check_availability() for timeout handling.
        """
        # Run the blocking I/O in a thread pool to not block the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._check_freebusy,
            email, date, start_time, end_time, timezone
        )
        return result
    
    def _check_freebusy(
        self,
        email: str,
        date: str,
        start_time: str,
        end_time: str,
        timezone: str = None
    ) -> Dict[str, Any]:
        """
        Check FreeBusy status using Google Calendar API.
        
        This is a synchronous function that will be run in a thread pool.
        """
        service = self._get_service()
        
        # Get timezone
        if timezone is None:
            tz = get_local_timezone()
            if hasattr(tz, 'zone'):
                timezone = tz.zone
            else:
                timezone = 'UTC'
        
        # Parse date and times
        date_obj = parse_date(date)
        start_t = parse_time(start_time)
        end_t = parse_time(end_time)
        
        if isinstance(start_t, timedelta):
            raise ValueError("Start time cannot be a duration")
        
        # Convert duration to end time if needed
        if isinstance(end_t, timedelta):
            dt_start = datetime.combine(date_obj, start_t)
            dt_end = dt_start + end_t
            end_t = dt_end.time()
            date_obj_end = dt_end.date()
        else:
            date_obj_end = date_obj
        
        # Convert to UTC ISO format for API
        start_iso = to_iso(date_obj, start_t, timezone)
        end_iso = to_iso(date_obj_end, end_t, timezone)
        
        # Query FreeBusy API for this specific email
        try:
            body = {
                "timeMin": start_iso,
                "timeMax": end_iso,
                "timeZone": "UTC",
                "items": [{"id": email}]
            }
            
            freebusy_result = service.freebusy().query(body=body).execute()
            
            # Parse result
            calendar_info = freebusy_result.get('calendars', {}).get(email, {})
            
            # Check for errors (e.g., calendar not accessible)
            if 'errors' in calendar_info:
                error_msg = calendar_info['errors'][0].get('reason', 'Unknown error')
                return {
                    "email": email,
                    "available": False,
                    "conflicts": [],
                    "error": f"Calendar access error: {error_msg}"
                }
            
            # Get busy times
            busy_times = calendar_info.get('busy', [])
            
            return {
                "email": email,
                "available": len(busy_times) == 0,
                "conflicts": busy_times,
                "error": None
            }
            
        except Exception as e:
            return {
                "email": email,
                "available": False,
                "conflicts": [],
                "error": f"API error: {str(e)}"
            }
