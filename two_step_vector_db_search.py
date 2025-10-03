#!/usr/bin/env python3
"""
Two-Step Vector DB Search
Step 1: Query → Table Names
Step 2: Table Names → Table Definitions
"""

import json
import os
from typing import Dict, List, Any, Optional
from loguru import logger
import chromadb
from chromadb.config import Settings


class TwoStepVectorDBSearch:
    """Two-step Vector DB search: Query → Tables, Tables → Definitions."""
    
    def __init__(self):
        """Initialize the two-step search."""
        self.vector_db_client = chromadb.PersistentClient(
            path="./chromadb",
            settings=Settings(allow_reset=False, anonymized_telemetry=False)
        )
        self._initialize_collections()
        
    def _initialize_collections(self):
        """Initialize Vector DB collections."""
        try:
            # Collection 1: Query to Table Names mapping
            try:
                self.query_to_tables_collection = self.vector_db_client.get_collection("query_to_tables")
                logger.info("Using existing query_to_tables collection")
            except:
                logger.info("Creating new query_to_tables collection")
                self.query_to_tables_collection = self.vector_db_client.create_collection("query_to_tables")
            
            # Collection 2: Table Names to Definitions mapping
            try:
                self.table_to_definitions_collection = self.vector_db_client.get_collection("table_to_definitions")
                logger.info("Using existing table_to_definitions collection")
            except:
                logger.info("Creating new table_to_definitions collection")
                self.table_to_definitions_collection = self.vector_db_client.create_collection("table_to_definitions")
            
            # Collection 3: Training Examples
            try:
                self.training_examples_collection = self.vector_db_client.get_collection("training_examples")
                logger.info("Using existing training_examples collection")
            except:
                logger.info("Creating new training_examples collection")
                self.training_examples_collection = self.vector_db_client.create_collection("training_examples")
                
            logger.info("Vector DB collections initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Vector DB collections: {e}")
    
    def step1_query_to_tables(self, query: str) -> List[str]:
        """Step 1: Search Vector DB with query to get table names."""
        logger.info(f"Step 1: Searching for tables using query: '{query}'")
        
        try:
            # Search in query_to_tables collection
            results = self.query_to_tables_collection.query(
                query_texts=[query],
                n_results=5,
                include=['documents', 'metadatas', 'distances']
            )
            
            
            if results['documents'] and results['documents'][0] and len(results['documents'][0]) > 0:
                # Get the best match
                best_metadata = results['metadatas'][0][0]
                best_distance = results['distances'][0][0]
                similarity_score = 1 - best_distance
                
                # Extract table names from metadata (comma-separated string)
                table_names_str = best_metadata.get('table_names', '')
                table_names = table_names_str.split(',') if table_names_str else []
                
                logger.info(f"Found tables: {table_names} (similarity: {similarity_score:.3f})")
                return table_names
            else:
                logger.warning("No table mappings found in Vector DB")
                return []
                
        except Exception as e:
            logger.error(f"Error in step 1 (query to tables): {e}")
            return []
    
    def step2_tables_to_definitions(self, table_names: List[str]) -> Dict[str, str]:
        """Step 2: Search Vector DB with table names to get definitions."""
        logger.info(f"Step 2: Searching for definitions of tables: {table_names}")
        
        table_definitions = {}
        
        for table_name in table_names:
            try:
                # Get the definition directly by ID (table name is the ID)
                results = self.table_to_definitions_collection.get(
                    ids=[table_name],
                    include=['documents', 'metadatas']
                )
                
                if results['documents'] and results['documents'][0]:
                    # Get the definition
                    definition = results['documents'][0]
                    
                    table_definitions[table_name] = definition
                    logger.info(f"Found definition for {table_name} (exact match)")
                else:
                    logger.warning(f"No definition found for table: {table_name}")
                    
            except Exception as e:
                logger.error(f"Error finding definition for {table_name}: {e}")
        
        logger.info(f"Retrieved definitions for {len(table_definitions)}/{len(table_names)} tables")
        return table_definitions
    
    def search_query_to_definitions(self, query: str) -> Dict[str, Any]:
        """Complete two-step search: Query → Tables → Definitions."""
        logger.info(f"Starting two-step search for query: '{query}'")
        
        # Step 1: Query → Table Names
        table_names = self.step1_query_to_tables(query)
        
        if not table_names:
            logger.error("Step 1 failed: No tables found for query")
            return {
                "query": query,
                "table_names": [],
                "table_definitions": {},
                "success": False,
                "error": "No tables found for query"
            }
        
        # Step 2: Table Names → Definitions
        table_definitions = self.step2_tables_to_definitions(table_names)
        
        if not table_definitions:
            logger.error("Step 2 failed: No definitions found for tables")
            return {
                "query": query,
                "table_names": table_names,
                "table_definitions": {},
                "success": False,
                "error": "No definitions found for tables"
            }
        
        logger.success(f"Two-step search completed successfully!")
        
        return {
            "query": query,
            "table_names": table_names,
            "table_definitions": table_definitions,
            "success": True,
            "tables_found": len(table_names),
            "definitions_found": len(table_definitions)
        }
    
    def generate_prompt_with_definitions(self, query: str) -> str:
        """Generate prompt using two-step Vector DB search."""
        result = self.search_query_to_definitions(query)
        
        if not result["success"]:
            return f"Error: {result['error']}"
        
        # Build table definitions text
        table_definitions_text = ""
        for table_name, definition in result["table_definitions"].items():
            table_definitions_text += f"\n\nCREATE TABLE `{table_name}`:\n{definition}\n"
        
        # Get training examples from Vector DB
        training_examples_text = self._get_training_examples_from_vector_db(query)
        
        # Generate prompt
        prompt = f"""
You are a MySQL expert, you need to write query for me in mysql.

You do have the following tables with their complete definitions:

{table_definitions_text}

{training_examples_text}

Based on these table definitions and training examples, generate the appropriate SQL query for the user's request.

Key points to remember:
- Always use proper JOINs when accessing multiple tables
- Include WHERE clauses for active users (i.inactive = 0 for active users)
- Use DISTINCT when appropriate to avoid duplicates
- Follow proper MySQL syntax and best practices

User Request: {query}

Generate ONLY the SQL query (no explanations or additional text):
"""
        
        return prompt
    
    def _get_training_examples_from_vector_db(self, query: str) -> str:
        """Get relevant training examples from Vector DB."""
        try:
            # Search for training examples similar to the query
            results = self.training_examples_collection.query(
                query_texts=[query],
                n_results=1,
                include=['documents', 'metadatas', 'distances']
            )
            
            if results['documents'] and results['documents'][0]:
                # Get the training example
                training_example = results['documents'][0][0]
                similarity_score = 1 - results['distances'][0][0]  # Convert distance to similarity
                
                # Get the corresponding SQL from iiq_training_examples.py
                from iiq_training_examples import IIQTrainingExamples
                training_data = IIQTrainingExamples()
                example_data = training_data.get_training_example()
                
                training_examples_text = f"""
## RELEVANT TRAINING EXAMPLE:

### Example (Similarity: {similarity_score:.3f}):
Q: {example_data['natural_language']}
A: {example_data['sql_query']}

Explanation: {example_data['explanation']}
"""
                return training_examples_text
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error getting training examples from Vector DB: {e}")
            return ""
    
    def populate_collections(self) -> bool:
        """Populate Vector DB collections with sample data."""
        try:
            logger.info("Populating Vector DB collections with sample data...")
            
            # Step 1: Populate query_to_tables collection
            query_to_tables_data = [
                {
                    "query": "give me all the identities who does have account in Workday application",
                    "table_names": ["spt_identity", "spt_application", "spt_link"]
                },
                {
                    "query": "show me users with application access",
                    "table_names": ["spt_identity", "spt_link", "spt_application"]
                },
                {
                    "query": "find users who have accounts in apps",
                    "table_names": ["spt_identity", "spt_link", "spt_application"]
                },
                {
                    "query": "list employees with system access",
                    "table_names": ["spt_identity", "spt_link", "spt_application"]
                },
                {
                    "query": "get all users accounts for applications",
                    "table_names": ["spt_identity", "spt_link", "spt_application"]
                }
            ]
            
            # Add to collection
            for i, data in enumerate(query_to_tables_data):
                self.query_to_tables_collection.add(
                    documents=[data["query"]],
                    metadatas=[{"table_names": ",".join(data["table_names"])}],
                    ids=[f"query_{i}"]
                )
            
            logger.info(f"Added {len(query_to_tables_data)} query-to-tables mappings")
            
            # Step 2: Populate table_to_definitions collection
            table_definitions_data = [
                {
                    "table_name": "spt_identity",
                    "definition": """CREATE TABLE `spt_identity` (
  `id` varchar(32) NOT NULL,
  `name` varchar(128) NOT NULL,
  `display_name` varchar(128) DEFAULT NULL,
  `firstname` varchar(128) DEFAULT NULL,
  `lastname` varchar(128) DEFAULT NULL,
  `email` varchar(128) DEFAULT NULL,
  `inactive` bit(1) DEFAULT NULL,
  `manager` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UK_afdtg40pi16y2smshwjgj2g6h` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;"""
                },
                {
                    "table_name": "spt_link",
                    "definition": """CREATE TABLE `spt_link` (
  `id` varchar(32) NOT NULL,
  `identity_id` varchar(32) DEFAULT NULL,
  `application` varchar(32) DEFAULT NULL,
  `native_identity` varchar(322) NOT NULL,
  `display_name` varchar(128) DEFAULT NULL,
  `attributes` longtext,
  PRIMARY KEY (`id`),
  CONSTRAINT `FK7do4oyl8j399aynq34dosvk6o` FOREIGN KEY (`identity_id`) REFERENCES `spt_identity` (`id`),
  CONSTRAINT `FKsc0du71d7t0p5jx4sqbwlrtc7` FOREIGN KEY (`application`) REFERENCES `spt_application` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;"""
                },
                {
                    "table_name": "spt_application",
                    "definition": """CREATE TABLE `spt_application` (
  `id` varchar(32) NOT NULL,
  `name` varchar(128) NOT NULL,
  `type` varchar(255) DEFAULT NULL,
  `connector` varchar(255) DEFAULT NULL,
  `owner` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UK_ol1192j17pnj5syamkr9ecb28` (`name`),
  CONSTRAINT `FKo50q3ykyumpddcaaokonvivah` FOREIGN KEY (`owner`) REFERENCES `spt_identity` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;"""
                }
            ]
            
            # Add to collection
            for data in table_definitions_data:
                self.table_to_definitions_collection.add(
                    documents=[data["definition"]],
                    metadatas=[{"table_name": data["table_name"]}],
                    ids=[data["table_name"]]
                )
            
            logger.info(f"Added {len(table_definitions_data)} table definitions")
            
            return True
            
        except Exception as e:
            logger.error(f"Error populating collections: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            return {
                "query_to_tables_collection": self.query_to_tables_collection.count(),
                "table_to_definitions_collection": self.table_to_definitions_collection.count()
            }
        except Exception as e:
            return {"error": str(e)}


