import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]

def get_gmail_credentials():
    creds = None
    token_path = ".credentials/token.json"
    creds_path = ".credentials/credentials.json"

    # ensure directory exists
    os.makedirs(os.path.dirname(token_path), exist_ok=True)

    # 1) load existing token if present
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        # 1a) if the saved token's scopes don't cover all current SCOPES, discard it
        if not creds.scopes or not set(SCOPES).issubset(set(creds.scopes)):
            print("⚠️  Token scopes have changed; discarding old token.json")
            creds = None

    # 2) if no valid creds, do the flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # 3) save the new token
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())
        print(f"🆕 Wrote new token to {token_path}")

    return creds

if __name__ == "__main__":
    creds = get_gmail_credentials()
    if creds:
        print("✅ Successfully obtained Gmail credentials.")
    else:
        print("❌ Failed to obtain Gmail credentials.")