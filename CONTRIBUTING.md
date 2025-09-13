# 🤝 Contributing to NL2SQL

Thank you for your interest in contributing to NL2SQL! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Issue Guidelines](#issue-guidelines)

## 🤝 Code of Conduct

This project follows a Code of Conduct to ensure a welcoming environment for all contributors:

- **Be respectful** and inclusive in all interactions
- **Be constructive** when providing feedback
- **Be patient** with new contributors
- **Be collaborative** and help others learn

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Docker and Docker Compose (for testing)
- Basic understanding of SQL and language models

### Areas for Contribution

We welcome contributions in these areas:

1. **🐛 Bug Fixes** - Fix issues and improve stability
2. **✨ New Features** - Add functionality and capabilities  
3. **📚 Documentation** - Improve guides, examples, and API docs
4. **🧪 Testing** - Add tests and improve coverage
5. **🎯 Performance** - Optimize speed and resource usage
6. **🔒 Security** - Enhance SQL validation and safety
7. **🌐 Internationalization** - Add support for other languages

## 🛠️ Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/yourusername/nl2sql.git
cd nl2sql

# Add upstream remote
git remote add upstream https://github.com/originalowner/nl2sql.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If exists

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

### 3. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit with your test database settings
nano .env
```

### 4. Set Up Test Database (Optional)

```bash
# Start test services with Docker
docker-compose -f docker-compose.test.yml up -d

# Or use your own MSSQL instance
```

## 🔧 Making Changes

### Branch Naming Convention

Use descriptive branch names:

```bash
# Feature branches
git checkout -b feature/add-postgres-support
git checkout -b feature/improve-query-optimization

# Bug fix branches  
git checkout -b fix/sql-injection-vulnerability
git checkout -b fix/memory-leak-in-embedder

# Documentation branches
git checkout -b docs/update-setup-guide
git checkout -b docs/add-api-examples
```

### Development Workflow

1. **Create a new branch** for your changes
2. **Make small, focused commits** with clear messages
3. **Test your changes** thoroughly
4. **Update documentation** if needed
5. **Submit a pull request** when ready

### Commit Message Guidelines

Use clear, descriptive commit messages:

```bash
# Good examples
git commit -m "feat: add PostgreSQL database adapter"
git commit -m "fix: resolve SQL injection in validator"
git commit -m "docs: update installation instructions"
git commit -m "test: add integration tests for schema embedder"

# Use conventional commits format
# type(scope): description
# 
# Types: feat, fix, docs, test, refactor, style, chore
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_schema.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run integration tests (requires database)
pytest tests/test_end_to_end.py
```

### Writing Tests

- **Unit tests** for individual components
- **Integration tests** for component interactions
- **End-to-end tests** for full workflows
- **Mock external services** (databases, APIs) when appropriate

Example test structure:

```python
def test_sql_validator_detects_injection():
    """Test that SQL validator detects injection attempts."""
    validator = SQLValidator()
    
    # Test case with SQL injection
    result = validator.validate_query("SELECT * FROM users WHERE id = 1; DROP TABLE users;")
    
    assert result["valid"] is False
    assert "injection" in result["security_issues"][0].lower()
```

### Test Coverage

- Aim for **80%+ code coverage**
- Focus on **critical paths** and **edge cases**
- Test **error conditions** and **failure scenarios**

## 📝 Submitting Changes

### Pull Request Process

1. **Update your branch** with latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request** on GitHub with:
   - Clear title describing the change
   - Detailed description of what was changed and why
   - Reference any related issues
   - Screenshots/examples if applicable

### Pull Request Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Other (specify):

## Testing
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or breaking changes documented)
```

## 🎨 Code Style

### Python Style Guidelines

We follow **PEP 8** with some modifications:

```python
# Line length: 88 characters (Black formatter default)
# Use type hints for function parameters and returns
def generate_sql(query: str, schema_context: str) -> Dict[str, Any]:
    """Generate SQL from natural language query."""
    pass

# Use docstrings for all public functions/classes
class SQLValidator:
    """Validate and sanitize SQL queries."""
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate SQL query for syntax and security issues.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            Dictionary containing validation results
        """
        pass
```

### Code Formatting

Use **Black** for code formatting:

```bash
# Format all files
black .

# Check formatting
black --check .
```

Use **isort** for import sorting:

```bash
# Sort imports
isort .

# Check import order
isort --check-only .
```

### Linting

Use **flake8** for linting:

```bash
# Run linter
flake8 .

# With specific configuration
flake8 --max-line-length=88 --ignore=E203,W503 .
```

## 🐛 Issue Guidelines

### Reporting Bugs

Use the bug report template and include:

- **Clear title** describing the issue
- **Steps to reproduce** the problem
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Error messages** or logs
- **Minimal code example** if applicable

### Feature Requests

Use the feature request template and include:

- **Clear description** of the proposed feature
- **Use case** - why is this needed?
- **Proposed solution** or implementation ideas
- **Alternatives considered**
- **Additional context** or examples

### Issue Labels

We use these labels to categorize issues:

- `bug` - Something isn't working
- `enhancement` - New feature or improvement
- `documentation` - Documentation needs
- `good first issue` - Good for new contributors
- `help wanted` - Extra attention needed
- `priority: high/medium/low` - Issue priority
- `area: api` - API-related changes
- `area: llm` - LLM adapter changes
- `area: database` - Database-related changes

## 🏆 Recognition

Contributors are recognized in several ways:

- **Contributors list** in README.md
- **Release notes** mention significant contributions
- **Special thanks** for major features or fixes

## 📚 Resources

### Documentation

- [Setup Guide](SETUP_GUIDE.md) - Complete setup instructions
- [LLM Comparison](LLM_COMPARISON.md) - Understanding LLM adapters
- [API Documentation](http://localhost:8000/docs) - Interactive API docs

### Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Ollama Documentation](https://ollama.ai/docs)

### Communication

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - Questions and general discussion
- **Pull Requests** - Code review and collaboration

## ❓ Questions?

If you have questions about contributing:

1. Check existing [GitHub Issues](https://github.com/yourname/nl2sql/issues)
2. Search [GitHub Discussions](https://github.com/yourname/nl2sql/discussions)
3. Create a new discussion if needed

Thank you for contributing to NL2SQL! 🚀
