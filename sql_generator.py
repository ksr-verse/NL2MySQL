"""SQL generator that combines LLM, schema retrieval, validation, and optimization."""

from typing import Dict, Any, Optional, List
from loguru import logger

from retriever import SchemaRetriever
from prompt_templates import PromptTemplates, PromptBuilder
from prompt_templates_enhanced import EnhancedPromptTemplates
from validator import SQLValidator, ValidationLevel
from optimizer import SQLOptimizer, OptimizationLevel
from adapters.llm_local import LocalLLMFactory
from adapters.llm_openai import OpenAIAdapter
from adapters.llm_sqlcoder import SQLCoderAdapter
from iiq_feedback import IIQFeedbackManager
from config import settings


class SQLGenerator:
    """Main SQL generation engine that orchestrates all components."""
    
    def __init__(
        self,
        validation_level: ValidationLevel = ValidationLevel.STANDARD,
        optimization_level: OptimizationLevel = OptimizationLevel.STANDARD
    ):
        """Initialize SQL generator with all components."""
        self.retriever = SchemaRetriever()
        self.validator = SQLValidator(validation_level)
        self.optimizer = SQLOptimizer(optimization_level)
        self.prompt_templates = PromptTemplates()
        self.enhanced_templates = EnhancedPromptTemplates()
        
        # Initialize feedback manager
        self.feedback_manager = IIQFeedbackManager()
        
        # Initialize LLM adapter based on configuration
        self.llm_adapter = self._initialize_llm_adapter()
        
        logger.info("SQL Generator initialized successfully")
    
    def _initialize_llm_adapter(self):
        """Initialize the appropriate LLM adapter."""
        try:
            provider = settings.llm.provider.lower()
            
            if provider == "sqlcoder":
                # Use SQLCoder - best for SQL generation
                adapter = SQLCoderAdapter()
                if adapter.is_available():
                    logger.info("Using SQLCoder adapter (SQL-optimized)")
                    return adapter
                else:
                    logger.error("SQLCoder not available")
                    raise RuntimeError("SQLCoder model not available. Please install transformers and download the model.")
            
            elif provider == "openai":
                if not settings.llm.openai_api_key:
                    logger.error("OpenAI API key not found")
                    raise RuntimeError("OpenAI API key required but not provided")
                
                adapter = OpenAIAdapter()
                if adapter.is_available():
                    return adapter
                else:
                    logger.error("OpenAI not available")
                    raise RuntimeError("OpenAI service not available")
            
            else:  # Local LLM (Ollama/GPT4All)
                adapter = LocalLLMFactory.get_best_available_adapter()
                if adapter is None:
                    logger.error("No local LLM adapters available")
                    raise RuntimeError("No local LLM adapters available. Please install Ollama or GPT4All.")
                return adapter
                
        except Exception as e:
            logger.error(f"Failed to initialize LLM adapter: {e}")
            raise RuntimeError(f"LLM initialization failed: {e}")
    
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
            # Step 1: Retrieve relevant schema
            logger.info(f"Retrieving schema for query: {natural_language_query}")
            retrieved_schema = self.retriever.retrieve_relevant_schema(natural_language_query)
            
            if not retrieved_schema.get("tables"):
                result["warnings"].append("No relevant schema found for the query")
            
            # Format schema context for the prompt
            schema_context = self.retriever.format_schema_context(retrieved_schema)
            result["schema_context"] = schema_context
            
            # Step 2: Generate SQL with retries
            sql_query = None
            for attempt in range(max_retries):
                result["generation_metadata"]["attempts"] = attempt + 1
                
                try:
                    sql_query = self._generate_sql_with_llm(
                        natural_language_query, schema_context, attempt
                    )
                    
                    if sql_query and sql_query.strip():
                        break
                    else:
                        logger.warning(f"Empty SQL generated on attempt {attempt + 1}")
                        
                except Exception as e:
                    logger.warning(f"SQL generation attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        result["errors"].append(f"All generation attempts failed. Last error: {e}")
                        return result
            
            if not sql_query or not sql_query.strip():
                result["errors"].append("Failed to generate SQL after all attempts")
                return result
            
            result["sql_query"] = sql_query
            
            # Record query generation for learning
            self.feedback_manager.record_query_execution(
                natural_query=natural_language_query,
                sql_query=sql_query,
                execution_time=0.0,  # Will be updated after execution
                row_count=0,  # Will be updated after execution
                success=True,
                error_message=""
            )
            
            # Step 3: Validate the generated SQL
            if validate_syntax:
                logger.info("Validating generated SQL")
                validation_result = self.validator.validate_query(sql_query)
                result["validation_result"] = validation_result
                
                if not validation_result["valid"]:
                    # Try to fix common issues and regenerate
                    if attempt < max_retries - 1:
                        logger.info("Attempting to fix validation errors")
                        fixed_sql = self._attempt_sql_fix(sql_query, validation_result["errors"])
                        if fixed_sql and fixed_sql != sql_query:
                            sql_query = fixed_sql
                            result["sql_query"] = sql_query
                            # Re-validate
                            validation_result = self.validator.validate_query(sql_query)
                            result["validation_result"] = validation_result
                
                result["warnings"].extend(validation_result.get("warnings", []))
                result["warnings"].extend(validation_result.get("security_issues", []))
            
            # Step 4: Optimize the SQL
            if optimize_query:
                logger.info("Optimizing generated SQL")
                optimization_result = self.optimizer.optimize_query(sql_query, retrieved_schema)
                result["optimization_result"] = optimization_result
                
                if optimization_result["optimized_query"] != sql_query:
                    result["sql_query"] = optimization_result["optimized_query"]
                    result["warnings"].extend(optimization_result.get("warnings", []))
            
            # Step 5: Generate explanation if requested
            if include_explanation:
                logger.info("Generating SQL explanation")
                try:
                    explanation = self._generate_explanation(result["sql_query"], schema_context)
                    result["explanation"] = explanation
                except Exception as e:
                    logger.warning(f"Failed to generate explanation: {e}")
                    result["warnings"].append("Could not generate explanation")
            
            result["success"] = True
            logger.info("SQL generation completed successfully")
            
        except Exception as e:
            logger.error(f"Error in SQL generation: {e}")
            result["errors"].append(f"Generation error: {str(e)}")
        
        return result
    
    def _generate_sql_with_llm(
        self, 
        natural_language_query: str, 
        schema_context: str, 
        attempt: int = 0
    ) -> str:
        """Generate SQL using the LLM adapter with enhanced prompts."""
        
        # Use optimized prompts for different providers
        if settings.llm.provider.lower() == "sqlcoder":
            # Use SQLCoder-specific prompt format
            prompt = self.enhanced_templates.build_for_sqlcoder(
                user_query=natural_language_query,
                schema_context=schema_context
            )
        else:
            # Use enhanced prompt with all features
            prompt = self.enhanced_templates.build_enhanced_prompt(
                user_query=natural_language_query,
                schema_context=schema_context,
                include_synonyms=True,
                include_examples=False,  # Disable examples for speed
                include_learning=False  # Disable learning for speed
            )
        
        # Add retry context for subsequent attempts
        if attempt > 0:
            retry_context = f"\n\nRETRY ATTEMPT {attempt}: Previous attempt failed. Please ensure the SQL is syntactically correct and follows MySQL standards."
            prompt += retry_context
        
        # Generate SQL using the LLM
        return self.llm_adapter.generate_sql(prompt)
    
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
            explanation_prompt = self.prompt_templates.get_query_explanation_prompt().format(
                sql_query=sql_query,
                schema_context=schema_context
            )
            
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
    
    def analyze_query_complexity(self, sql_query: str) -> Dict[str, Any]:
        """Analyze the complexity of a SQL query."""
        try:
            # Get complexity from validator
            complexity_result = self.validator.get_query_complexity_score(sql_query)
            
            # Get performance analysis from optimizer
            performance_result = self.optimizer.analyze_query_performance(sql_query)
            
            return {
                "complexity": complexity_result,
                "performance": performance_result,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error analyzing query complexity: {e}")
            return {
                "complexity": {},
                "performance": {},
                "success": False,
                "error": str(e)
            }
    
    def get_schema_suggestions(self, natural_language_query: str) -> Dict[str, Any]:
        """Get schema suggestions for a natural language query."""
        try:
            retrieved_schema = self.retriever.retrieve_relevant_schema(natural_language_query)
            
            suggestions = {
                "relevant_tables": list(retrieved_schema.get("tables", {}).keys()),
                "relationships": retrieved_schema.get("relationships", []),
                "schema_context": self.retriever.format_schema_context(retrieved_schema),
                "success": True
            }
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting schema suggestions: {e}")
            return {
                "relevant_tables": [],
                "relationships": [],
                "schema_context": "",
                "success": False,
                "error": str(e)
            }
    
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
        
        if args.schema_suggestions:
            suggestions = generator.get_schema_suggestions(args.query)
            print("Schema Suggestions:")
            print(f"  Relevant Tables: {suggestions['relevant_tables']}")
            if suggestions['relationships']:
                print("  Relationships:")
                for rel in suggestions['relationships']:
                    print(f"    - {rel}")
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
