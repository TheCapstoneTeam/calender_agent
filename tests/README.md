# Test Suite for Calendar Agent

This directory contains all tests for the calendar agent project.

## Setup

Install test dependencies:
```bash
pip install -r tests/requirements-test.txt
```

## Running Tests

### Run all tests:
```bash
pytest tests/ -v
```

### Run specific test file:
```bash
pytest tests/test_calendar_tools.py -v
```

### Run with coverage:
```bash
pytest tests/ --cov=scheduler_agent --cov-report=term-missing
```

### Run specific test class:
```bash
pytest tests/test_calendar_tools.py::TestToIso -v
```

### Run specific test:
```bash
pytest tests/test_calendar_tools.py::TestToIso::test_to_iso_with_datetime_and_tz_string -v
```

## Test Files

- `test_calendar_tools.py` - Tests for tools package functions
  - `TestParseDate` - Date parsing tests
  - `TestParseTime` - Time parsing tests
  - `TestToIso` - UTC/ISO conversion tests
  - `TestAllAttendeesFree` - Helper function tests
  - `TestCheckAttendeesAvailability` - Attendee availability checking
  - `TestCreateEventWithAttendees` - Full event creation workflow

## Mocking

All tests use mocked Google Calendar API calls, so no credentials are required to run tests.
