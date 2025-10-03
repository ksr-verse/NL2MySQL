"""Configuration module for NL2SQL application.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    connection_string: str = Field(
        default="mysql+pymysql://root@localhost:3306/database",
        description="MySQL connection string"
    )
    max_pool_size: int = Field(default=10, description="Maximum database connection pool size")
    timeout: int = Field(default=30, description="Database query timeout in seconds")
    
    class Config:
        env_prefix = "DB_"


class LLMConfig(BaseSettings):
    """LLM configuration settings."""
    
    provider: str = Field(default="groq", description="LLM provider: GROQ ONLY")
    
    # Groq settings (ONLY LLM provider)
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key - set via LLM_GROQ_API_KEY environment variable")
    groq_model: str = Field(default="llama-3.1-8b-instant", description="Groq model name")
    
    # Generation parameters
    temperature: float = Field(default=0.1, description="Temperature for text generation")
    max_tokens: int = Field(default=1000, description="Maximum tokens to generate")
    
    class Config:
        env_prefix = "LLM_"


class VectorDBConfig(BaseSettings):
    """Vector database configuration."""
    
    persist_directory: str = Field(default="./chromadb", description="ChromaDB persistence directory")
    collection_name: str = Field(default="schema_embeddings", description="Collection name for schema embeddings")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model for embeddings")
    top_k: int = Field(default=5, description="Number of top similar chunks to retrieve")
    
    class Config:
        env_prefix = "VECTOR_"


class AppConfig(BaseSettings):
    """Application configuration."""
    
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    
    # Schema files
    schema_file: str = Field(default="schema.json", description="Auto-generated schema file")
    manual_schema_file: str = Field(default="schema_manual.json", description="Manual schema file")
    
    class Config:
        env_prefix = "APP_"


class Settings:
    """Main settings class that combines all configurations."""
    
    def __init__(self):
        self.db = DatabaseConfig()
        self.llm = LLMConfig()
        self.vector_db = VectorDBConfig()
        self.app = AppConfig()


# Global settings instance
settings = Settings()
