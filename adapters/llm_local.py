"""Local LLM adapter for Ollama and other local models.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

import json
import requests
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from loguru import logger
from config import settings


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


class OllamaAdapter(BaseLLMAdapter):
    """Adapter for Ollama local LLM service."""
    
    def __init__(self, model_name: str = None, base_url: str = None):
        """Initialize Ollama adapter."""
        self.model_name = model_name or settings.llm.local_model
        self.base_url = base_url or settings.llm.local_url
        self.api_url = f"{self.base_url}/api/generate"
        self.models_url = f"{self.base_url}/api/tags"
        
        logger.info(f"Initialized Ollama adapter with model: {self.model_name}")
    
    def is_available(self) -> bool:
        """Check if Ollama service is running and model is available."""
        try:
            # Check if Ollama service is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False
            
            # Check if the specific model is available
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            # Check for exact match or partial match (for different tags)
            model_available = any(
                self.model_name in model_name or model_name.startswith(self.model_name)
                for model_name in available_models
            )
            
            if not model_available:
                logger.warning(f"Model {self.model_name} not found. Available models: {available_models}")
                return False
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama service not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {e}")
            return False
    
    def generate_sql(self, prompt: str) -> str:
        """Generate SQL using Ollama."""
        if not self.is_available():
            raise RuntimeError("Ollama service is not available")
        
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
            "options": {
                "temperature": settings.llm.temperature,
                "num_predict": min(settings.llm.max_tokens, 500),  # Limit to 500 tokens for faster response
                "top_k": 40,
                "top_p": 0.9,
                "stop": ["Human:", "Assistant:", "\n\n---", "```"]
            }
            }
            
            logger.debug(f"Sending request to Ollama: {self.api_url}")
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=120,  # Increased timeout for local models
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                raise RuntimeError(f"Ollama API error: {response.status_code}")
            
            result = response.json()
            generated_text = result.get("response", "").strip()
            
            if not generated_text:
                raise RuntimeError("Empty response from Ollama")
            
            # Clean up the response - remove any markdown formatting
            sql_query = self._clean_sql_response(generated_text)
            
            logger.info(f"Generated SQL query using Ollama model: {self.model_name}")
            return sql_query
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error calling Ollama: {e}")
            raise RuntimeError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Error generating SQL with Ollama: {e}")
            raise RuntimeError(f"SQL generation error: {e}")
    
    def _clean_sql_response(self, response: str) -> str:
        """Clean up the SQL response from the model."""
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
        
        # Remove common prefixes
        prefixes_to_remove = [
            "SQL:",
            "Query:",
            "Answer:",
            "Here's the SQL query:",
            "The SQL query is:",
        ]
        
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # Remove trailing explanations (common with some models)
        lines = response.split('\n')
        sql_lines = []
        for line in lines:
            # Stop if we hit an explanation line
            if any(phrase in line.lower() for phrase in ["this query", "explanation:", "note:"]):
                break
            sql_lines.append(line)
        
        cleaned_response = '\n'.join(sql_lines).strip()
        
        # Ensure query ends with semicolon if it doesn't already
        if cleaned_response and not cleaned_response.endswith(';'):
            cleaned_response += ';'
        
        return cleaned_response
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            response = requests.get(self.models_url, timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                return [model['name'] for model in models_data.get('models', [])]
            else:
                logger.error(f"Error fetching models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching available models: {e}")
            return []
    
    def pull_model(self, model_name: str = None) -> bool:
        """Pull a model to Ollama."""
        model_to_pull = model_name or self.model_name
        
        try:
            pull_url = f"{self.base_url}/api/pull"
            payload = {"name": model_to_pull}
            
            logger.info(f"Pulling model: {model_to_pull}")
            response = requests.post(pull_url, json=payload, timeout=600)  # 10 minutes timeout
            
            if response.status_code == 200:
                logger.info(f"Successfully pulled model: {model_to_pull}")
                return True
            else:
                logger.error(f"Error pulling model: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error pulling model {model_to_pull}: {e}")
            return False


class GPT4AllAdapter(BaseLLMAdapter):
    """Adapter for GPT4All local models (placeholder implementation)."""
    
    def __init__(self, model_path: str = None):
        """Initialize GPT4All adapter."""
        self.model_path = model_path
        logger.warning("GPT4All adapter is a placeholder implementation")
    
    def is_available(self) -> bool:
        """Check if GPT4All is available."""
        try:
            import gpt4all
            return True
        except ImportError:
            logger.error("GPT4All not installed. Install with: pip install gpt4all")
            return False
    
    def generate_sql(self, prompt: str) -> str:
        """Generate SQL using GPT4All."""
        if not self.is_available():
            raise RuntimeError("GPT4All is not available")
        
        try:
            import gpt4all
            
            # Initialize model (this is a simplified implementation)
            model = gpt4all.GPT4All(self.model_path or "orca-mini-3b.q4_0.bin")
            
            # Generate response
            response = model.generate(
                prompt,
                max_tokens=settings.llm.max_tokens,
                temp=settings.llm.temperature
            )
            
            return self._clean_sql_response(response)
            
        except Exception as e:
            logger.error(f"Error generating SQL with GPT4All: {e}")
            raise RuntimeError(f"GPT4All error: {e}")
    
    def _clean_sql_response(self, response: str) -> str:
        """Clean up SQL response (same as Ollama)."""
        # Reuse the same cleaning logic as Ollama
        adapter = OllamaAdapter()
        return adapter._clean_sql_response(response)


class LocalLLMFactory:
    """Factory for creating local LLM adapters."""
    
    @staticmethod
    def create_adapter(provider: str = "ollama", **kwargs) -> BaseLLMAdapter:
        """Create a local LLM adapter."""
        if provider.lower() == "ollama":
            return OllamaAdapter(**kwargs)
        elif provider.lower() == "gpt4all":
            return GPT4AllAdapter(**kwargs)
        else:
            raise ValueError(f"Unsupported local LLM provider: {provider}")
    
    @staticmethod
    def get_best_available_adapter() -> Optional[BaseLLMAdapter]:
        """Get the best available local LLM adapter."""
        # Try Ollama first
        try:
            ollama_adapter = OllamaAdapter()
            if ollama_adapter.is_available():
                return ollama_adapter
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
        
        # Try GPT4All as fallback
        try:
            gpt4all_adapter = GPT4AllAdapter()
            if gpt4all_adapter.is_available():
                return gpt4all_adapter
        except Exception as e:
            logger.debug(f"GPT4All not available: {e}")
        
        logger.warning("No local LLM adapters available")
        return None


def main():
    """Test the local LLM adapter."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test local LLM adapter")
    parser.add_argument("--provider", choices=["ollama", "gpt4all"], default="ollama")
    parser.add_argument("--model", help="Model name")
    parser.add_argument("--prompt", help="Test prompt", default="SELECT * FROM users WHERE active = 1;")
    parser.add_argument("--check", action="store_true", help="Check availability only")
    parser.add_argument("--pull", help="Pull a specific model (Ollama only)")
    
    args = parser.parse_args()
    
    try:
        if args.provider == "ollama":
            adapter = OllamaAdapter(model_name=args.model)
        else:
            adapter = GPT4AllAdapter(model_path=args.model)
        
        if args.pull and args.provider == "ollama":
            success = adapter.pull_model(args.pull)
            print(f"Model pull {'successful' if success else 'failed'}")
            return
        
        if args.check or not args.prompt:
            available = adapter.is_available()
            print(f"{args.provider} adapter available: {available}")
            
            if args.provider == "ollama" and available:
                models = adapter.get_available_models()
                print(f"Available models: {models}")
            return
        
        if adapter.is_available():
            print(f"Testing {args.provider} with prompt: {args.prompt}")
            result = adapter.generate_sql(args.prompt)
            print(f"Generated SQL:\n{result}")
        else:
            print(f"{args.provider} is not available")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
