"""SQL generator that combines LLM, schema retrieval, validation, and optimization.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

from typing import Dict, Any, Optional, List
from loguru import logger
import os

# Removed old retriever - using two-step Vector DB search only
from two_step_vector_db_search import TwoStepVectorDBSearch
from validator import SQLValidator, ValidationLevel
# Removed context_translator - added no value, just complexity
# Removed schema_aware_llm - not used, replaced by dynamic vector retrieval
# Removed optimizer - Groq generates well-formatted SQL already
from adapters.llm_groq import GroqAdapter
# Removed iiq_feedback - focusing on core functionality
from config import settings


class SQLGenerator:
    """Main SQL generation engine that orchestrates all components."""
    
    def __init__(
        self,
        validation_level: ValidationLevel = ValidationLevel.STANDARD
    ):
        """Initialize SQL generator with all components."""
        # Using only the new two-step Vector DB search - no old retriever needed
        self.validator = SQLValidator(validation_level)
        self.vector_search = TwoStepVectorDBSearch()
        # Removed schema_aware_llm - using dynamic vector retrieval instead
        
        # Removed feedback manager - focusing on core functionality
        
        # Initialize LLM adapter based on configuration
        self.llm_adapter = self._initialize_llm_adapter()
        
        logger.info("SQL Generator initialized successfully")
    
    def _initialize_llm_adapter(self):
        """Initialize the appropriate LLM adapter - GROQ ONLY."""
        try:
            provider = settings.llm.provider.lower()
            
            # FORCE GROQ USAGE ONLY - NO FALLBACKS
            logger.info(f"Current provider setting: {provider}")
            if provider != "groq":
                logger.warning(f"Provider is {provider}, forcing to groq")
                provider = "groq"  # Force groq
            
            # Get API key from settings or environment
            groq_api_key = settings.llm.groq_api_key or os.getenv("GROQ_API_KEY") or os.getenv("LLM_GROQ_API_KEY")
            
            if not groq_api_key:
                logger.error("Groq API key not found in settings or environment")
                raise RuntimeError("Groq API key required. Set GROQ_API_KEY or LLM_GROQ_API_KEY environment variable.")
            
            # Use Groq API with Llama-3.1-8b-instant - ultra-fast and reliable
            adapter = GroqAdapter(
                api_key=groq_api_key,
                model_name="openai/gpt-oss-20b"  # Match Groq UI model
            )
            
            if adapter.is_available():
                logger.info("Using Groq adapter ONLY (openai/gpt-oss-20b)")
                logger.info("Local models disabled - Groq only mode")
                return adapter
            else:
                logger.error("Groq not available - API key invalid or service down")
                raise RuntimeError("Groq API not available. Check your API key and internet connection.")
                
        except Exception as e:
            logger.error(f"Failed to initialize Groq adapter: {e}")
            raise RuntimeError(f"Groq initialization failed: {e}")
    
    def generate_sql(
        self,
        natural_language_query: str,
        include_explanation: bool = False,
        max_retries: int = 3,
        validate_syntax: bool = True,
        optimize_query: bool = True
    ) -> Dict[str, Any]:
        """
        Generate SQL from natural language query.
        
        Args:
            natural_language_query: The user's question in natural language
            include_explanation: Whether to include explanation of the generated SQL
            max_retries: Maximum number of retry attempts if generation fails
            validate_syntax: Whether to validate the generated SQL
            optimize_query: Whether to optimize the generated SQL
            
        Returns:
            Dictionary containing generation results
        """
        logger.info(f"SQL_GEN: Starting SQL generation pipeline")
        logger.info(f"SQL_GEN: Query: '{natural_language_query}'")
        logger.info(f"SQL_GEN: Parameters - explanation: {include_explanation}, retries: {max_retries}, validate: {validate_syntax}")
        
        result = {
            "success": False,
            "natural_language_query": natural_language_query,
            "sql_query": "",
            "explanation": "",
            "schema_context": "",
            "validation_result": None,
            "optimization_result": None,
            "generation_metadata": {
                "attempts": 0,
                "llm_provider": settings.llm.provider,
                "model_used": getattr(self.llm_adapter, 'model_name', 'unknown')
            },
            "errors": [],
            "warnings": []
        }
        
        try:
            # Step 1: Use two-step Vector DB search for prompt generation
            logger.info(f"SQL_GEN: Step 1 - Using two-step Vector DB search")
            logger.info(f"SQL_GEN: This will handle both schema retrieval and prompt generation")
            
            # The two-step search will handle everything - we don't need the old retriever
            result["approach"] = "two_step_vector_search"
            
            # Step 2: Generate SQL with retries
            logger.info(f"SQL_GEN: Step 2 - Generating SQL with LLM")
            logger.info(f"SQL_GEN: Starting retry loop (max {max_retries} attempts)")
            
            sql_query = None
            for attempt in range(max_retries):
                result["generation_metadata"]["attempts"] = attempt + 1
                logger.info(f"SQL_GEN: Attempt {attempt + 1}/{max_retries}")
                
                try:
                    logger.info(f"SQL_GEN: Calling _generate_sql_with_llm()")
                    sql_query = self._generate_sql_with_llm(
                        natural_language_query, attempt
                    )
                    
                    if sql_query and sql_query.strip():
                        logger.info(f"SQL_GEN: SQL generated successfully on attempt {attempt + 1}")
                        logger.info(f"SQL_GEN: Generated SQL: {sql_query[:100]}...")
                        break
                    else:
                        logger.warning(f"SQL_GEN: Empty SQL generated on attempt {attempt + 1}")
                        
                except Exception as e:
                    logger.warning(f"SQL_GEN: SQL generation attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"SQL_GEN: All generation attempts failed. Last error: {e}")
                        result["errors"].append(f"All generation attempts failed. Last error: {e}")
                        return result
            
            if not sql_query or not sql_query.strip():
                result["errors"].append("Failed to generate SQL after all attempts")
                return result
            
            result["sql_query"] = sql_query
            logger.info(f"SQL_GEN: SQL stored in result: {len(sql_query)} characters")
            
            # Step 3: Validate the generated SQL
            if validate_syntax:
                logger.info(f"SQL_GEN: Step 3 - Validating generated SQL")
                validation_result = self.validator.validate_query(sql_query)
                result["validation_result"] = validation_result
                
                logger.info(f"SQL_GEN: Validation results:")
                logger.info(f"   - Valid: {validation_result.get('valid', False)}")
                logger.info(f"   - Errors: {len(validation_result.get('errors', []))}")
                logger.info(f"   - Warnings: {len(validation_result.get('warnings', []))}")
                logger.info(f"   - Security issues: {len(validation_result.get('security_issues', []))}")
                
                if not validation_result["valid"]:
                    logger.warning(f"SQL_GEN: SQL validation failed")
                    # Try to fix common issues and regenerate
                    if attempt < max_retries - 1:
                        logger.info(f"SQL_GEN: Attempting to fix validation errors")
                        fixed_sql = self._attempt_sql_fix(sql_query, validation_result["errors"])
                        if fixed_sql and fixed_sql != sql_query:
                            logger.info(f"SQL_GEN: SQL fixed, re-validating")
                            sql_query = fixed_sql
                            result["sql_query"] = sql_query
                            # Re-validate
                            validation_result = self.validator.validate_query(sql_query)
                            result["validation_result"] = validation_result
                
                result["warnings"].extend(validation_result.get("warnings", []))
                result["warnings"].extend(validation_result.get("security_issues", []))
            else:
                logger.info(f"SQL_GEN: Skipping validation (validate_syntax=False)")
            
            # Step 4: Optimize the SQL (Groq generates well-formatted SQL, so skip optimization)
            if optimize_query:
                logger.info(f"SQL_GEN: No additional post-processing")
                result["optimization_result"] = {
                    "optimized_query": sql_query,
                    "optimizations_applied": [],
                    "warnings": []
                }
            else:
                logger.info(f"SQL_GEN: No additional post-processing")
            
            # Step 5: Generate explanation if requested
            if include_explanation:
                logger.info(f"SQL_GEN: Step 5 - Generating SQL explanation")
                try:
                    explanation = self._generate_explanation(result["sql_query"], schema_context)
                    result["explanation"] = explanation
                    logger.info(f"SQL_GEN: Explanation generated ({len(explanation)} characters)")
                except Exception as e:
                    logger.warning(f"SQL_GEN: Failed to generate explanation: {e}")
                    result["warnings"].append("Could not generate explanation")
            else:
                logger.info(f"SQL_GEN: Skipping explanation (include_explanation=False)")
            
            result["success"] = True
            logger.info(f"SQL_GEN: SQL generation completed successfully!")
            logger.info(f"SQL_GEN: Final result summary:")
            logger.info(f"   - SQL length: {len(result['sql_query'])}")
            logger.info(f"   - Explanation length: {len(result.get('explanation', ''))}")
            logger.info(f"   - Warnings: {len(result['warnings'])}")
            logger.info(f"   - Errors: {len(result['errors'])}")
            
        except Exception as e:
            logger.error(f"Error in SQL generation: {e}")
            result["errors"].append(f"Generation error: {str(e)}")
        
        return result
    
    def _generate_sql_with_llm(
        self, 
        natural_language_query: str, 
        attempt: int = 0,
        translation_result: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate SQL using the LLM adapter with enhanced prompts."""
        
        logger.info(f"LLM_GEN: Starting LLM SQL generation")
        logger.info(f"LLM_GEN: Query: '{natural_language_query}'")
        logger.info(f"LLM_GEN: Attempt: {attempt + 1}")
        
        # Build prompt using two-step Vector DB search
        logger.info(f"LLM_GEN: Building prompt using two-step Vector DB search")
        # Get complete prompt from Vector DB (includes schema + training + prompt template)
        complete_prompt = self.vector_search.generate_prompt_with_definitions(natural_language_query)
        
        logger.info(f"LLM_GEN: Prompt components:")
        logger.info(f"   - Complete prompt length: {len(complete_prompt)}")
        logger.info(f"   - Prompt preview: {complete_prompt[:300]}...")
        
        # Use the complete prompt from two-step search
        prompt = complete_prompt
        
        # Add retry context for subsequent attempts
        if attempt > 0:
            logger.info(f"LLM_GEN: Adding retry context for attempt {attempt + 1}")
            retry_context = f"\n\nRETRY ATTEMPT {attempt}: Previous attempt failed. Please ensure the SQL is syntactically correct and follows MySQL standards."
            prompt += retry_context
        
        logger.info(f"LLM_GEN: Final prompt length: {len(prompt)}")
        logger.info(f"LLM_GEN: Sending prompt to Groq LLM")
        logger.info(f"LLM_GEN: COMPLETE FINAL PROMPT:")
        logger.info(f"LLM_GEN: ================================================================================")
        logger.info(prompt)
        logger.info(f"LLM_GEN: ================================================================================")
        
        # Generate SQL using the LLM
        try:
            sql_result = self.llm_adapter.generate_sql(prompt)
            logger.info(f"LLM_GEN: LLM response received")
            logger.info(f"LLM_GEN: Generated SQL: {sql_result[:100]}...")
            logger.info(f"LLM_GEN: SQL length: {len(sql_result)}")
            return sql_result
        except Exception as e:
            logger.error(f"LLM_GEN: LLM generation failed: {e}")
            raise
    
    def _attempt_sql_fix(self, sql_query: str, errors: List[str]) -> str:
        """Attempt to fix common SQL errors."""
        fixed_sql = sql_query
        
        try:
            # Common fixes
            for error in errors:
                error_lower = error.lower()
                
                # Fix missing semicolon
                if "semicolon" in error_lower and not fixed_sql.strip().endswith(';'):
                    fixed_sql = fixed_sql.strip() + ';'
                
                # Fix unmatched quotes
                if "quote" in error_lower:
                    # Simple fix: ensure even number of single quotes
                    quote_count = fixed_sql.count("'")
                    if quote_count % 2 != 0:
                        fixed_sql += "'"
                
                # Fix unmatched parentheses
                if "parenthes" in error_lower:
                    open_count = fixed_sql.count('(')
                    close_count = fixed_sql.count(')')
                    if open_count > close_count:
                        fixed_sql += ')' * (open_count - close_count)
                    elif close_count > open_count:
                        fixed_sql = '(' * (close_count - open_count) + fixed_sql
            
            return fixed_sql
            
        except Exception as e:
            logger.warning(f"Error attempting to fix SQL: {e}")
            return sql_query
    
    def _generate_explanation(self, sql_query: str, schema_context: str) -> str:
        """Generate explanation for the SQL query."""
        try:
            explanation_prompt = f"""EXPLANATION REQUEST:
SQL Query: {sql_query}
Schema Context: {schema_context}

Please explain what this query does in plain English."""
            
            if hasattr(self.llm_adapter, 'generate_sql'):
                return self.llm_adapter.generate_sql(explanation_prompt)
            else:
                return self.llm_adapter.generate_sql(explanation_prompt)
                
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return "Could not generate explanation for this query."
    
    def validate_and_optimize_existing_sql(self, sql_query: str) -> Dict[str, Any]:
        """Validate and optimize an existing SQL query."""
        result = {
            "original_query": sql_query,
            "validation_result": None,
            "optimization_result": None,
            "final_query": sql_query,
            "success": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Validate the query
            validation_result = self.validator.validate_query(sql_query)
            result["validation_result"] = validation_result
            
            if not validation_result["valid"]:
                result["errors"].extend(validation_result["errors"])
                result["success"] = False
            
            result["warnings"].extend(validation_result.get("warnings", []))
            result["warnings"].extend(validation_result.get("security_issues", []))
            
            # Optimize the query
            optimization_result = self.optimizer.optimize_query(sql_query)
            result["optimization_result"] = optimization_result
            result["final_query"] = optimization_result["optimized_query"]
            
        except Exception as e:
            logger.error(f"Error validating/optimizing SQL: {e}")
            result["errors"].append(f"Processing error: {str(e)}")
            result["success"] = False
        
        return result
    
    
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of all components."""
        health = {
            "overall_status": "healthy",
            "components": {},
            "issues": []
        }
        
        try:
            # Check LLM adapter
            if self.llm_adapter and self.llm_adapter.is_available():
                health["components"]["llm"] = "healthy"
            else:
                health["components"]["llm"] = "unhealthy"
                health["issues"].append("LLM adapter not available")
                health["overall_status"] = "degraded"
            
            # Check schema retriever
            try:
                info = self.retriever.get_collection_info()
                if info.get("total_chunks", 0) > 0:
                    health["components"]["schema_retriever"] = "healthy"
                    health["components"]["schema_chunks"] = str(info.get("total_chunks", 0))
                else:
                    health["components"]["schema_retriever"] = "unhealthy"
                    health["issues"].append("No schema chunks available")
                    health["overall_status"] = "degraded"
            except Exception as e:
                health["components"]["schema_retriever"] = "unhealthy"
                health["issues"].append(f"Schema retriever error: {e}")
                health["overall_status"] = "degraded"
            
            # Validator and optimizer are always available (no external dependencies)
            health["components"]["validator"] = "healthy"
            health["components"]["optimizer"] = "healthy"
            
        except Exception as e:
            health["overall_status"] = "unhealthy"
            health["issues"].append(f"Health check error: {e}")
        
        return health


def main():
    """Test the SQL generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test SQL generator")
    parser.add_argument("query", help="Natural language query")
    parser.add_argument("--explain", action="store_true", help="Include explanation")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    parser.add_argument("--no-optimize", action="store_true", help="Skip optimization")
    parser.add_argument("--health", action="store_true", help="Check system health")
    parser.add_argument("--schema-suggestions", action="store_true", help="Get schema suggestions only")
    
    args = parser.parse_args()
    
    try:
        generator = SQLGenerator()
        
        if args.health:
            health = generator.health_check()
            print("System Health Check:")
            print(f"  Overall Status: {health['overall_status']}")
            print("  Components:")
            for component, status in health['components'].items():
                print(f"    {component}: {status}")
            if health['issues']:
                print("  Issues:")
                for issue in health['issues']:
                    print(f"    - {issue}")
            return
        
        
        # Generate SQL
        result = generator.generate_sql(
            args.query,
            include_explanation=args.explain,
            validate_syntax=not args.no_validate,
            optimize_query=not args.no_optimize
        )
        
        if result["success"]:
            print("SQL Generation Successful!")
            print(f"Query: {args.query}")
            print(f"Generated SQL:\n{result['sql_query']}")
            
            if result.get("explanation"):
                print(f"\nExplanation:\n{result['explanation']}")
            
            if result.get("validation_result"):
                val_result = result["validation_result"]
                print(f"\nValidation: {'PASSED' if val_result['valid'] else 'FAILED'}")
                print(f"Risk Level: {val_result['risk_level']}")
            
            if result.get("optimization_result"):
                opt_result = result["optimization_result"]
                print(f"\nOptimization: {opt_result['estimated_improvement']}% estimated improvement")
                if opt_result["optimizations_applied"]:
                    print("Applied optimizations:")
                    for opt in opt_result["optimizations_applied"]:
                        print(f"  - {opt}")
            
            if result["warnings"]:
                print("\nWarnings:")
                for warning in result["warnings"]:
                    print(f"  - {warning}")
        
        else:
            print("SQL Generation Failed!")
            if result["errors"]:
                print("Errors:")
                for error in result["errors"]:
                    print(f"  - {error}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
