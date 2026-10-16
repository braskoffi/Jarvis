import os, sqlite3
from contextlib import contextmanager

DB_PATH = os.getenv("DATABASE_PATH", "jarvis.db")

@contextmanager
def connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with connection() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL,
          password_hash TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          role TEXT NOT NULL CHECK(role IN ('user','assistant')), content TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id,id);
        CREATE TABLE IF NOT EXISTS pending_actions(id TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          action_type TEXT NOT NULL, payload TEXT NOT NULL, status TEXT DEFAULT 'pending');
        ''')

def create_user(email, password_hash):
    with connection() as c:
        cur = c.execute("INSERT INTO users(email,password_hash) VALUES (?,?)", (email,password_hash))
        return cur.lastrowid

def get_user_by_email(email):
    with connection() as c: return c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

def get_user_by_id(uid):
    with connection() as c: return c.execute("SELECT id,email FROM users WHERE id=?", (uid,)).fetchone()

def add_message(uid, role, content):
    with connection() as c: c.execute("INSERT INTO messages(user_id,role,content) VALUES (?,?,?)", (uid,role,content))

def get_messages(uid, limit=40):
    with connection() as c:
        rows = c.execute("SELECT role,content,created_at FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid,limit)).fetchall()
    return [dict(r) for r in reversed(rows)]

def clear_messages(uid):
    with connection() as c: c.execute("DELETE FROM messages WHERE user_id=?", (uid,))

def add_action(aid, uid, kind, payload):
    with connection() as c: c.execute("INSERT INTO pending_actions(id,user_id,action_type,payload) VALUES (?,?,?,?)", (aid,uid,kind,payload))

def pending_action(aid, uid):
    with connection() as c:
        r = c.execute("SELECT * FROM pending_actions WHERE id=? AND user_id=? AND status='pending'", (aid,uid)).fetchone()
        return dict(r) if r else None

def finish_action(aid, uid):
    with connection() as c: c.execute("UPDATE pending_actions SET status='confirmed_demo' WHERE id=? AND user_id=? AND status='pending'", (aid,uid))
