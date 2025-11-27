"""
Pytest configuration and shared fixtures for tests
"""

import pytest
import sys
import os

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def test_date_str():
    """Return test date string (Next Tuesday Dec 2nd 2025)"""
    return "02-12-2025"

@pytest.fixture
def test_date_obj():
    """Return test date object"""
    from datetime import date
    return date(2025, 12, 2)

@pytest.fixture
def test_start_time():
    return "14:00"

@pytest.fixture
def test_end_time():
    return "15:00"

@pytest.fixture
def test_timezone():
    return "Asia/Singapore"

@pytest.fixture
def test_attendees():
    return "alice@example.com, bob@example.com"
