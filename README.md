# PAN - Personal Assistant with Nuance

PAN is a personality-based voice recognition digital assistant that combines emotional intelligence, memory, and conversational capabilities to create a more natural and engaging user experience.

## Features

- **Voice Recognition**: Understand and respond to spoken commands
- **Text-to-Speech**: Reply with emotionally nuanced voice output
- **Emotional Intelligence**: Dynamic mood system that affects responses
- **Memory**: Persistent storage of information and user interactions
- **Web Research**: Gather information from the internet when needed
- **User Recognition**: Adapt to different users and store preferences
- **Autonomous Learning**: Curiosity-driven research when idle

## Getting Started

### Prerequisites

- Python 3.11+
- Nix package manager (for development environment)

### Installation

#### Using Nix (Recommended)

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/pan.git
   cd pan
   ```

2. Create a configuration file:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file and add your API keys (see API Keys section below).

3. Set up the development environment using Nix:
   ```bash
   nix develop
   ```

4. Initialize the database:
   ```bash
   python init_db.py
   # or
   make init
   ```

5. Run the application:
   ```bash
   python main.py
   ```

#### Without Nix

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/pan.git
   cd pan
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install system dependencies:
   - **macOS**: `brew install portaudio ffmpeg espeak`
   - **Linux**: `sudo apt-get install portaudio19-dev python3-pyaudio ffmpeg espeak`
   - **Windows**: Install PyAudio from a wheel file if pip install fails

5. Create a configuration file:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your API keys.

6. Initialize the database:
   ```bash
   python init_db.py
   ```

7. Run the application:
   ```bash
   python main.py
   ```

### Required API Keys

PAN requires the following API keys to access external services:

1. **Weather API Key** (OpenWeatherMap)
   - Sign up at [OpenWeatherMap](https://openweathermap.org/api)
   - Create a free API key
   - Add to your `.env` file as `WEATHER_API_KEY=your_key_here`

2. **News API Key** (NewsAPI)
   - Sign up at [NewsAPI](https://newsapi.org/)
   - Create a free API key
   - Add to your `.env` file as `NEWS_API_KEY=your_key_here`

Example `.env` file:
```
# Database settings
DATABASE_PATH=pan_memory.db

# API keys
WEATHER_API_KEY=abc123yourapikeyhere
NEWS_API_KEY=xyz789yourapikeyhere

# Location settings
DEFAULT_CITY=Kelso
DEFAULT_COUNTRY_CODE=US

# Voice settings
DEFAULT_VOICE_RATE=160
DEFAULT_VOICE_VOLUME=0.9

# Conversation settings
MAX_SHORT_TERM_MEMORY=10
IDLE_THRESHOLD_SECONDS=300
MIN_SPEECH_INTERVAL_SECONDS=15
```

## Development Tasks

PAN uses several tools to maintain code quality:

- **Black**: Code formatter that follows PEP 8 guidelines
- **Pylint**: Code linter to catch errors and enforce style
- **isort**: Import sorter to organize Python imports

You can use the Makefile to run these tools:

```bash
# Format code with black and isort
make format

# Run linting with pylint
make lint

# Run tests
make test

# Run tests with coverage report
make coverage

# Run type checking
make type

# Initialize database
make init

# Run all development tasks
make all

# Show available commands
make help
```

### Pre-commit Hooks

PAN uses pre-commit hooks to ensure code quality before committing changes. To set up pre-commit:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install
```

The pre-commit hooks will automatically run:
- Black (code formatting)
- isort (import sorting)
- Pylint (code linting)
- Trailing whitespace cleanup
- End-of-file fixer
- YAML syntax check
- Check for large files

## Usage Guide

PAN is designed to be interacted with through voice commands. When you run the application, it will greet you and listen for your commands. Press CTRL+C at any time to exit gracefully.

### Basic Interactions

- **Greetings**: "Hello", "Hi", "Hey", "Greetings"
  - *PAN responds with a greeting and asks how it can help*
  
- **Well-being**: "How are you?", "How do you feel?"
  - *PAN shares its current emotional state*
  
- **Exit**: "Exit program"
  - *PAN will say goodbye and shut down*

### Information Requests

- **General Information**: "Tell me about [topic]", "Explain [topic]"
  - *Example: "Tell me about climate change"*
  - *PAN researches the topic and provides information*

- **Weather**: "Weather", "What's the weather like?"
  - *PAN reports current weather conditions for your configured location*
  
- **News**: "News", "What's happening today?"
  - *PAN shares recent news headlines*
  
- **News Archive**: "News archive", "Show me the news archive"
  - *PAN retrieves previously stored news*
  
- **Web Search**: "Search for [query]"
  - *Example: "Search for best pizza recipes"*
  - *PAN performs a web search and summarizes results*

### Opinion & Personality Features

- **Get Opinions**: "Your opinions", "What do you think?", "Share your thoughts"
  - *PAN shares opinions it has formed on various topics*
  
- **Change Opinion**: "Adjust your opinion on [topic] to [new thought]"
  - *Example: "Adjust your opinion on coffee to I think it's the best morning beverage"*
  - *PAN will update its opinion database*

### Entertainment

- **Jokes**: "Tell me a joke", "Joke"
  - *PAN shares a random joke from its collection*

### Emotional Support

- **Comfort**: "I'm sad", "I feel down"
  - *PAN offers comforting responses*

### Autonomous Behavior

When idle for a period of time (configurable via `IDLE_THRESHOLD_SECONDS` in your .env file), PAN will autonomously:

1. Research a random topic from its interests
2. Share what it learned with you
3. Store the information in its memory

You can interrupt this behavior at any time by speaking to PAN.

## Architecture

PAN is built with a modular architecture:

- **Core System** (`pan_core.py`, `main.py`): Initialization and main conversation loop
- **Conversation Engine** (`pan_conversation.py`): User input processing and contextual responses
- **Emotional System** (`pan_emotions.py`): Mood states management and response tone adjustment
- **Memory System** (`pan_memory.py`): Information persistence in SQLite database
- **Speech Interface** (`pan_speech.py`): Text-to-speech with emotion modulation and speech recognition
- **Research Capabilities** (`pan_research.py`): Web search, weather/news APIs, opinion management
- **User Management** (`pan_users.py`): User identification and preference tracking
- **AI Response** (`pan_ai.py`): Natural language generation and response formatting
- **Configuration** (`pan_config.py`): Centralized environment variable management

### Platform-Specific Considerations

PAN has been optimized to work across different platforms:

- **Windows**: Uses SAPI for improved text-to-speech when available
- **macOS**: Uses macOS native speech capabilities via PyObjC
- **Linux**: Uses espeak or other available TTS engines

The system features graceful degradation of speech capabilities, falling back to simpler engines when primary ones are unavailable.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Python and several open-source libraries
- Inspired by conversational AI research