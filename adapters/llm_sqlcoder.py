#!/usr/bin/env python3
"""SQLCoder LLM adapter for SQL-specific generation."""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Dict, Any, Optional
from loguru import logger
from .llm_local import BaseLLMAdapter

class SQLCoderAdapter(BaseLLMAdapter):
    """Adapter for SQLCoder model - specifically trained for SQL generation."""
    
    def __init__(self, model_id: str = "defog/sqlcoder-7b-2"):
        """Initialize SQLCoder adapter."""
        self.model_id = model_id
        self.model_name = "sqlcoder-7b-2"
        
        logger.info(f"Loading SQLCoder model: {model_id}")
        
        try:
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id, 
                device_map="auto",
                torch_dtype=torch.float16,  # Use half precision for speed
                trust_remote_code=True
            )
            
            logger.info(f"SQLCoder model loaded successfully on device: {self.model.device}")
            
        except Exception as e:
            logger.error(f"Failed to load SQLCoder model: {e}")
            raise RuntimeError(f"SQLCoder model loading failed: {e}")
    
    def is_available(self) -> bool:
        """Check if SQLCoder is available."""
        try:
            return self.model is not None and self.tokenizer is not None
        except:
            return False
    
    def generate_sql(self, prompt: str, **kwargs) -> str:
        """Generate SQL using SQLCoder model."""
        try:
            logger.debug(f"Generating SQL with SQLCoder for prompt length: {len(prompt)}")
            
            # Format prompt for SQLCoder
            formatted_prompt = self._format_prompt_for_sqlcoder(prompt)
            
            # Tokenize input
            inputs = self.tokenizer(
                formatted_prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=2048
            ).to(self.model.device)
            
            # Generate SQL
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,  # Reasonable limit for SQL
                    temperature=0.1,     # Low temperature for deterministic SQL
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract SQL from response
            sql_query = self._extract_sql_from_response(response, formatted_prompt)
            
            logger.info(f"Generated SQL query using SQLCoder: {self.model_name}")
            logger.debug(f"Generated SQL: {sql_query[:200]}...")
            
            return sql_query
            
        except Exception as e:
            logger.error(f"SQLCoder generation failed: {e}")
            return "SELECT 'Error generating SQL' as error_message;"
    
    def _format_prompt_for_sqlcoder(self, prompt: str) -> str:
        """Format the prompt specifically for SQLCoder model."""
        
        # Extract schema and query from the complex prompt
        schema_context = ""
        user_query = ""
        
        # Look for schema context
        if "DATABASE SCHEMA:" in prompt:
            schema_start = prompt.find("DATABASE SCHEMA:")
            schema_end = prompt.find("USER QUERY:", schema_start)
            if schema_end == -1:
                schema_end = prompt.find("NATURAL LANGUAGE QUERY:", schema_start)
            if schema_end > schema_start:
                schema_context = prompt[schema_start:schema_end].strip()
        
        # Look for user query
        if "USER QUERY:" in prompt:
            query_start = prompt.find("USER QUERY:")
            user_query = prompt[query_start:].replace("USER QUERY:", "").strip()
        elif "NATURAL LANGUAGE QUERY:" in prompt:
            query_start = prompt.find("NATURAL LANGUAGE QUERY:")
            user_query = prompt[query_start:].replace("NATURAL LANGUAGE QUERY:", "").strip()
        else:
            # Fallback - use the whole prompt
            user_query = prompt
        
        # Format for SQLCoder
        sqlcoder_prompt = f"""Schema:
{schema_context}

Question: {user_query}
Write a MySQL query:"""
        
        return sqlcoder_prompt
    
    def _extract_sql_from_response(self, response: str, original_prompt: str) -> str:
        """Extract SQL query from SQLCoder response."""
        
        # Look for SQL after "Write a MySQL query:"
        if "Write a MySQL query:" in response:
            sql_start = response.find("Write a MySQL query:") + len("Write a MySQL query:")
            sql_part = response[sql_start:].strip()
        else:
            sql_part = response
        
        # Clean up the SQL
        lines = sql_part.split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('Question:', 'Schema:', 'Write a')):
                sql_lines.append(line)
        
        sql_query = '\n'.join(sql_lines).strip()
        
        # Ensure it starts with SELECT
        if not sql_query.upper().startswith(('SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE')):
            # Try to find SQL in the response
            for line in lines:
                if line.upper().startswith(('SELECT', 'WITH')):
                    sql_query = line.strip()
                    break
        
        return sql_query if sql_query else "SELECT 'No SQL generated' as error_message;"
    
    def test_connection(self) -> bool:
        """Test if SQLCoder is working."""
        try:
            test_prompt = "Schema:\nTable users(id, name, email)\nQuestion: List all users\nWrite a MySQL query:"
            result = self.generate_sql(test_prompt)
            return "SELECT" in result.upper()
        except:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        return {
            "model_name": self.model_name,
            "model_id": self.model_id,
            "type": "sqlcoder",
            "capabilities": [
                "SQL generation",
                "MySQL optimization", 
                "Schema-aware queries",
                "Fast inference"
            ],
            "status": "healthy" if self.is_available() else "unavailable"
        }
