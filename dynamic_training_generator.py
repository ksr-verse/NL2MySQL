#!/usr/bin/env python3
"""Dynamic Training Generator - Generates training examples for new discoveries.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
from schema_discovery import SchemaDiscovery
from training_embedder import training_embedder


class DynamicTrainingGenerator:
    """Generates and updates training examples based on schema discoveries."""
    
    def __init__(self):
        """Initialize dynamic training generator."""
        self.schema_discovery = SchemaDiscovery()
        self.training_embedder = training_embedder
        self.generated_patterns_file = "generated_training_patterns.json"
        self.generated_patterns = self._load_generated_patterns()
        
        logger.info("Dynamic training generator initialized")
    
    def _load_generated_patterns(self) -> List[Dict[str, Any]]:
        """Load previously generated patterns."""
        if os.path.exists(self.generated_patterns_file):
            try:
                with open(self.generated_patterns_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load generated patterns: {e}")
        return []
    
    def _save_generated_patterns(self):
        """Save generated patterns."""
        try:
            with open(self.generated_patterns_file, 'w') as f:
                json.dump(self.generated_patterns, f, indent=2)
            logger.info(f"Generated patterns saved to {self.generated_patterns_file}")
        except Exception as e:
            logger.error(f"Error saving generated patterns: {e}")
    
    def generate_comprehensive_patterns(self, app_name: str, entitlement_type: str) -> List[Dict[str, Any]]:
        """Generate comprehensive training patterns for an application/entitlement type."""
        patterns = []
        
        # Pattern 1: Basic entitlement query
        patterns.append({
            "natural_language": f"Show me users who have {entitlement_type} in {app_name}",
            "sql": f"""SELECT DISTINCT 
    i.firstname, 
    i.lastname, 
    i.displayname, 
    i.email,
    ie.value as {entitlement_type}_value,
    a.name as application_name
FROM spt_identity_entitlement ie
JOIN spt_identity i ON ie.identity_id = i.id
JOIN spt_application a ON ie.application = a.id
WHERE a.name = '{app_name}' 
  AND ie.name = '{entitlement_type}'
ORDER BY i.lastname, i.firstname;""",
            "explanation": f"Basic query to find users with {entitlement_type} in {app_name} application",
            "application": app_name,
            "entitlement_type": entitlement_type,
            "pattern_type": "basic_entitlement"
        })
        
        # Pattern 2: Specific value query
        patterns.append({
            "natural_language": f"Find users with specific {entitlement_type} value in {app_name}",
            "sql": f"""SELECT DISTINCT 
    i.firstname, 
    i.lastname, 
    i.displayname, 
    i.email,
    ie.value as {entitlement_type}_value
FROM spt_identity_entitlement ie
JOIN spt_identity i ON ie.identity_id = i.id
JOIN spt_application a ON ie.application = a.id
WHERE a.name = '{app_name}' 
  AND ie.name = '{entitlement_type}'
  AND ie.value = 'SpecificValue'
ORDER BY i.lastname, i.firstname;""",
            "explanation": f"Query to find users with specific {entitlement_type} value in {app_name}",
            "application": app_name,
            "entitlement_type": entitlement_type,
            "pattern_type": "specific_value"
        })
        
        # Pattern 3: Count query
        patterns.append({
            "natural_language": f"How many users have {entitlement_type} in {app_name}",
            "sql": f"""SELECT 
    COUNT(DISTINCT i.id) as user_count,
    ie.name as entitlement_type,
    a.name as application_name
FROM spt_identity_entitlement ie
JOIN spt_identity i ON ie.identity_id = i.id
JOIN spt_application a ON ie.application = a.id
WHERE a.name = '{app_name}' 
  AND ie.name = '{entitlement_type}'
GROUP BY ie.name, a.name;""",
            "explanation": f"Count query for users with {entitlement_type} in {app_name}",
            "application": app_name,
            "entitlement_type": entitlement_type,
            "pattern_type": "count_query"
        })
        
        # Pattern 4: Multi-application query
        patterns.append({
            "natural_language": f"Show users who have {entitlement_type} in {app_name} and other applications",
            "sql": f"""SELECT DISTINCT 
    i.firstname, 
    i.lastname, 
    i.displayname, 
    i.email,
    ie.value as {entitlement_type}_value,
    a.name as application_name
FROM spt_identity_entitlement ie
JOIN spt_identity i ON ie.identity_id = i.id
JOIN spt_application a ON ie.application = a.id
WHERE ie.name = '{entitlement_type}'
  AND a.name IN ('{app_name}', 'OtherApp1', 'OtherApp2')
