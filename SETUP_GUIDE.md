# 🚀 NL2SQL Complete Setup Guide

This comprehensive guide will walk you through setting up the NL2SQL system from scratch. Follow these steps to get your natural language to SQL converter running.

## 📋 Prerequisites

### System Requirements
- **Python 3.11+** (recommended)
- **Git** for cloning the repository
- **Docker & Docker Compose** (for containerized deployment)
- **MSSQL Server** access (local or remote)

### Hardware Recommendations

#### For Local LLM (Ollama):
- **Minimum**: 8GB RAM, 4-core CPU
- **Recommended**: 16GB+ RAM, 8-core CPU, GPU (NVIDIA preferred)
- **Storage**: 10GB+ free space for models

#### For OpenAI Only:
- **Minimum**: 4GB RAM, 2-core CPU
- **Storage**: 2GB free space

---

## 🛠️ Installation Methods

Choose one of the following installation methods:

### Method 1: Docker Deployment (Recommended)

#### Step 1: Clone Repository
```bash
git clone https://github.com/yourname/nl2sql.git
cd nl2sql
```

#### Step 2: Configure Environment
```bash
# Copy environment template
cp env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

**Required Configuration:**
```bash
# Database Connection - REPLACE WITH YOUR DETAILS
DB_CONNECTION_STRING=mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+17+for+SQL+Server

# Choose LLM Provider
LLM_PROVIDER=local  # or 'openai'

# If using OpenAI, add your API key
LLM_OPENAI_API_KEY=your_api_key_here
```

#### Step 3: Start Services
```bash
# Start all services (includes Ollama for local LLM)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f nl2sql
```

#### Step 4: Pull Local Model (if using local LLM)
```bash
# Pull a model (this may take several minutes)
docker-compose exec ollama ollama pull mistral

# Alternative models:
# docker-compose exec ollama ollama pull llama2
# docker-compose exec ollama ollama pull codellama
```

#### Step 5: Extract and Embed Schema
```bash
# Extract schema from your database
docker-compose exec nl2sql python schema_inspector.py --connection "$DB_CONNECTION_STRING"

# Embed schema into vector database
docker-compose exec nl2sql python schema_embedder.py

# Verify embedding worked
docker-compose exec nl2sql python schema_embedder.py --stats
```

#### Step 6: Test the System
```bash
# Check health
curl http://localhost:8000/health

# Test query generation
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all customers"}'
```

---

### Method 2: Local Installation

#### Step 1: System Dependencies

**Windows:**
```powershell
# Install Python 3.11+ from python.org
# Install Git from git-scm.com

# Install Microsoft ODBC Driver
# Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

**Linux (Ubuntu/Debian):**
```bash
# Update system
sudo apt update

# Install Python and dependencies
sudo apt install python3.11 python3.11-pip python3.11-venv git

# Install ODBC drivers
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt update
sudo ACCEPT_EULA=Y apt install msodbcsql18 unixodbc-dev
```

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and dependencies
brew install python@3.11 git

# Install ODBC drivers
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew install msodbcsql18 mssql-tools18
```

#### Step 2: Clone and Setup Python Environment
```bash
# Clone repository
git clone https://github.com/yourname/nl2sql.git
cd nl2sql

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Install and Configure Local LLM

Choose one of these local LLM options:

##### **Option A: Ollama (Recommended)**

**Windows Installation:**
```powershell
# Download from https://ollama.ai/download/windows
# Or install using winget:
winget install Ollama.Ollama

# After installation, restart your terminal and verify:
ollama --version

# Start Ollama service (runs automatically on Windows)
# If not running, start manually:
ollama serve

# In another terminal, pull a model
ollama pull mistral

# Alternative models:
ollama pull llama2        # Meta's Llama 2 (7B)
ollama pull codellama     # Code-focused model
ollama pull phi           # Microsoft's efficient model (3B)
```

**Linux Installation:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# In another terminal, pull a model
ollama pull mistral
```

**macOS Installation:**
```bash
# Download from https://ollama.ai/download/mac
# Or install using Homebrew:
brew install ollama

# Start Ollama
ollama serve

# Pull a model
ollama pull mistral
```

**Verify Ollama Installation:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# List installed models
ollama list

# Test model generation
ollama run mistral "SELECT * FROM users WHERE active = 1"
```

##### **Option B: GPT4All**

**Install GPT4All:**
```bash
# Install the Python package
pip install gpt4all

# Download models (will happen automatically on first use)
python -c "
import gpt4all
model = gpt4all.GPT4All('orca-mini-3b.q4_0.bin')
print('GPT4All installed successfully')
"
```

##### **Option C: Docker Ollama (Alternative)**
```bash
# Run Ollama in Docker
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Pull model
docker exec -it ollama ollama pull mistral

# Test model
docker exec -it ollama ollama run mistral "SELECT * FROM customers"
```

##### **Choosing the Right Model:**

