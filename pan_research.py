"""
Research and Web Capabilities for PAN

This module provides PAN with the ability to gather information from the internet,
manage opinions, track user affinity, and access web APIs for real-time data like
weather and news. It serves as PAN's connection to external data sources.
"""

import sqlite3

import requests  # type: ignore # Missing type stubs

from pan_config import (
    DATABASE_PATH,
    DEFAULT_CITY,
    DEFAULT_COUNTRY_CODE,
    NEWS_API_KEY,
    WEATHER_API_KEY,
)

# Database setup for long-term memory
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()
cursor.execute(
    """CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY, category TEXT, content TEXT)"""
)
cursor.execute(
    """CREATE TABLE IF NOT EXISTS opinions (id INTEGER PRIMARY KEY, topic TEXT, opinion TEXT, strength INTEGER)"""
)
cursor.execute(
    """CREATE TABLE IF NOT EXISTS affinity (user_id TEXT PRIMARY KEY, score INTEGER)"""
)
cursor.execute(
    """CREATE TABLE IF NOT EXISTS news_archive (id INTEGER PRIMARY KEY, headline TEXT, date TEXT)"""
)
conn.commit()


def store_memory(category, content):
    """
    Store information in the memories database table.

    Args:
        category (str): The category or type of memory
        content (str): The content to store
    """
    cursor.execute(
        "INSERT INTO memories (category, content) VALUES (?, ?)", (category, content)
    )
    conn.commit()


def store_news_archive(headline):
    """
    Store a news headline in the news archive with the current timestamp.

    Args:
        headline (str): The news headline to archive
    """
    import datetime

    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO news_archive (headline, date) VALUES (?, ?)", (headline, date)
    )
    conn.commit()


def list_news_archive():
    """
    Retrieve and format the most recent news headlines from the archive.

    Returns:
        str: A formatted string containing recent news headlines with dates
    """
    cursor.execute(
        "SELECT headline, date FROM news_archive ORDER BY date DESC LIMIT 10"
    )
    rows = cursor.fetchall()
    if rows:
        return "Here's a brief news archive: " + ", ".join(
            [f"{date}: {headline}" for headline, date in rows]
        )
    return "I haven't archived any news yet."


def get_weather():
    """
    Retrieve current weather information for the default city.

    Makes a request to the OpenWeatherMap API, parses the response,
    stores the data in memory, and returns a formatted weather description.

    Returns:
        str: A formatted description of the current weather conditions
    """
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={DEFAULT_CITY},{DEFAULT_COUNTRY_CODE}&appid={WEATHER_API_KEY}&units=metric"
        print(f"Using weather API key: {WEATHER_API_KEY}")
        print(f"Request URL: {url}")

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        temp = data["main"]["temp"]
        conditions = data["weather"][0]["description"]
        description = (
            f"The current temperature in {DEFAULT_CITY} is {temp}°C with {conditions}."
        )

        print("Weather API call succeeded:", description)
        store_memory("weather", description)
        return description

    except requests.RequestException as e:
        print(f"Weather API request failed: {e}")
        return "Sorry, I couldn't access the weather data."
    except KeyError as e:
        print(f"Weather API response missing expected data: {e}")
        return "Sorry, I couldn't understand the weather data."


def get_local_news():
    """
    Retrieve the latest news headlines from NewsAPI.

    Makes a request to the NewsAPI, parses the response for headlines,
    stores them in both the news archive and memory, and returns a
    formatted summary of the latest news.

    Returns:
        str: A formatted summary of the latest news headlines
    """
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}&pageSize=5"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = data.get("articles", [])
        if not articles:
            return "I couldn't find any local news."

        headlines = [article["title"] for article in articles]
        for headline in headlines:
            store_news_archive(headline)
        store_memory("news", ", ".join(headlines))

        news_summary = "Here are the latest news headlines: " + ", ".join(headlines)
        print("News API call succeeded:", news_summary)
        return news_summary

    except requests.RequestException as e:
        print(f"News API request failed: {e}")
        return "Sorry, I couldn't access the local news data."
    except KeyError as e:
        print(f"News API response missing expected data: {e}")
        return "Sorry, I couldn't understand the news data."


def list_opinions(user_id, share=False):
    """
    Retrieve and list PAN's opinions on various topics.

    Args:
        user_id (str): The ID of the user requesting opinions
        share (bool, optional): Whether to share opinions readily. Defaults to False.

    Returns:
        str: Formatted text of PAN's opinions
    """
    # Placeholder: Return dummy opinion
    # Parameters are unused in this placeholder implementation
    _ = user_id  # Mark as used
    _ = share  # Mark as used
    return "I think technology is fascinating."


def adjust_opinion(topic, new_thought):
    """
    Update PAN's opinion on a specific topic.

    Args:
        topic (str): The topic to adjust the opinion on
        new_thought (str): The new opinion content
    """
    # Placeholder: Store or update opinion
    # Parameters are unused in this placeholder implementation
    _ = topic  # Mark as used
    _ = new_thought  # Mark as used
    # Implementation will be added later


def get_affinity(user_id):
    """
    Retrieve the affinity score for a specific user.

    Affinity represents how much PAN trusts or likes a user.

    Args:
        user_id (str): The ID of the user to check

    Returns:
        int: The affinity score (negative = distrust, positive = trust)
    """
    # Placeholder: Return neutral affinity
    # Parameter is unused in this placeholder implementation
    _ = user_id  # Mark as used
    return 0


def warn_low_affinity(user_id):
    """
    Generate a warning message if user has low affinity.

    Args:
        user_id (str): The ID of the user to check

    Returns:
        str: Warning message if affinity is low, empty string otherwise
    """
    affinity = get_affinity(user_id)
    if affinity < -5:
        return "Warning: I don't trust you much."
    return ""


def live_search(query, user_id=None):
    """
    Perform a web search for the given query.

    Args:
        query (str): The search query text
        user_id (str, optional): The ID of the user making the request.
                                Defaults to None.

    Returns:
        str: Search results or an error message
    """
    # Placeholder: Return generic message
    # user_id parameter is unused in this placeholder implementation
    _ = user_id  # Mark as used
    return f"Sorry, I couldn't find information on '{query}'."


def multi_step_research(topic, user_id=None):
    """
    Perform a multi-step research process on a complex topic.

    This function is intended for more in-depth research that may
    involve multiple API calls, database lookups, or inference steps.

    Args:
        topic (str): The research topic
        user_id (str, optional): The ID of the user making the request.
                                Defaults to None.

    Returns:
        str: Research results or an error message
    """
    # Placeholder stub — extend with multi-step or API chaining logic later
    # Simply delegates to live_search in this placeholder implementation
    return live_search(topic, user_id)
