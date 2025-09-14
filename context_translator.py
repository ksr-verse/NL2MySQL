#!/usr/bin/env python3
"""Context-aware keyword translator for IIQ queries.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

from typing import Dict, List, Any, Optional
from loguru import logger
from iiq_training_data import iiq_training


class ContextTranslator:
    """Translates human language to IIQ-specific keywords based on context."""
    
    def __init__(self):
        """Initialize context translator with training data."""
        self.training_data = iiq_training
        logger.info("Context translator initialized")
    
    def translate_query(self, natural_language_query: str) -> Dict[str, Any]:
        """
        Translate natural language query to IIQ-specific keywords.
        
        Args:
            natural_language_query: Original human query
            
        Returns:
            Dictionary with translated query and context information
        """
        logger.info(f"Translating query: {natural_language_query}")
        
        # Check if query mentions accounts/applications
        has_account_context = self._has_account_context(natural_language_query)
        
        # Apply context-aware translations
        translated_query = self._apply_context_translations(
            natural_language_query, 
            has_account_context
        )
        
        # Extract key entities
        entities = self._extract_entities(translated_query)
        
        result = {
            "original_query": natural_language_query,
            "translated_query": translated_query,
            "has_account_context": has_account_context,
            "entities": entities,
            "translation_applied": translated_query != natural_language_query
        }
        
        logger.info(f"Translation result: {result}")
        return result
    
    def _has_account_context(self, query: str) -> bool:
        """Check if query has account/application context."""
        account_keywords = [
            "account", "accounts", "application", "applications", 
            "app", "apps", "system", "systems", "in", "on"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in account_keywords)
    
    def _apply_context_translations(self, query: str, has_account_context: bool) -> str:
        """Apply context-aware translations to the query."""
        translated = query
        
        if has_account_context:
            # Account-level context translations
            translations = {
                # When talking about groups in account context = entitlements
                "group": "entitlement",
                "groups": "entitlements", 
                "role": "entitlement",
                "roles": "entitlements",
                "capability": "entitlement", 
                "capabilities": "entitlements",
                "permission": "entitlement",
                "permissions": "entitlements",
                "responsibility": "entitlement",
                "responsibilities": "entitlements"
            }
            
            # Apply translations
            for human_term, iiq_term in translations.items():
                # Use word boundaries to avoid partial matches
                import re
                pattern = r'\b' + re.escape(human_term) + r'\b'
                translated = re.sub(pattern, iiq_term, translated, flags=re.IGNORECASE)
                logger.debug(f"Translated '{human_term}' -> '{iiq_term}' in account context")
        
        return translated
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract key entities from the query."""
        entities = {
            "applications": [],
            "entitlements": [],
            "users": [],
            "attributes": []
        }
        
        query_lower = query.lower()
        
        # Extract application names (common ones)
        common_apps = ["workday", "trakk", "finance", "apache ds", "apache", "sap", "oracle"]
        for app in common_apps:
            if app in query_lower:
                entities["applications"].append(app)
        
        # Extract entitlement values (common patterns)
        import re
        # Look for quoted strings or capitalized words that might be entitlement values
        entitlement_patterns = [
            r'"([^"]+)"',  # Quoted strings
            r"'([^']+)'",  # Single quoted strings
            r'\b([A-Z][a-zA-Z0-9]+)\b'  # Capitalized words
        ]
        
        for pattern in entitlement_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                if len(match) > 3:  # Filter out short matches
                    entities["entitlements"].append(match)
        
        return entities
    
    def get_translation_rules(self) -> Dict[str, Any]:
        """Get the translation rules being applied."""
        return {
            "account_context_translations": {
                "group": "entitlement",
                "role": "entitlement", 
                "capability": "entitlement",
                "permission": "entitlement",
                "responsibility": "entitlement"
            },
            "context_detection_keywords": [
                "account", "application", "app", "system", "in", "on"
            ],
            "explanation": "When query mentions accounts/applications, translate group/role/capability to entitlement"
        }


# Global instance
context_translator = ContextTranslator()