| Model | Size | RAM Required | Speed | Quality | Best For |
|-------|------|--------------|-------|---------|----------|
| **phi** | 3B | 4GB | Fast | Good | Resource-constrained systems |
| **mistral** | 7B | 6GB | Medium | Very Good | Balanced performance |
| **llama2** | 7B | 6GB | Medium | Good | General purpose |
| **llama2:13b** | 13B | 10GB | Slow | Excellent | High-quality results |
| **codellama** | 7B | 6GB | Medium | Very Good | Code-focused tasks |

**Recommended for NL2SQL:**
- **Start with**: `mistral` (good balance of speed and quality)
- **If you have 16GB+ RAM**: `llama2:13b` (better quality)
- **If limited RAM**: `phi` (fastest, still decent quality)

#### Step 4: Configure Environment
```bash
# Copy and edit environment file
cp env.example .env

# Edit configuration
nano .env
```

#### Step 5: Extract and Embed Schema
```bash
# Extract schema
python schema_inspector.py --connection "your_connection_string_here"

# Embed schema
python schema_embedder.py

# Check embedding stats
python schema_embedder.py --stats
```

#### Step 6: Start the API Server
```bash
# Start development server
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Or for production
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🔧 Configuration Details

### Database Connection Strings

**SQL Server with SQL Authentication:**
```bash
DB_CONNECTION_STRING=mssql+pyodbc://username:password@server:1433/database?driver=ODBC+Driver+17+for+SQL+Server
```

**SQL Server with Windows Authentication:**
```bash
DB_CONNECTION_STRING=mssql+pyodbc://server/database?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes
```

**Azure SQL Database:**
```bash
DB_CONNECTION_STRING=mssql+pyodbc://username:password@server.database.windows.net/database?driver=ODBC+Driver+17+for+SQL+Server&encrypt=yes&trustServerCertificate=no
```

**SQL Server Express (Local):**
```bash
DB_CONNECTION_STRING=mssql+pyodbc://./SQLEXPRESS/database?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes
```

### LLM Configuration

**Local LLM (Ollama):**
```bash
LLM_PROVIDER=local
LLM_LOCAL_MODEL=mistral  # or llama2, codellama, etc.
LLM_LOCAL_URL=http://localhost:11434
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=1000
```

**OpenAI:**
```bash
LLM_PROVIDER=openai
LLM_OPENAI_API_KEY=sk-your-key-here
LLM_OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=1000
```

**Azure OpenAI:**
```bash
LLM_PROVIDER=openai
LLM_OPENAI_API_KEY=your-azure-key
# Additional Azure-specific configuration needed in code
```

---

## 🧪 Testing Your Setup

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "components": {
    "llm": "healthy",
    "schema_retriever": "healthy"
  }
}
```

### 2. Schema Information
```bash
curl http://localhost:8000/schema/info
```

### 3. Simple Query Test
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me all customers",
    "include_explanation": true
  }'
```

### 4. SQL Validation Test
```bash
curl -X POST "http://localhost:8000/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM customers WHERE active = 1",
    "validation_level": "standard"
  }'
```

### 5. Query Execution Test (if database is accessible)
```bash
curl -X POST "http://localhost:8000/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT TOP 5 * FROM customers",
    "max_rows": 10
  }'
```

---

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. "LLM adapter not available"
**Symptoms:** Health check shows LLM as unhealthy
**Solutions:**
- **For Ollama:** Check if Ollama is running (`ollama serve`)
- **For OpenAI:** Verify API key is correct and has credits
- Check network connectivity

#### 2. "No schema chunks available"
**Symptoms:** Schema retriever shows 0 chunks
**Solutions:**
```bash
# Re-run schema extraction
python schema_inspector.py --connection "your_connection_string"

# Re-run embedding
python schema_embedder.py --reset

# Check if schema.json exists and has content
ls -la schema*.json
```

#### 3. Database Connection Issues
**Symptoms:** Cannot connect to database
**Solutions:**
- Verify connection string format
- Check database server is accessible
- Ensure ODBC driver is installed
- Test connection with a simple tool first

#### 4. Docker Issues
**Symptoms:** Services won't start
**Solutions:**
```bash
# Check Docker is running
docker --version

# Check logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

#### 5. Memory Issues with Local LLM
**Symptoms:** Ollama crashes or very slow
**Solutions:**
- Use smaller models (`ollama pull phi` or `ollama pull mistral:7b`)
- Increase Docker memory limits
- Close other applications
- Check available RAM: `ollama ps` (shows running models)
- Consider using OpenAI instead

#### 6. Ollama Installation Issues
**Symptoms:** `ollama` command not found
**Solutions:**
```bash
# Windows: Add to PATH or reinstall
winget uninstall Ollama.Ollama
winget install Ollama.Ollama

# Linux: Reinstall with proper permissions
sudo rm -rf /usr/local/bin/ollama
curl -fsSL https://ollama.ai/install.sh | sh

# macOS: Reinstall via Homebrew
brew uninstall ollama
brew install ollama

# Verify installation
ollama --version
which ollama  # Should show installation path
```

