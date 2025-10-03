#!/usr/bin/env python3
"""
Populate Vector DB with Patterns, Table Names, Table Definitions, Prompts, and Training Data
This script sets up the complete Vector DB for the Two-Step Search system
"""

import json
import os
from typing import Dict, List, Any, Optional
from loguru import logger
import chromadb
from sentence_transformers import SentenceTransformer
from config import settings


class VectorDBPopulator:
    """Populate Vector DB with all necessary data."""
    
    def __init__(self):
        """Initialize the Vector DB populator."""
        self.vector_db_client = chromadb.PersistentClient(path="./chromadb")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self._initialize_collections()
        
    def _initialize_collections(self):
        """Initialize all Vector DB collections."""
        self.collections = {}
        
        # Collection 1: Pattern → Table Names mapping
        try:
            self.collections['pattern_to_tables'] = self.vector_db_client.get_collection("pattern_to_tables")
            logger.info("Using existing pattern_to_tables collection")
        except:
            logger.info("Creating new pattern_to_tables collection")
            self.collections['pattern_to_tables'] = self.vector_db_client.create_collection("pattern_to_tables")
        
        # Collection 2: Table Names → Table Definitions
        try:
            self.collections['table_definitions'] = self.vector_db_client.get_collection("table_definitions")
            logger.info("Using existing table_definitions collection")
        except:
            logger.info("Creating new table_definitions collection")
            self.collections['table_definitions'] = self.vector_db_client.create_collection("table_definitions")
        
        # Collection 3: Prompt Templates
        try:
            self.collections['prompt_templates'] = self.vector_db_client.get_collection("prompt_templates")
            logger.info("Using existing prompt_templates collection")
        except:
            logger.info("Creating new prompt_templates collection")
            self.collections['prompt_templates'] = self.vector_db_client.create_collection("prompt_templates")
        
        # Collection 4: Training Examples
        try:
            self.collections['training_examples'] = self.vector_db_client.get_collection("training_examples")
            logger.info("Using existing training_examples collection")
        except:
            logger.info("Creating new training_examples collection")
            self.collections['training_examples'] = self.vector_db_client.create_collection("training_examples")
        
        logger.info("All Vector DB collections initialized successfully")
    
    def populate_pattern_to_tables(self):
        """Populate pattern to table names mapping."""
        logger.info("Populating pattern_to_tables collection...")
        
        # Import patterns from iiq_prompt_templates.py
        from iiq_prompt_templates import IIQPromptTemplates
        prompt_templates = IIQPromptTemplates()
        
        # Create pattern to table mapping
        pattern_to_tables_data = []
        
        for pattern in prompt_templates.patterns:
            pattern_to_tables_data.append({
                "pattern": pattern["pattern"],
                "table_names": "spt_identity,spt_application,spt_link",  # All 260 patterns map to these 3 tables
                "pattern_type": "user_application_access"
            })
        
        # Add to Vector DB
        for i, data in enumerate(pattern_to_tables_data):
            self.collections['pattern_to_tables'].add(
                documents=[data["pattern"]],
                metadatas=[{
                    "table_names": data["table_names"],
                    "pattern_type": data["pattern_type"]
                }],
                ids=[f"pattern_{i}"]
            )
        
        logger.info(f"Added {len(pattern_to_tables_data)} pattern-to-tables mappings")
    
    def populate_table_definitions(self):
        """Populate table definitions from database."""
        logger.info("Populating table_definitions collection...")
        
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(settings.db.connection_string)
            
            # Get table names dynamically from iiq_prompt_templates.py patterns
            # All 260 patterns map to these 3 tables, but in future this can be expanded
            table_names = self._get_relevant_table_names()
            
            for table_name in table_names:
                # Get CREATE TABLE statement from database
                query = f"SHOW CREATE TABLE identityiq.{table_name}"
                with engine.connect() as connection:
                    result = connection.execute(text(query))
                    row = result.fetchone()
                    create_statement = row[1] if row else ""
                
                if create_statement:
                    # Add to Vector DB
                    self.collections['table_definitions'].add(
                        documents=[create_statement],
                        metadatas=[{"table_name": table_name}],
                        ids=[table_name]
                    )
                    logger.info(f"Added definition for table: {table_name}")
                else:
                    logger.warning(f"No CREATE TABLE statement found for: {table_name}")
        
        except Exception as e:
            logger.error(f"Error fetching table definitions from database: {e}")
            logger.error("Cannot proceed without table definitions from database!")
            raise e
    
    def _get_relevant_table_names(self) -> List[str]:
        """Get ONLY the essential IdentityIQ table names that users commonly query."""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(settings.db.connection_string)
            
            # Get ONLY the essential IdentityIQ tables that users commonly query
            # This includes core identity, application, link tables and related entities
            query = """
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'identityiq' 
            AND (
                TABLE_NAME IN ('spt_identity', 'spt_application', 'spt_link', 'spt_identity_entitlement', 'spt_identity_request', 'spt_identity_request_item', 'spt_identity_assigned_roles', 'spt_identity_workgroups', 'spt_identity_capabilities', 'spt_identity_bundles', 'spt_identity_controlled_scopes', 'spt_identity_external_attr', 'spt_identity_history_item', 'spt_identity_role_metadata', 'spt_identity_snapshot', 'spt_identity_trigger')
                OR TABLE_NAME IN ('spt_app_dependencies', 'spt_app_secondary_owners', 'spt_application_activity', 'spt_application_remediators', 'spt_application_schema', 'spt_application_scorecard')
                OR TABLE_NAME IN ('spt_link_external_attr', 'spt_managed_attribute', 'spt_managed_attr_inheritance', 'spt_managed_attr_perms', 'spt_managed_attr_target_perms')
                OR TABLE_NAME IN ('spt_bundle', 'spt_bundle_children', 'spt_bundle_permits', 'spt_bundle_requirements', 'spt_capability', 'spt_capability_children', 'spt_capability_rights')
                OR TABLE_NAME IN ('spt_profile', 'spt_profile_constraints', 'spt_profile_permissions', 'spt_scope', 'spt_target', 'spt_target_association', 'spt_target_source', 'spt_target_sources')
                OR TABLE_NAME IN ('spt_right', 'spt_right_config', 'spt_rule', 'spt_rule_dependencies', 'spt_rule_registry', 'spt_rule_registry_callouts', 'spt_rule_signature_arguments', 'spt_rule_signature_returns')
                OR TABLE_NAME IN ('spt_policy', 'spt_policy_violation', 'spt_sodconstraint', 'spt_sodconstraint_left', 'spt_sodconstraint_right')
                OR TABLE_NAME IN ('spt_certification', 'spt_certification_action', 'spt_certification_definition', 'spt_certification_delegation', 'spt_certification_entity', 'spt_certification_group', 'spt_certification_groups', 'spt_certification_item', 'spt_certification_tags', 'spt_certifiers')
                OR TABLE_NAME IN ('spt_work_item', 'spt_work_item_comments', 'spt_work_item_config', 'spt_work_item_owners', 'spt_workflow', 'spt_workflow_case', 'spt_workflow_registry', 'spt_workflow_rule_libraries', 'spt_workflow_target')
                OR TABLE_NAME IN ('spt_audit_event', 'spt_audit_config', 'spt_alert', 'spt_alert_action', 'spt_alert_definition', 'spt_configuration')
                OR TABLE_NAME IN ('spt_account_group', 'spt_account_group_inheritance', 'spt_account_group_perms', 'spt_account_group_target_perms', 'spt_entitlement_group', 'spt_entitlement_snapshot')
            )
            ORDER BY TABLE_NAME
            """
            with engine.connect() as connection:
                result = connection.execute(text(query))
                table_names = [row[0] for row in result]
            
            logger.info(f"Found {len(table_names)} essential IdentityIQ tables for user queries: {table_names}")
            return table_names
            
        except Exception as e:
            logger.error(f"Error fetching table names from database: {e}")
            # Fallback to the 3 core tables if database query fails
            logger.warning("Falling back to core tables")
            return ["spt_identity", "spt_application", "spt_link"]
    
    
    def populate_prompt_templates(self):
        """Populate prompt templates."""
        logger.info("Populating prompt_templates collection...")
        
        # Import prompt from iiq_prompt_templates.py
        from iiq_prompt_templates import IIQPromptTemplates
        prompt_templates = IIQPromptTemplates()
        
        # Add the MySQL expert prompt
        self.collections['prompt_templates'].add(
            documents=[prompt_templates.prompt_template],
            metadatas=[{"prompt_type": "mysql_expert", "description": "MySQL expert prompt for IdentityIQ queries"}],
            ids=["mysql_expert_prompt"]
        )
        
        logger.info("Added MySQL expert prompt template")
    
    def populate_training_examples(self):
        """Populate training examples."""
        logger.info("Populating training_examples collection...")
        
        # Import training example from iiq_training_examples.py
        from iiq_training_examples import IIQTrainingExamples
        training_examples = IIQTrainingExamples()
        
        # Add the training example
        example = training_examples.example
        self.collections['training_examples'].add(
            documents=[example["natural_language"]],
            metadatas=[{
                "sql_query": example["sql_query"],
                "explanation": example["explanation"],
                "query_type": example["query_type"],
                "tables_used": ",".join(example["tables_used"]),
                "key_concepts": ",".join(example["key_concepts"]),
                "difficulty": example["difficulty"]
            }],
            ids=["training_example_1"]
        )
        
        logger.info("Added training example")
    
    def populate_all_collections(self):
        """Populate all Vector DB collections."""
        logger.info("Starting complete Vector DB population...")
        
        try:
            # Clear existing collections
            self._clear_collections()
            
            # Populate all collections
            self.populate_pattern_to_tables()
            self.populate_table_definitions()
            self.populate_prompt_templates()
            self.populate_training_examples()
            
            logger.success("Vector DB population completed successfully!")
            
            # Print statistics
            self.print_statistics()
            
        except Exception as e:
            logger.error(f"Error during Vector DB population: {e}")
    
    def _clear_collections(self):
        """Clear all existing collections."""
        logger.info("Clearing existing collections...")
        
        for collection_name, collection in self.collections.items():
            try:
                # Delete and recreate collection
                self.vector_db_client.delete_collection(collection_name)
                self.collections[collection_name] = self.vector_db_client.create_collection(collection_name)
                logger.info(f"Cleared collection: {collection_name}")
            except Exception as e:
                logger.warning(f"Could not clear collection {collection_name}: {e}")
    
    def print_statistics(self):
        """Print collection statistics."""
        logger.info("Vector DB Statistics:")
        logger.info("=" * 50)
        
        for collection_name, collection in self.collections.items():
            count = collection.count()
            logger.info(f"{collection_name}: {count} documents")


def main():
    """Main function to populate Vector DB."""
    logger.info("Vector DB Population Script")
    logger.info("=" * 50)
    
    populator = VectorDBPopulator()
    populator.populate_all_collections()
    
    logger.success("Vector DB setup completed!")


if __name__ == "__main__":
    main()
