"""FastAPI application for NL2SQL service."""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import time
from loguru import logger
import sys

from sql_generator import SQLGenerator
from validator import ValidationLevel
from optimizer import OptimizationLevel
from adapters.db_mysql import MySQLAdapter
from config import settings

# Configure logging
logger.remove()
logger.add(sys.stdout, level=settings.app.log_level)
logger.add("nl2sql.log", rotation="1 day", level="DEBUG")

# Initialize FastAPI app
app = FastAPI(
    title="NL2SQL - Natural Language to SQL",
    description="Convert natural language queries to optimized MySQL queries using AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
sql_generator: Optional[SQLGenerator] = None
db_adapter: Optional[MySQLAdapter] = None


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for SQL generation."""
    question: str = Field(..., description="Natural language question", min_length=1, max_length=1000)
    include_explanation: bool = Field(default=False, description="Include explanation of generated SQL")
    validation_level: str = Field(default="standard", description="Validation level: basic, standard, strict")
    optimization_level: str = Field(default="standard", description="Optimization level: basic, standard, aggressive")
    max_retries: int = Field(default=3, description="Maximum retry attempts", ge=1, le=5)


class ExecuteRequest(BaseModel):
    """Request model for SQL execution."""
    sql: str = Field(..., description="SQL query to execute", min_length=1)
    max_rows: int = Field(default=1000, description="Maximum rows to return", ge=1, le=10000)
    timeout: int = Field(default=30, description="Query timeout in seconds", ge=5, le=300)


class ValidateRequest(BaseModel):
    """Request model for SQL validation."""
    sql: str = Field(..., description="SQL query to validate", min_length=1)
    validation_level: str = Field(default="standard", description="Validation level: basic, standard, strict")


class OptimizeRequest(BaseModel):
    """Request model for SQL optimization."""
    sql: str = Field(..., description="SQL query to optimize", min_length=1)
    optimization_level: str = Field(default="standard", description="Optimization level: basic, standard, aggressive")


class QueryResponse(BaseModel):
    """Response model for SQL generation."""
    success: bool
    sql: str = ""
    explanation: str = ""
    natural_language_query: str
    execution_time_ms: int
    validation_result: Optional[Dict[str, Any]] = None
    optimization_result: Optional[Dict[str, Any]] = None
    warnings: List[str] = []
    errors: List[str] = []
    metadata: Dict[str, Any] = {}


class ExecuteResponse(BaseModel):
    """Response model for SQL execution."""
    success: bool
    sql: str
    execution_time_ms: int
    row_count: int = 0
    columns: List[str] = []
    data: List[List[Any]] = []
    errors: List[str] = []
    warnings: List[str] = []
    truncated: bool = False


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    components: Dict[str, str]
    issues: List[str] = []
    version: str = "1.0.0"


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global sql_generator, db_adapter
    
    try:
        logger.info("Starting NL2SQL service...")
        
        # Initialize SQL generator
        validation_level = ValidationLevel.STANDARD
        optimization_level = OptimizationLevel.STANDARD
        
        sql_generator = SQLGenerator(validation_level, optimization_level)
        logger.info("SQL generator initialized")
        
        # Initialize database adapter (optional)
        try:
            db_adapter = MySQLAdapter()
            if db_adapter.test_connection():
                logger.info("Database adapter initialized and connected")
            else:
                logger.warning("Database adapter initialized but connection failed")
        except Exception as e:
            logger.warning(f"Database adapter initialization failed: {e}")
            db_adapter = None
        
        logger.info("NL2SQL service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global db_adapter
    
    logger.info("Shutting down NL2SQL service...")
    
    if db_adapter:
        try:
            db_adapter.close()
            logger.info("Database connections closed")
        except Exception as e:
            logger.warning(f"Error closing database connections: {e}")
    
    logger.info("NL2SQL service shutdown complete")


# Dependency injection
def get_sql_generator() -> SQLGenerator:
    """Get SQL generator instance."""
    if sql_generator is None:
        raise HTTPException(status_code=503, detail="SQL generator not initialized")
    return sql_generator


def get_db_adapter() -> MySQLAdapter:
    """Get database adapter instance."""
    if db_adapter is None:
        raise HTTPException(status_code=503, detail="Database adapter not available")
    return db_adapter


# API endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with service information."""
    return {
        "service": "NL2SQL - Natural Language to SQL",
        "version": "1.0.0",
        "description": "Convert natural language queries to optimized MySQL queries",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(generator: SQLGenerator = Depends(get_sql_generator)):
    """Health check endpoint."""
    try:
        health_result = generator.health_check()
        
        return HealthResponse(
            status=health_result["overall_status"],
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            components=health_result["components"],
            issues=health_result["issues"]
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            components={"error": "health_check_failed"},
            issues=[str(e)]
        )


@app.post("/query", response_model=QueryResponse)
async def generate_sql(
    request: QueryRequest,
    generator: SQLGenerator = Depends(get_sql_generator)
):
    """Generate SQL from natural language query."""
    start_time = time.time()
    
    try:
        logger.info(f"Generating SQL for query: {request.question}")
        
        # Parse validation and optimization levels
        try:
            validation_level = ValidationLevel(request.validation_level.lower())
            optimization_level = OptimizationLevel(request.optimization_level.lower())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid level parameter: {e}")
        
        # Update generator levels if different
        if generator.validator.validation_level != validation_level:
            generator.validator.validation_level = validation_level
        if generator.optimizer.optimization_level != optimization_level:
            generator.optimizer.optimization_level = optimization_level
        
        # Generate SQL
        result = generator.generate_sql(
            natural_language_query=request.question,
            include_explanation=request.include_explanation,
            max_retries=request.max_retries,
            validate_syntax=True,
            optimize_query=True
        )
        
        execution_time = int((time.time() - start_time) * 1000)
        
        response = QueryResponse(
            success=result["success"],
            sql=result["sql_query"],
            explanation=result.get("explanation", ""),
            natural_language_query=request.question,
            execution_time_ms=execution_time,
            validation_result=result.get("validation_result"),
            optimization_result=result.get("optimization_result"),
            warnings=result.get("warnings", []),
            errors=result.get("errors", []),
            metadata=result.get("generation_metadata", {})
        )
        
        logger.info(f"SQL generation {'successful' if result['success'] else 'failed'} in {execution_time}ms")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        logger.error(f"Error in SQL generation: {e}")
        
        return QueryResponse(
            success=False,
            natural_language_query=request.question,
            execution_time_ms=execution_time,
            errors=[str(e)]
        )


@app.post("/execute", response_model=ExecuteResponse)
async def execute_sql(
    request: ExecuteRequest,
    db: MySQLAdapter = Depends(get_db_adapter)
):
    """Execute SQL query against the database."""
    start_time = time.time()
    
    try:
        logger.info(f"Executing SQL query: {request.sql[:100]}...")
        
        # Execute the query
        result = db.execute_query(
            query=request.sql,
            max_rows=request.max_rows,
            fetch_results=True
        )
        
        execution_time = int((time.time() - start_time) * 1000)
        
        response = ExecuteResponse(
            success=result["success"],
            sql=request.sql,
            execution_time_ms=execution_time,
            row_count=result.get("row_count", 0),
            columns=result.get("columns", []),
            data=result.get("data", []),
            errors=[result["error"]] if result.get("error") else [],
            truncated=result.get("truncated", False)
        )
        
        logger.info(f"SQL execution {'successful' if result['success'] else 'failed'} in {execution_time}ms")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        logger.error(f"Error executing SQL: {e}")
        
        return ExecuteResponse(
            success=False,
            sql=request.sql,
            execution_time_ms=execution_time,
            errors=[str(e)]
        )


@app.post("/validate")
async def validate_sql(
    request: ValidateRequest,
    generator: SQLGenerator = Depends(get_sql_generator)
):
    """Validate SQL query."""
    try:
        logger.info("Validating SQL query")
        
        # Parse validation level
        try:
            validation_level = ValidationLevel(request.validation_level.lower())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid validation level: {e}")
        
        # Update validator level if different
        if generator.validator.validation_level != validation_level:
            generator.validator.validation_level = validation_level
        
        # Validate the query
        result = generator.validator.validate_query(request.sql)
        
        return {
            "success": True,
            "validation_result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating SQL: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/optimize")
async def optimize_sql(
    request: OptimizeRequest,
    generator: SQLGenerator = Depends(get_sql_generator)
):
    """Optimize SQL query."""
    try:
        logger.info("Optimizing SQL query")
        
        # Parse optimization level
        try:
            optimization_level = OptimizationLevel(request.optimization_level.lower())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid optimization level: {e}")
        
        # Update optimizer level if different
        if generator.optimizer.optimization_level != optimization_level:
            generator.optimizer.optimization_level = optimization_level
        
        # Optimize the query
        result = generator.optimizer.optimize_query(request.sql)
        
        return {
            "success": True,
            "optimization_result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing SQL: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/analyze")
async def analyze_query(
    sql: str,
    generator: SQLGenerator = Depends(get_sql_generator)
):
    """Analyze query complexity and performance."""
    try:
        logger.info("Analyzing query complexity")
        
        result = generator.analyze_query_complexity(sql)
        
        return {
            "success": True,
            "analysis_result": result
        }
        
    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/schema/suggestions")
async def get_schema_suggestions(
    query: str,
    generator: SQLGenerator = Depends(get_sql_generator)
):
    """Get schema suggestions for a natural language query."""
    try:
        logger.info(f"Getting schema suggestions for: {query}")
        
        result = generator.get_schema_suggestions(query)
        
        return {
            "success": True,
            "suggestions": result
        }
        
    except Exception as e:
        logger.error(f"Error getting schema suggestions: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/schema/info")
async def get_schema_info(generator: SQLGenerator = Depends(get_sql_generator)):
    """Get information about the loaded schema."""
    try:
        info = generator.retriever.get_collection_info()
        
        return {
            "success": True,
            "schema_info": info
        }
        
    except Exception as e:
        logger.error(f"Error getting schema info: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "status_code": 500
        }
    )


# Additional utility endpoints
@app.get("/models/info")
async def get_model_info(generator: SQLGenerator = Depends(get_sql_generator)):
    """Get information about available models."""
    try:
        info = {
            "llm_provider": settings.llm.provider,
            "model_name": getattr(generator.llm_adapter, 'model_name', 'unknown'),
            "available": generator.llm_adapter.is_available() if generator.llm_adapter else False
        }
        
        # Get available models if supported
        if hasattr(generator.llm_adapter, 'get_available_models'):
            try:
                info["available_models"] = generator.llm_adapter.get_available_models()
            except:
                pass
        
        return {
            "success": True,
            "model_info": info
        }
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower()
    )
