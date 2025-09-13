# NL2MySQL - Natural Language to MySQL

A FastAPI-based service that converts natural language queries into MySQL SQL queries using AI/LLM technology.

## Overview

This project is adapted from NL2SQL to work specifically with MySQL databases. It provides a REST API that accepts natural language questions and returns corresponding SQL queries, with optional query execution and result formatting.

## Features

- 🧠 **AI-Powered SQL Generation**: Uses local LLM (Ollama) or OpenAI to generate SQL from natural language
- 🔍 **Schema-Aware**: Automatically inspects and understands your database schema
- ✅ **Query Validation**: Validates generated SQL before execution
- ⚡ **Query Optimization**: Optimizes SQL queries for better performance
- 🗄️ **MySQL Support**: Native MySQL database connectivity and syntax
- 🔧 **REST API**: FastAPI-based API with automatic documentation
- 📊 **Result Formatting**: Returns query results in JSON format
- 🎯 **Semantic Search**: Uses vector embeddings to find relevant schema information

## Prerequisites

- Python 3.8+
- MySQL Server 5.7+ or 8.0+
- (Optional) Ollama for local LLM support

## Quick Setup

### 1. Install Dependencies

Run the automated setup script:

```bash
python setup_mysql.py
```

Or install manually:

```bash
pip install -r requirements.txt
```

### 2. Configure MySQL Connection

Update the `.env` file with your MySQL connection details:

```env
DB_CONNECTION_STRING=mysql+pymysql://root@localhost:3306/your_database
```

### 3. Test Connection

```bash
python simple_mysql_test.py
```

### 4. Start the Server

```bash
python app.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Generate SQL Query
```http
POST /query
Content-Type: application/json

{
    "question": "Show me all users who placed orders in the last month",
    "include_explanation": true,
    "validation_level": "standard",
    "optimization_level": "standard"
}
```

### Execute SQL Query
```http
POST /execute
Content-Type: application/json

{
    "sql": "SELECT * FROM users WHERE age > 25",
    "max_rows": 100
}
```

### Validate SQL
```http
POST /validate
Content-Type: application/json

{
    "sql": "SELECT * FROM users",
    "validation_level": "standard"
}
```

## Configuration

### Database Configuration

```env
# MySQL Connection
DB_CONNECTION_STRING=mysql+pymysql://username:password@host:port/database
DB_MAX_POOL_SIZE=10
DB_TIMEOUT=30
```

### LLM Configuration

```env
# Use local LLM (Ollama)
LLM_PROVIDER=local
LLM_LOCAL_MODEL=mistral
LLM_LOCAL_URL=http://localhost:11434

# Or use OpenAI
LLM_PROVIDER=openai
LLM_OPENAI_API_KEY=your_api_key
LLM_OPENAI_MODEL=gpt-3.5-turbo
```

## Sample Usage

### Example Natural Language Queries

1. **Basic Selection**:
   - "Show me all users"
   - "List products with price greater than 100"

2. **Aggregation**:
   - "Count orders by status"
   - "Average age of users"

3. **Joins**:
   - "Show users and their orders"
   - "Find customers who never placed an order"

4. **Complex Queries**:
   - "Top 5 products by sales volume last quarter"
   - "Users who placed more than 3 orders this year"

### Example Response

```json
{
    "success": true,
    "sql": "SELECT * FROM users WHERE age > 25",
    "explanation": "This query selects all users older than 25 years",
    "natural_language_query": "Show me users older than 25",
    "execution_time_ms": 45,
    "validation_result": {
        "valid": true,
        "warnings": []
    }
}
```

## MySQL-Specific Features

### Query Syntax
- Uses MySQL-specific syntax (LIMIT instead of TOP)
- Supports MySQL functions and operators
- Handles MySQL data types correctly

### Schema Inspection
- Reads MySQL INFORMATION_SCHEMA tables
- Supports MySQL-specific column attributes
- Handles MySQL indexes and constraints

### Connection Options
```python
# Various MySQL connection formats
"mysql+pymysql://user:pass@localhost:3306/db"
"mysql+mysqlconnector://user:pass@localhost:3306/db"
```

## Development

### Project Structure

```
NL2MySQL/
├── adapters/
│   ├── db_mysql.py          # MySQL database adapter
│   ├── llm_local.py         # Local LLM integration
│   └── llm_openai.py        # OpenAI integration
├── app.py                   # FastAPI application
├── config.py                # Configuration management
├── sql_generator.py         # Main SQL generation engine
├── validator.py             # SQL validation
├── optimizer.py             # Query optimization
├── schema_inspector.py      # Database schema analysis
├── retriever.py             # Vector-based schema retrieval
└── requirements.txt         # Python dependencies
```

### Testing

Run the test suite:

```bash
python -m pytest tests/
```

Test specific components:

```bash
# Test MySQL connection
python simple_mysql_test.py

# Test API endpoints
python test_api.py
```

## Troubleshooting

### Common Issues

1. **Connection Error**: Ensure MySQL server is running and credentials are correct
2. **Permission Denied**: Grant necessary privileges to the MySQL user
3. **Module Not Found**: Install missing dependencies with `pip install -r requirements.txt`

### MySQL Setup

```sql
-- Create user and database
CREATE DATABASE nl2mysql_demo;
CREATE USER 'nl2mysql'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON nl2mysql_demo.* TO 'nl2mysql'@'localhost';
FLUSH PRIVILEGES;
```

## Performance Tips

1. **Database Indexing**: Ensure proper indexes on frequently queried columns
2. **Connection Pooling**: Adjust `DB_MAX_POOL_SIZE` based on your needs
3. **Query Limits**: Use reasonable `max_rows` limits for large datasets
4. **Schema Caching**: The system caches schema information for better performance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on the original NL2SQL project
- Uses FastAPI for the REST API framework
- Integrates with Ollama for local LLM support
- Uses ChromaDB for vector storage and retrieval
