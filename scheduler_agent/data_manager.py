import json
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

class DataManager:
    def __init__(self, users_file: str, facilities_file: str):
        self.users_df = self._load_users(users_file)
        self.facilities_df = self._load_facilities(facilities_file)

    def _load_users(self, filepath: str) -> pd.DataFrame:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            # Normalize 'users' key if present, otherwise assume list
            users_list = data.get('users', data) if isinstance(data, dict) else data
            return pd.DataFrame(users_list)
        except Exception as e:
            print(f"Error loading users: {e}")
            return pd.DataFrame()

    def _load_facilities(self, filepath: str) -> pd.DataFrame:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error loading facilities: {e}")
            return pd.DataFrame()

    def get_team_members(self, team_name: str) -> List[str]:
        """
        Returns a list of email addresses for members of the specified team.
        Case-insensitive match on team name.
        """
        if self.users_df.empty:
            return []
        
        # Explode teams column if it's a list, or check string containment
        # Assuming 'teams' is a list of strings based on file preview
        
        # Filter users where team_name is in their 'teams' list
        # We use apply because 'teams' is a list object in the cell
        try:
            team_members = self.users_df[
                self.users_df['teams'].apply(
                    lambda teams: any(t.lower() == team_name.lower() for t in teams) 
                    if isinstance(teams, list) else False
                )
            ]
            return team_members['email'].tolist()
        except KeyError:
            return []

    def get_facility_info(self, facility_name: str) -> Optional[Dict[str, Any]]:
        """
        Returns details for a specific facility by name.
        """
        if self.facilities_df.empty:
            return None
            
        match = self.facilities_df[
            self.facilities_df['name'].str.lower() == facility_name.lower()
        ]
        
        if not match.empty:
            return match.iloc[0].to_dict()
        return None

    def find_facility(self, capacity: int = 0, amenities: List[str] = None) -> List[Dict[str, Any]]:
        """
        Finds facilities matching minimum capacity and containing ALL specified amenities.
        """
        if self.facilities_df.empty:
            return []
            
        df = self.facilities_df.copy()
        
        # Filter by capacity
        if capacity > 0:
            df = df[df['capacity'] >= capacity]
            
        # Filter by amenities
        if amenities:
            # Normalize amenities to lower case for comparison
            required_amenities = [a.lower() for a in amenities]
            
            def has_all_amenities(facility_amenities):
                if not isinstance(facility_amenities, list):
                    return False
                fac_amenities_lower = [a.lower() for a in facility_amenities]
                return all(req in fac_amenities_lower for req in required_amenities)
                
            df = df[df['amenities'].apply(has_all_amenities)]
            
        return df.to_dict('records')

# Global instance (can be initialized later)
_data_manager = None

def get_data_manager():
    global _data_manager
    if _data_manager is None:
        # Assuming data is in project_root/data
        # We need to resolve path relative to this file or project root
        base_path = Path(__file__).parent.parent / "data"
        _data_manager = DataManager(
            str(base_path / "users.json"),
            str(base_path / "facilities.json")
        )
    return _data_manager
