from auth import get_calendar_service

service = get_calendar_service()

event = {
    'summary': 'Test Event 2 from Python Agent',
    'start': {
        'dateTime': '2025-11-16T20:00:00',
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': '2025-11-16T21:00:00',
        'timeZone': 'Asia/Kolkata',
    },
}

created_event = service.events().insert(calendarId='primary', body=event).execute()

print("Event created:", created_event.get('htmlLink'))
