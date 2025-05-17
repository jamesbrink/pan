"""
Memory Management for PAN

This module handles both in-memory and persistent storage of information for PAN.
It manages both short-term and long-term memory, allowing PAN to remember
information across sessions and retain context during conversations.
"""

import sqlite3

from pan_config import DATABASE_PATH, MAX_SHORT_TERM_MEMORY


class PanMemory:
    """
    Manages PAN's in-memory storage system.

    Provides functionality for storing, retrieving, and managing both
    short-term (conversation context) and long-term (key-value pairs) memory.
    """

    def __init__(self):
        """
        Initialize PanMemory with empty memory structures.

        Creates two memory stores:
        - memory: A dictionary for long-term key-value storage
        - short_term_memory: A list for recent conversation context
        """
        self.memory = {}
        self.short_term_memory = []

    def remember(self, key, value):
        """
        Store a value in long-term memory with the given key.

        Args:
            key (str): The key to associate with the value
            value (any): The value to store
        """
        self.memory[key] = value

    def recall(self, key):
        """
        Retrieve a value from long-term memory by its key.

        Args:
            key (str): The key to look up

        Returns:
            any: The stored value, or None if the key doesn't exist
        """
        return self.memory.get(key, None)

    def forget(self, key):
        """
        Remove a value from long-term memory.

        Args:
            key (str): The key to remove
        """
        if key in self.memory:
            del self.memory[key]

    def clear_memory(self):
        """
        Clear all items from long-term memory.
        """
        self.memory.clear()

    def remember_short_term(self, phrase):
        """
        Add a phrase to short-term memory.

        Maintains a rolling window of the most recent items, based on MAX_SHORT_TERM_MEMORY.

        Args:
            phrase (str): The phrase to remember
        """
        self.short_term_memory.append(phrase)
        if len(self.short_term_memory) > MAX_SHORT_TERM_MEMORY:
            self.short_term_memory.pop(0)  # Maintain a maximum number of items

    def recall_short_term(self):
        """
        Retrieve all phrases in short-term memory.

        Returns:
            list: A list of the most recent phrases in short-term memory
        """
        return self.short_term_memory


def remember(topic, content):
    """
    Store a memory in the persistent SQLite database.

    This function adds a new memory to the database, categorized by topic.

    Args:
        topic (str): The category or topic of the memory
        content (str): The content of the memory to store
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (category, content) VALUES (?, ?)", (topic, content)
        )
        conn.commit()


def retrieve_memories(topic=None, limit=5):
    """
    Retrieve memories from the persistent database.

    Args:
        topic (str, optional): If provided, only memories with this category will be retrieved
        limit (int, optional): Maximum number of memories to retrieve, defaults to 5

    Returns:
        list: A list of tuples containing (category, content) for each memory
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        if topic:
            cursor.execute(
                "SELECT category, content FROM memories WHERE category = ? ORDER BY id DESC LIMIT ?",
                (topic, limit),
            )
        else:
            cursor.execute(
                "SELECT category, content FROM memories ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        return cursor.fetchall()


# Global PanMemory instance for in-memory storage
pan_memory = PanMemory()
