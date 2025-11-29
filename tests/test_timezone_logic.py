import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date, time
from scheduler_agent.tools.validation import check_conflict
from scheduler_agent.tools.search import get_user_details
from scheduler_agent.data_manager import DataManager

# Mock DataManager to avoid reading actual files
@pytest.fixture
def mock_data_manager():
    with patch('scheduler_agent.tools.search.get_data_manager') as mock_get_dm:
        mock_dm = MagicMock()
        mock_get_dm.return_value = mock_dm
        yield mock_dm

def test_get_user_details(mock_data_manager):
    # Setup mock return
    mock_data_manager.get_user_details.return_value = {
        "username": "Test User",
        "email": "test@example.com",
        "country": "Japan",
        "timezone": "Asia/Tokyo"
    }
    
    details = get_user_details("test@example.com")
    assert details["country"] == "Japan"
    assert details["timezone"] == "Asia/Tokyo"

@patch('scheduler_agent.tools.validation.get_calendar_service')
@patch('scheduler_agent.tools.validation.get_local_timezone')
def test_check_conflict_timezone(mock_get_local_tz, mock_get_service):
    # Setup mocks
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    mock_get_local_tz.return_value = "UTC" # Default if no tz provided
    
    # Mock calendar list
    mock_service.calendarList().list().execute.return_value = {
        "items": [{"id": "primary", "selected": True}]
    }
    
    # Mock events list
    mock_service.events().list().execute.return_value = {"items": []}
    
    # Test with specific timezone (Tokyo is UTC+9)
    # 10:00 AM Tokyo = 1:00 AM UTC
    check_conflict("2025-12-01", "10:00", "11:00", timezone="Asia/Tokyo")
    
    # Verify events().list was called with correct UTC conversion
    # We expect start time to be converted to UTC
    # 2025-12-01 10:00:00+09:00 -> 2025-12-01 01:00:00+00:00
    call_args = mock_service.events().list.call_args[1]
    assert "2025-12-01T01:00:00+00:00" in call_args["timeMin"]
    assert "2025-12-01T02:00:00+00:00" in call_args["timeMax"]

@patch('scheduler_agent.tools.validation.get_calendar_service')
@patch('scheduler_agent.tools.validation.get_local_timezone')
def test_check_conflict_default_timezone(mock_get_local_tz, mock_get_service):
    # Setup mocks
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    mock_get_local_tz.return_value = "Asia/Singapore" # System local is Singapore (UTC+8)
    
    # Mock calendar list
    mock_service.calendarList().list().execute.return_value = {
        "items": [{"id": "primary", "selected": True}]
    }
    
    # Mock events list
    mock_service.events().list().execute.return_value = {"items": []}
    
    # Test without timezone argument (should use local default)
    # 10:00 AM Singapore = 2:00 AM UTC
    check_conflict("2025-12-01", "10:00", "11:00")
    
    # Verify events().list was called with correct UTC conversion
    # 2025-12-01 10:00:00+08:00 -> 2025-12-01 02:00:00+00:00
    call_args = mock_service.events().list.call_args[1]
    assert "2025-12-01T02:00:00+00:00" in call_args["timeMin"]
    assert "2025-12-01T03:00:00+00:00" in call_args["timeMax"]
