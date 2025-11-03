# QnA Support Application

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-ready Question & Answer support application powered by LangChain and Azure OpenAI. This application provides intelligent, context-aware responses to customer queries using state-of-the-art language models.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- 🤖 **AI-Powered Responses**: Leverages Azure OpenAI's GPT-4o-mini for intelligent answers
- 🔍 **Context-Aware**: Maintains conversation context for better understanding
- 📊 **Confidence Scoring**: Returns confidence levels with each response
- 📝 **Comprehensive Logging**: Detailed logging for debugging and monitoring
- 🔒 **Secure**: Environment-based configuration for API keys and secrets
- 🧪 **Well-Tested**: Comprehensive test suite with pytest
- 📦 **Easy Deployment**: Ready for containerization and cloud deployment

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: 3.11 or higher
- **Conda**: Anaconda or Miniconda (recommended for environment management)
- **Git**: For version control
- **Azure OpenAI Account**: With API access and deployment configured

### System Requirements

- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: At least 2GB free space

## Installation

### 1. Clone the Repository

```powershell
git clone <repository-url>
cd "QnA Support Application"
```

### 2. Create Python Environment

We use Conda for environment management to ensure consistency across different systems.

```powershell
# Create a new conda environment with Python 3.11
conda create -n qna-support python=3.11 -y

# Activate the environment
conda activate qna-support

# Verify Python version
python --version
# Expected output: Python 3.11.x
```

### 3. Install Dependencies

```powershell
# Install production dependencies
pip install -r requirements.txt

# Freeze exact versions (for production deployment)
pip freeze > requirements-freeze.txt
```

### 4. Environment Configuration

```powershell
# Copy the example environment file
copy .env.example .env

# Edit .env with your actual credentials
notepad .env  # or use your preferred editor
```

**Required Environment Variables:**

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_actual_api_key_here
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_MODEL_NAME=gpt-4o-mini

# Application Settings
CONFIDENCE_THRESHOLD=0.7
MAX_TOKENS=150
TEMPERATURE=0.3
```

## Configuration

### Application Settings

| Variable | Description | Default | Valid Range |
|----------|-------------|---------|-------------|
| `CONFIDENCE_THRESHOLD` | Minimum confidence score for responses | `0.7` | `0.0 - 1.0` |
| `MAX_TOKENS` | Maximum tokens in response | `150` | `1 - 4096` |
| `TEMPERATURE` | Response creativity level | `0.3` | `0.0 - 2.0` |
| `LOG_LEVEL` | Logging verbosity | `INFO` | `DEBUG, INFO, WARNING, ERROR` |

### Azure OpenAI Setup

1. **Create Azure OpenAI Resource**
   - Navigate to [Azure Portal](https://portal.azure.com)
   - Create a new Azure OpenAI resource
   - Deploy a `gpt-4o-mini` model

2. **Get API Credentials**
   - Go to your Azure OpenAI resource
   - Navigate to "Keys and Endpoint"
   - Copy the API key and endpoint URL

3. **Update `.env` File**
   - Paste your API key into `AZURE_OPENAI_API_KEY`
   - Verify the endpoint URL matches your deployment

## Project Structure

```
QnA Support Application/
├── .env                      # Environment variables (not in git)
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── requirements-freeze.txt   # Locked dependency versions
│
├── src/                      # Source code
│   ├── __init__.py
│   ├── core/                 # Core business logic
│   │   ├── __init__.py
│   │   ├── llm_handler.py    # LLM interaction logic
│   │   ├── prompt_manager.py # Prompt templates
│   │   └── response_handler.py # Response processing
│   │
│   └── utils/                # Utility modules
│       ├── __init__.py
│       ├── logger.py         # Logging configuration
│       ├── config.py         # Configuration loader
│       └── validators.py     # Input validation
│
├── data/                     # Data directory
│   ├── logs/                 # Application logs (gitignored)
│   └── rules/                # Business rules and configurations
│
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_core/            # Core module tests
│   ├── test_utils/           # Utility tests
│   └── conftest.py           # Pytest configuration
│
└── config/                   # Configuration files
    └── logging.yaml          # Logging configuration
```

## Usage

### Basic Example

```python
from src.core.llm_handler import LLMHandler
from src.utils.logger import setup_logger

# Initialize logger
logger = setup_logger()

# Initialize LLM handler
llm = LLMHandler()

# Ask a question
question = "How do I reset my password?"
response = llm.get_answer(question)

print(f"Answer: {response['answer']}")
print(f"Confidence: {response['confidence']}")
```

### Running as a Script

```powershell
# Activate environment
conda activate qna-support

