# NL2MySQL - AI-Driven Natural Language to MySQL Query Generator

> **AI-powered system that converts natural language queries into optimized MySQL queries specifically for SailPoint IdentityIQ databases.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: Dual](https://img.shields.io/badge/License-Dual-orange.svg)](LICENSE)

---

## 🎯 What This Project Demonstrates

This project showcases how to build an **AI-powered application** that combines:

- **Large Language Models (LLMs)** for natural language understanding
- **Vector Databases (ChromaDB)** for semantic schema search
- **Database Introspection** using SQLAlchemy
- **Domain-Specific Knowledge** for SailPoint IdentityIQ
- **Modern API Design** with FastAPI
- **Learning Systems** with continuous improvement

## ✨ Key Features

- 🧠 **AI-Powered SQL Generation** - Converts natural language to MySQL queries
- 🔍 **Schema-Aware** - Uses ChromaDB vector search for relevant table/column retrieval
- 🎯 **IIQ-Specific** - Built-in knowledge of SailPoint IdentityIQ database structure
- ⚡ **Multiple LLM Support** - Ollama (local), OpenAI (cloud), SQLCoder (specialized)
- ✅ **Query Validation & Optimization** - Built-in security and performance checks
- 📊 **Learning System** - Continuous improvement through feedback
- 🌐 **Web Interface** - Streamlit frontend for easy interaction
- 🐳 **Docker Ready** - Containerized deployment

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **MySQL Server** (for SailPoint IdentityIQ database)
- **8GB+ RAM** (for LLM models)
- **Ollama** (optional, for local LLM models)

### Installation

```bash
# Clone the repository
git clone https://github.com/ksr-verse/NL2MySQL.git
cd NL2MySQL

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your MySQL connection details
```

### Basic Usage

```bash
# Start the API server
python app.py

# Or use the web interface
streamlit run iiq_frontend.py
```

### Example Query

```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Show me all users with Workday accounts",
       "max_rows": 100
     }'
```

## 🏗️ Architecture Overview

```
Natural Language Query
         ↓
Schema Retrieval (ChromaDB)
         ↓
Synonyms Mapping (IIQ Knowledge)
         ↓
Enhanced Prompt Building
         ↓
LLM Generation (Ollama/OpenAI/SQLCoder)
         ↓
SQL Validation & Optimization
         ↓
Database Execution (MySQL)
         ↓
Results & Learning
```

## 📚 Documentation

- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - Comprehensive learning and usage guide
- **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** - Detailed system architecture
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete setup instructions
- **[VISUAL_ARCHITECTURE.txt](VISUAL_ARCHITECTURE.txt)** - Visual architecture representation

## 🎓 Learning Objectives

This project teaches:

- **AI/ML Integration** - How to integrate LLMs into applications
- **Vector Databases** - ChromaDB implementation and usage
- **Database Introspection** - SQLAlchemy schema analysis
- **API Development** - FastAPI best practices
- **Prompt Engineering** - Crafting effective LLM prompts
- **Domain-Specific AI** - Building specialized business logic
- **Learning Systems** - Continuous improvement patterns

## 🔧 Core Components

- **`app.py`** - FastAPI application and API endpoints
- **`sql_generator.py`** - Main orchestration and business logic
- **`adapters/`** - LLM and database adapters
- **`iiq_synonyms.py`** - IIQ-specific knowledge and synonyms
- **`iiq_feedback.py`** - Learning and continuous improvement
- **`retriever.py`** - ChromaDB vector search
- **`validator.py`** - SQL security and validation
- **`optimizer.py`** - Query performance optimization

## 🌟 Example Queries

Try these natural language queries:

- "List all active users with their email addresses"
- "Show me users who have accounts in multiple applications"
- "Find users with specific entitlements in Trakk application"
- "Get employees with manager information"
- "Show users with TimeSheetEnterAuthority in Trakk"

## 🛠️ Technologies Used

- **FastAPI** - Modern Python web framework
- **ChromaDB** - Vector database for embeddings
- **SQLAlchemy** - Database toolkit and ORM
- **Ollama** - Local LLM serving
- **Sentence Transformers** - Text embeddings
- **Streamlit** - Web interface framework
- **MySQL** - Target database system

## 📄 License

This project is licensed under a **Dual License**:

- **Personal/Educational Use** - Free
- **Commercial Use** - Requires license

See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

This project demonstrates the integration of several open-source technologies:

- **ChromaDB** for vector database functionality
- **FastAPI** for the robust API framework
- **Ollama** for local LLM serving
- **SQLAlchemy** for database introspection
- **Sentence Transformers** for text embeddings

## 📞 Contact

- **Email:** rautela.ks.job@gmail.com
- **LinkedIn:** [Kuldeep Singh Rautela](https://www.linkedin.com/in/kuldeep-rautela-808a8558/)

---

**Happy Learning!** 🚀

This project is designed for educational purposes to help you understand modern AI application development. For detailed usage instructions, see [USAGE_GUIDE.md](USAGE_GUIDE.md).