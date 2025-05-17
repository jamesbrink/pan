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

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/pan.git
   cd pan
   ```

2. Create a configuration file:
   ```bash
   touch .env
   ```
   Edit the `.env` file and add your API keys (see API Keys section below).

3. Set up the development environment using Nix:
   ```bash
   nix develop
   ```

4. Initialize the database:
   ```bash
   python init_db.py
   ```

5. Run the application:
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
WEATHER_API_KEY=abc123yourapikeyhere
NEWS_API_KEY=xyz789yourapikeyhere
DEFAULT_CITY=Kelso
DEFAULT_COUNTRY_CODE=US
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

### Voice Commands

PAN understands various commands, including:

- "Search for [topic]" - Performs a web search
- "Weather" - Gets current weather information
- "News" - Retrieves recent news headlines
- "Share your thoughts" - PAN shares opinions on topics it knows about
- "Adjust your opinion on [topic] to [new thought]" - Changes PAN's opinion
- "Exit program" - Shuts down the application

## Architecture

PAN is built with a modular architecture:

- **Core System**: Initialization and main loop
- **Conversation Engine**: User input processing
- **Emotional System**: Mood and tone management
- **Memory System**: Information persistence
- **Speech Interface**: Voice I/O
- **Research Capabilities**: Web search and API integration
- **User Management**: User profiles and preferences

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Python and several open-source libraries
- Inspired by conversational AI research