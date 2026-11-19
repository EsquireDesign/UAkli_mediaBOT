# Telegram Event Media Bot

A Telegram bot for collecting, organizing, and automatically uploading photos and videos from multiple events to Google Drive.

## 🎯 Project Overview

Telegram Event Media Bot is designed for event organizers, production teams, conferences, festivals, concerts, and other events where multiple participants need to submit their media files to one centralized storage location.

Instead of creating separate Telegram bots or chats for each event, organizers can use **one Telegram bot with an interactive event selection menu**.

Participants select an event, upload their media, and the bot automatically saves their files to the corresponding Google Drive folder.

## ✨ Planned Features

### For Participants

- Select an event using Telegram inline buttons.
- Upload photos, videos, and documents.
- Upload multiple files and media albums.
- Automatically route files to the selected event.
- Switch between events at any time.
- Receive upload confirmations and error notifications.
- No Google account required for participants.

### For Administrators

- Create, edit, and close events.
- Assign event names and dates.
- Automatically create event-specific Google Drive folders.
- Manage the list of available events.
- Monitor upload status and failures.
- Manage authorized administrators.

### File Management

- Centralized Google Drive storage.
- Separate folders for each event.
- Preserve original file contents without additional re-encoding.
- Persistent upload queue.
- Automatic retries after temporary failures.
- Duplicate upload protection.
- Recovery after application restarts.
- Support for large media files, subject to Telegram API limits and deployment configuration.

## 🔄 How It Works

**1. Event Creation**

An administrator creates an event:

`Conference Kyiv — 2026-11-19`

The bot associates the event with a dedicated Google Drive folder.

**2. Event Selection**

A participant opens the Telegram bot and selects an event from the available buttons.

**3. Media Submission**

The participant sends photos, videos, or documents directly to the bot.

**4. Automatic Processing**

The bot records the selected event for each incoming file, queues the upload, and transfers the media to Google Drive.

**5. Organized Storage**

Example directory structure:

    Event Media Archive/
    ├── 2026-11-19_Conference_Kyiv/
    │   ├── photo_001.jpg
    │   ├── photo_002.jpg
    │   └── video_001.mp4
    ├── 2026-11-20_Concert/
    │   ├── photo_001.jpg
    │   └── video_001.mp4
    └── 2026-11-21_Festival/
        └── photo_001.jpg

## 🏗️ Planned Architecture

| Component | Technology |
|---|---|
| Programming language | Python |
| Telegram integration | Pyrogram or python-telegram-bot |
| User interface | Telegram Inline Keyboard |
| Database | SQLite |
| Cloud storage | Google Drive API v3 |
| Authentication | Google OAuth 2.0 |
| Deployment | Docker |
| Hosting | Linux VPS / Google Cloud VM |

### Processing Flow

Telegram User → Telegram Bot → Event Selection → Persistent Upload Queue → Media Processor → Google Drive → Event Folder

Each uploaded file is assigned to an event when the message is received, preventing incorrect routing if the participant switches events while uploads are in progress.

## 🔐 Security

The project is designed around the following principles:

- Only authorized administrators can manage events.
- Participants do not need access to Google Drive.
- Telegram tokens and Google credentials must never be committed to GitHub.
- Sensitive credentials are stored in secure deployment configuration.
- Upload operations are verified before temporary files are removed.
- Application permissions should follow the principle of least privilege.

## 🚀 Development Roadmap

### Phase 1 — Core Bot
- [ ] Initialize project structure.
- [ ] Configure Telegram integration.
- [ ] Implement event selection buttons.
- [ ] Create administrator commands.
- [ ] Implement SQLite database.

### Phase 2 — Google Drive Integration
- [ ] Configure Google Drive OAuth authentication.
- [ ] Implement automatic folder creation.
- [ ] Implement photo and video uploads.
- [ ] Implement persistent upload queue.
- [ ] Add retry and duplicate protection.

### Phase 3 — Deployment
- [ ] Create Docker configuration.
- [ ] Configure environment variables.
- [ ] Prepare Linux deployment instructions.
- [ ] Implement logging and health checks.
- [ ] Test multiple concurrent participants.
- [ ] Test large files and recovery after restarts.

## 📦 Project Status

**Status: Planning / Initial Development**

The architecture and requirements are defined. Implementation and integration testing are pending.

The application is not yet ready for production use.

## 🛠️ Reference Project

Initial technical reference:

[Alirewa/tg-bot-uploader-drive](https://github.com/Alirewa/tg-bot-uploader-drive)

The planned implementation will adapt the Telegram-to-Google-Drive workflow for centralized event management instead of individual user storage.

Any reused source code will retain the applicable original license and copyright notices.

## 📄 License

To be determined before the first public release.

---

**Telegram Event Media Bot**

One bot. Multiple events. Organized media storage.
