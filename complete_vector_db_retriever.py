#!/usr/bin/env python3
"""
Complete Vector DB Retriever
Combines pattern matching, table retrieval, prompt templates, and training examples
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
import chromadb
from sentence_transformers import SentenceTransformer


class CompleteVectorDBRetriever:
    """Complete Vector DB retriever for all components."""
    
    def __init__(self):
        """Initialize the complete retriever."""
        self.vector_db_client = chromadb.PersistentClient(path="./chromadb")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self._initialize_collections()
        
    def _initialize_collections(self):
        """Initialize all Vector DB collections."""
        try:
            self.collections = {
                'pattern_to_tables': self.vector_db_client.get_collection("pattern_to_tables"),
                'table_definitions': self.vector_db_client.get_collection("table_definitions"),
                'prompt_templates': self.vector_db_client.get_collection("prompt_templates"),
                'training_examples': self.vector_db_client.get_collection("training_examples")
            }
            logger.info("All Vector DB collections initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Vector DB collections: {e}")
            raise
    
    def step1_get_prompt_template(self, user_query: str) -> Tuple[str, float]:
        """Step 1: Get prompt template from Vector DB."""
        logger.info(f"Step 1: Getting prompt template for query: '{user_query}'")
        
        try:
            # Get the MySQL expert prompt (we only have one prompt type)
            results = self.collections['prompt_templates'].query(
                query_texts=[user_query],
                n_results=1,
                include=['documents', 'distances']
            )
            
            if results['documents'] and results['documents'][0] and len(results['documents'][0]) > 0:
                prompt_template = results['documents'][0][0]
                similarity_score = 1 - results['distances'][0][0]
                
                logger.info(f"Found prompt template (similarity: {similarity_score:.3f})")
                return prompt_template, similarity_score
            else:
                logger.warning("No prompt template found in Vector DB")
                return "", 0.0
                
        except Exception as e:
            logger.error(f"Error in step 1 (getting prompt template): {e}")
            return "", 0.0
    
    def step2_get_training_example(self, user_query: str) -> Tuple[Dict[str, Any], float]:
        """Step 2: Get training example from Vector DB."""
        logger.info(f"Step 2: Getting training example for query: '{user_query}'")
        
        try:
            # Get the training example
            results = self.collections['training_examples'].query(
                query_texts=[user_query],
                n_results=1,
                include=['documents', 'metadatas', 'distances']
            )
            
            if results['documents'] and results['documents'][0] and len(results['documents'][0]) > 0:
                # Get training example data
                natural_language = results['documents'][0][0]
                metadata = results['metadatas'][0][0]
                similarity_score = 1 - results['distances'][0][0]
                
                training_example = {
                    "natural_language": natural_language,
                    "sql_query": metadata.get("sql_query", ""),
                    "explanation": metadata.get("explanation", ""),
                    "query_type": metadata.get("query_type", ""),
                    "tables_used": metadata.get("tables_used", "").split(",") if metadata.get("tables_used") else [],
                    "key_concepts": metadata.get("key_concepts", "").split(",") if metadata.get("key_concepts") else [],
                    "difficulty": metadata.get("difficulty", "")
                }
                
                logger.info(f"Found training example (similarity: {similarity_score:.3f})")
                return training_example, similarity_score
            else:
                logger.warning("No training example found in Vector DB")
                return {}, 0.0
                
        except Exception as e:
            logger.error(f"Error in step 2 (getting training example): {e}")
            return {}, 0.0
    
    def step3_get_table_names(self, user_query: str) -> Tuple[List[str], float]:
        """Step 3: Get table names from pattern matching."""
        logger.info(f"Step 3: Getting table names for query: '{user_query}'")
        
        try:
            # Search for matching pattern
            results = self.collections['pattern_to_tables'].query(
                query_texts=[user_query],
                n_results=1,
                include=['documents', 'metadatas', 'distances']
            )
            
            if results['documents'] and results['documents'][0] and len(results['documents'][0]) > 0:
                # Get table names from metadata
                metadata = results['metadatas'][0][0]
                table_names_str = metadata.get('table_names', '')
                table_names = table_names_str.split(',') if table_names_str else []
                similarity_score = 1 - results['distances'][0][0]
                
                logger.info(f"Found table names: {table_names} (similarity: {similarity_score:.3f})")
                return table_names, similarity_score
            else:
                logger.warning("No table names found in Vector DB")
                return [], 0.0
                
        except Exception as e:
            logger.error(f"Error in step 3 (getting table names): {e}")
            return [], 0.0
    
    def step4_get_table_definitions(self, table_names: List[str]) -> Dict[str, str]:
        """Step 4: Get table definitions for the given table names."""
        logger.info(f"Step 4: Getting table definitions for tables: {table_names}")
        
        table_definitions = {}
        
        for table_name in table_names:
            try:
                # Get table definition by ID (exact match)
                results = self.collections['table_definitions'].get(
                    ids=[table_name],
                    include=['documents', 'metadatas']
                )
                
                if results['documents'] and results['documents'][0] and len(results['documents'][0]) > 0:
                    definition = results['documents'][0][0]
                    table_definitions[table_name] = definition
                    logger.info(f"Found definition for {table_name} (exact match)")
                else:
                    logger.warning(f"No definition found for table: {table_name}")
                    
            except Exception as e:
                logger.error(f"Error finding definition for {table_name}: {e}")
        
        logger.info(f"Retrieved definitions for {len(table_definitions)}/{len(table_names)} tables")
        return table_definitions
    
    def retrieve_complete_context(self, user_query: str) -> Dict[str, Any]:
        """Retrieve complete context for the user query."""
        logger.info(f"Starting complete context retrieval for query: '{user_query}'")
        logger.info("=" * 80)
        
        # Step 1: Get prompt template
        prompt_template, prompt_similarity = self.step1_get_prompt_template(user_query)
        
        # Step 2: Get training example
        training_example, training_similarity = self.step2_get_training_example(user_query)
        
        # Step 3: Get table names
        table_names, table_similarity = self.step3_get_table_names(user_query)
        
        # Step 4: Get table definitions
        table_definitions = self.step4_get_table_definitions(table_names) if table_names else {}
        
        # Combine everything
        result = {
            "user_query": user_query,
            "prompt_template": prompt_template,
            "prompt_similarity": prompt_similarity,
            "training_example": training_example,
            "training_similarity": training_similarity,
            "table_names": table_names,
            "table_similarity": table_similarity,
            "table_definitions": table_definitions,
            "success": bool(prompt_template and training_example and table_names and table_definitions),
            "steps_completed": {
                "prompt_template": bool(prompt_template),
                "training_example": bool(training_example),
                "table_names": bool(table_names),
                "table_definitions": bool(table_definitions)
            }
        }
        
        if result["success"]:
            logger.success("Complete context retrieval successful!")
        else:
            logger.error("Complete context retrieval failed!")
            failed_steps = [step for step, completed in result["steps_completed"].items() if not completed]
            logger.error(f"Failed steps: {failed_steps}")
        
        return result
    
    def generate_final_prompt(self, context: Dict[str, Any]) -> str:
        """Generate final prompt combining all retrieved context."""
        logger.info("Generating final prompt...")
        
        if not context["success"]:
            return "Error: Could not retrieve complete context for the query."
        
        # Build table definitions text
        table_definitions_text = ""
        for table_name, definition in context["table_definitions"].items():
            table_definitions_text += f"\n\nCREATE TABLE `{table_name}`:\n{definition}\n"
        
        # Build training example text
        training_example_text = ""
        if context["training_example"]:
            example = context["training_example"]
            training_example_text = f"""
