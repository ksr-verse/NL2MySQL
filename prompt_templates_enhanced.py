#!/usr/bin/env python3
"""Enhanced prompt templates for IIQ Natural Language to SQL with synonyms and learning.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from iiq_training_data import iiq_training
from iiq_feedback import IIQFeedbackManager


class EnhancedPromptTemplates:
    """Enhanced prompt templates with IIQ-specific knowledge, synonyms, and learning."""
    
    def __init__(self):
        """Initialize with synonyms and feedback managers."""
        self.training_data = iiq_training
        self.feedback_manager = IIQFeedbackManager()
    
    def get_system_prompt(self) -> str:
        """Get the enhanced system prompt with IIQ knowledge."""
        return """You are an expert in SailPoint IdentityIQ database schema and MySQL SQL generation.

IDENTITYIQ DATA MODEL - HOW DATA IS STORED:

1. spt_identity (IDENTITIES/USERS):
   Purpose: Core identity/user repository - represents people in your organization
   Key columns: id (PK), firstname, lastname, display_name, email, manager (FK to spt_identity.id)
   Data storage: Each person has exactly ONE record | Manager relationship stored as manager column pointing to another identity's id

2. spt_link (ACCOUNT LINKS):
   Purpose: Account links - represents accounts that identities have on various applications
   Key columns: id (PK), identity_id (FK), application (FK), native_identity, attributes, entitlements
   Data storage: One identity can have MULTIPLE links (accounts on different applications) | Each link represents ONE account on ONE application | Entitlements/permissions stored in 'attributes' and 'entitlements' columns as structured data

3. spt_application (APPLICATIONS):
   Purpose: Catalog of applications/systems that IdentityIQ manages
   Key columns: id (PK), name, connector_type
   Data storage: Application names should be used for filtering, not IDs

4. spt_entitlement (ENTITLEMENTS):
   Purpose: Specific entitlements/permissions/groups
   Key columns: id (PK), link_id (FK), name, type
   Data storage: Links to spt_link for specific permissions

KEY RELATIONSHIPS:
- Identity to Accounts: spt_identity.id → spt_link.identity_id (one person, many accounts)
- Accounts to Apps: spt_application.id → spt_link.application (one app, many accounts)
- Manager Hierarchy: spt_identity.manager → spt_identity.id (self-reference)
- Link to Entitlements: spt_link.id → spt_entitlement.link_id (one account, many entitlements)

CRITICAL: ENTITLEMENT/PERMISSION STORAGE:
IdentityIQ stores entitlements/permissions in spt_link.attributes and spt_link.entitlements as structured data
ALWAYS search BOTH l.attributes AND l.entitlements using LIKE operator!

MANDATORY RULES:
- Always use DISTINCT when joining through spt_link to avoid duplicate identities
- Search both l.attributes AND l.entitlements for permissions/groups/capabilities
- Use LEFT JOIN for managers since not all identities have managers
- For 'accounts on all applications' use GROUP BY identity_id HAVING COUNT(DISTINCT app.name) = X
- For DIFFERENT entitlements in DIFFERENT apps: Use separate WHERE i.id IN (...) subqueries for EACH app/entitlement combination
- Manager information requires self-join: LEFT JOIN spt_identity mgr ON i.manager = mgr.id
- Always include manager_name in SELECT when manager info is requested: mgr.display_name as manager_name
- Use MySQL syntax (LIMIT not TOP, NOW() not GETDATE())
- Column names: identity_id (not iid), application (not app_id)

RESPONSE FORMAT: Return ONLY the MySQL SQL query without explanation"""
    
    def build_enhanced_prompt(self, 
                            user_query: str, 
                            schema_context: str,
                            include_synonyms: bool = True,
                            include_examples: bool = True,
                            include_learning: bool = True,
                            translation_result: Optional[Dict[str, Any]] = None,
                            relevant_examples: Optional[List[Dict[str, Any]]] = None) -> str:
        """Build enhanced prompt with synonyms, examples, and learning data."""
        
        prompt_parts = []
        
        # 1. System prompt
        prompt_parts.append(self.get_system_prompt())
        
        # 2. Synonyms mapping
        if include_synonyms:
            synonyms_text = self._get_synonyms_text()
            prompt_parts.append(synonyms_text)
        
        # 3. Translation context (if available)
        if translation_result and translation_result.get("translation_applied"):
            translation_context = f"""
