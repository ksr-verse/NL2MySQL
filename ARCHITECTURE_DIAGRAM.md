# NL2MySQL - Complete Architecture Diagram

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NL2MySQL SYSTEM ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   USER INPUT    │    │   WEB FRONTEND  │    │   API GATEWAY   │
│                 │    │                 │    │                 │
│ Natural Language│───▶│   Streamlit     │───▶│   FastAPI       │
│ Query           │    │   Frontend      │    │   Backend       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CORE PROCESSING LAYER                             │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  SQL GENERATOR  │    │  SCHEMA RETRIEVER│    │  PROMPT BUILDER │
│                 │    │                 │    │                 │
│ • Orchestrates  │◀──▶│ • ChromaDB      │◀──▶│ • Enhanced      │
│ • Coordinates   │    │ • Vector Search │    │ • Templates     │
│ • Manages Flow  │    │ • Schema Context│    │ • IIQ Knowledge │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  LLM ADAPTER    │    │  SCHEMA EMBEDDER│    │  SYNONYMS MGR   │
│                 │    │                 │    │                 │
│ • Ollama (Phi)  │    │ • Sentence      │    │ • IIQ Terms     │
│ • GPT-OSS       │    │   Transformers  │    │ • Natural Lang  │
│ • SQLCoder      │    │ • ChromaDB      │    │ • Mappings      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  VALIDATOR      │    │  OPTIMIZER      │    │  FEEDBACK MGR   │
│                 │    │                 │    │                 │
│ • SQL Syntax    │    │ • Performance   │    │ • Learning      │
│ • Security      │    │ • Index Usage   │    │ • Corrections   │
│ • Logic Check   │    │ • Query Plan    │    │ • Training Data │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                        │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  MYSQL DATABASE │    │  CHROMADB       │    │  TRAINING DATA  │
│                 │    │                 │    │                 │
│ • IdentityIQ    │    │ • Schema        │    │ • Examples      │
│ • spt_identity  │    │   Embeddings    │    │ • Corrections   │
│ • spt_link      │    │ • Vector Search │    │ • Learning      │
│ • spt_application│   │ • Similarity    │    │ • Feedback      │
│ • spt_entitlement│   │   Matching      │    │ • Synonyms      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔄 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              REQUEST FLOW                                      │
└─────────────────────────────────────────────────────────────────────────────────┘

1. USER INPUT
   └── "Give me employees with Workday accounts"

2. API GATEWAY (FastAPI)
   └── POST /query endpoint
   └── Request validation
   └── Route to SQL Generator

3. SQL GENERATOR (Orchestrator)
   ├── Retrieve relevant schema (ChromaDB)
   ├── Build enhanced prompt (Templates + Synonyms)
   ├── Generate SQL (LLM)
   ├── Validate SQL (Validator)
   ├── Optimize SQL (Optimizer)
   └── Return result

4. SCHEMA RETRIEVAL
   ├── Query ChromaDB for relevant tables
   ├── Vector similarity search
   ├── Return schema context
   └── Format for prompt

5. PROMPT BUILDING
   ├── Load IIQ knowledge
   ├── Apply synonyms mapping
   ├── Include training examples
   ├── Add schema context
   └── Format for LLM

6. LLM GENERATION
   ├── Send prompt to Ollama (Phi model)
   ├── Generate SQL response
   ├── Parse and clean SQL
   └── Return to generator

7. VALIDATION & OPTIMIZATION
   ├── Check SQL syntax
   ├── Validate table/column names
   ├── Optimize query performance
   └── Apply security checks

8. RESPONSE
   └── Return SQL + metadata
   └── Log for learning
   └── Update feedback system
```

## 🧠 Component Details

### 1. API Layer
```
┌─────────────────┐
│   FastAPI App   │
├─────────────────┤
│ • /query        │ - Natural language to SQL
│ • /execute      │ - Direct SQL execution
│ • /health       │ - System health check
│ • /docs         │ - API documentation
└─────────────────┘
```

### 2. Core Processing
```
┌─────────────────┐
│  SQL Generator  │
├─────────────────┤
│ • Orchestrates  │ - All components
│ • Manages retries│ - Error handling
│ • Coordinates   │ - Data flow
│ • Logs activity │ - Audit trail
└─────────────────┘

