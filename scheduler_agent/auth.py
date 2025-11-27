# auth.py
import os
import pathlib
from dotenv import load_dotenv
from datetime import datetime

# Google OAuth libraries
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# --- Load .env ---
load_dotenv()


# --- Constants ---
SCOPES = ["https://www.googleapis.com/auth/calendar"]

PROJECT_DIR = pathlib.Path(__file__).parent
TOKEN_PATH = PROJECT_DIR / "../token.json"
CREDENTIALS_FILE = PROJECT_DIR / "../credentials.json"   # <-- YOU MUST PROVIDE THIS


# ---------------------------------------------------
#   API KEY FOR AGENT (Gemini / ADK)
# ---------------------------------------------------
def get_api_key():
    key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not key:
        raise RuntimeError(
            "Missing GENAI_API_KEY. Create a .env file with:\nGENAI_API_KEY=your_api_key"
        )

    # Ensure ADK can pick it up
    os.environ["GENAI_API_KEY"] = key
    os.environ["GOOGLE_API_KEY"] = key
    return key


# ---------------------------------------------------
#   Get OAuth Credentials (load / refresh / create)
# ---------------------------------------------------
def get_credentials():
    creds = None

    # 1) Load existing token.json
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # 2) If token exists but expired → refresh
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None  # force new OAuth login

    # 3) If no valid creds → run OAuth
    if not creds:
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                "Missing credentials.json.\n"
                "Download your OAuth CLIENT ID (Desktop App) from Google Cloud and place it here:\n"
                f"{CREDENTIALS_FILE}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)

        # Save token.json
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

        print(f"OAuth completed. token.json saved at:\n{TOKEN_PATH}")

    return creds


# ---------------------------------------------------
#   Calendar API service
# ---------------------------------------------------
def get_calendar_service():
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    return service



# ---------------------------------------------------
# Manual test (optional)
# ---------------------------------------------------
if __name__ == "__main__":
    print("Running OAuth...")
    service = get_calendar_service()
    print("Google Calendar service is ready!")