CONTEXT TRANSLATION APPLIED:
Original Query: {translation_result['original_query']}
Translated Query: {translation_result['translated_query']}
Context: {'Account-level entitlements' if translation_result.get('has_account_context') else 'General query'}
Entities Found: {translation_result.get('entities', {})}

IMPORTANT: The query has been translated to use correct IIQ terminology. Use the translated context to understand the intent.
"""
            prompt_parts.append(translation_context)
        
        # 4. Schema context
        prompt_parts.append(f"DATABASE SCHEMA:\n{schema_context}")
        
        # 5. Relevant examples from vector search
        if relevant_examples and len(relevant_examples) > 0:
            examples_text = "🎯 RELEVANT TRAINING EXAMPLES - FOLLOW THESE EXACTLY:\n"
            for i, example in enumerate(relevant_examples, 1):
                examples_text += f"\n{i}. Human: {example['natural_language']}\n"
                examples_text += f"   SQL: {example['sql']}\n"
                if example.get('explanation'):
                    examples_text += f"   Note: {example['explanation']}\n"
                examples_text += f"   Relevance: {example.get('relevance_score', 0):.2f}\n"
            
            # Add specific directive for entitlements
            examples_text += f"""

🚨 CRITICAL ENTITLEMENT RULES - MUST FOLLOW:
- For ANY account-level group/role/capability/permission = USE spt_identity_entitlement table
- NEVER use spt_group, spt_role, spt_capability for account-level entitlements
- ALWAYS join: spt_identity_entitlement.identity_id = spt_identity.id
- ALWAYS join: spt_identity_entitlement.application = spt_application.id
- For groups: WHERE spt_identity_entitlement.name = 'group' AND spt_identity_entitlement.value = 'GroupName'
- For capabilities: WHERE spt_identity_entitlement.name = 'capability' AND spt_identity_entitlement.value = 'CapabilityName'
"""
            prompt_parts.append(examples_text)
        elif include_examples:
            # Fallback to all examples if no relevant examples found
            examples_text = "IIQ TRAINING EXAMPLES:\n"
            for i, example in enumerate(self.training_data.examples[:2], 1):
                examples_text += f"\n{i}. Human: {example['natural_language']}\n"
                examples_text += f"   SQL: {example['sql']}\n"
                if example.get('explanation'):
                    examples_text += f"   Note: {example['explanation']}\n"
            prompt_parts.append(examples_text)
        
        # 5. User query
        prompt_parts.append(f"USER QUERY: {user_query}")
        
        # 6. Template-based approach for complex queries
        if "group" in user_query.lower() and "application" in user_query.lower():
            template = """
🚨 TEMPLATE FOR MULTI-ACCOUNT + GROUP ENTITLEMENT QUERIES:
Use this EXACT pattern for queries with multiple accounts and group entitlements:

SELECT DISTINCT i.firstname, i.lastname, i.display_name, i.email, m.display_name AS manager_name
FROM spt_identity i
LEFT JOIN spt_identity m ON i.manager = m.id
JOIN spt_link l1 ON i.id = l1.identity_id
JOIN spt_application app1 ON l1.application = app1.id AND app1.name = 'Application1'
JOIN spt_link l2 ON i.id = l2.identity_id  
JOIN spt_application app2 ON l2.application = app2.id AND app2.name = 'Application2'
JOIN spt_link l3 ON i.id = l3.identity_id
JOIN spt_application app3 ON l3.application = app3.id AND app3.name = 'Application3'
JOIN spt_link l4 ON i.id = l4.identity_id
JOIN spt_application app4 ON l4.application = app4.id AND app4.name = 'Application4'
JOIN spt_identity_entitlement ie ON i.id = ie.identity_id
JOIN spt_application app_finance ON ie.application = app_finance.id
WHERE app_finance.name = 'Finance' AND ie.name = 'group' AND ie.value = 'PayrollAnalysis';

REPLACE Application1, Application2, Application3, Application4 with the actual application names from the query.
"""
            prompt_parts.append(template)
        
        # 7. Final instruction
        prompt_parts.append("""
