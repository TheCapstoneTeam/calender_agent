import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from scheduler_agent.tools.holidays import is_holiday, is_working_time

# Mock GoogleSearchTool
@pytest.fixture
def mock_search_tool():
    with patch('scheduler_agent.tools.holidays._search_tool') as mock_tool:
        yield mock_tool

# Mock get_user_details
@pytest.fixture
def mock_get_user_details():
    with patch('scheduler_agent.tools.holidays.get_user_details') as mock_details:
        yield mock_details

def test_is_holiday_true(mock_search_tool):
    # Setup mock to return a result indicating a holiday
    mock_search_tool.search.return_value = "Christmas Day is a public holiday in UK."
    
    assert is_holiday("2025-12-25", "UK") is True

def test_is_holiday_false(mock_search_tool):
    # Setup mock to return a result indicating NOT a holiday
    mock_search_tool.search.return_value = "December 28th is not a public holiday in UK."
    
    assert is_holiday("2025-12-28", "UK") is False

def test_is_holiday_no_country():
    assert is_holiday("2025-12-25", "") is False

def test_is_working_time_normal(mock_get_user_details):
    # User works Mon-Fri, 9-5
    mock_get_user_details.return_value = {
        "email": "test@example.com",
        "country": "UK",
        "preferences": {
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "working_hours": {"start": "09:00", "end": "17:00"},
            "work_on_holidays": False
        }
    }
    
    # Test a Tuesday at 10am (2025-12-02 is a Tuesday)
    result = is_working_time("2025-12-02", "10:00", "11:00", "test@example.com")
    assert result["is_working"] is True

def test_is_working_time_weekend(mock_get_user_details):
    mock_get_user_details.return_value = {
        "email": "test@example.com",
        "country": "UK",
        "preferences": {
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "working_hours": {"start": "09:00", "end": "17:00"},
            "work_on_holidays": False
        }
    }
    
    # Test a Saturday (2025-12-06)
    result = is_working_time("2025-12-06", "10:00", "11:00", "test@example.com")
    assert result["is_working"] is False
    assert "Non-working day" in result["reason"]

def test_is_working_time_outside_hours(mock_get_user_details):
    mock_get_user_details.return_value = {
        "email": "test@example.com",
        "country": "UK",
        "preferences": {
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "working_hours": {"start": "09:00", "end": "17:00"},
            "work_on_holidays": False
        }
    }
    
    # Test Tuesday at 8pm
    result = is_working_time("2025-12-02", "20:00", "21:00", "test@example.com")
    assert result["is_working"] is False
    assert "Outside working hours" in result["reason"]

@patch('scheduler_agent.tools.holidays.is_holiday')
def test_is_working_time_holiday(mock_is_holiday, mock_get_user_details):
    mock_get_user_details.return_value = {
        "email": "test@example.com",
        "country": "UK",
        "preferences": {
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "working_hours": {"start": "09:00", "end": "17:00"},
            "work_on_holidays": False
        }
    }
    
    # Mock is_holiday to return True
    mock_is_holiday.return_value = True
    
    # Test a working day that is a holiday
    result = is_working_time("2025-12-25", "10:00", "11:00", "test@example.com")
    assert result["is_working"] is False
    assert "Public Holiday" in result["reason"]

@patch('scheduler_agent.tools.holidays.is_holiday')
def test_is_working_time_work_on_holiday(mock_is_holiday, mock_get_user_details):
    mock_get_user_details.return_value = {
        "email": "test@example.com",
        "country": "UK",
        "preferences": {
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "working_hours": {"start": "09:00", "end": "17:00"},
            "work_on_holidays": True  # User works on holidays
        }
    }
    
    # Mock is_holiday to return True
    mock_is_holiday.return_value = True
    
    # Test a working day that is a holiday
    result = is_working_time("2025-12-25", "10:00", "11:00", "test@example.com")
    assert result["is_working"] is True

def test_is_working_time_vacation(mock_get_user_details):
    mock_get_user_details.return_value = {
        "email": "test@example.com",
        "country": "UK",
        "preferences": {
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "working_hours": {"start": "09:00", "end": "17:00"},
            "work_on_holidays": False,
            "vacation_dates": ["2025-12-20", "2025-12-21"]
        }
    }
    
    # Test a vacation date
    result = is_working_time("2025-12-20", "10:00", "11:00", "test@example.com")
    assert result["is_working"] is False
    assert "Vacation" in result["reason"]
