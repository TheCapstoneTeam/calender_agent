# auth.py
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly"
]

CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_FILE = "token.json"

def get_credentials(interactive=True):
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        # Attempt refresh
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                return creds
            except Exception:
                creds = None

        # If still no valid creds → do OAuth login
        if not creds:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError("client_secrets.json missing. Download from Google Cloud OAuth.")

            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )

            creds = flow.run_local_server(port=0)

            # Save token
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

    return creds

def get_calendar_service(interactive=True):
    creds = get_credentials(interactive)
    return build("calendar", "v3", credentials=creds)

if __name__ == "__main__":
    # Quick test: print next 5 events
    service = get_calendar_service()
    events = (
        service.events()
        .list(
            calendarId="primary",
            maxResults=5,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
        .get("items", [])
    )

    if not events:
        print("No events found.")
    else:
        for ev in events:
            start = ev["start"].get("dateTime", ev["start"].get("date"))
            print(f"{start} — {ev.get('summary', '(no title)')}")