ORDER BY a.name, i.lastname, i.firstname;""",
            "explanation": f"Multi-application query for {entitlement_type} including {app_name}",
            "application": app_name,
            "entitlement_type": entitlement_type,
            "pattern_type": "multi_application"
        })
        
        # Pattern 5: Manager information query
        patterns.append({
            "natural_language": f"Show users with {entitlement_type} in {app_name} and their managers",
            "sql": f"""SELECT DISTINCT 
    i.firstname, 
    i.lastname, 
    i.displayname, 
    i.email,
    ie.value as {entitlement_type}_value,
    m.displayname as manager_name,
    a.name as application_name
FROM spt_identity_entitlement ie
JOIN spt_identity i ON ie.identity_id = i.id
JOIN spt_application a ON ie.application = a.id
LEFT JOIN spt_identity m ON i.manager = m.id
WHERE a.name = '{app_name}' 
  AND ie.name = '{entitlement_type}'
ORDER BY i.lastname, i.firstname;""",
            "explanation": f"Query with manager information for users with {entitlement_type} in {app_name}",
            "application": app_name,
            "entitlement_type": entitlement_type,
            "pattern_type": "with_manager"
        })
        
        return patterns
    
    def generate_entitlement_type_patterns(self, entitlement_type: str) -> List[Dict[str, Any]]:
        """Generate patterns for a specific entitlement type across applications."""
        patterns = []
        
        # Generic entitlement type patterns
        patterns.append({
            "natural_language": f"Show me all users with {entitlement_type} entitlements",
            "sql": f"""SELECT DISTINCT 
    i.firstname, 
    i.lastname, 
    i.displayname, 
    i.email,
    ie.value as {entitlement_type}_value,
    a.name as application_name
FROM spt_identity_entitlement ie
JOIN spt_identity i ON ie.identity_id = i.id
JOIN spt_application a ON ie.application = a.id
WHERE ie.name = '{entitlement_type}'
ORDER BY a.name, i.lastname, i.firstname;""",
            "explanation": f"Generic query for all users with {entitlement_type} across applications",
            "entitlement_type": entitlement_type,
            "pattern_type": "generic_entitlement"
        })
        
        # Entitlement type with specific value pattern
        patterns.append({
            "natural_language": f"Find users with specific {entitlement_type} value across all applications",
            "sql": f"""SELECT DISTINCT 
    i.firstname, 
    i.lastname, 
    i.displayname, 
    i.email,
    ie.value as {entitlement_type}_value,
    a.name as application_name
FROM spt_identity_entitlement ie
JOIN spt_identity i ON ie.identity_id = i.id
JOIN spt_application a ON ie.application = a.id
WHERE ie.name = '{entitlement_type}'
  AND ie.value = 'SpecificValue'
