#!/usr/bin/env python3
"""IIQ Synonyms and Examples Management for Natural Language to SQL."""

import json
import os
from typing import Dict, List, Any, Optional
from loguru import logger

class IIQSynonymsManager:
    """Manages IIQ-specific synonyms and example queries."""
    
    def __init__(self, synonyms_file: str = "iiq_synonyms.json", examples_file: str = "iiq_examples.json"):
        """Initialize synonyms and examples manager."""
        self.synonyms_file = synonyms_file
        self.examples_file = examples_file
        self.synonyms = self._load_synonyms()
        self.examples = self._load_examples()
        
        logger.info(f"Loaded {len(self.synonyms)} synonyms and {len(self.examples)} examples")
    
    def _load_synonyms(self) -> Dict[str, str]:
        """Load synonyms from file or create default set."""
        if os.path.exists(self.synonyms_file):
            try:
                with open(self.synonyms_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load synonyms: {e}")
        
        # Default IIQ synonyms
        return {
            # Core entities
            "users": "spt_identity",
            "employees": "spt_identity",
            "people": "spt_identity",
            "identities": "spt_identity",
            
            "accounts": "spt_link",
            "user accounts": "spt_link",
            "identity accounts": "spt_link",
            "links": "spt_link",
            
            "applications": "spt_application",
            "apps": "spt_application",
            "systems": "spt_application",
            
            "groups": "spt_entitlement",
            "entitlements": "spt_entitlement",
            "permissions": "spt_entitlement",
            "roles": "spt_entitlement",
            "capabilities": "spt_entitlement",
            
            # Common attributes
            "first name": "firstname",
            "last name": "lastname",
            "display name": "display_name",
            "email address": "email",
            "manager": "manager",
            "department": "department",
            "title": "title",
            "employee id": "employee_id",
            
            # Status fields
            "active": "active",
            "enabled": "active",
            "disabled": "!active",
            "inactive": "!active",
            
            # Common values
            "workday": "Workday",
            "trakk": "Trakk",
            "finance": "Finance",
            "apache ds": "Apache DS",
            "apache": "Apache DS"
        }
    
    def _load_examples(self) -> List[Dict[str, str]]:
        """Load example queries from file or create default set."""
        if os.path.exists(self.examples_file):
            try:
                with open(self.examples_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load examples: {e}")
        
        # Default IIQ examples
        return [
            {
                "natural_language": "List all users with their email addresses",
                "sql": "SELECT firstname, lastname, email FROM spt_identity WHERE active = 1",
                "description": "Basic user listing with email"
            },
            {
                "natural_language": "Show me users who have accounts in Workday",
                "sql": """SELECT DISTINCT i.firstname, i.lastname, i.email 
                         FROM spt_identity i 
                         JOIN spt_link l ON i.id = l.identity_id 
                         JOIN spt_application a ON l.application = a.id 
                         WHERE a.name = 'Workday' AND i.active = 1""",
                "description": "Users with Workday accounts"
            },
            {
                "natural_language": "Find users with TimeSheetEnterAuthority in Trakk",
                "sql": """SELECT DISTINCT i.firstname, i.lastname, i.email 
                         FROM spt_identity i 
                         JOIN spt_link l ON i.id = l.identity_id 
                         JOIN spt_application a ON l.application = a.id 
                         JOIN spt_entitlement e ON l.id = e.link_id 
                         WHERE a.name = 'Trakk' AND e.name = 'TimeSheetEnterAuthority' AND i.active = 1""",
                "description": "Users with specific Trakk entitlement"
            },
            {
                "natural_language": "Get employees with accounts in multiple applications",
                "sql": """SELECT i.firstname, i.lastname, i.email, 
                                GROUP_CONCAT(a.name) as applications
                         FROM spt_identity i 
                         JOIN spt_link l ON i.id = l.identity_id 
                         JOIN spt_application a ON l.application = a.id 
                         WHERE i.active = 1 
                         GROUP BY i.id, i.firstname, i.lastname, i.email 
                         HAVING COUNT(DISTINCT a.name) > 1""",
                "description": "Users with multiple application accounts"
            },
            {
                "natural_language": "Give me identities (First name, last name, displayname and emails, manager) who does have accounts (link) on workday, Trakk, Finance and Apache DS. User must have capability 'TimeSheetEnterAuthority' in Trakk application and user should also have PayrollAnalysis group in Finance application",
                "sql": """SELECT DISTINCT i.firstname, i.lastname, i.display_name, i.email, mgr.display_name as manager_name 
                         FROM spt_identity i 
                         LEFT JOIN spt_identity mgr ON i.manager = mgr.id 
                         WHERE i.id IN (
                             SELECT l.identity_id FROM spt_link l JOIN spt_application app ON l.application = app.id 
                             WHERE app.name IN ('Workday', 'Trakk', 'Finance', 'Apache DS') 
                             GROUP BY l.identity_id HAVING COUNT(DISTINCT app.name) = 4
                         ) 
                         AND i.id IN (
                             SELECT l.identity_id FROM spt_link l JOIN spt_application app ON l.application = app.id 
                             WHERE app.name = 'Trakk' AND (l.attributes LIKE '%TimeSheetEnterAuthority%' OR l.entitlements LIKE '%TimeSheetEnterAuthority%')
                         ) 
                         AND i.id IN (
                             SELECT l.identity_id FROM spt_link l JOIN spt_application app ON l.application = app.id 
                             WHERE app.name = 'Finance' AND (l.attributes LIKE '%PayrollAnalysis%' OR l.entitlements LIKE '%PayrollAnalysis%')
                         ) 
                         ORDER BY i.lastname""",
                "description": "Complex multi-app query with specific entitlements"
            },
            {
                "natural_language": "Show me users with manager information",
                "sql": """SELECT i.firstname, i.lastname, i.display_name, i.email, 
                                mgr.firstname as manager_firstname, mgr.lastname as manager_lastname
                         FROM spt_identity i 
                         LEFT JOIN spt_identity mgr ON i.manager = mgr.id 
                         WHERE i.active = 1""",
                "description": "Users with manager details"
            },
            {
                "natural_language": "Find users with specific entitlement in any application",
                "sql": """SELECT DISTINCT i.firstname, i.lastname, i.email, a.name as application_name
                         FROM spt_identity i 
                         JOIN spt_link l ON i.id = l.identity_id 
                         JOIN spt_application a ON l.application = a.id 
                         WHERE (l.attributes LIKE '%TimeSheetEnterAuthority%' OR l.entitlements LIKE '%TimeSheetEnterAuthority%')
                         AND i.active = 1""",
                "description": "Users with specific entitlement across applications"
            }
        ]
    
    def get_synonyms(self) -> Dict[str, str]:
        """Get all synonyms."""
        return self.synonyms
    
    def get_examples(self) -> List[Dict[str, str]]:
        """Get all examples."""
        return self.examples
    
    def add_synonym(self, natural_term: str, iiq_term: str) -> None:
        """Add a new synonym."""
        self.synonyms[natural_term.lower()] = iiq_term
        self._save_synonyms()
        logger.info(f"Added synonym: '{natural_term}' → '{iiq_term}'")
    
    def add_example(self, natural_language: str, sql: str, description: str = "") -> None:
        """Add a new example query."""
        example = {
            "natural_language": natural_language,
            "sql": sql,
            "description": description
        }
        self.examples.append(example)
        self._save_examples()
        logger.info(f"Added example: '{natural_language[:50]}...'")
    
    def find_synonyms(self, text: str) -> Dict[str, str]:
        """Find synonyms in the given text."""
        found_synonyms = {}
        text_lower = text.lower()
        
        for natural_term, iiq_term in self.synonyms.items():
            if natural_term in text_lower:
                found_synonyms[natural_term] = iiq_term
        
        return found_synonyms
    
    def get_relevant_examples(self, query: str, limit: int = 3) -> List[Dict[str, str]]:
        """Get examples relevant to the query."""
        query_lower = query.lower()
        relevant_examples = []
        
        for example in self.examples:
            # Simple keyword matching
            if any(keyword in query_lower for keyword in example["natural_language"].lower().split()):
                relevant_examples.append(example)
                if len(relevant_examples) >= limit:
                    break
        
        return relevant_examples
    
    def _save_synonyms(self) -> None:
        """Save synonyms to file."""
        try:
            with open(self.synonyms_file, 'w') as f:
                json.dump(self.synonyms, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save synonyms: {e}")
    
    def _save_examples(self) -> None:
        """Save examples to file."""
        try:
            with open(self.examples_file, 'w') as f:
                json.dump(self.examples, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save examples: {e}")
    
    def get_synonyms_text(self) -> str:
        """Get synonyms as formatted text for LLM prompts."""
        if not self.synonyms:
            return "No synonyms available."
        
        synonyms_text = "IIQ SYNONYMS:\n"
        for natural_term, iiq_term in self.synonyms.items():
            synonyms_text += f"  '{natural_term}' → {iiq_term}\n"
        
        return synonyms_text
    
    def get_examples_text(self) -> str:
        """Get examples as formatted text for LLM prompts."""
        if not self.examples:
            return "No examples available."
        
        examples_text = "EXAMPLE QUERIES:\n"
        for i, example in enumerate(self.examples, 1):
            examples_text += f"\n{i}. Human: {example['natural_language']}\n"
            examples_text += f"   SQL: {example['sql']}\n"
            if example.get('description'):
                examples_text += f"   Description: {example['description']}\n"
        
        return examples_text
