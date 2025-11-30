import pytest
import json
import os
import pandas as pd
from scheduler_agent.data_manager import DataManager

@pytest.fixture
def temp_data_files(tmp_path):
    users_file = tmp_path / "users.json"
    facilities_file = tmp_path / "facilities.json"
    
    users_data = {
        "users": [
            {"username": "User A", "email": "a@example.com", "teams": ["TeamA"]},
            {"username": "User B", "email": "b@example.com", "teams": ["TeamA", "TeamB"]},
            {"username": "User C", "email": "c@example.com", "teams": ["TeamB"]}
        ]
    }
    
    facilities_data = [
        {"name": "Room 1", "capacity": 5, "amenities": ["Projector", "Whiteboard"]},
        {"name": "Room 2", "capacity": 10, "amenities": ["Video Conf"]},
        {"name": "Room 3", "capacity": 2, "amenities": ["Whiteboard"]}
    ]
    
    with open(users_file, 'w') as f:
        json.dump(users_data, f)
        
    with open(facilities_file, 'w') as f:
        json.dump(facilities_data, f)
        
    return str(users_file), str(facilities_file)

def test_load_data(temp_data_files):
    users_file, facilities_file = temp_data_files
    dm = DataManager(users_file, facilities_file)
    assert not dm.users_df.empty
    assert not dm.facilities_df.empty
    assert len(dm.users_df) == 3
    assert len(dm.facilities_df) == 3

def test_get_team_members(temp_data_files):
    users_file, facilities_file = temp_data_files
    dm = DataManager(users_file, facilities_file)
    
    team_a = dm.get_team_members("TeamA")
    assert len(team_a) == 2
    assert "a@example.com" in team_a
    assert "b@example.com" in team_a
    
    team_b = dm.get_team_members("TeamB")
    assert len(team_b) == 2
    assert "b@example.com" in team_b
    assert "c@example.com" in team_b
    
    team_c = dm.get_team_members("TeamC")
    assert len(team_c) == 0

def test_find_facility(temp_data_files):
    users_file, facilities_file = temp_data_files
    dm = DataManager(users_file, facilities_file)
    
    # Capacity check
    large_rooms = dm.find_facility(capacity=6)
    assert len(large_rooms) == 1
    assert large_rooms[0]['name'] == "Room 2"
    
    # Amenities check
    whiteboard_rooms = dm.find_facility(amenities=["Whiteboard"])
    assert len(whiteboard_rooms) == 2
    names = [r['name'] for r in whiteboard_rooms]
    assert "Room 1" in names
    assert "Room 3" in names
    
    # Combined check
    small_whiteboard = dm.find_facility(capacity=4, amenities=["Whiteboard"])
    assert len(small_whiteboard) == 1
    assert small_whiteboard[0]['name'] == "Room 1"

def test_get_facility_info(temp_data_files):
    users_file, facilities_file = temp_data_files
    dm = DataManager(users_file, facilities_file)
    
    info = dm.get_facility_info("Room 1")
    assert info is not None
    assert info['capacity'] == 5
    
    info = dm.get_facility_info("NonExistent")
    assert info is None
