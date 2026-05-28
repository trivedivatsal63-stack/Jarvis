import sqlite3
import json
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "jarvis.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            trigger_at DATETIME NOT NULL,
            fired INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '',
            tags TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

init_db()

def get_history(session_id: str, limit: int = 20):
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT ?",
        (session_id, limit)
    ).fetchall()
    conn.close()
    messages = []
    for r in reversed(rows):
        messages.append({"role": r["role"], "content": r["content"]})
    return messages

def add_message(session_id: str, role: str, content: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()

def clear_history(session_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

def get_pref(key: str, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM preferences WHERE key = ?", (key,)).fetchone()
    conn.close()
    if row:
        return row["value"]
    return default

def set_pref(key: str, value: str):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()

def add_reminder(message: str, trigger_at: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO reminders (message, trigger_at) VALUES (?, ?)",
        (message, trigger_at)
    )
    conn.commit()
    conn.close()

def get_pending_reminders():
    conn = get_connection()
    now = datetime.datetime.now().isoformat()
    rows = conn.execute(
        "SELECT id, message FROM reminders WHERE fired = 0 AND trigger_at <= ?",
        (now,)
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "message": r["message"]} for r in rows]

def mark_reminder_fired(reminder_id: int):
    conn = get_connection()
    conn.execute("UPDATE reminders SET fired = 1 WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()

def create_note(title: str, content: str = "", tags: str = ""):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO notes (title, content, tags) VALUES (?, ?, ?)",
        (title, content, tags)
    )
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return note_id

def list_notes():
    conn = get_connection()
    rows = conn.execute("SELECT id, title, tags, created_at, updated_at FROM notes ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_note(note_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_note(note_id: int, title: str = None, content: str = None, tags: str = None):
    conn = get_connection()
    fields = []
    values = []
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if content is not None:
        fields.append("content = ?")
        values.append(content)
    if tags is not None:
        fields.append("tags = ?")
        values.append(tags)
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(note_id)
    conn.execute(f"UPDATE notes SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()

def delete_note(note_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

def search_notes(query: str):
    conn = get_connection()
    like = f"%{query}%"
    rows = conn.execute(
        "SELECT id, title, tags, created_at FROM notes WHERE title LIKE ? OR content LIKE ? OR tags LIKE ? ORDER BY updated_at DESC",
        (like, like, like)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
