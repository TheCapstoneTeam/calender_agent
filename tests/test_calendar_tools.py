import pytest
from unittest.mock import MagicMock, patch
from scheduler_agent.calendar_tools import check_conflict

@pytest.fixture
def mock_service():
    with patch('scheduler_agent.calendar_tools.get_calendar_service') as mock:
        yield mock

def test_check_conflict_multi_calendar(mock_service):
    # Setup mock service
    service = mock_service.return_value
    
    # Mock calendar list
    service.calendarList().list.return_value.execute.return_value = {
        'items': [
            {'id': 'primary', 'summary': 'Primary', 'selected': True},
            {'id': 'work', 'summary': 'Work', 'selected': True},
            {'id': 'hidden', 'summary': 'Hidden', 'selected': False}
        ]
    }
    
    # Mock events list
    # Primary has no events
    # Work has 1 event
    # Hidden should not be called
    
    def events_list_side_effect(calendarId, **kwargs):
        mock_list = MagicMock()
        if calendarId == 'primary':
            mock_list.execute.return_value = {'items': []}
        elif calendarId == 'work':
            mock_list.execute.return_value = {
                'items': [{'summary': 'Work Meeting', 'start': {}, 'end': {}}]
            }
        elif calendarId == 'hidden':
             # Should not happen if logic is correct
             mock_list.execute.return_value = {'items': [{'summary': 'Hidden Event'}]}
        return mock_list

    service.events().list.side_effect = events_list_side_effect

    # Run check_conflict
    result = check_conflict("2025-12-02", "10:00", "11:00")
    
    # Verify
    assert result['conflict'] is True
    assert len(result['events']) == 1
    assert result['events'][0]['summary'] == 'Work Meeting'
    assert result['events'][0]['calendarSummary'] == 'Work'
    
    # Verify service calls
    # Should list calendars
    service.calendarList().list.assert_called_once()
    
    # Should list events for primary and work, but not hidden
    calls = service.events().list.call_args_list
    cal_ids = [c.kwargs['calendarId'] for c in calls]
    assert 'primary' in cal_ids
    assert 'work' in cal_ids
    assert 'hidden' not in cal_ids

def test_check_conflict_no_conflict(mock_service):
    service = mock_service.return_value
    service.calendarList().list.return_value.execute.return_value = {
        'items': [{'id': 'primary', 'selected': True}]
    }
    service.events().list.return_value.execute.return_value = {'items': []}
    
    result = check_conflict("2025-12-02", "10:00", "11:00")
    
    assert result['conflict'] is False
    assert len(result['events']) == 0