#### 7. Ollama Service Not Starting
**Symptoms:** Cannot connect to Ollama API
**Solutions:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Windows: Start service manually
ollama serve

# Linux: Start as systemd service
sudo systemctl start ollama
sudo systemctl enable ollama

# macOS: Start manually
ollama serve

# Check process
ps aux | grep ollama
```

#### 8. Model Download Issues
**Symptoms:** Model download fails or is very slow
**Solutions:**
```bash
# Check available space (models are 2-40GB)
df -h  # Linux/macOS
dir   # Windows

# Download smaller model first
ollama pull phi  # Only 3GB

# Check download progress
ollama ps

# Manual model management
ollama list                    # List installed models
ollama rm model_name          # Remove model
ollama pull model_name:tag    # Pull specific version
```

#### 9. GPT4All Issues
**Symptoms:** GPT4All import fails or models don't download
**Solutions:**
```bash
# Reinstall GPT4All
pip uninstall gpt4all
pip install gpt4all

# Test installation
python -c "
import gpt4all
print('Available models:', gpt4all.GPT4All.list_models())
"

# Manual model download
python -c "
import gpt4all
model = gpt4all.GPT4All('orca-mini-3b-gguf2-q4_0.gguf')
print('Model downloaded successfully')
"
```

### Debug Mode

Enable debug mode for more detailed logging:
```bash
# In .env file
APP_DEBUG=true
APP_LOG_LEVEL=DEBUG

# Restart the service
docker-compose restart nl2sql
```

---

## 📊 Performance Optimization

### For Local LLM
1. **Use GPU acceleration** if available
2. **Choose appropriate model size**:
   - Small: `mistral:7b` (4GB RAM)
   - Medium: `llama2:13b` (8GB RAM)
   - Large: `llama2:70b` (40GB+ RAM)
3. **Optimize Docker resources**:
   ```yaml
   # In docker-compose.yml
   services:
     ollama:
       deploy:
         resources:
           limits:
             memory: 8G
   ```

### For OpenAI
1. **Use appropriate model**:
   - Fast & Cheap: `gpt-3.5-turbo`
   - Best Quality: `gpt-4`
2. **Optimize token usage**:
   ```bash
   LLM_MAX_TOKENS=500  # Reduce for shorter responses
   LLM_TEMPERATURE=0.05  # More deterministic
   ```

### Database Optimization
1. **Use connection pooling**:
   ```bash
   DB_MAX_POOL_SIZE=20
   DB_TIMEOUT=60
   ```
2. **Optimize schema embedding**:
   ```bash
   VECTOR_TOP_K=3  # Reduce for faster retrieval
   ```

---

## 🚀 Production Deployment

### Environment Variables for Production
```bash
# Security
APP_DEBUG=false
APP_LOG_LEVEL=WARNING

# Performance
LLM_TEMPERATURE=0.05
VECTOR_TOP_K=3
DB_MAX_POOL_SIZE=20

# Monitoring
APP_HOST=0.0.0.0
APP_PORT=8000
```

### Docker Production Setup
```bash
# Use production docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Scale the service
docker-compose up -d --scale nl2sql=3

# Setup reverse proxy (nginx/traefik)
# Setup SSL certificates
# Setup monitoring (prometheus/grafana)
```

### Security Considerations
1. **Use environment variables** for all secrets
2. **Enable HTTPS** in production
3. **Configure CORS** properly
4. **Set up rate limiting**
5. **Monitor for unusual queries**

---

## 📚 API Documentation

Once running, visit these URLs:
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Key Endpoints:
- `POST /query` - Generate SQL from natural language
- `POST /execute` - Execute SQL query
- `POST /validate` - Validate SQL syntax and security
- `POST /optimize` - Optimize SQL performance
- `GET /schema/info` - Get schema information

---

## 🤝 Getting Help

### Common Resources
1. **Check logs**: `docker-compose logs nl2sql`
2. **Health endpoint**: `curl http://localhost:8000/health`
3. **Schema stats**: `python schema_embedder.py --stats`
4. **Test LLM**: `python adapters/llm_local.py --check`

### Support Channels
- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Ask questions and share experiences
- **Documentation**: Comprehensive API docs at `/docs`

---

## ✅ Setup Checklist

- [ ] System requirements met (Python 3.11+, Docker, ODBC drivers)
- [ ] Repository cloned and dependencies installed
- [ ] Environment configured (`.env` file)
- [ ] LLM service running (Ollama or OpenAI configured)
- [ ] Database accessible and connection string correct
- [ ] Schema extracted (`schema.json` exists)
- [ ] Schema embedded (ChromaDB populated)
- [ ] API server running on port 8000
- [ ] Health check returns "healthy"
- [ ] Test query successful
- [ ] Ready for production use! 🎉

---

**Need help?** Check the troubleshooting section above or create an issue on GitHub!
