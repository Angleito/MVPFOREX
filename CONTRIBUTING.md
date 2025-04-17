# Contributing Guidelines

Thank you for your interest in contributing to the XAUUSD Fibonacci Strategy Advisor project! This document provides guidelines and instructions for contributing.

## Development Setup

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `config/.env.example` to `.env` in the project root and configure your API keys
5. Run the API key check script to verify your configuration:
   ```bash
   python scripts/check_api_keys.py
   ```

## Development Workflow

1. Create a feature branch from `main`
2. Implement your changes with appropriate tests
3. Run tests to ensure all tests pass:
   ```bash
   pytest
   ```
4. Format your code using the project's style guidelines
5. Submit a pull request with a clear description of your changes

## Code Style Guidelines

- Follow PEP 8 for Python code formatting
- Use meaningful variable and function names
- Write docstrings for all functions, classes, and modules
- Include type hints where appropriate
- Keep functions focused on a single responsibility
- Write unit tests for new functionality

## Commit Message Guidelines

- Use clear, descriptive commit messages
- Start with a concise summary line (50 chars or less)
- Separate the summary from the body with a blank line
- Use the body to explain what and why vs. how
- Reference issues and pull requests where appropriate

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the requirements.txt if you've added new dependencies
3. The PR should work on the target branch without any issues
4. PRs require review by at least one maintainer before merging