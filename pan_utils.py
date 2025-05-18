"""
Utility functions for PAN (Personal Assistant with Nuance)

This module provides shared utility functions and common code used across different modules.
"""

import sqlite3

import torch

from pan_config import DATABASE_PATH


def create_quantization_config(quant_level):
    """
    Create a quantization configuration for loading transformer models.

    Args:
        quant_level (str): Quantization level, either "4bit", "8bit", or "none"

    Returns:
        tuple: (quantization_config, bits) where bits is 4, 8, or None, and
              quantization_config is the BitsAndBytesConfig or None
    """
    from transformers import BitsAndBytesConfig

    # Default to no quantization
    quantization_config = None
    bits = None

    try:
        if quant_level.lower() in ("4bit", "8bit"):
            bits = 4 if quant_level.lower() == "4bit" else 8
            # Check if bitsandbytes is available with required features
            try:
                import bitsandbytes

                bnb_version = getattr(bitsandbytes, "__version__", "0.0.0")
                if bits == 4 and tuple(map(int, bnb_version.split("."))) < (0, 41, 0):
                    print(
                        f"Warning: bitsandbytes version {bnb_version} may not support 4-bit quantization. Using 8-bit instead."
                    )
                    bits = 8

                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=bits == 4,
                    load_in_8bit=bits == 8,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
                print(f"Using {bits}-bit quantization for model loading")
            except (ImportError, AttributeError):
                print(
                    "Warning: bitsandbytes not available or not supported, falling back to standard loading"
                )
                bits = None
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(
            f"Warning: Error setting up quantization, falling back to standard loading: {e}"
        )
        bits = None
    return quantization_config, bits


def initialize_database(verbose=True):
    """
    Initialize the SQLite database used by PAN for persistent storage.

    Creates the database and necessary tables if they don't already exist.
    Tables include:
    - users: Store user information
    - memories: Store PAN's memories and knowledge
    - opinions: Store PAN's opinions on various topics
    - affinity: Store relationship scores with different users
    - news_archive: Cache news information to avoid redundant notifications

    Args:
        verbose (bool): Whether to print status messages during initialization

    Returns:
        None
    """
    if verbose:
        print(f"Initializing database at {DATABASE_PATH}...")

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Create tables if they don't exist
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY,
            category TEXT,
            content TEXT
        )"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS opinions (
            id INTEGER PRIMARY KEY,
            topic TEXT,
            opinion TEXT,
            strength INTEGER
        )"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS affinity (
            user_id TEXT PRIMARY KEY,
            score INTEGER
        )"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS news_archive (
            id INTEGER PRIMARY KEY,
            headline TEXT,
            date TEXT
        )"""
        )
        conn.commit()

    if verbose:
        print("Database initialization complete!")