🚨 FINAL INSTRUCTIONS - CRITICAL:
1. If the query mentions account-level groups/roles/capabilities/permissions, you MUST use spt_identity_entitlement table
2. NEVER use spt_group, spt_role, spt_capability tables for account-level entitlements
3. Follow the exact pattern from the training examples above
4. Use proper JOIN syntax: spt_identity_entitlement.identity_id = spt_identity.id
5. Use proper JOIN syntax: spt_identity_entitlement.application = spt_application.id
6. For groups: WHERE spt_identity_entitlement.name = 'group' AND spt_identity_entitlement.value = 'GroupName'
7. For capabilities: WHERE spt_identity_entitlement.name = 'capability' AND spt_identity_entitlement.value = 'CapabilityName'

Generate an optimized MySQL query:
""")
        
        return "\n\n".join(prompt_parts)
    
    def _get_synonyms_text(self) -> str:
        """Get formatted synonyms text."""
        synonyms_text = "IIQ SYNONYMS MAPPING:\n"
        for human_term, db_term in self.training_data.synonyms.items():
            synonyms_text += f"- '{human_term}' → {db_term}\n"
        return synonyms_text
    
    def _find_synonyms(self, user_query: str) -> Dict[str, str]:
        """Find synonyms in user query."""
        found_synonyms = {}
        query_lower = user_query.lower()
        
        for human_term, db_term in self.training_data.synonyms.items():
            if human_term.lower() in query_lower:
                found_synonyms[human_term] = db_term
        
        return found_synonyms
    
    def get_synonyms_context(self, user_query: str) -> str:
        """Get synonyms context for the user query."""
        found_synonyms = self._find_synonyms(user_query)
        
        if not found_synonyms:
            return "No synonyms found in query."
        
        synonyms_text = "SYNONYMS FOUND IN QUERY:\n"
        for natural_term, iiq_term in found_synonyms.items():
            synonyms_text += f"  '{natural_term}' → {iiq_term}\n"
        
        return synonyms_text
    
    def get_learning_context(self, user_query: str) -> str:
        """Get relevant learning examples for the user query."""
        relevant_examples = self.feedback_manager.get_relevant_learning(user_query, limit=3)
        
        if not relevant_examples:
            return "No relevant learning examples found."
        
        learning_text = "RELEVANT LEARNING EXAMPLES:\n"
        for i, example in enumerate(relevant_examples, 1):
            learning_text += f"\n{i}. Human: {example['natural_language']}\n"
            learning_text += f"   SQL: {example['sql_query']}\n"
            if example.get('description'):
                learning_text += f"   Description: {example['description']}\n"
        
        return learning_text
    
    def get_audit_prompt(self, user_query: str, generated_sql: str) -> str:
        """Get prompt for audit logging."""
        return f"""AUDIT LOG ENTRY:
Timestamp: {datetime.now().isoformat()}
User Query: {user_query}
Generated SQL: {generated_sql}
Status: Generated
"""
    
    def get_feedback_prompt(self, user_query: str, generated_sql: str, corrected_sql: str) -> str:
        """Get prompt for feedback collection."""
        return f"""FEEDBACK COLLECTION:
Original Query: {user_query}
Generated SQL: {generated_sql}
Corrected SQL: {corrected_sql}
Please provide feedback on what was wrong and how it was corrected.
"""
    
    def get_optimization_prompt(self, sql_query: str, execution_time: float, row_count: int) -> str:
        """Get prompt for query optimization based on execution metrics."""
        return f"""QUERY OPTIMIZATION ANALYSIS:
SQL Query: {sql_query}
Execution Time: {execution_time:.2f} seconds
Row Count: {row_count}
Performance: {'Good' if execution_time < 1.0 else 'Needs Optimization'}

