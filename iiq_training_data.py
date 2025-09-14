#!/usr/bin/env python3
"""Consolidated IIQ Training Data - All synonyms, examples, and mappings in one place.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

import json
import os
from typing import Dict, List, Any, Optional
from loguru import logger

class IIQTrainingData:
    """Consolidated IIQ training data manager - everything in one place."""
    
    def __init__(self):
        """Initialize with all training data."""
        self.synonyms = self._get_synonyms()
        self.examples = self._get_examples()
        self.entity_mappings = self._get_entity_mappings()
        self.query_patterns = self._get_query_patterns()
        
        logger.info(f"Loaded {len(self.synonyms)} synonyms, {len(self.examples)} examples, {len(self.entity_mappings)} entity mappings")
    
    def _get_synonyms(self) -> Dict[str, str]:
        """Get all IIQ synonyms."""
        return {
            # Core entities
            "users": "spt_identity",
            "employees": "spt_identity", 
            "people": "spt_identity",
            "identities": "spt_identity",
            "personas": "spt_identity",
            "reviewers": "spt_identity",
            "system accounts": "spt_identity",
            
            "accounts": "spt_link",
            "user accounts": "spt_link",
            "identity accounts": "spt_link",
            "links": "spt_link",
            "logins": "spt_link",
            "profiles": "spt_link",
            "access": "spt_link",
            
            "applications": "spt_application",
            "apps": "spt_application",
            "systems": "spt_application",
            "target systems": "spt_application",
            "connected apps": "spt_application",
           
            "entitlements": "spt_identity_entitlement",
            "privileges": "spt_identity_entitlement",
            "access rights": "spt_identity_entitlement",
            "access": "spt_identity_entitlement",
            "permission": "spt_identity_entitlement",
            
            # CRITICAL: Account-level entitlements (NOT IIQ groups/roles)
            "group": "spt_identity_entitlement",  # When talking about account groups
            "role": "spt_identity_entitlement",   # When talking about account roles
            "capability": "spt_identity_entitlement",  # When talking about account capabilities
            "responsibility": "spt_identity_entitlement",  # When talking about account responsibilities
           
            # Common fields
            "first name": "firstname",
            "last name": "lastname"
        }
    
    def _get_entity_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed entity mappings with rules."""
        return {
            "GENERAL_RULES": {
                "description": "Universal mapping rules for all tables",
                "rules": [
                    "Any column named 'identity_id' = maps to spt_identity.id (can always join to get user data)",
                    "Any column named 'application' = maps to spt_application.id (can always join to get app details)",
                    "CRITICAL: When user mentions 'group' for an account = spt_identity_entitlement (NOT spt_group table)",
                    "CRITICAL: When user mentions 'role' for an account = spt_identity_entitlement (NOT spt_role table)",
                    "CRITICAL: When user mentions 'capability' for an account = spt_identity_entitlement",
                    "CRITICAL: When user mentions 'permission' for an account = spt_identity_entitlement",
                    "CRITICAL: Account-level entitlements are stored in spt_identity_entitlement table"
                ]
            },
            "IDENTITIES": {
                "table": "spt_identity",
                "primary_key": "id",
                "important_columns": ["id", "firstname", "lastname", "display_name", "email", "manager", "inactive"],
                "rules": [
                    "user/identity/persona = spt_identity",
                    "manager = self-join on manager column",
                    "Active users = inactive = 0"
                ],
                "example_query": """
SELECT i.firstname, i.lastname, i.display_name, i.email
FROM spt_identity i
WHERE i.inactive = 0;
"""
            },
            
            "APPLICATIONS": {
                "table": "spt_application", 
                "primary_key": "id",
                "important_columns": ["id", "name"],
                "rules": [
                    "App references always via name",
                    "Keep application list dynamically updated"
                ],
                "example_query": """
SELECT app.id, app.name
FROM spt_application app;
"""
            },
            
            "ACCOUNTS_LINKS": {
                "table": "spt_link",
                "primary_key": "id", 
                "important_columns": ["id", "identity_id", "application", "attributes", "entitlements"],
                "rules": [
                    "Existence in spt_link = identity has an account in that application",
                    "Entitlements often stored in entitlements or attributes"
                ],
                "example_query": """
SELECT i.display_name, app.name AS application
FROM spt_identity i
JOIN spt_link l ON i.id = l.identity_id
JOIN spt_application app ON l.application = app.id;
"""
            },
            
            "ENTITLEMENTS": {
                "table": "spt_identity_entitlement",
                "primary_key": "id",
                "important_columns": ["id", "identity_id", "application", "name", "value"],
                "rules": [
                    "CRITICAL: All account-level entitlements are in spt_identity_entitlement table",
                    "identity_id maps to spt_identity.id",
                    "application maps to spt_application.id",
                    "name = entitlement type (capability, group, role, permission, etc.)",
                    "value = specific entitlement value",
                    "CRITICAL: When user says 'group in Finance' = spt_identity_entitlement where name='group' and application=Finance",
                    "CRITICAL: When user says 'capability in Trakk' = spt_identity_entitlement where name='capability' and application=Trakk",
                    "CRITICAL: When user says 'role in Workday' = spt_identity_entitlement where name='role' and application=Workday",
                    "DO NOT use spt_group, spt_role, or spt_capability tables for account-level entitlements"
                ],
                "example_query": """
SELECT spt_identity.firstname, spt_identity_entitlement.value, spt_application.name, spt_identity_entitlement.name 
FROM spt_identity_entitlement 
JOIN spt_identity ON spt_identity_entitlement.identity_id = spt_identity.id
JOIN spt_application ON spt_application.id = spt_identity_entitlement.application;
"""
            }
        }
    
    def _get_examples(self) -> List[Dict[str, str]]:
        """Get example queries with natural language inputs."""
        return [
            {
                "natural_language": "Show me all active employees",
                "sql": "SELECT i.firstname, i.lastname, i.display_name, i.email FROM spt_identity i WHERE i.inactive = 0;",
                "explanation": "Query for active employees using inactive = 0 filter"
            },
            {
                "natural_language": "List all applications in the system",
                "sql": "SELECT app.id, app.name FROM spt_application app;",
                "explanation": "Simple query to get all applications"
            },
            {
                "natural_language": "Show users who have accounts in Workday",
                "sql": "SELECT i.display_name, app.name AS application FROM spt_identity i JOIN spt_link l ON i.id = l.identity_id JOIN spt_application app ON l.application = app.id WHERE app.name = 'Workday';",
                "explanation": "Join identities with their application accounts"
            },
            {
                "natural_language": "Give me employees who have account in Trakk application, must have capability 'TimeSheetEnterAuthority' in Trakk",
                "sql": "SELECT spt_identity.firstname, spt_identity_entitlement.value, spt_application.name, spt_identity_entitlement.name FROM spt_identity_entitlement JOIN spt_identity ON spt_identity_entitlement.identity_id = spt_identity.id JOIN spt_application ON spt_application.id = spt_identity_entitlement.application WHERE spt_application.name = 'Trakk' AND spt_identity_entitlement.name = 'capability' AND spt_identity_entitlement.value = 'TimeSheetEnterAuthority';",
                "explanation": "Complex query combining multiple entities with specific requirements"
            },
            {
                "natural_language": "give me identities who have accounts on workday, Trakk, Finance and Apache DS. User must have PayrollAnalysis group in Finance application",
                "sql": "SELECT DISTINCT i.firstname, i.lastname, i.display_name, i.email, m.display_name AS manager_name FROM spt_identity i LEFT JOIN spt_identity m ON i.manager = m.id JOIN spt_link l1 ON i.id = l1.identity_id JOIN spt_application app1 ON l1.application = app1.id JOIN spt_link l2 ON i.id = l2.identity_id JOIN spt_application app2 ON l2.application = app2.id JOIN spt_link l3 ON i.id = l3.identity_id JOIN spt_application app3 ON l3.application = app3.id JOIN spt_link l4 ON i.id = l4.identity_id JOIN spt_application app4 ON l4.application = app4.id JOIN spt_identity_entitlement ie ON i.id = ie.identity_id JOIN spt_application app_finance ON ie.application = app_finance.id WHERE app1.name = 'Workday' AND app2.name = 'Trakk' AND app3.name = 'Finance' AND app4.name = 'Apache DS' AND app_finance.name = 'Finance' AND ie.name = 'group' AND ie.value = 'PayrollAnalysis';",
                "explanation": "Complex multi-account query with specific group entitlement requirement"
            },
            {
                "natural_language": "Give me identities who have accounts on Workday, Trakk, Finance and Apache DS. User must have PayrollAnalysis group in Finance application",
                "sql": "SELECT DISTINCT spt_identity.firstname, spt_identity.lastname, spt_identity.display_name, spt_identity.email FROM spt_identity JOIN spt_link l1 ON spt_identity.id = l1.identity_id JOIN spt_application app1 ON l1.application = app1.id AND app1.name = 'Workday' JOIN spt_link l2 ON spt_identity.id = l2.identity_id JOIN spt_application app2 ON l2.application = app2.id AND app2.name = 'Trakk' JOIN spt_link l3 ON spt_identity.id = l3.identity_id JOIN spt_application app3 ON l3.application = app3.id AND app3.name = 'Finance' JOIN spt_link l4 ON spt_identity.id = l4.identity_id JOIN spt_application app4 ON l4.application = app4.id AND app4.name = 'Apache DS' JOIN spt_identity_entitlement ie ON spt_identity.id = ie.identity_id JOIN spt_application app5 ON ie.application = app5.id WHERE app5.name = 'Finance' AND ie.name = 'group' AND ie.value = 'PayrollAnalysis';",
                "explanation": "Complex query for identities with multiple accounts and specific group entitlement in Finance"
            }
        ]
    
    def _get_query_patterns(self) -> Dict[str, str]:
        """Get common query patterns and templates."""
        return {
            "active_users": "SELECT * FROM spt_identity WHERE inactive = 0",
            "user_with_apps": "SELECT i.display_name, app.name FROM spt_identity i JOIN spt_link l ON i.id = l.identity_id JOIN spt_application app ON l.application = app.id",
            "user_entitlements": "SELECT spt_identity.firstname, spt_identity_entitlement.value, spt_application.name, spt_identity_entitlement.name FROM spt_identity_entitlement JOIN spt_identity ON spt_identity_entitlement.identity_id = spt_identity.id JOIN spt_application ON spt_application.id = spt_identity_entitlement.application",
            "capability_holders": "SELECT spt_identity.display_name, spt_identity_entitlement.value FROM spt_identity_entitlement JOIN spt_identity ON spt_identity_entitlement.identity_id = spt_identity.id WHERE spt_identity_entitlement.name = 'capability'"
        }
    
    def get_all_training_data(self) -> Dict[str, Any]:
        """Get all training data in one structure."""
        return {
            "synonyms": self.synonyms,
            "examples": self.examples,
            "entity_mappings": self.entity_mappings,
            "query_patterns": self.query_patterns
        }
    
    def add_example(self, natural_language: str, sql: str, explanation: str = ""):
        """Add a new example to training data."""
        self.examples.append({
            "natural_language": natural_language,
            "sql": sql,
            "explanation": explanation
        })
        logger.info(f"Added new example: {natural_language}")
    
    def add_synonym(self, human_term: str, database_term: str):
        """Add a new synonym mapping."""
        self.synonyms[human_term] = database_term
        logger.info(f"Added synonym: {human_term} -> {database_term}")

# Global instance for easy access
iiq_training = IIQTrainingData()