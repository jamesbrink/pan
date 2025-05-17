# pan_core.py - Core Initialization and Setup for Pan

import sqlite3
import pan_emotions
import pan_speech

def initialize_database():
    with sqlite3.connect('pan_memory.db') as conn:
        cursor = conn.cursor()
        # Create tables if they don't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY,
            category TEXT,
            content TEXT
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS opinions (
            id INTEGER PRIMARY KEY,
            topic TEXT,
            opinion TEXT,
            strength INTEGER
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS affinity (
            user_id TEXT PRIMARY KEY,
            score INTEGER
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS news_archive (
            id INTEGER PRIMARY KEY,
            headline TEXT,
            date TEXT
        )''')
        conn.commit()

def initialize_pan():
    print("Initializing Pan...")
    initialize_database()

    # Set default mood to neutral on startup
    pan_emotions.pan_emotions.mood = "neutral"
    print("Pan is ready and feeling neutral.")

    # Announce startup
    # pan_speech.speak("Hello! I'm Pan, ready to help you. How can I assist you today?")
