#!/usr/bin/env python3
"""
IIQ Training Examples - SQL Generation Patterns
Contains training examples for different types of SQL queries
"""

from typing import Dict, List, Any, Optional
from loguru import logger
from sentence_transformers import SentenceTransformer


class IIQTrainingExamples:
    """Training examples for SQL generation patterns."""
    
    def __init__(self):
        """Initialize training examples."""
        self.example = self._get_single_training_example()
        self.patterns = self._get_all_patterns()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.pattern_embeddings = self._compute_pattern_embeddings()
        
        logger.info(f"Loaded 1 training example and {len(self.patterns)} patterns")
    
    def _get_single_training_example(self) -> Dict[str, Any]:
        """Get the single training example."""
        return {
            "natural_language": "give me all the identities who does have account in Workday application",
            "sql_query": "SELECT DISTINCT i.firstname, i.lastname, i.email FROM spt_identity i JOIN spt_link l ON i.id = l.identity_id JOIN spt_application a ON l.application = a.id WHERE a.name = 'Workday' AND i.inactive = 0;",
            "explanation": "Finds all active users who have accounts in the Workday application by joining identity, link, and application tables",
            "query_type": "user_application_access",
            "tables_used": ["spt_identity", "spt_link", "spt_application"],
            "key_concepts": ["JOIN", "WHERE", "DISTINCT", "application filtering", "active users"],
            "difficulty": "basic"
        }
    
    def _get_all_patterns(self) -> List[Dict[str, Any]]:
        """Get all patterns that map to this training example - same 260 patterns as prompt templates."""
        actions = ["provide", "give", "generate", "show", "fetch", "get", "list", "display", "retrieve", "return", "find", "search", "query", "select"]
        users = ["users", "employees", "people", "identities", "personas", "reviewers", "system accounts", "Owners", "Administrators", "Admins", "Adminsitrators", "Owner", "person", "individual", "staff", "worker", "personnel", "members"]
        accounts = ["accounts", "user accounts", "identity accounts", "links", "access", "connections", "provisioned accounts", "account links", "user access", "system access", "permissions", "entitlements"]
        apps = ["applications", "apps", "systems", "target systems", "connected apps", "platforms", "services", "tools", "software", "environments", "programs", "solutions"]
        
        # This list is dynamically updated by update_training_examples_from_db.py
        app_names = ["Apache DS", "BAPS", "CMDB", "Finance", "OpenDJ", "Trakk", "Workday", "xSign"]
        
        patterns = []
        pattern_id = 1
        
        # Pattern 1: Action + users + accounts + for + apps
        for action in actions[:10]:
            for user in users[:10]:
                for account in accounts[:5]:
                    for app in apps[:5]:
                        if pattern_id > 50:  # Limit first batch
                            break
                        pattern_text = f"{action} me all {user} {account} for {app}"
                        patterns.append({
                            "id": f"training_pattern_{pattern_id}",
                            "pattern": pattern_text,
                            "example": self.example,
                            "pattern_type": "user_application_access"
                        })
                        pattern_id += 1
                    if pattern_id > 50:
                        break
                if pattern_id > 50:
                    break
            if pattern_id > 50:
                break
        
        # Pattern 2: Users + with + app_name + access
        for user in users[:10]:
            for app_name in app_names[:10]:
                patterns.append({
                    "id": f"training_pattern_{pattern_id}",
                    "pattern": f"show me {user} with {app_name} access",
                    "example": self.example,
                    "pattern_type": "user_application_access",
                    "app_type": app_name
                })
                pattern_id += 1
        
        # Pattern 3: Find + users + who + have + app_name
        for user in users[:10]:
            for app_name in app_names[:10]:
                patterns.append({
                    "id": f"training_pattern_{pattern_id}",
                    "pattern": f"find {user} who have {app_name}",
                    "example": self.example,
                    "pattern_type": "user_application_access",
                    "app_type": app_name
                })
                pattern_id += 1
        
        # Pattern 4: List + users + in + app_name
        for user in users[:10]:
            for app_name in app_names[:10]:
                patterns.append({
                    "id": f"training_pattern_{pattern_id}",
                    "pattern": f"list {user} in {app_name}",
                    "example": self.example,
                    "pattern_type": "user_application_access",
                    "app_type": app_name
                })
                pattern_id += 1
        
        return patterns
    
    def _compute_pattern_embeddings(self) -> List[List[float]]:
        """Pre-compute embeddings for all patterns."""
        pattern_texts = [p["pattern"] for p in self.patterns]
        return self.embedding_model.encode(pattern_texts)
    
    def get_example_for_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Find the best matching pattern and return the training example."""
        query_embedding = self.embedding_model.encode([query])
        
        # Calculate similarities
        similarities = []
        for i, pattern_embedding in enumerate(self.pattern_embeddings):
            # Calculate cosine similarity
            import numpy as np
            similarity = np.dot(query_embedding[0], pattern_embedding) / (
                np.linalg.norm(query_embedding[0]) * np.linalg.norm(pattern_embedding)
            )
            similarities.append((similarity, i))
        
        # Get best match
        similarities.sort(reverse=True, key=lambda x: x[0])
        best_match_idx = similarities[0][1]
        best_similarity = similarities[0][0]
        
        if best_similarity > 0.7:  # Threshold for good match
            logger.info(f"Found matching pattern: {self.patterns[best_match_idx]['pattern']} (similarity: {best_similarity:.3f})")
            return self.patterns[best_match_idx]["example"]
        else:
            logger.warning(f"No good pattern match found for query: {query} (best similarity: {best_similarity:.3f})")
            return None
    
    def get_all_patterns(self) -> List[Dict[str, Any]]:
        """Get all patterns."""
        return self.patterns
    
    def get_training_example(self) -> Dict[str, Any]:
        """Get the single training example."""
        return self.example
    
    def test_pattern_matching(self):
        """Test pattern matching with sample queries."""
        test_queries = [
            "give me all the identities who does have account in Workday application",
            "provide me all users accounts for Workday",
            "show me employees who have access to Trakk",
            "find all people with accounts in applications"
        ]
        
        print("Testing Training Example Pattern Matching")
        print("=" * 50)
        
        for query in test_queries:
            example = self.get_example_for_query(query)
            if example:
                print(f"Query: {query}")
                print(f"Match: {example['natural_language']}")
                print(f"SQL: {example['sql_query']}")
                print("-" * 30)
            else:
                print(f"Query: {query}")
                print("No match found")
                print("-" * 30)


def main():
    """Test the training examples."""
    training_examples = IIQTrainingExamples()
    training_examples.test_pattern_matching()
    
    print(f"\nTotal patterns: {len(training_examples.get_all_patterns())}")
    print(f"Training example: {training_examples.get_training_example()['natural_language']}")


if __name__ == "__main__":
    main()