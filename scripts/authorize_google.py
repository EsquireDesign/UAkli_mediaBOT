"""One-time local Google OAuth setup. Never commit credentials.json or .env."""
from pathlib import Path
from dotenv import set_key
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS = ROOT / "credentials.json"
DOTENV = ROOT / ".env"
SCOPES = ["https://www.googleapis.com/auth/drive"]


def main():
    if not CREDENTIALS.is_file():
        raise SystemExit("Place downloaded Desktop OAuth JSON at ./credentials.json first.")
    if not DOTENV.is_file():
        raise SystemExit("First copy .env.example to .env.")
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS), SCOPES)
    credentials = flow.run_local_server(
        host="localhost",
        port=0,
        open_browser=True,
        access_type="offline",
        prompt="consent",
    )
    if not credentials.refresh_token:
        raise SystemExit("No refresh token returned. Check the OAuth consent configuration.")
    client = flow.client_config["client_id"]
    secret = flow.client_config["client_secret"]
    set_key(str(DOTENV), "GOOGLE_CLIENT_ID", client)
    set_key(str(DOTENV), "GOOGLE_CLIENT_SECRET", secret)
    set_key(str(DOTENV), "GOOGLE_REFRESH_TOKEN", credentials.refresh_token)
    DOTENV.chmod(0o600)
    print("Google authorization completed. Secrets saved locally to .env (not printed).")
    print("Keep credentials.json and .env private and out of GitHub.")


if __name__ == "__main__":
    main()
