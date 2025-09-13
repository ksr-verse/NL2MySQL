"""OpenAI LLM adapter for cloud-based SQL generation."""

from typing import Dict, Any, Optional, List
import openai
from openai import OpenAI
from loguru import logger
from config import settings
from .llm_local import BaseLLMAdapter


class OpenAIAdapter(BaseLLMAdapter):
    """Adapter for OpenAI GPT models."""
    
    def __init__(self, api_key: str = None, model_name: str = None):
        """Initialize OpenAI adapter."""
        self.api_key = api_key or settings.llm.openai_api_key
        self.model_name = model_name or settings.llm.openai_model
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"Initialized OpenAI adapter with model: {self.model_name}")
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        try:
            # Test with a simple API call
            response = self.client.models.list()
            
            # Check if our model is available
            available_models = [model.id for model in response.data]
            
            if self.model_name not in available_models:
                logger.warning(f"Model {self.model_name} not found in available models")
                # Don't fail if model not in list - it might still work
            
            return True
            
        except openai.AuthenticationError:
            logger.error("OpenAI authentication failed - check API key")
            return False
        except openai.RateLimitError:
            logger.warning("OpenAI rate limit exceeded")
            return True  # Service is available, just rate limited
        except Exception as e:
            logger.error(f"OpenAI service not available: {e}")
            return False
    
    def generate_sql(self, prompt: str, system_prompt: str = None) -> str:
        """Generate SQL using OpenAI."""
        if not self.is_available():
            raise RuntimeError("OpenAI service is not available")
        
        try:
            # Prepare messages
            messages = []
            
            # Add system prompt if provided
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add user prompt
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Make API call
            logger.debug(f"Sending request to OpenAI model: {self.model_name}")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=settings.llm.temperature,
                max_tokens=settings.llm.max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )
            
            # Extract generated text
            if not response.choices:
                raise RuntimeError("No response choices from OpenAI")
            
            generated_text = response.choices[0].message.content.strip()
            
            if not generated_text:
                raise RuntimeError("Empty response from OpenAI")
            
            # Clean up the response
            sql_query = self._clean_sql_response(generated_text)
            
            logger.info(f"Generated SQL query using OpenAI model: {self.model_name}")
            logger.debug(f"Token usage: {response.usage}")
            
            return sql_query
            
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise RuntimeError("Rate limit exceeded. Please try again later.")
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {e}")
            raise RuntimeError("Authentication failed. Check your API key.")
        except openai.BadRequestError as e:
            logger.error(f"OpenAI bad request: {e}")
            raise RuntimeError(f"Bad request: {e}")
        except Exception as e:
            logger.error(f"Error generating SQL with OpenAI: {e}")
            raise RuntimeError(f"OpenAI error: {e}")
    
    def _clean_sql_response(self, response: str) -> str:
        """Clean up the SQL response from OpenAI."""
        # Remove markdown code blocks if present
        if "```sql" in response.lower():
            # Extract content between ```sql and ```
            start = response.lower().find("```sql") + 6
            end = response.find("```", start)
            if end != -1:
                response = response[start:end].strip()
        elif "```" in response:
            # Extract content between ``` blocks
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                response = response[start:end].strip()
        
        # Remove common prefixes and explanatory text
        lines = response.split('\n')
        sql_lines = []
        in_sql_block = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines at the beginning
            if not line and not sql_lines:
                continue
            
            # Skip explanatory lines
            if any(phrase in line.lower() for phrase in [
                "here's the sql", "here is the sql", "the query is",
                "this query", "explanation:", "note:", "answer:"
            ]):
                continue
            
            # Start of SQL (common patterns)
            if any(line.upper().startswith(keyword) for keyword in [
                "SELECT", "INSERT", "UPDATE", "DELETE", "WITH", "CREATE", "ALTER", "DROP"
            ]):
                in_sql_block = True
            
            # If we're in SQL block or this looks like SQL
            if in_sql_block or any(keyword in line.upper() for keyword in [
                "SELECT", "FROM", "WHERE", "JOIN", "GROUP BY", "ORDER BY", "HAVING"
            ]):
                sql_lines.append(line)
            # Stop if we hit explanatory text after SQL
            elif sql_lines and any(phrase in line.lower() for phrase in [
                "this query", "explanation", "note", "the above"
            ]):
                break
        
        cleaned_response = '\n'.join(sql_lines).strip()
        
        # Remove common prefixes that might remain
        prefixes_to_remove = [
            "SQL:", "Query:", "Answer:", "Result:"
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned_response.startswith(prefix):
                cleaned_response = cleaned_response[len(prefix):].strip()
        
        # Ensure query ends with semicolon if it doesn't already
        if cleaned_response and not cleaned_response.endswith(';'):
            cleaned_response += ';'
        
        return cleaned_response
    
    def generate_with_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Generate SQL with conversation history."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=settings.llm.temperature,
                max_tokens=settings.llm.max_tokens
            )
            
            generated_text = response.choices[0].message.content.strip()
            return self._clean_sql_response(generated_text)
            
        except Exception as e:
            logger.error(f"Error in conversation generation: {e}")
            raise RuntimeError(f"Conversation error: {e}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        try:
            response = self.client.models.list()
            models = [model.id for model in response.data]
            
            # Filter for chat models (GPT-3.5, GPT-4, etc.)
            chat_models = [
                model for model in models 
                if any(prefix in model for prefix in ['gpt-3.5', 'gpt-4', 'gpt-35'])
            ]
            
            return sorted(chat_models)
            
        except Exception as e:
            logger.error(f"Error fetching OpenAI models: {e}")
            return []
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count."""
        # Very rough estimation: ~4 characters per token
        return len(text) // 4
    
    def validate_api_key(self) -> bool:
        """Validate the OpenAI API key."""
        try:
            self.client.models.list()
            return True
        except openai.AuthenticationError:
            return False
        except Exception:
            # Other errors might indicate network issues, not invalid key
            return True


class AzureOpenAIAdapter(OpenAIAdapter):
    """Adapter for Azure OpenAI Service."""
    
    def __init__(
        self, 
        api_key: str = None, 
        endpoint: str = None, 
        deployment_name: str = None,
        api_version: str = "2023-12-01-preview"
    ):
        """Initialize Azure OpenAI adapter."""
        self.api_key = api_key or settings.llm.openai_api_key
        self.endpoint = endpoint
        self.deployment_name = deployment_name
        self.api_version = api_version
        
        if not self.api_key or not self.endpoint or not self.deployment_name:
            raise ValueError("Azure OpenAI requires API key, endpoint, and deployment name")
        
        # Initialize Azure OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=f"{self.endpoint}/openai/deployments/{self.deployment_name}",
            default_query={"api-version": self.api_version}
        )
        
        # Use deployment name as model name for Azure
        self.model_name = self.deployment_name
        
        logger.info(f"Initialized Azure OpenAI adapter with deployment: {self.deployment_name}")


def main():
    """Test the OpenAI adapter."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test OpenAI LLM adapter")
    parser.add_argument("--model", help="Model name", default="gpt-3.5-turbo")
    parser.add_argument("--prompt", help="Test prompt", 
                       default="Generate a SQL query to find all active users")
    parser.add_argument("--check", action="store_true", help="Check availability only")
    parser.add_argument("--models", action="store_true", help="List available models")
    parser.add_argument("--azure", action="store_true", help="Use Azure OpenAI")
    parser.add_argument("--endpoint", help="Azure endpoint")
    parser.add_argument("--deployment", help="Azure deployment name")
    
    args = parser.parse_args()
    
    try:
        if args.azure:
            if not args.endpoint or not args.deployment:
                print("Azure OpenAI requires --endpoint and --deployment")
                return
            adapter = AzureOpenAIAdapter(
                endpoint=args.endpoint,
                deployment_name=args.deployment
            )
        else:
            adapter = OpenAIAdapter(model_name=args.model)
        
        if args.models:
            models = adapter.get_available_models()
            print("Available models:")
            for model in models:
                print(f"  - {model}")
            return
        
        if args.check:
            available = adapter.is_available()
            valid_key = adapter.validate_api_key()
            print(f"OpenAI adapter available: {available}")
            print(f"API key valid: {valid_key}")
            return
        
        if adapter.is_available():
            print(f"Testing OpenAI with prompt: {args.prompt}")
            result = adapter.generate_sql(args.prompt)
            print(f"Generated SQL:\n{result}")
        else:
            print("OpenAI is not available")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
