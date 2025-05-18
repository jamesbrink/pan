"""
Core Initialization and Setup for PAN

This module handles the initialization of PAN's core systems including
database creation and setup. It serves as the foundation for the PAN assistant
by preparing the environment and dependencies before operation.
"""

import sqlite3
import pan_emotions
import pan_speech
from pan_config import DATABASE_PATH

def initialize_database():
    """
    Initialize the SQLite database used by PAN for persistent storage.
    
    Creates the database and necessary tables if they don't already exist.
    Tables include:
    - users: Store user information
    - memories: Store PAN's memories and knowledge
    - opinions: Store PAN's opinions on various topics
    - affinity: Store relationship scores with different users
    - news_archive: Cache news information to avoid redundant notifications
    
    Returns:
        None
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
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
    """
    Initialize all PAN systems and prepare for operation.
    
    This function serves as the main entry point for starting up PAN.
    It initializes the database, sets the default emotional state,
    and prepares all necessary components for operation.
    
    Returns:
        None
    """
    print("Initializing Pan...")
    initialize_database()

    # Set default mood to neutral on startup
    pan_emotions.pan_emotions.mood = "neutral"
    print("Pan is ready and feeling neutral.")

    # Announce startup - commented out because main.py will handle greeting
    # pan_speech.speak("Hello! I'm Pan, ready to help you. How can I assist you today?")
