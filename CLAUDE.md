# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Rules

1. Avoid creating unnecessary files - follow the existing module structure
2. Use the LICENSE file for legal notices (MIT License)
3. Only create new files when they represent a distinct, reusable functionality

## Project Overview

PAN (Personal Assistant with Nuance) is a personality-based voice recognition digital assistant with emotions, memory, and conversational capabilities. It uses speech recognition, text-to-speech, and web APIs to provide an interactive assistant experience.

## Development Setup

### Environment Setup

The project uses Nix with the unstable channel for dependency management and python-dotenv for configuration:

```bash
# Set up development environment
nix develop

# Create configuration file from example
cp .env.example .env
```

Edit the `.env` file to configure API keys and other settings.

### Initializing the Database

```bash
# Initialize the database
python init_db.py
```

### Running the Application

```bash
# Run the main application
python main.py
```

### Testing the Application

```bash
# Run tests
make test

# Run tests with coverage
make coverage

# Run type checking
make type
```

### Code Quality and Development Tools

The project includes the following development tools (in the Nix environment):
- Black (code formatting)
- Pylint (code linting)
- isort (import sorting)
- pytest (testing)
- pytest-cov (test coverage)
- mypy (type checking)
- pre-commit (git hooks)

These tools can be run using the Makefile:

```bash
# Format code with Black and isort
make format

# Run linting with Pylint
make lint

# Run all development tasks
make all

# Show all available commands
make help
```

Configuration files:
- `.pylintrc` - Pylint configuration
- `pyproject.toml` - Black configuration
- `.isort.cfg` - isort configuration
- `.pre-commit-config.yaml` - pre-commit hooks configuration
- `pytest.ini` - pytest configuration
- `mypy.ini` - mypy configuration
- `.editorconfig` - Editor configuration

The project uses pre-commit hooks to enforce code quality before commits. To set up:

```bash
# Install pre-commit hooks
pre-commit install
```

### Project Structure

Key files in addition to Python modules:
- `Makefile` - Build and development tasks
- `flake.nix` - Nix development environment
- `requirements.txt` - Python dependencies for non-Nix users
- `runtime.txt` - Python version specification
- `.env.example` - Template for environment variables
- `.dockerignore` - Files to exclude from Docker builds

## Code Architecture

PAN is structured as a modular system with the following key components:

1. **Core System** (`pan_core.py`, `main.py`):
   - Initializes the system and database
   - Manages the main conversation loop
   - Handles user input and routes to appropriate modules

2. **Conversation Engine** (`pan_conversation.py`):
   - Processes user input and generates contextual responses
   - Handles different types of queries and commands

3. **Emotional System** (`pan_emotions.py`):
   - Manages PAN's mood states (happy, sad, neutral, etc.)
   - Adjusts response tone based on emotional state

4. **Memory System** (`pan_memory.py`):
   - Persists information in SQLite database
   - Retrieves relevant memories based on context

5. **Speech Interface** (`pan_speech.py`):
   - Text-to-speech with emotion modulation (using pyttsx3)
   - Multiple TTS engine fallbacks with graceful degradation
   - Speech recognition with timeout handling (using SpeechRecognition)

6. **Research Capabilities** (`pan_research.py`):
   - Web searches and information gathering
   - Weather and news API integration
   - Opinion management

7. **User Management** (`pan_users.py`):
   - User identification and persistence
   - User preference tracking

8. **AI Response Generation** (`pan_ai.py`):
   - Natural language generation
   - Context-aware response formatting

## Dependencies

Key external dependencies include:
- pyttsx3 (text-to-speech)
- speech_recognition (speech-to-text)
- pyaudio (audio I/O)
- requests (API calls)
- sqlite3 (database)
- python-dotenv (configuration management)
- transformers and torch (AI text generation)
- numpy (numerical operations)
- python-dateutil (date handling)
- Platform-specific dependencies:
  - Windows: win32com.client for better TTS via SAPI
  - macOS: pyobjc and pyobjc-core for TTS
  - Linux/macOS: espeak-ng as fallback TTS engine

All dependencies are managed through:
1. Nix flake for development environment (including system dependencies like portaudio and espeak-ng)
2. requirements.txt for non-Nix installations (Python packages only)

## Database Schema

PAN uses SQLite for persistence with the following tables:
- `users`: User identification and preferences
- `memories`: Stored information and knowledge
- `opinions`: PAN's thoughts on various topics
- `affinity`: Trust/relationship scores with users
- `news_archive`: Cached news information

Database initialization is handled by:
1. `init_db.py` - Standalone script to initialize the database
2. `pan_core.py` - Runtime initialization during application startup

## Configuration

Configuration is managed through environment variables loaded from the `.env` file:

```
# Database settings
DATABASE_PATH=pan_memory.db

# API keys
WEATHER_API_KEY=your_api_key
NEWS_API_KEY=your_api_key

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

Environment variables are accessed through the `pan_config.py` module.

## Quick Command Reminder
### Important!
- Remember to use `nix develop -c <your command>` to run any python tasks