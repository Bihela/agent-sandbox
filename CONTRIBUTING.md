# Contributing to Agent Sandbox

Thank you for your interest in contributing to the Agent Sandbox! This project is designed to be a collaborative ecosystem for LLM negotiation research.

## Code of Conduct
Please be respectful and professional in all interactions. We aim to build a welcoming community for researchers and developers alike.

## How Can I Contribute?

### Reporting Bugs
- Use the **Bug Report** template.
- Provide a clear description and steps to reproduce.
- Include environment details (OS, Python version, Ollama version).

### Suggesting Features
- Use the **Feature Request** template.
- Explain the research or utility value of the proposed feature.

### Pull Requests
1. Fork the repo and create your branch from `main`.
2. Ensure your code follows the existing style (type hints, docstrings).
3. If you add a new Model Provider, include a sample configuration in `docs/providers.md`.
4. Run tests and linting (see below) before submitting.

## Development Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the dev server:
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```

## Testing
We use `pytest` for unit and integration tests.
```bash
pytest scripts/test_api.py
```

## License
By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
