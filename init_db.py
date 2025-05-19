"""
Database Initialization for PAN

This script initializes the PAN database with the necessary tables.
"""

# pylint: disable=duplicate-code
# The duplication with pan_core.py and version.py is intentional
# as this is a standalone bootstrap script

import sqlite3

from pan_config import DATABASE_PATH


def initialize_database():
    """
    Initialize the SQLite database with all required tables.
    """
    print(f"Initializing database at {DATABASE_PATH}...")

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )"""
        )

        # Memories table
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY,
            category TEXT,
            content TEXT
        )"""
        )

        # Opinions table
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS opinions (
            id INTEGER PRIMARY KEY,
            topic TEXT,
            opinion TEXT,
            strength INTEGER
        )"""
        )

        # Affinity table
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS affinity (
            user_id TEXT PRIMARY KEY,
            score INTEGER
        )"""
        )

        # News archive table
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS news_archive (
            id INTEGER PRIMARY KEY,
            headline TEXT,
            date TEXT
        )"""
        )

        conn.commit()

    print("Database initialization complete!")


if __name__ == "__main__":
    initialize_database()
