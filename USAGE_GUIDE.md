# 📚 NL2MySQL Usage Guide

Welcome to NL2MySQL! This guide will help you understand how to use this AI-driven Natural Language to MySQL Query Generator for SailPoint IdentityIQ.

## 🎯 Project Purpose

This project is designed for **learning and educational purposes**. It demonstrates how to build an AI-powered system that converts natural language queries into optimized MySQL queries specifically for SailPoint IdentityIQ databases.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Understanding the Architecture](#understanding-the-architecture)
- [Learning Resources](#learning-resources)
- [Troubleshooting](#troubleshooting)

## 🚀 Getting Started

### What This Project Teaches

This project demonstrates several important concepts:

1. **AI/ML Integration** - How to integrate Large Language Models (LLMs) into applications
2. **Vector Databases** - Using ChromaDB for semantic search and schema retrieval
3. **Database Introspection** - Using SQLAlchemy to understand database structure
4. **API Design** - Building RESTful APIs with FastAPI
5. **Prompt Engineering** - Crafting effective prompts for LLM-based SQL generation
6. **Domain-Specific Knowledge** - Building systems with specialized business logic

### Learning Objectives

By studying this codebase, you will learn:

- How to build AI-powered applications
- Vector database implementation and usage
- Database schema analysis and introspection
- LLM integration patterns and best practices
- API development with modern Python frameworks
- Domain-specific AI system design

## 💻 System Requirements

### Hardware Requirements

- **RAM:** 8GB minimum, 16GB+ recommended
- **Storage:** 5GB free space
- **CPU:** Modern multi-core processor

### Software Requirements

- **Python:** 3.11 or higher
- **Git:** For cloning the repository
- **Docker:** Optional, for containerized deployment
- **MySQL:** For the target database (SailPoint IdentityIQ)

### Optional Requirements

- **Ollama:** For local LLM models
- **CUDA:** For GPU acceleration (if using local models)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/ksr-verse/NL2MySQL.git
cd NL2MySQL
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Configuration

```bash
# Copy the example environment file
cp env.example .env

# Edit the configuration file
# Update database connection string and other settings
```

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database Configuration
DB_CONNECTION_STRING=mysql+pymysql://username:password@localhost:3306/identityiq

# LLM Configuration
LLM_PROVIDER=local  # Options: local, openai, sqlcoder
LLM_LOCAL_MODEL=phi  # For Ollama models

# Vector Database
VECTOR_PERSIST_DIRECTORY=./chromadb
VECTOR_COLLECTION_NAME=schema_embeddings
```

### Database Setup

1. **Install MySQL** and create a database
2. **Import SailPoint IdentityIQ schema** (if available)
3. **Update connection string** in `.env` file
4. **Test connection** using the provided scripts

## 📖 Usage Examples

### 1. Basic API Usage

Start the FastAPI server:

```bash
python app.py
```

The API will be available at `http://localhost:8000`

### 2. Natural Language to SQL

Send a POST request to `/query`:

```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Show me all users with Workday accounts",
       "max_rows": 100
     }'
```

### 3. Web Interface

Launch the Streamlit interface:

```bash
streamlit run iiq_frontend.py
```

### 4. Example Queries

Try these natural language queries:

- "List all active users with their email addresses"
- "Show me users who have accounts in multiple applications"
- "Find users with specific entitlements in Trakk application"
- "Get employees with manager information"

## 🏗️ Understanding the Architecture

### Core Components

1. **SQL Generator** (`sql_generator.py`)
   - Main orchestrator that coordinates all components
   - Handles the complete NL2MySQL workflow
   - Manages retry logic and error handling

2. **Schema Retriever** (`retriever.py`)
   - Uses ChromaDB for vector-based schema search
   - Finds relevant tables and columns for queries
   - Provides semantic similarity matching

3. **LLM Adapters** (`adapters/`)
   - **Local LLM** (`llm_local.py`) - Ollama integration for Phi, GPT-OSS models
   - **OpenAI** (`llm_openai.py`) - Cloud-based GPT models
   - **SQLCoder** (`llm_sqlcoder.py`) - Specialized SQL generation model
   - **Database** (`db_mysql.py`) - MySQL operations and query execution

4. **IIQ Knowledge System**
   - **Consolidated Training** (`iiq_training_data.py`) - **ALL training data in one place**
     - Synonyms and mappings
     - Example queries  
     - Entity relationships
     - Query patterns
   - **Feedback System** (`iiq_feedback.py`) - Learning and continuous improvement

5. **Prompt Templates**
   - **Enhanced Templates** (`prompt_templates_enhanced.py`) - IIQ-specific prompts with synonyms and learning

6. **Schema Management**
   - **Schema Inspector** (`schema_inspector.py`) - Database introspection
   - **Schema Embedder** (`schema_embedder.py`) - ChromaDB vector generation

7. **Web Interface**
   - **Streamlit Frontend** (`iiq_frontend.py`) - User-friendly web interface
   - **FastAPI Backend** (`app.py`) - REST API endpoints

8. **Validation & Optimization**
   - **SQL Validator** (`validator.py`) - Security and syntax checking
   - **Query Optimizer** (`optimizer.py`) - Performance improvements

### Data Flow

```
Natural Language Query
         ↓
Schema Retrieval (ChromaDB)
         ↓
Synonyms Mapping (IIQ Knowledge)
         ↓
Enhanced Prompt Building (IIQ-specific)
         ↓
LLM Generation (Ollama/OpenAI/SQLCoder)
         ↓
SQL Validation & Optimization
         ↓
Database Execution (MySQL)
         ↓
Results & Learning (Feedback System)
```

## 📚 Learning Resources

### Key Technologies Used

- **FastAPI:** Modern Python web framework
- **ChromaDB:** Vector database for embeddings
- **SQLAlchemy:** Database toolkit and ORM
- **Ollama:** Local LLM serving
- **Sentence Transformers:** Text embeddings
- **Streamlit:** Web interface framework

### Recommended Learning Path

1. **Start with the README** - Understand the project overview
2. **Study the Architecture** - Review `ARCHITECTURE_DIAGRAM.md`
3. **Examine Core Components** - Look at `sql_generator.py` and `app.py`
4. **Understand Adapters** - Study the `adapters/` directory
5. **Explore IIQ Knowledge** - Review `iiq_synonyms.py` and related files
6. **Run the System** - Follow the setup guide and try examples

### Code Structure Learning

- **`app.py`** - FastAPI application and API endpoints
- **`sql_generator.py`** - Main business logic and orchestration
- **`retriever.py`** - Vector database integration
- **`adapters/`** - Modular adapter pattern implementation
- **`iiq_synonyms.py`** - IIQ-specific knowledge and synonyms mapping
- **`iiq_feedback.py`** - Learning system and continuous improvement
- **`iiq_frontend.py`** - Streamlit web interface
- **`prompt_templates_enhanced.py`** - IIQ-optimized prompt engineering
- **`validator.py`** - SQL security and validation
- **`optimizer.py`** - Query performance optimization

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check MySQL service is running
   - Verify connection string in `.env`
   - Ensure database exists and is accessible

2. **LLM Model Not Available**
   - For Ollama: Ensure Ollama is running and model is installed
   - For OpenAI: Check API key is valid
   - Check model availability in respective services

3. **ChromaDB Issues**
   - Ensure `chromadb` directory is writable
   - Check if schema embeddings are generated
   - Run schema embedder if needed

4. **Import Errors**
   - Ensure virtual environment is activated
   - Check all dependencies are installed
   - Verify Python version compatibility

### Getting Help

- **Study the code** - This is a learning project, so reading the code is the best way to understand
- **Check logs** - Look at console output for error messages
- **Review documentation** - Read through all `.md` files in the repository

## 🎓 Learning Outcomes

After studying this project, you should understand:

- How to build AI-powered applications from scratch
- Vector database implementation and usage patterns
- LLM integration strategies and prompt engineering
- Database introspection and schema analysis
- API design and development best practices
- Domain-specific AI system architecture
- Modular software design with adapter patterns

## 📄 License

This project is for educational and personal use. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

This project demonstrates the integration of several open-source technologies:

- **ChromaDB** for vector database functionality
- **FastAPI** for the robust API framework
- **Ollama** for local LLM serving
- **SQLAlchemy** for database introspection
- **Sentence Transformers** for text embeddings

---

## Training Data Management

### **Single File Approach** 
All training data is now consolidated in **`iiq_training_data.py`**:

```python
# Add new synonyms
iiq_training.add_synonym("contractors", "spt_identity")

# Add new examples  
iiq_training.add_example(
    "Show me all contractors",
    "SELECT * FROM spt_identity WHERE employee_type = 'Contractor'",
    "Query for contractor employees"
)
```

### **Schema Management**
- **`schema.json`** - Auto-generated from database (DO NOT edit manually)
- **Regenerate schema**: `python schema_inspector.py` (pulls from live DB)
- **Reset vector DB**: `python schema_embedder.py --reset --verbose`

### **Complete Refresh Workflow**
When you make changes to training data:

1. **Edit `iiq_training_data.py`** - Add your examples, synonyms, mappings
2. **Regenerate schema** (if DB changed): `python schema_inspector.py`  
3. **Reset vector DB**: `python schema_embedder.py --reset --verbose`
4. **Restart API** to pick up changes
5. **Test with a query** to verify new knowledge is working

---

**Happy Learning!** 🚀

This project is designed to help you understand modern AI application development. Take your time to explore the codebase and experiment with different configurations and queries.
