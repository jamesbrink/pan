import sqlite3

def get_user_name(user_id):
    with sqlite3.connect('pan_memory.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None

def add_user(user_id, name):
    with sqlite3.connect('pan_memory.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (user_id, name) VALUES (?, ?)", (user_id, name))
        conn.commit()
