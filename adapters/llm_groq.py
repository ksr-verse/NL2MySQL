#!/usr/bin/env python3
"""Groq API adapter for fast and reliable SQL generation.

Uses Groq's ultra-fast inference platform with Llama-2-70B for high-quality SQL generation.
Perfect combination of speed and intelligence for natural-language-to-SQL conversion.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

import json
import requests
from typing import Dict, Any, Optional
from loguru import logger
import time
import os
from abc import ABC, abstractmethod


class BaseLLMAdapter(ABC):
    """Base class for LLM adapters."""
    
    @abstractmethod
    def generate_sql(self, prompt: str) -> str:
        """Generate SQL from a prompt."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM service is available."""
        pass


class GroqAdapter(BaseLLMAdapter):
    """Adapter for Groq API with Llama-2-70B - ultra-fast SQL generation."""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model_name: str = "meta-llama/llama-4-maverick-17b-128e-instruct",
                 base_url: str = "https://api.groq.com/openai/v1"):
        """Initialize Groq adapter."""
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("No Groq API key found. Please set GROQ_API_KEY environment variable.")
            logger.info("Get your free API key at: https://console.groq.com/")
        
        self.model_name = model_name
        self.base_url = base_url
        self.chat_url = f"{self.base_url}/chat/completions"
        
        logger.info(f"Initializing Groq adapter")
        logger.info(f"   Model: {model_name}")
        logger.info(f"   API URL: {base_url}")
        logger.info(f"   API Key: {'Set' if self.api_key else 'Missing'}")
        
        if self.api_key:
            logger.info("Groq adapter ready for ultra-fast SQL generation!")
    
    def is_available(self) -> bool:
        """Check if Groq API is available."""
        if not self.api_key:
            return False
        
        try:
            # Test with a simple request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "messages": [{"role": "user", "content": "Hi"}],
                "model": self.model_name,
                "max_tokens": 5,
                "temperature": 0.1
            }
            
            response = requests.post(
                self.chat_url,
                headers=headers,
                json=test_payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.debug(f"Groq availability check failed: {e}")
            return False
    
    def generate_sql(self, prompt: str, timeout: int = 30, **kwargs) -> str:
        """Generate SQL using Groq's ultra-fast Llama-2-70B."""
        
        logger.info(f"GROQ: Starting SQL generation")
        logger.info(f"GROQ: Prompt length: {len(prompt)} characters")
        logger.info(f"GROQ: Model: {self.model_name}")
        logger.info(f"GROQ: Timeout: {timeout}s")
        
        if not self.api_key:
            logger.error(f"GROQ: API key not configured")
            return "SELECT 'Groq API key not configured' as error_message;"
        
        try:
            # Format prompt for Llama-2-70B via Groq
            logger.info(f"GROQ: Formatting prompt for Groq API")
            messages = self._format_prompt_for_groq(prompt)
            logger.info(f"GROQ: Prompt formatted into {len(messages)} messages")
            logger.info(f"GROQ: First message preview: {messages[0]['content'][:200]}...")
            
            # Log complete content of all messages
            for i, message in enumerate(messages):
                logger.info(f"GROQ: Complete Message {i+1}/{len(messages)}:")
                logger.info(f"Role: {message.get('role', 'unknown')}")
                logger.info(f"Content: {message.get('content', '')}")
                logger.info("=" * 80)
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": messages,
                "model": self.model_name,
                "max_tokens": 300,  # Sufficient for most SQL queries
                "temperature": 0.1,  # Low temperature for consistent SQL
                "top_p": 0.9,
                "stream": False,
                "stop": ["Human:", "Assistant:", "\n\n---"]
            }
            
            logger.info(f"GROQ: Sending request to {self.chat_url}")
            logger.info(f"GROQ: Request parameters - max_tokens: {payload['max_tokens']}, temperature: {payload['temperature']}")
            logger.info(f"GROQ: Headers: {headers}")
            logger.info(f"GROQ: Payload keys: {list(payload.keys())}")
            
            start_time = time.time()
            
            response = requests.post(
                self.chat_url,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            generation_time = time.time() - start_time
            logger.info(f"GROQ: Response received in {generation_time:.2f}s")
            logger.info(f"GROQ: Response status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"GROQ: Request successful")
                response_data = response.json()
                logger.info(f"GROQ: Response data structure: {list(response_data.keys())}")
                
                if "choices" not in response_data or not response_data["choices"]:
                    logger.error(f"GROQ: No choices in response: {response_data}")
                    return "SELECT 'No response choices from Groq API' as error_message;"
                
                choice = response_data["choices"][0]
                logger.info(f"GROQ: Choice structure: {list(choice.keys())}")
                
                if "message" not in choice or "content" not in choice["message"]:
                    logger.error(f"GROQ: Invalid choice structure: {choice}")
                    return "SELECT 'Invalid response structure from Groq API' as error_message;"
                
                generated_text = choice["message"]["content"]
                
                logger.info(f"GROQ: Raw response length: {len(generated_text)} characters")
                logger.info(f"GROQ: Raw response preview: {generated_text[:200]}...")
                
                if not generated_text or len(generated_text.strip()) == 0:
                    logger.error(f"GROQ: Empty response from API")
                    logger.error(f"GROQ: Full response data: {response_data}")
                    return "SELECT 'Empty response from Groq API' as error_message;"
                
                # Extract SQL from response
                logger.info(f"GROQ: Extracting SQL from response")
                sql_query = self._extract_sql_from_groq_response(generated_text)
                logger.info(f"GROQ: SQL extraction complete")
                logger.info(f"GROQ: Extracted SQL length: {len(sql_query)} characters")
                logger.info(f"GROQ: Final SQL: {sql_query}")
                
                return sql_query
                
            else:
                logger.error(f"GROQ: Request failed with status {response.status_code}")
                error_msg = f"Groq API error: {response.status_code}"
                if response.status_code == 401:
                    error_msg += " - Invalid API key"
                    logger.error(f"GROQ: API key authentication failed")
                elif response.status_code == 429:
                    error_msg += " - Rate limit exceeded"
                    logger.error(f"GROQ: Rate limit exceeded")
                elif response.status_code == 400:
                    try:
                        error_detail = response.json().get("error", {}).get("message", "")
                        error_msg += f" - {error_detail}"
                        logger.error(f"GROQ: Bad request details: {error_detail}")
                    except:
                        logger.error(f"GROQ: Bad request (no details available)")
                        pass
                
                logger.error(f"GROQ: Returning error SQL: {error_msg}")
                return f"SELECT '{error_msg}' as error_message;"
                
        except requests.exceptions.Timeout:
            logger.error(f"Groq API timeout after {timeout}s")
            return f"SELECT 'Groq API timeout after {timeout}s' as error_message;"
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            return f"SELECT 'Error: {str(e)[:100]}' as error_message;"
    
    def _format_prompt_for_groq(self, prompt: str) -> list:
        """Format the prompt for Groq's chat format - pass through the Vector DB prompt as-is."""
        
        # Simple system message - let the Vector DB prompt handle everything
        system_message = """You are a MySQL database expert. Generate clean SQL queries based on the provided schema and examples."""
        
        # Pass the complete prompt from Vector DB as the user message
        user_message = prompt
        
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    
    def _extract_user_query(self, prompt: str) -> str:
        """Extract user query from intelligent prompt."""
        if "## USER QUERY:" in prompt:
            start = prompt.find("## USER QUERY:") + len("## USER QUERY:")
            end = prompt.find("\n\n", start)
            if end == -1:
                end = prompt.find("##", start)
            if end > start:
                return prompt[start:end].strip()
        
        # Fallback - look for query patterns
        lines = prompt.split('\n')
        for line in lines[:15]:
            line = line.strip()
            if any(word in line.lower() for word in ['show', 'find', 'get', 'list', 'users', 'accounts', 'give me']):
                return line
        
        return "List all users"
    
    def _extract_schema_context(self, prompt: str) -> str:
        """Extract and format schema context from intelligent prompt."""
        if "## SCHEMA CONTEXT:" in prompt:
            start = prompt.find("## SCHEMA CONTEXT:")
            end = prompt.find("## TABLE RELATIONSHIPS:", start)
            if end == -1:
                end = prompt.find("## RELEVANT EXAMPLES:", start)
            if end > start:
                schema_section = prompt[start:end]
                
                # Convert to clean table definitions
                tables = []
                lines = schema_section.split('\n')
                current_table = None
                current_columns = []
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('### ') and ':' in line:
                        # Save previous table
                        if current_table and current_columns:
                            tables.append(f"identityiq.{current_table}({', '.join(current_columns[:10])})")
                        
                        # Start new table
                        current_table = line.replace('###', '').replace(':', '').strip()
                        current_columns = []
                        
                    elif line.startswith('- Columns:') and current_table:
                        columns_part = line.replace('- Columns:', '').strip()
                        if columns_part:
                            cols = [col.strip() for col in columns_part.split(',')]
                            # Prioritize important columns
                            important_cols = []
                            
                            # Always include id first
                            if 'id' in cols:
                                important_cols.append('id')
                            
                            # Add other key columns
                            for col in cols:
                                if col != 'id' and any(key in col.lower() for key in [
                                    'name', 'email', 'display', 'first', 'last', 'application', 
                                    'identity', 'native', 'attributes', 'entitlements', 'active'
                                ]):
                                    important_cols.append(col)
                                    if len(important_cols) >= 10:
                                        break
                            
                            current_columns = important_cols if important_cols else cols[:8]
                
                # Save last table
                if current_table and current_columns:
                    tables.append(f"identityiq.{current_table}({', '.join(current_columns[:10])})")
                
                if tables:
                    return '\n'.join(tables)
        
        # Default schema for IdentityIQ
        return """identityiq.spt_identity(id, name, display_name, firstname, lastname, email, manager, active)
identityiq.spt_link(id, identity_id, application, display_name, native_identity, attributes, entitlements)
identityiq.spt_application(id, name)
identityiq.spt_identity_entitlement(id, identity_id, application, name, value, granted_by_role)"""
    
    def _extract_examples(self, prompt: str) -> str:
        """Extract and format examples from intelligent prompt."""
        if "## RELEVANT EXAMPLES:" in prompt:
            start = prompt.find("## RELEVANT EXAMPLES:")
            end = prompt.find("## CONSTRUCTION RULES:", start)
            if end == -1:
                end = prompt.find("## GENERATE SQL:", start)
            if end > start:
                examples_section = prompt[start:end]
                
                # Format examples for Groq
                formatted_examples = []
                lines = examples_section.split('\n')
                current_nl = None
                
                for line in lines:
                    line = line.strip()
                    if line.startswith(('1.', '2.', '3.')) and any(word in line.lower() for word in ['show', 'list', 'find', 'give']):
                        current_nl = line.split('.', 1)[1].strip()
                    elif line.startswith('SQL:') and current_nl:
                        sql_part = line.replace('SQL:', '').strip()
                        if sql_part:
                            formatted_examples.append(f"Q: {current_nl}\nA: {sql_part}")
                        current_nl = None
                
                if formatted_examples:
                    return '\n\n'.join(formatted_examples)
        
        # Default examples for IdentityIQ
        return """Q: Show me users who have accounts in Trakk
A: SELECT DISTINCT i.firstname, i.lastname, i.email FROM spt_identity i JOIN spt_link l ON i.id = l.identity_id JOIN spt_application a ON l.application = a.id WHERE a.name = 'Trakk' AND i.inactive = 0;

Q: Find users with TimeSheetEnterAuthority capability
A: SELECT DISTINCT i.firstname, i.lastname, i.email, a.name as application FROM spt_identity i JOIN spt_link l ON i.id = l.identity_id JOIN spt_application a ON l.application = a.id WHERE (l.attributes LIKE '%TimeSheetEnterAuthority%' OR l.entitlements LIKE '%TimeSheetEnterAuthority%') AND i.inactive = 0;

Q: List all users with their email addresses
A: SELECT firstname, lastname, email FROM spt_identity WHERE inactive = 0;"""
    
    def _extract_sql_from_groq_response(self, response: str) -> str:
        """Extract clean SQL query from Groq response."""
        
        logger.debug(f"Raw Groq response: {response[:200]}...")
        
        # Clean the response
        sql_query = response.strip()
        
        # Remove markdown and formatting
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        
        # Remove explanatory text at the beginning
        lines = sql_query.split('\n')
        sql_lines = []
        found_select = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Start collecting from SELECT
            if line.upper().startswith('SELECT') or found_select:
                found_select = True
                
                # Stop at explanatory text
                if any(phrase in line.lower() for phrase in [
                    'this query', 'explanation', 'note:', 'the above query', 
                    'here is', 'this will', 'the result', 'this sql'
                ]):
                    break
                    
                sql_lines.append(line)
            elif any(word in line.upper() for word in ['SELECT', 'WITH', 'FROM']):
                # Catch SELECT that might not be at the start
                found_select = True
                sql_lines.append(line)
        
        sql_query = ' '.join(sql_lines).strip()
        
        # If no SELECT found, try to prepend it
        if sql_query and not sql_query.upper().startswith('SELECT'):
            # Look for common SQL patterns
            if any(word in sql_query.upper() for word in ['FROM', 'WHERE', 'JOIN']):
                sql_query = f"SELECT {sql_query}"
        
        # Clean up formatting
        sql_query = ' '.join(sql_query.split())  # Normalize whitespace
        sql_query = sql_query.replace(' .', '.').replace('. ', '.')
        sql_query = sql_query.replace(' ,', ',').replace('( ', '(').replace(' )', ')')
        
        # Ensure semicolon
        if sql_query and not sql_query.endswith(';'):
            sql_query += ';'
        
        # Validate basic SQL structure
        if (not sql_query or len(sql_query) < 15 or 
            not sql_query.upper().startswith('SELECT')):
            logger.warning(f"Generated SQL appears invalid: {sql_query[:100]}")
            return "SELECT 'Invalid SQL generated by Groq' as error_message;"
        
        logger.debug(f"Extracted SQL: {sql_query}")
        return sql_query
    
    def test_connection(self) -> bool:
        """Test if Groq API is working."""
        try:
            if not self.is_available():
                return False
            
            test_prompt = """You are a MySQL expert. Generate a simple query.

Schema: spt_identity(id, name, email)
Query: List all users
Generate MySQL query:"""
            
            result = self.generate_sql(test_prompt, timeout=15)
            return ("SELECT" in result.upper() and 
                    "error" not in result.lower() and
                    "spt_identity" in result)
        except:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Groq model."""
        return {
            "model_name": self.model_name,
            "provider": "Groq",
            "type": "groq-llama2",
            "capabilities": [
                "Ultra-fast inference (~1-2 seconds)",
                "Natural language to SQL conversion", 
                "MySQL syntax optimization",
                "Complex query generation",
                "70B parameter intelligence",
                "Schema-aware queries"
            ],
            "status": "healthy" if self.is_available() else "unavailable",
            "free_tier": "14,400 requests/day",
            "setup_url": "https://console.groq.com/",
            "speed": "Ultra-fast (~100 tokens/second)"
        }
