import requests
import sqlite3

# Database setup for long-term memory
conn = sqlite3.connect('pan_memory.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY, category TEXT, content TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS opinions (id INTEGER PRIMARY KEY, topic TEXT, opinion TEXT, strength INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS affinity (user_id TEXT PRIMARY KEY, score INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS news_archive (id INTEGER PRIMARY KEY, headline TEXT, date TEXT)''')
conn.commit()

WEATHER_API_KEY = "1cde1e0fa62fea2a862d4089901cf775"
NEWS_API_KEY = "0df5b75db35c4289b12b44030508d563"
DEFAULT_CITY = "Kelso"
DEFAULT_COUNTRY_CODE = "US"

def store_memory(category, content):
    cursor.execute("INSERT INTO memories (category, content) VALUES (?, ?)", (category, content))
    conn.commit()

def store_news_archive(headline):
    import datetime
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO news_archive (headline, date) VALUES (?, ?)", (headline, date))
    conn.commit()

def list_news_archive():
    cursor.execute("SELECT headline, date FROM news_archive ORDER BY date DESC LIMIT 10")
    rows = cursor.fetchall()
    if rows:
        return "Here's a brief news archive: " + ", ".join([f"{date}: {headline}" for headline, date in rows])
    return "I haven't archived any news yet."

def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={DEFAULT_CITY},{DEFAULT_COUNTRY_CODE}&appid={WEATHER_API_KEY}&units=metric"
        print(f"Using weather API key: {WEATHER_API_KEY}")
        print(f"Request URL: {url}")

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        temp = data["main"]["temp"]
        conditions = data["weather"][0]["description"]
        description = f"The current temperature in {DEFAULT_CITY} is {temp}°C with {conditions}."

        print("Weather API call succeeded:", description)
        store_memory('weather', description)
        return description

    except requests.RequestException as e:
        print(f"Weather API request failed: {e}")
        return "Sorry, I couldn't access the weather data."
    except KeyError as e:
        print(f"Weather API response missing expected data: {e}")
        return "Sorry, I couldn't understand the weather data."

def get_local_news():
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}&pageSize=5"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        articles = data.get("articles", [])
        if not articles:
            return "I couldn't find any local news."

        headlines = [article['title'] for article in articles]
        for headline in headlines:
            store_news_archive(headline)
        store_memory('news', ", ".join(headlines))

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
    # Placeholder: Return dummy opinion
    return "I think technology is fascinating."

def adjust_opinion(topic, new_thought):
    # Placeholder: Store or update opinion
    pass

def get_affinity(user_id):
    # Placeholder: Return neutral affinity
    return 0

def warn_low_affinity(user_id):
    affinity = get_affinity(user_id)
    if affinity < -5:
        return "Warning: I don't trust you much."
    return ""

def live_search(query, user_id=None):
    # Placeholder: Return generic message
    return f"Sorry, I couldn't find information on '{query}'."

def multi_step_research(topic, user_id=None):
    # Placeholder stub — extend with multi-step or API chaining logic later
    return live_search(topic, user_id)
