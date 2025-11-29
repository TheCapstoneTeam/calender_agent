from ..data_manager import get_data_manager

def get_team_members(team_name: str) -> str:
    """
    Returns a comma-separated list of email addresses for a given team.
    Useful for resolving "TeamElla" to actual attendees.
    """
    dm = get_data_manager()
    emails = dm.get_team_members(team_name)
    return ", ".join(emails)

def get_user_details(email_or_name: str) -> dict:
    """
    Returns full details for a user including country and timezone.
    Args:
        email_or_name: Email address or username
    Returns:
        Dictionary with user details or empty dict if not found
    """
    dm = get_data_manager()
    details = dm.get_user_details(email_or_name)
    return details if details else {}
