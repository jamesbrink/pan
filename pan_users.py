"""
User Management Module for PAN

This module handles user-related functionality including identification, 
persistence, and retrieval of user information. It provides a simple interface
to the users table in the SQLite database.
"""

import sqlite3
from pan_config import DATABASE_PATH

def get_user_name(user_id):
    """
    Retrieve a user's name from the database using their ID.
    
    Args:
        user_id (str): The unique identifier for the user
        
    Returns:
        str or None: The user's name if found, None otherwise
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None

def add_user(user_id, name):
    """
    Add a new user to the database or update an existing user.
    
    This function uses INSERT OR REPLACE to either create a new user record
    or update an existing user with the same ID.
    
    Args:
        user_id (str): The unique identifier for the user
        name (str): The user's name
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (user_id, name) VALUES (?, ?)", (user_id, name))
        conn.commit()
