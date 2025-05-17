"""
Research and Web Capabilities for PAN

This module provides PAN with the ability to gather information from the internet, 
manage opinions, track user affinity, and access web APIs for real-time data like
weather and news. It serves as PAN's connection to external data sources.
"""

import requests
from bs4 import BeautifulSoup
import pan_settings

# Free Web Search using DuckDuckGo with Google Fallback
def live_search(query):
    response = duckduckgo_search(query)
    if "Error" in response or "Sorry" in response:
        print("DuckDuckGo failed, trying Google...")
        response = google_search(query)
    return response

# DuckDuckGo Search
def duckduckgo_search(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://html.duckduckgo.com/html?q={query.replace(' ', '+')}"
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        results = [a.get_text() for a in soup.find_all('a', class_='result__a')]
        return results[0] if results else "No relevant result found."
    
    return "Error: Could not connect to DuckDuckGo."

# Google Search (Fallback)
def google_search(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        results = [g.get_text() for g in soup.find_all('h3')]
        return results[0] if results else "No relevant result found."
    
    return "Error: Could not connect to Google."

# Weather Functionality (OpenWeatherMap API)
def get_weather(city="Kelso", country_code="US"):
    api_key = pan_settings.OPENWEATHERMAP_API_KEY
    if not api_key:
        return "Weather API key is missing in settings."

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country_code}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        return f"The current temperature in {city} is {temp}°C with {description}."
    except:
        return "Sorry, I couldn't fetch the weather data."

# Local News Functionality (NewsAPI)
def get_local_news():
    api_key = pan_settings.NEWS_API_KEY
    if not api_key:
        return "News API key is missing in settings."
    
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
    try:
        response = requests.get(url)
        articles = response.json().get("articles", [])
        headlines = [article["title"] for article in articles[:5]]
        return "Here are the latest news headlines: " + ", ".join(headlines) if headlines else "No news available."
    except:
        return "Sorry, I couldn't fetch the local news."

# Archive for Past News
def list_news_archive():
    archive = [
        "NASA's Artemis mission launches successfully.",
        "OpenAI releases GPT-5 with enhanced capabilities.",
        "Global temperatures hit record highs in 2025."
    ]
    return "Here's a brief news archive: " + ", ".join(archive)

# User Opinions (Dynamic and Configurable)
def list_opinions(user_id, share=False):
    opinions = {
        "AI": "I think AI is a powerful tool that can help humanity.",
        "Climate Change": "I believe we should take action to protect the environment.",
        "Space Exploration": "Exploring the universe is humanity's greatest adventure."
    }
    if share:
        return "Here's what I think: " + ", ".join([f"{topic}: {opinion}" for topic, opinion in opinions.items()])
    return "I have opinions on several topics. Ask me about AI, climate change, or space exploration."

# Adjust User Opinions
def adjust_opinion(topic, new_thought):
    print(f"Adjusting opinion on {topic} to: {new_thought}")

# User Affinity Tracking (Simple Example)
user_affinity = {}

def get_affinity(user_id):
    return user_affinity.get(user_id, 0)

def warn_low_affinity(user_id):
    affinity = get_affinity(user_id)
    if affinity < -5:
        return "Warning: I don't trust you much."
    return ""

# Multi-Step Research (Extensible)
def multi_step_research(topic, user_id=None):
    response = live_search(topic)
    if "Sorry" in response:
        response = f"I couldn't find detailed information on {topic}."
    return response