# Run the application
python -m src.main
```

## Development

### Setting Up Development Environment

```powershell
# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Code Quality Tools

```powershell
# Format code with Black
black src/ tests/

# Lint with Flake8
flake8 src/ tests/ --max-line-length=88

# Type checking with MyPy
mypy src/

# Run all quality checks
black src/ tests/ && flake8 src/ tests/ --max-line-length=88 && mypy src/
```

### Git Workflow

```powershell
# Create a new branch for your feature
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add your feature description"

# Push to remote
git push origin feature/your-feature-name
```

**Commit Message Convention:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or modifications
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

## Testing

### Running Tests

```powershell
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_core/test_llm_handler.py

# Run with verbose output
pytest -v

# Run and generate coverage report
pytest --cov=src --cov-report=term-missing
```

### Test Coverage Goals

- **Minimum Coverage**: 80%
- **Target Coverage**: 90%+
- **Critical Modules**: 95%+

## Deployment

### Environment-Specific Configuration

1. **Development**: Use `.env` with dev credentials
2. **Staging**: Use environment variables in staging environment
3. **Production**: Use secure secrets management (Azure Key Vault, AWS Secrets Manager)

### Docker Deployment (Future)

```powershell
# Build Docker image
docker build -t qna-support:latest .

# Run container
docker run -d --env-file .env -p 8000:8000 qna-support:latest
```

## Maintenance

### Dependency Management

```powershell
# Check for outdated packages
pip list --outdated

# Update all packages (use with caution)
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade langchain-openai

# Freeze updated dependencies
pip freeze > requirements-freeze.txt
```

### Log Management

- **Location**: `data/logs/`
- **Retention**: Configurable via `LOG_RETENTION_DAYS` (default: 7 days)
- **Rotation**: Automatic daily rotation
- **Size Limit**: 10MB per log file

```powershell
# View recent logs
Get-Content data/logs/app.log -Tail 50

# Clear old logs (manually)
Remove-Item data/logs/*.log -Force
```

### Monitoring

Monitor these key metrics:

- **Response Time**: Average time to generate answers
- **Error Rate**: Percentage of failed requests
- **API Usage**: Azure OpenAI token consumption
- **Confidence Scores**: Distribution of response confidence

### Backup Strategy

- **Code**: Versioned in Git
- **Configuration**: Stored in environment variables
- **Logs**: Archived weekly (if required)
- **Data**: Regular backups of `data/rules/` directory

## Troubleshooting

### Common Issues

#### 1. API Key Errors

```
Error: Azure OpenAI API key not found
```

**Solution**: Verify `.env` file exists and contains `AZURE_OPENAI_API_KEY`

```powershell
# Check if .env exists
Test-Path .env

# Verify environment variable is loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('AZURE_OPENAI_API_KEY'))"
```

#### 2. Module Import Errors

```
ModuleNotFoundError: No module named 'langchain'
```

**Solution**: Ensure you're in the correct conda environment and dependencies are installed

```powershell
# Verify active environment
conda info --envs

# Reinstall dependencies
pip install -r requirements.txt
```

#### 3. Connection Errors

```
Error: Connection timeout to Azure OpenAI
```

**Solution**: Check network connectivity and Azure service status

```powershell
# Test connection to Azure endpoint
curl https://datascienceazureopenai.openai.azure.com/

# Verify API endpoint in .env is correct
```

#### 4. Permission Errors (Logs)

```
PermissionError: [Errno 13] Permission denied: 'data/logs/app.log'
```

**Solution**: Ensure `data/logs/` directory exists and is writable

```powershell
# Create logs directory if missing
New-Item -ItemType Directory -Path "data\logs" -Force
```

### Getting Help

- **Documentation**: Check this README and code comments
- **Issues**: Open an issue on GitHub
- **Logs**: Check `data/logs/app.log` for detailed error messages

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the Repository**
2. **Create a Feature Branch**: `git checkout -b feature/amazing-feature`
3. **Make Your Changes**: Follow code style guidelines
4. **Add Tests**: Ensure coverage remains above 80%
5. **Commit Changes**: Use conventional commit messages
6. **Push to Branch**: `git push origin feature/amazing-feature`
7. **Open Pull Request**: Describe your changes clearly

### Code Style Guidelines

- Follow PEP 8 style guide
- Use Black for code formatting (88 character line length)
- Add docstrings to all functions and classes
- Write meaningful variable and function names
- Add type hints where applicable

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contact & Support

- **Project Maintainer**: [Your Name]
- **Email**: [your.email@example.com]
- **Issue Tracker**: [GitHub Issues](https://github.com/your-repo/issues)

---

**Built with ❤️ using LangChain and Azure OpenAI**
