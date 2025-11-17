# Contributing to RepoForgeX

Thank you for your interest in contributing to RepoForgeX!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/kabir308/repoforgex.git
cd repoforgex
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Run tests:
```bash
pytest
```

4. Run linter:
```bash
flake8 src tests --max-line-length=120
```

## Project Structure

```
RepoForgeX/
├── src/repoforgex/          # Main package
│   ├── auth/                # Authentication modules
│   │   └── github_app.py    # GitHub App authentication
│   ├── cli.py               # Command-line interface
│   ├── config.py            # Configuration validation
│   ├── github_client.py     # GitHub API client
│   ├── multi_sync.py        # Parallel processing
│   ├── scaffold.py          # Repository scaffolding
│   └── web.py               # Flask web API
├── templates/               # Repository templates
│   ├── python-basic/
│   └── node-basic/
├── tests/                   # Unit tests
├── Dockerfile               # Docker image
├── docker-compose.yml       # Docker compose config
└── requirements.txt         # Python dependencies
```

## Making Changes

1. Create a new branch for your feature
2. Write tests for your changes
3. Ensure all tests pass
4. Submit a pull request

## Code Style

- Follow PEP 8 guidelines
- Maximum line length: 120 characters
- Use type hints where appropriate
- Add docstrings to functions and classes
