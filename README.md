# XAUUSD Fibonacci Strategy Advisor

An AI-powered trading strategy advisor that analyzes XAUUSD (Gold) using Fibonacci retracement levels and multiple AI vision models.

## Features

- Real-time XAUUSD market data analysis
- Integration with multiple AI vision models:
  - ChatGPT 4.1 Vision
  - Claude 3.7 Vision
  - Perplexity Vision
- Fibonacci retracement analysis
- Web-based interface for easy access
- Comprehensive trading strategy recommendations

## Setup

1. Clone the repository
2. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure your API keys:
   - OANDA API credentials
   - OpenAI API key
   - Anthropic API key
   - Flask configuration

## Running the Application

1. Activate the virtual environment if not already active:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Start the Flask application:
   ```bash
   python run.py
   ```
3. Access the application at http://localhost:5000

## Running Tests

```bash
pytest
```

## Project Structure

```
/app
  /models - Data models
  /routes - Flask route definitions
  /utils  - Utility functions
/config   - Configuration files
/static   - Static assets (CSS, JS, images)
/templates - HTML templates
/tests    - Test suite
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License
