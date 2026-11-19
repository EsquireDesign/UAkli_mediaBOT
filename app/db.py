"""SQLite persistence for events, selections, and upload jobs."""
import sqlite3
from pathlib import Path


class Store:
    def __init__(self, data_dir: str):
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        self.path = str(Path(data_dir) / "bot.sqlite3")
        with self.connect() as c:
            c.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    event_date TEXT NOT NULL,
                    folder_id TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS selections (
                    user_id INTEGER PRIMARY KEY,
                    event_id INTEGER NOT NULL REFERENCES events(id)
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    event_id INTEGER NOT NULL REFERENCES events(id),
                    telegram_file_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    drive_file_id TEXT,
                    error TEXT,
                    UNIQUE(chat_id, message_id)
                );
            """)
            c.execute("UPDATE jobs SET status = 'queued' WHERE status = 'processing'")

    def connect(self):
        c = sqlite3.connect(self.path, timeout=30)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        return c

    def add_event(self, name, event_date, folder_id):
        with self.connect() as c:
            cur = c.execute("INSERT INTO events(name,event_date,folder_id) VALUES(?,?,?)",
                            (name, event_date, folder_id))
            return cur.lastrowid

    def active_events(self):
        with self.connect() as c:
            return c.execute("SELECT * FROM events WHERE active=1 ORDER BY event_date DESC,id DESC").fetchall()

    def get_event(self, event_id):
        with self.connect() as c:
            return c.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()

    def close_event(self, event_id):
        with self.connect() as c:
            return c.execute("UPDATE events SET active=0 WHERE id=? AND active=1", (event_id,)).rowcount

    def select(self, user_id, event_id):
        with self.connect() as c:
            row = c.execute("SELECT id FROM events WHERE id=? AND active=1", (event_id,)).fetchone()
            if not row:
                return False
            c.execute("INSERT INTO selections(user_id,event_id) VALUES(?,?) "
                      "ON CONFLICT(user_id) DO UPDATE SET event_id=excluded.event_id", (user_id,event_id))
            return True

    def selected_event(self, user_id):
        with self.connect() as c:
            return c.execute(
                "SELECT e.* FROM selections s JOIN events e ON e.id=s.event_id "
                "WHERE s.user_id=? AND e.active=1", (user_id,)
            ).fetchone()

    def enqueue(self, chat_id, message_id, user_id, event_id, file_id, filename, mime_type):
        with self.connect() as c:
            cur = c.execute(
                "INSERT OR IGNORE INTO jobs(chat_id,message_id,user_id,event_id,"
                "telegram_file_id,filename,mime_type) VALUES(?,?,?,?,?,?,?)",
                (chat_id,message_id,user_id,event_id,file_id,filename,mime_type)
            )
            return bool(cur.rowcount)

    def next_job(self):
        with self.connect() as c:
            row = c.execute(
                "SELECT j.*,e.folder_id FROM jobs j JOIN events e ON e.id=j.event_id "
                "WHERE j.status='queued' ORDER BY j.id LIMIT 1"
            ).fetchone()
            if row:
                c.execute("UPDATE jobs SET status='processing',attempts=attempts+1 WHERE id=?", (row["id"],))
            return dict(row) if row else None

    def completed(self, job_id, drive_id):
        with self.connect() as c:
            c.execute("UPDATE jobs SET status='done',drive_file_id=?,error=NULL WHERE id=?",
                      (drive_id,job_id))

    def failed(self, job_id, error, retry):
        with self.connect() as c:
            c.execute("UPDATE jobs SET status=?,error=? WHERE id=?",
                      ("queued" if retry else "failed",str(error)[:1000],job_id))
