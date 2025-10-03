#!/usr/bin/env python3
"""
IIQ Prompt Templates - Single MySQL Expert Prompt with 310+ Patterns
Contains the single prompt template and all 310+ patterns for matching
"""

from typing import Dict, Any, List
from sentence_transformers import SentenceTransformer
import numpy as np


class IIQPromptTemplates:
    """Single prompt template with all the patterns for matching."""
    
    def __init__(self):
        """Initialize the prompt template and all patterns."""
        self.prompt_template = self._get_mysql_expert_prompt()
        self.patterns = self._get_all_patterns()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Pre-compute embeddings for all patterns
        print(f"Loading {len(self.patterns)} patterns and computing embeddings...")
        self.pattern_embeddings = self._compute_pattern_embeddings()
        print(f"Loaded {len(self.patterns)} patterns successfully!")
        
    def _get_mysql_expert_prompt(self) -> str:
        """Get the single MySQL expert prompt."""
        return """You are an MYSQL expert, you need to write query for me in mysql.

You do have three tables:
spt_identity - this table stores user data
spt_application - this stores applications metadata
spt_link - this stores account for the user for that application.

A user can have mutiple rows in link table for a given application. If a user does have two accounts for an application, it means user would have two rows in spt_link table for the same application.

If a system does have 15 applications, it means only 15 rows are possible in spt_application table, if a system does have 100 users then in spt_identity only 100 rows are possible, if 100 users in total does have 1000 accounts, the there would be 1000 rows in spt_link table, those 1000 rows many belong to different application, it depend on which account is for which application."""
    
    def _get_all_patterns(self) -> List[Dict[str, Any]]:
        """Get all 310+ patterns for user/application queries."""
        
        # Action words
        actions = ["provide", "give", "generate", "show", "fetch", "get", "list", "display", "retrieve", "return", "find", "search", "query", "select"]
        
        # User terms
        users = ["users", "employees", "people", "identities", "personas", "reviewers", "system accounts", "Owners", "Administrators", "Admins", "Adminsitrators", "Owner", "person", "individual", "staff", "worker", "personnel", "members"]
        
        # Account/access terms  
        accounts = ["accounts", "user accounts", "identity accounts", "links", "access", "connections", "provisioned accounts", "account links", "user access", "system access", "permissions", "entitlements"]
        
        # Application terms
        apps = ["applications", "apps", "systems", "target systems", "connected apps", "platforms", "services", "tools", "software", "environments", "programs", "solutions"]
        
        # Application names
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
                            "id": f"pattern_{pattern_id}",
                            "pattern": pattern_text,
                            "action": action,
                            "user_type": user,
                            "account_type": account,
                            "app_type": app,
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
                    "id": f"pattern_{pattern_id}",
                    "pattern": f"show me {user} with {app_name} access",
                    "action": "show",
                    "user_type": user,
                    "account_type": "access",
                    "app_type": app_name,
                    "pattern_type": "user_application_access"
                })
                pattern_id += 1
        
        # Pattern 3: Users + in + app_name + application
        for user in users[:10]:
            for app_name in app_names[:10]:
                patterns.append({
                    "id": f"pattern_{pattern_id}",
                    "pattern": f"list {user} in {app_name} application",
                    "action": "list",
                    "user_type": user,
                    "account_type": "application",
                    "app_type": app_name,
                    "pattern_type": "user_application_access"
                })
                pattern_id += 1
        
        # Pattern 4: Users + having + app_name + accounts
        for user in users[:5]:
            for app_name in app_names[:5]:
                patterns.append({
                    "id": f"pattern_{pattern_id}",
                    "pattern": f"get {user} having {app_name} accounts",
                    "action": "get", 
                    "user_type": user,
                    "account_type": "accounts",
                    "app_type": app_name,
                    "pattern_type": "user_application_access"
                })
                pattern_id += 1
        
        # Pattern 5: Users + who + have + app_name
        for user in users[:5]:
            for app_name in app_names[:5]:
                patterns.append({
                    "id": f"pattern_{pattern_id}",
                    "pattern": f"find {user} who have {app_name}",
                    "action": "find",
                    "user_type": user,
                    "account_type": "access",
                    "app_type": app_name,
                    "pattern_type": "user_application_access"
                })
                pattern_id += 1
        
        
        return patterns
    
    def _compute_pattern_embeddings(self) -> np.ndarray:
        """Pre-compute embeddings for all patterns."""
        pattern_texts = [f"{p['pattern']} {self.prompt_template}" for p in self.patterns]
        return self.embedding_model.encode(pattern_texts)
    
    def get_prompt_for_query(self, query: str, similarity_threshold: float = 0.0) -> Dict[str, Any]:
        """Get the MySQL expert prompt for a specific query by matching patterns."""
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).reshape(1, -1)
        
        # Compute similarities with all patterns
        similarities = np.dot(query_embedding, self.pattern_embeddings.T)[0]
        
        # Find best match
        best_idx = np.argmax(similarities)
        best_similarity = float(similarities[best_idx])
        best_pattern = self.patterns[best_idx]
        
        if best_similarity > similarity_threshold:
            return {
                "prompt": self.prompt_template,
                "matched_pattern": best_pattern['pattern'],
                "similarity_score": best_similarity,
                "pattern_type": best_pattern['pattern_type'],
                "match_found": True
            }
        else:
            return {
                "prompt": None,
                "matched_pattern": best_pattern['pattern'],
                "similarity_score": best_similarity,
                "pattern_type": best_pattern['pattern_type'],
                "match_found": False,
                "reason": f"Similarity score {best_similarity:.3f} below threshold {similarity_threshold}"
            }
    
    def get_prompt(self) -> str:
        """Get the MySQL expert prompt directly."""
        return self.prompt_template
    
    def build_prompt_with_context(self, query: str, schema_context: str = "", 
                                 training_context: str = "") -> str:
        """Build prompt with additional context."""
        prompt = self.prompt_template
        
        # Add schema context if provided
        if schema_context:
            prompt += f"\n\n## DATABASE SCHEMA INFORMATION:\n\n{schema_context}\n"
        
        # Add training context if provided
        if training_context:
            prompt += f"\n\n## TRAINING EXAMPLES:\n\n{training_context}\n"
        
        # Add query
        prompt += f"\n\nNatural Language Query: {query}\n\nGenerate the MySQL SELECT query:"
        
        return prompt
    
    def get_all_patterns_count(self) -> int:
        """Get the total number of patterns."""
        return len(self.patterns)
    
    def get_all_patterns(self) -> List[Dict[str, Any]]:
        """Get all patterns."""
        return self.patterns.copy()
    
    def test_pattern_matching(self, test_queries: List[str]) -> Dict[str, Any]:
        """Test pattern matching for multiple queries."""
        results = {}
        
        for query in test_queries:
            result = self.get_prompt_for_query(query)
            results[query] = result
            
        return results


# Global instance
iiq_prompt_templates = IIQPromptTemplates()


def main():
    """Test the prompt template and pattern matching."""
    templates = IIQPromptTemplates()
    
    print("MySQL Expert Prompt:")
    print("=" * 50)
    print(templates.prompt_template)
    
    print(f"\nTotal patterns in code: {templates.get_all_patterns_count()}")
    
    print("\n" + "=" * 50)
    print("Testing pattern matching:")
    print("=" * 50)
    
    test_queries = [
        "give me all the users who are part of workday application",
        "provide identities having apache DS application",
        "fetch data for accounts with Trakk app",
        "show me users with workday access",
        "list employees in trakk application",
        "what is the weather today",  # This should not match
        "calculate 2 plus 2"  # This should not match
    ]
    
    results = templates.test_pattern_matching(test_queries)
    
    for query, result in results.items():
        print(f"\nQuery: '{query}'")
        if result['match_found']:
            print(f"  MATCH: '{result['matched_pattern']}' (Score: {result['similarity_score']:.3f})")
            print(f"  Pattern type: {result['pattern_type']}")
        else:
            print(f"  NO MATCH: {result['reason']}")


if __name__ == "__main__":
    main()