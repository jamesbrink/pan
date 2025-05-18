# PAN - Personal AI Assistant

PAN is a customizable, voice-activated personal AI assistant designed to provide real-time information, manage conversations, perform research, and offer a conversational experience using cutting-edge AI technology.

## 🚀 Features

* **Voice Interaction:**

  * Natural text-to-speech (TTS) using SAPI5 (Windows) or espeak (Linux).
  * Voice recognition with Google Speech API (online) and VOSK (offline).
  * Customizable speech rate and volume based on user mood.

* **Intelligent Response Generation:**

  * Generates context-aware responses using GPT-Neo.
  * Supports dynamic memory management, maintaining context without repetition.

* **Command Detection:**

  * Recognizes direct commands such as "news" and "weather."
  * Instantly provides the latest news headlines and local weather.

* **Advanced Web Capabilities:**

  * Live search with DuckDuckGo and Google fallback.
  * Fetches news and weather using API integrations.

* **Interruptible Interaction:**

  * Users can say "stop," "cancel," or "halt" to immediately stop response generation or speaking.

* **Configurable Settings:**

  * API keys for weather and news are stored securely in `pan_settings.py`.
  * Speech rate, volume, and mood are customizable.

---

## 📌 Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/PAN.git
   cd PAN
   ```

2. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys (Weather and News):**

   * Open `pan_settings.py`.
   * Set your OpenWeatherMap API key:

     ```python
     OPENWEATHERMAP_API_KEY = "YOUR_OPENWEATHER_API_KEY"
     ```
   * Set your NewsAPI key:

     ```python
     NEWS_API_KEY = "YOUR_NEWSAPI_KEY"
     ```

4. **Run PAN:**

   ```bash
   python main.py
   ```

---

## 🗣 Usage

### **Voice Interaction**

* Simply speak to PAN. It will respond with natural speech.
* You can interrupt PAN at any time by saying "stop", "cancel", or "halt".

### **Commands**

* **"What's the weather?"** - PAN will provide the latest weather information.
* **"Give me the latest news."** - PAN will fetch the latest news headlines.
* **"Tell me about \[topic]."** - PAN will use its AI model to generate an informative response.

### **Research and Web Search**

* PAN can search the web using DuckDuckGo with Google as a fallback.
* If direct answers are not available, it will summarize the top search result.

---

## ⚙️ Configuration

### `pan_settings.py`

* **API Keys:**

  * Set your OpenWeatherMap and NewsAPI keys for full functionality.
* **Speech Settings:**

  * Adjust the default voice rate and volume.
  * Set default mood-based voice tones.

### Customization

* You can easily add new commands in `pan_conversation.py`.
* Modify TTS settings directly in `pan_speech.py`.
* Integrate additional APIs in `pan_research.py`.

---

## 📌 File Structure

```
PAN/
├── main.py             # Main entry point
├── pan_ai.py           # AI response generation using GPT-Neo
├── pan_conversation.py # Manages conversation flow and commands
├── pan_speech.py       # Handles text-to-speech and voice recognition
├── pan_research.py     # Manages news, weather, and web search
├── pan_settings.py     # Configurable settings (API keys, voice settings)
└── requirements.txt    # List of dependencies
```

---

## 🌐 API Integrations

* **OpenWeatherMap API** (for weather information)
* **NewsAPI** (for latest news headlines)
* **Google Speech API (Online)** and **VOSK (Offline)** for voice recognition

---

## 🚨 Troubleshooting

### Common Issues

* **PAN repeats user text:** Ensure `pan_conversation.py` is using the clean memory version.
* **Weather or news not working:** Make sure API keys are set in `pan_settings.py`.
* **Speech is too fast:** Adjust the speech rate in `pan_speech.py`.

### Debugging

* Use the command line to view debug logs.
* Error messages will indicate if an API key is missing.

---

## ✅ Future Improvements

* Add support for more APIs (e.g., sports scores, stock prices).
* Enhance offline voice recognition with improved VOSK models.
* Expand TTS support to other platforms (macOS).

---

## 💡 Contributing

1. Fork the repository.
2. Create a new branch (`feature/new-feature`).
3. Commit your changes (`git commit -m "Add new feature"`).
4. Push to the branch (`git push origin feature/new-feature`).
5. Create a Pull Request.

---

## 📄 License

This project is licensed under the MIT License.

---

## ❤️ Credits

* Developed by Kelsi Davis.
* Voice recognition powered by Google Speech API and VOSK.
* News and weather powered by NewsAPI and OpenWeatherMap.