┌─────────────────┐
│ Schema Retriever│
├─────────────────┤
│ • ChromaDB      │ - Vector database
│ • Embeddings    │ - Schema vectors
│ • Similarity    │ - Semantic search
│ • Context       │ - Relevant tables
└─────────────────┘
```

### 3. LLM Integration
```
┌─────────────────┐
│  LLM Adapters   │
├─────────────────┤
│ • Ollama        │ - Local models
│   - Phi:latest  │ - 1.6GB (current)
│   - GPT-OSS:20b │ - 13GB (available)
│ • SQLCoder      │ - SQL-specific
│ • OpenAI        │ - Cloud option
└─────────────────┘
```

### 4. Knowledge Management
```
┌─────────────────┐
│  IIQ Knowledge  │
├─────────────────┤
│ • Synonyms      │ - Natural → IIQ terms
│ • Examples      │ - Training data
│ • Relationships │ - Table connections
│ • Patterns      │ - Query templates
└─────────────────┘

┌─────────────────┐
│  Training Data  │
├─────────────────┤
│ • Examples      │ - NL → SQL pairs
│ • Corrections   │ - DBA feedback
│ • Learning      │ - Continuous improvement
│ • Feedback      │ - User corrections
└─────────────────┘
```

### 5. Data Storage
```
┌─────────────────┐
│  MySQL Database │
├─────────────────┤
│ • spt_identity  │ - Users/employees
│ • spt_link      │ - Account links
│ • spt_application│ - Applications
│ • spt_entitlement│ - Permissions
└─────────────────┘

┌─────────────────┐
│  ChromaDB       │
├─────────────────┤
│ • Schema chunks │ - Table/column info
│ • Embeddings    │ - Vector representations
│ • Similarity    │ - Semantic search
│ • Context       │ - Relevant schema
└─────────────────┘
```

## 🔧 Configuration Files

```
┌─────────────────┐
│  Configuration  │
├─────────────────┤
│ • .env          │ - Environment variables
│ • config.py     │ - Application settings
│ • requirements.txt│ - Dependencies
└─────────────────┘
```

## 📁 File Structure

```
NL2MySQL/
├── app.py                    # FastAPI application
├── config.py                 # Configuration settings
├── sql_generator.py          # Main orchestrator
├── retriever.py              # Schema retrieval
├── schema_embedder.py        # ChromaDB embeddings
├── prompt_templates_enhanced.py # Enhanced prompts with IIQ knowledge
├── validator.py              # SQL validation
├── optimizer.py              # Query optimization
├── iiq_synonyms.py           # IIQ knowledge
├── iiq_feedback.py           # Learning system
├── adapters/
│   ├── llm_local.py          # Ollama adapter
│   ├── llm_openai.py         # OpenAI adapter
│   ├── llm_sqlcoder.py       # SQLCoder adapter
│   └── db_mysql.py           # MySQL adapter
├── iiq_frontend.py           # Streamlit UI
├── iiq_training_data.json    # Training examples
├── test_*.py                 # Test scripts
└── *.txt                     # Environment configs
```

## 🚀 Deployment Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Development   │    │   Production    │    │   Monitoring    │
│                 │    │                 │    │                 │
│ • Local dev     │    │ • Docker        │    │ • Logs          │
│ • Testing       │    │ • Kubernetes    │    │ • Metrics       │
│ • Debugging     │    │ • Scaling       │    │ • Alerts        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔄 Learning Loop

```
┌─────────────────┐
│  Continuous     │
│  Learning       │
├─────────────────┤
│ 1. User Query   │
│ 2. Generate SQL │
│ 3. Execute      │
│ 4. Get Results  │
│ 5. DBA Feedback │
│ 6. Store        │
│ 7. Improve      │
└─────────────────┘
```

## 📊 Performance Metrics

```
┌─────────────────┐
│  Performance    │
├─────────────────┤
│ • Response Time │ - 10-30 seconds
│ • Accuracy      │ - Training dependent
│ • Memory Usage  │ - 32GB available
│ • Model Size    │ - Phi: 1.6GB
└─────────────────┘
```

## 🛡️ Security & Validation

```
┌─────────────────┐
│  Security       │
├─────────────────┤
│ • SQL Injection │ - Prevention
│ • Access Control│ - Authentication
│ • Query Limits  │ - Resource protection
│ • Audit Logs    │ - Compliance
└─────────────────┘
```

This architecture provides a complete, scalable, and maintainable system for converting natural language queries to optimized MySQL queries for SailPoint IdentityIQ.
