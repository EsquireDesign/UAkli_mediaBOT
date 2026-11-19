"""Google Drive integration using organizer-owned OAuth refresh credentials."""
import re
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]


def service(settings):
    required = ("GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET","GOOGLE_REFRESH_TOKEN")
    missing = [k for k in required if not settings.get(k)]
    if missing:
        raise RuntimeError("Missing Google credentials: " + ", ".join(missing))
    credentials = Credentials(
        token=None,
        refresh_token=settings["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings["GOOGLE_CLIENT_ID"],
        client_secret=settings["GOOGLE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    credentials.refresh(Request())
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def create_event_folder(settings, event_date, name):
    parent = settings.get("GOOGLE_DRIVE_ROOT_FOLDER_ID")
    if not parent:
        raise RuntimeError("GOOGLE_DRIVE_ROOT_FOLDER_ID not configured")
    folder_name = event_date + "_" + re.sub(r"[^\w .-]+", "_", name, flags=re.UNICODE).strip(" ._")
    metadata = {"name":folder_name, "mimeType":"application/vnd.google-apps.folder","parents":[parent]}
    result = service(settings).files().create(body=metadata, fields="id").execute()
    return result["id"]


def upload(settings, local_path, folder_id, filename, mime_type):
    media = MediaFileUpload(str(local_path), mimetype=mime_type,
                            resumable=True, chunksize=8 * 1024 * 1024)
    request = service(settings).files().create(
        body={"name":filename, "parents":[folder_id]},
        media_body=media, fields="id"
    )
    response = None
    while response is None:
        _, response = request.next_chunk()
    return response["id"]