def main():
    """Test the two-step Vector DB search."""
    searcher = TwoStepVectorDBSearch()
    
    print("Two-Step Vector DB Search - Test")
    print("=" * 60)
    
    # Check if collections are populated
    stats = searcher.get_statistics()
    print(f"\nCollection Statistics:")
    print(f"  Query to Tables: {stats.get('query_to_tables_collection', 0)}")
    print(f"  Table to Definitions: {stats.get('table_to_definitions_collection', 0)}")
    
    # Populate collections if empty
    if stats.get('query_to_tables_collection', 0) == 0:
        print("\nPopulating collections with sample data...")
        success = searcher.populate_collections()
        print(f"Population result: {'Success' if success else 'Failed'}")
    
    # Test queries
    test_queries = [
        "give me all the identities who does have account in Workday application",
        "show me users with application access",
        "find users who have accounts in apps",
        "list employees with system access"
    ]
    
    print("\nTesting Two-Step Search:")
    print("-" * 60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Step 1: Query → Tables
        table_names = searcher.step1_query_to_tables(query)
        print(f"  Step 1 - Tables found: {table_names}")
        
        if table_names:
            # Step 2: Tables → Definitions
            table_definitions = searcher.step2_tables_to_definitions(table_names)
            print(f"  Step 2 - Definitions found: {list(table_definitions.keys())}")
            
            # Generate prompt
            prompt = searcher.generate_prompt_with_definitions(query)
            print(f"  Prompt length: {len(prompt)} characters")
            
            # Show prompt preview
            prompt_preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
            print(f"  Prompt preview: {prompt_preview}")
        else:
            print("  No tables found - skipping step 2")


if __name__ == "__main__":
    main()
