# UAkli Media Bot

Telegram bot for collecting photos, videos, and documents from multiple events in dedicated Google Drive folders.

**Status: initial MVP.** The application code is in place but has not yet been connected to a real Telegram bot or Google Drive, or load-tested.

## What is implemented

- One Telegram bot for all participants, with inline event-selection buttons (`/start`, `/events`).
- Separate event selection per Telegram user.
- Admin-only event creation (`/add_event YYYY-MM-DD Event name`) and closure (`/close_event ID`).
- Automatic Google Drive folder creation for new events.
- Photo, video, document intake, durable SQLite upload queue, and upload confirmation.
- Up to three upload attempts, and queue restart recovery.
- Dockerfile, environment variable configuration, and .gitignore.

## Setup

1. Install Python 3.12+ and run `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env`.
3. Create a **new** Telegram bot token through @BotFather and set `TELEGRAM_BOT_TOKEN`. Revoke any token previously shared in a chat.
4. Set `ADMIN_TELEGRAM_IDS` to your numeric Telegram user ID (find it with `/myid`). Separate several IDs with commas.
5. Enable the Google Drive API in a Google Cloud project. Authorize an OAuth client **out of band** with Google Drive scope, and configure `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`. The ChatGPT Google Drive connector cannot substitute for the bot's OAuth credentials. Do not commit secrets.
6. Create a destination folder on your Google Drive and put its folder ID in `GOOGLE_DRIVE_ROOT_FOLDER_ID`.
7. Run `python -m app.main`. Docker is also supported: build the image and run it with an env file and a persistent writable volume at `/opt/app/data`.

Participant workflow: `/start` → choose an event → send media in the bot's private chat → receive queued/success status.

Admin workflow: `/myid` → configure admin ID → `/add_event 2026-11-19 Conference Kyiv` → participants select the event.

## Architecture

- `app/main.py`: Telegram handlers, event menu, queue worker.
- `app/db.py`: SQLite events, selections and upload job state.
- `app/drive.py`: Google Drive folder creation and resumable uploads.
- `data/`: SQLite database and temporary incoming files (ignored by Git).
- `Dockerfile`: deployment image.

## Important limitations

- Normal Telegram hosted Bot API file downloads are limited to **20 MB**. Large videos require a properly configured **local Telegram Bot API server**, with `TELEGRAM_LOCAL_API_URL` and `TELEGRAM_LOCAL_FILE_URL`, and integration testing.
- The current worker processes one file at a time. Concurrent uploads and large-file behavior have not been validated.
- Photos sent as Telegram photos may already be compressed; send as documents to preserve original bytes.
- A process crash after an upload succeeds but before completion is recorded may create a duplicate Google Drive file on retry. Exactly-once reconciliation is not yet implemented.
- Jobs that fail three times need manual remediation; no admin retry command exists yet.
- OAuth setup/refresh credentials, bot token, hosting, monitoring, and backup are the operator's responsibility.
- No production end-to-end testing, performance testing, or security review has been completed.
- Private chat only; the bot does not monitor Telegram groups.

## Development reference

[Alirewa/tg-bot-uploader-drive](https://github.com/Alirewa/tg-bot-uploader-drive) was researched as a reference. This repository's initial Python source was authored independently, not copied from that repository.

## License

Not yet selected.