ORDER BY a.name, i.lastname, i.firstname;""",
            "explanation": f"Query for specific {entitlement_type} value across applications",
            "entitlement_type": entitlement_type,
            "pattern_type": "specific_value_generic"
        })
        
        return patterns
    
    def process_new_discoveries(self, force_generate: bool = False) -> List[Dict[str, Any]]:
        """Process new discoveries and generate training patterns."""
        logger.info("Processing new discoveries...")
        
        # Run schema discovery first
        discovery_results = self.schema_discovery.run_discovery()
        new_discoveries = discovery_results.get("new_discoveries", {})
        all_applications = discovery_results.get("applications", {})
        
        new_patterns = []
        
        # Process new applications
        for new_app in new_discoveries.get("new_applications", []):
            app_name = new_app["name"]
            entitlement_types = new_app["entitlement_types"]
            
            logger.info(f"Generating patterns for new application: {app_name}")
            
            for ent_type in entitlement_types:
                patterns = self.generate_comprehensive_patterns(app_name, ent_type)
                new_patterns.extend(patterns)
        
        # Process new entitlement types
        for new_ent in new_discoveries.get("new_entitlement_types", []):
            app_name = new_ent["application"]
            new_types = new_ent["new_types"]
            
            logger.info(f"Generating patterns for new entitlement types in {app_name}: {new_types}")
            
            for ent_type in new_types:
                # Generate application-specific patterns
                patterns = self.generate_comprehensive_patterns(app_name, ent_type)
                new_patterns.extend(patterns)
                
                # Generate generic entitlement type patterns
                generic_patterns = self.generate_entitlement_type_patterns(ent_type)
                new_patterns.extend(generic_patterns)
        
        # If force_generate is True, generate patterns for all applications (first run)
        if force_generate and not new_patterns:
            logger.info("Force generating patterns for all discovered applications...")
            for app_name, app_data in all_applications.items():
                entitlement_types = app_data.get("entitlement_types", [])
                if entitlement_types:  # Only if app has entitlements
                    logger.info(f"Generating patterns for application: {app_name}")
                    for ent_type in entitlement_types:
                        patterns = self.generate_comprehensive_patterns(app_name, ent_type)
                        new_patterns.extend(patterns)
        
        # Add metadata to patterns
        for pattern in new_patterns:
            pattern["generated_at"] = datetime.now().isoformat()
            pattern["generated_by"] = "dynamic_training_generator"
        
        # Store generated patterns
        self.generated_patterns.extend(new_patterns)
        self._save_generated_patterns()
        
        logger.info(f"Generated {len(new_patterns)} new training patterns")
        return new_patterns
    
    def update_vector_database(self, new_patterns: List[Dict[str, Any]]) -> bool:
        """Update vector database with new training patterns."""
        if not new_patterns:
            logger.info("No new patterns to update in vector database")
            return True
        
        try:
            # Add new patterns to training data
            from iiq_training_data import iiq_training
            
            # Add new patterns to the training data
            for pattern in new_patterns:
                iiq_training.examples.append({
                    "natural_language": pattern["natural_language"],
                    "sql": pattern["sql"],
                    "explanation": pattern["explanation"]
                })
            
            # Re-embed all training data (including new patterns)
            success = self.training_embedder.embed_training_data(reset=True)
            
            if success:
                logger.info(f"Successfully updated vector database with {len(new_patterns)} new patterns")
                return True
            else:
                logger.error("Failed to update vector database")
                return False
                
        except Exception as e:
            logger.error(f"Error updating vector database: {e}")
            return False
    
    def run_daily_update(self) -> Dict[str, Any]:
        """Run daily update process."""
        logger.info("Starting daily training update...")
        
        try:
            # Process new discoveries
            new_patterns = self.process_new_discoveries()
            
            # Update vector database
            update_success = self.update_vector_database(new_patterns)
            
            # Prepare results
            results = {
                "timestamp": datetime.now().isoformat(),
                "new_patterns_generated": len(new_patterns),
                "vector_db_updated": update_success,
                "patterns": new_patterns,
                "status": "success" if update_success else "partial_success"
            }
            
            logger.info(f"Daily update completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in daily update: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "error"
            }


def main():
    """Command-line interface for dynamic training generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate dynamic training patterns")
    parser.add_argument("--discover", action="store_true", help="Process new discoveries and generate patterns")
    parser.add_argument("--force-generate", action="store_true", help="Force generate patterns for all applications (first run)")
    parser.add_argument("--update-vector", action="store_true", help="Update vector database with new patterns")
    parser.add_argument("--daily-update", action="store_true", help="Run complete daily update")
    parser.add_argument("--show-patterns", action="store_true", help="Show generated patterns")
    
    args = parser.parse_args()
    
    try:
        generator = DynamicTrainingGenerator()
        
        if args.daily_update:
            results = generator.run_daily_update()
            print("✅ Daily update completed!")
            print(f"New patterns generated: {results['new_patterns_generated']}")
            print(f"Vector DB updated: {results['vector_db_updated']}")
            print(f"Status: {results['status']}")
        
        if args.discover:
            patterns = generator.process_new_discoveries()
            print(f"✅ Generated {len(patterns)} new training patterns")
            for pattern in patterns:
                print(f"  - {pattern['natural_language']}")
        
        if args.force_generate:
            patterns = generator.process_new_discoveries(force_generate=True)
            print(f"✅ Force generated {len(patterns)} training patterns")
            for pattern in patterns:
                print(f"  - {pattern['natural_language']}")
        
        if args.update_vector:
            # Load existing patterns and update vector DB
            patterns = generator.generated_patterns
            success = generator.update_vector_database(patterns)
            if success:
                print("✅ Vector database updated successfully")
            else:
                print("❌ Failed to update vector database")
        
        if args.show_patterns:
            patterns = generator.generated_patterns
            print(f"\n📋 Generated Patterns ({len(patterns)} total):")
            for i, pattern in enumerate(patterns, 1):
                print(f"\n{i}. {pattern['natural_language']}")
                print(f"   App: {pattern.get('application', 'N/A')}")
                print(f"   Type: {pattern.get('entitlement_type', 'N/A')}")
                print(f"   Pattern: {pattern.get('pattern_type', 'N/A')}")
        
        if not any([args.discover, args.update_vector, args.daily_update, args.show_patterns]):
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
