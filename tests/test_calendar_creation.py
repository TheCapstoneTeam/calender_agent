import pytest
from unittest.mock import MagicMock, patch
from scheduler_agent.calendar_tools import create_event, get_calendar_id

@pytest.fixture
def mock_service():
    with patch('scheduler_agent.calendar_tools.get_calendar_service') as mock:
        yield mock

def test_get_calendar_id(mock_service):
    service = mock_service.return_value
    service.calendarList().list.return_value.execute.return_value = {
        'items': [
            {'id': 'primary', 'summary': 'Primary'},
            {'id': 'team_ella_id', 'summary': 'TeamElla'}
        ]
    }
    
    assert get_calendar_id(service, 'TeamElla') == 'team_ella_id'
    assert get_calendar_id(service, 'teamella') == 'team_ella_id' # Case insensitive
    assert get_calendar_id(service, 'NonExistent') == 'primary'
    assert get_calendar_id(service, '') == 'primary'

def test_create_event_on_specific_calendar(mock_service):
    service = mock_service.return_value
    
    # Mock get_calendar_id behavior by mocking calendarList
    service.calendarList().list.return_value.execute.return_value = {
        'items': [{'id': 'team_ella_id', 'summary': 'TeamElla'}]
    }
    
    # Mock insert
    service.events().insert.return_value.execute.return_value = {
        'id': 'new_event_id',
        'htmlLink': 'http://link'
    }

    result = create_event(
        title="Meeting", 
        date="2025-12-01", 
        start_time="10:00", 
        end_time="11:00", 
        calendar_name="TeamElla"
    )
    
    # Verify insert called with correct calendarId
    call_args = service.events().insert.call_args[1]
    assert call_args['calendarId'] == 'team_ella_id'
    assert result['calendar_id'] == 'team_ella_id'

def test_create_event_default_primary(mock_service):
    service = mock_service.return_value
    service.calendarList().list.return_value.execute.return_value = {'items': []}
    service.events().insert.return_value.execute.return_value = {'id': 'ev1'}

    result = create_event("Meeting", "2025-12-01", "10:00", "11:00")
    
    call_args = service.events().insert.call_args[1]
    assert call_args['calendarId'] == 'primary'
    assert result['calendar_id'] == 'primary'