Training Example:
If a user says - {example["natural_language"]} then this would be query:

{example["sql_query"]}

Explanation: {example["explanation"]}
Key Concepts: {', '.join(example["key_concepts"])}
Difficulty: {example["difficulty"]}
"""
        
        # Generate final prompt
        final_prompt = f"""
{context["prompt_template"]}

{training_example_text}

Here are the tables definitions, this will help you to understand the relations:

{table_definitions_text}

Based on these table definitions and the training example, generate the appropriate SQL query for the user's request.

Key points to remember:
- Always use proper JOINs when accessing multiple tables
- Include WHERE clauses for active users (i.inactive = 0 for active users)
- Use DISTINCT when appropriate to avoid duplicates
- Follow proper MySQL syntax and best practices

User Request: {context["user_query"]}

Generate the SQL query:
"""
        
        logger.info(f"Final prompt generated (length: {len(final_prompt)} characters)")
        return final_prompt
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            return {
                "pattern_to_tables": self.collections['pattern_to_tables'].count(),
                "table_definitions": self.collections['table_definitions'].count(),
                "prompt_templates": self.collections['prompt_templates'].count(),
                "training_examples": self.collections['training_examples'].count()
            }
        except Exception as e:
            return {"error": str(e)}


def main():
    """Test the complete Vector DB retriever."""
    retriever = CompleteVectorDBRetriever()
    
    print("Complete Vector DB Retriever - Test")
    print("=" * 60)
    
    # Check statistics
    stats = retriever.get_statistics()
    print(f"\nCollection Statistics:")
    for collection, count in stats.items():
        print(f"  {collection}: {count}")
    
    # Test complete retrieval
    test_queries = [
        "give me all the identities who does have account in Workday application",
        "show me users with application access",
        "find users who have accounts in apps"
    ]
    
    print(f"\nTesting Complete Retrieval:")
    print("-" * 60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Get complete context
        context = retriever.retrieve_complete_context(query)
        
        if context["success"]:
            print(f"  [SUCCESS] All steps completed successfully")
            print(f"  [STEP 1] Prompt template: {'Found' if context['prompt_template'] else 'Missing'}")
            print(f"  [STEP 2] Training example: {'Found' if context['training_example'] else 'Missing'}")
            print(f"  [STEP 3] Table names: {context['table_names']}")
            print(f"  [STEP 4] Table definitions: {len(context['table_definitions'])} found")
            
            # Generate final prompt
            final_prompt = retriever.generate_final_prompt(context)
            print(f"  [FINAL] Prompt length: {len(final_prompt)} characters")
            
            # Show prompt preview
            prompt_preview = final_prompt[:200] + "..." if len(final_prompt) > 200 else final_prompt
            print(f"  [FINAL] Prompt preview: {prompt_preview}")
        else:
            print(f"  [ERROR] Retrieval failed")
            failed_steps = [step for step, completed in context["steps_completed"].items() if not completed]
            print(f"  [ERROR] Failed steps: {failed_steps}")


if __name__ == "__main__":
    main()