Suggestions for optimization:
- Consider adding indexes on join columns
- Review WHERE clause conditions
- Check for unnecessary subqueries
- Optimize GROUP BY and ORDER BY clauses
"""


class PromptBuilder:
    """Enhanced builder class for constructing complex prompts with IIQ knowledge."""
    
    def __init__(self):
        self.components = []
        self.templates = EnhancedPromptTemplates()
    
    def add_system_context(self) -> 'PromptBuilder':
        """Add system context to the prompt."""
        self.components.append(("system", self.templates.get_system_prompt()))
        return self
    
    def add_synonyms_context(self, user_query: str) -> 'PromptBuilder':
        """Add synonyms context to the prompt."""
        synonyms_text = self.templates.get_synonyms_context(user_query)
        self.components.append(("synonyms", synonyms_text))
        return self
    
    def add_schema_context(self, schema_context: str) -> 'PromptBuilder':
        """Add schema context to the prompt."""
        self.components.append(("schema", f"DATABASE SCHEMA:\n{schema_context}"))
        return self
    
    def add_learning_context(self, user_query: str) -> 'PromptBuilder':
        """Add learning context to the prompt."""
        learning_text = self.templates.get_learning_context(user_query)
        self.components.append(("learning", learning_text))
        return self
    
    def add_user_query(self, user_query: str) -> 'PromptBuilder':
        """Add user query to the prompt."""
        self.components.append(("query", f"USER QUERY: {user_query}"))
        return self
    
    def add_audit_context(self, user_query: str, generated_sql: str) -> 'PromptBuilder':
        """Add audit context to the prompt."""
        audit_text = self.templates.get_audit_prompt(user_query, generated_sql)
        self.components.append(("audit", audit_text))
        return self
    
    def build(self) -> str:
        """Build the final prompt from all components."""
        prompt_parts = []
        
        for component_type, content in self.components:
            if content and content.strip():
                prompt_parts.append(content)
        
        # Add the final instruction
        prompt_parts.append("Generate an optimized MySQL query:")
        
        return "\n\n".join(prompt_parts)
    
    def build_for_sqlcoder(self, user_query: str, schema_context: str) -> str:
        """Build prompt specifically formatted for SQLCoder model."""
        
        # Format for SQLCoder - keep it concise
        sqlcoder_prompt = f"""Schema:
{schema_context[:1000]}...

Question: {user_query}
Write a MySQL query:"""
        
        return sqlcoder_prompt
    
    def build_optimized_ollama_prompt(self, user_query: str, schema_context: str) -> str:
        """Build optimized prompt for Ollama (shorter, faster)."""
        
        # Get synonyms for the query
        synonyms = self._find_synonyms(user_query)
        synonyms_text = ""
        if synonyms:
            synonyms_text = f"\nSynonyms: {', '.join([f'{k}→{v}' for k, v in synonyms.items()])}\n"
        
        # Truncate schema context to avoid timeout
        truncated_schema = schema_context[:800] + "..." if len(schema_context) > 800 else schema_context
        
        # Build concise prompt
        prompt = f"""You are an expert in SailPoint IdentityIQ and MySQL.

Key tables:
- spt_identity: users (id, firstname, lastname, display_name, email, manager)
- spt_link: accounts (id, identity_id, application, attributes, entitlements)  
- spt_application: apps (id, name)
- spt_entitlement: permissions (id, link_id, name)

{synonyms_text}
Schema: {truncated_schema}

Query: {user_query}

Generate MySQL query:"""
        
        return prompt
    
    def build_optimized_ollama_prompt(self, user_query: str, schema_context: str) -> str:
        """Build optimized prompt for Ollama (shorter, faster)."""
        
        # Get synonyms for the query
        synonyms = self._find_synonyms(user_query)
        synonyms_text = ""
        if synonyms:
            synonyms_text = f"\nSynonyms: {', '.join([f'{k}→{v}' for k, v in synonyms.items()])}\n"
        
        # Truncate schema context to avoid timeout
        truncated_schema = schema_context[:800] + "..." if len(schema_context) > 800 else schema_context
        
        # Build concise prompt
        prompt = f"""You are an expert in SailPoint IdentityIQ and MySQL.

Key tables:
- spt_identity: users (id, firstname, lastname, display_name, email, manager)
- spt_link: accounts (id, identity_id, application, attributes, entitlements)  
- spt_application: apps (id, name)
- spt_entitlement: permissions (id, link_id, name)

{synonyms_text}
Schema: {truncated_schema}

Query: {user_query}

Generate MySQL query:"""
        
        return prompt
