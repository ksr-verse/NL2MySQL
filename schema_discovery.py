#!/usr/bin/env python3
"""Schema Discovery - Automatically discovers new applications and entitlement types.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

import os
import json
from typing import Dict, List, Any, Set, Optional
from datetime import datetime
from loguru import logger
import mysql.connector
from config import settings


class SchemaDiscovery:
    """Discovers new applications and entitlement types from the database."""
    
    def __init__(self):
        """Initialize schema discovery."""
        # Parse connection string to get database config
        conn_str = settings.db.connection_string
        # Format: mysql+pymysql://username:password@host:port/database
        if '://' in conn_str:
            parts = conn_str.split('://')[1]  # Remove mysql+pymysql://
            if '@' in parts:
                auth, host_db = parts.split('@')
                if ':' in auth:
                    username, password = auth.split(':')
                else:
                    username, password = auth, ''
                
                if '/' in host_db:
                    host_port, database = host_db.split('/')
                    if ':' in host_port:
                        host, port = host_port.split(':')
                        port = int(port)
                    else:
                        host, port = host_port, 3306
                else:
                    host, port, database = host_db, 3306, 'database'
            else:
                # No auth
                if '/' in parts:
                    host_port, database = parts.split('/')
                    if ':' in host_port:
                        host, port = host_port.split(':')
                        port = int(port)
                    else:
                        host, port = host_port, 3306
                else:
                    host, port, database = parts, 3306, 'database'
                username, password = 'root', ''
        else:
            # Fallback - use working config
            host, port, username, password, database = 'localhost', 3306, 'root', 'root', 'identityiq'
        
        self.db_config = {
            'host': host,
            'port': port,
            'user': username,
            'password': password,
            'database': database
        }
        self.discovery_file = "schema_discovery.json"
        self.last_discovery = self._load_last_discovery()
        
        logger.info("Schema discovery initialized")
    
    def _load_last_discovery(self) -> Dict[str, Any]:
        """Load last discovery results."""
        if os.path.exists(self.discovery_file):
            try:
                with open(self.discovery_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load last discovery: {e}")
        
        return {
            "last_run": None,
            "applications": {},
            "entitlement_types": {},
            "new_discoveries": {}
        }
    
    def _save_discovery(self, discovery_data: Dict[str, Any]):
        """Save discovery results."""
        try:
            with open(self.discovery_file, 'w') as f:
                json.dump(discovery_data, f, indent=2)
            logger.info(f"Discovery results saved to {self.discovery_file}")
        except Exception as e:
            logger.error(f"Error saving discovery: {e}")
    
    def discover_applications(self) -> Dict[str, Any]:
        """Discover all applications in the system."""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor(dictionary=True)
            
            # Get all applications
            cursor.execute("""
                SELECT id, name, created, modified
                FROM spt_application 
                ORDER BY name
            """)
            
            applications = {}
            for app in cursor.fetchall():
                applications[app['name']] = {
                    "id": app['id'],
                    "name": app['name'],
                    "description": "",  # No description column
                    "created": str(app.get('created', '')),
                    "modified": str(app.get('modified', '')),
                    "entitlement_types": []  # Will be populated later
                }
            
            cursor.close()
            connection.close()
            
            logger.info(f"Discovered {len(applications)} applications")
            return applications
            
        except Exception as e:
            logger.error(f"Error discovering applications: {e}")
            return {}
    
    def discover_entitlement_types(self, applications: Dict[str, Any]) -> Dict[str, Any]:
        """Discover entitlement types for each application."""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor(dictionary=True)
            
            # Get entitlement types from spt_identity_entitlement
            cursor.execute("""
                SELECT DISTINCT 
                    a.name as application_name,
                    ie.name as entitlement_type,
                    COUNT(*) as count,
                    MIN(ie.value) as sample_value
                FROM spt_identity_entitlement ie
                JOIN spt_application a ON ie.application = a.id
                GROUP BY a.name, ie.name
                ORDER BY a.name, ie.name
            """)
            
            entitlement_data = cursor.fetchall()
            
            # Organize by application
            for row in entitlement_data:
                app_name = row['application_name']
                entitlement_type = row['entitlement_type']
                
                if app_name in applications:
                    if entitlement_type not in applications[app_name]['entitlement_types']:
                        applications[app_name]['entitlement_types'].append(entitlement_type)
                    
                    # Store detailed info
                    if 'entitlement_details' not in applications[app_name]:
                        applications[app_name]['entitlement_details'] = {}
                    
                    applications[app_name]['entitlement_details'][entitlement_type] = {
                        "count": row['count'],
                        "sample_value": row['sample_value'],
                        "description": self._get_entitlement_description(entitlement_type)
                    }
            
            cursor.close()
            connection.close()
            
            logger.info("Entitlement types discovered for all applications")
            return applications
            
        except Exception as e:
            logger.error(f"Error discovering entitlement types: {e}")
            return applications
    
    def _get_entitlement_description(self, entitlement_type: str) -> str:
        """Get description for entitlement type."""
        descriptions = {
            "group": "User group membership",
            "capability": "Application capability or permission",
            "role": "User role assignment",
            "permission": "Specific permission",
            "access": "Access level",
            "privilege": "System privilege",
            "right": "User right",
            "authority": "Authority level"
        }
        return descriptions.get(entitlement_type.lower(), f"{entitlement_type} entitlement")
    
    def compare_discoveries(self, new_applications: Dict[str, Any]) -> Dict[str, Any]:
        """Compare with last discovery to find new items."""
        new_discoveries = {
            "new_applications": [],
            "new_entitlement_types": [],
            "modified_applications": []
        }
        
        last_apps = self.last_discovery.get("applications", {})
        
        for app_name, app_data in new_applications.items():
            if app_name not in last_apps:
                # New application
                new_discoveries["new_applications"].append({
                    "name": app_name,
                    "entitlement_types": list(app_data.get("entitlement_types", set())),
                    "description": app_data.get("description", "")
                })
            else:
                # Check for new entitlement types
                last_entitlements = set(last_apps[app_name].get("entitlement_types", []))
                new_entitlements = set(app_data.get("entitlement_types", []))
                
                if new_entitlements - last_entitlements:
                    new_discoveries["new_entitlement_types"].append({
                        "application": app_name,
                        "new_types": list(new_entitlements - last_entitlements),
                        "all_types": list(new_entitlements)
                    })
        
        return new_discoveries
    
    def run_discovery(self) -> Dict[str, Any]:
        """Run complete schema discovery."""
        logger.info("Starting schema discovery...")
        
        # Discover applications
        applications = self.discover_applications()
        
        # Discover entitlement types
        applications = self.discover_entitlement_types(applications)
        
        # Compare with last discovery
        new_discoveries = self.compare_discoveries(applications)
        
        # Prepare discovery results
        discovery_results = {
            "last_run": datetime.now().isoformat(),
            "applications": applications,
            "entitlement_types": self._extract_entitlement_types(applications),
            "new_discoveries": new_discoveries,
            "summary": {
                "total_applications": len(applications),
                "new_applications": len(new_discoveries["new_applications"]),
                "new_entitlement_types": len(new_discoveries["new_entitlement_types"])
            }
        }
        
        # Save results
        self._save_discovery(discovery_results)
        
        # Update last discovery
        self.last_discovery = discovery_results
        
        logger.info(f"Discovery completed: {discovery_results['summary']}")
        return discovery_results
    
    def _extract_entitlement_types(self, applications: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract all entitlement types by application."""
        entitlement_types = {}
        for app_name, app_data in applications.items():
            entitlement_types[app_name] = app_data.get("entitlement_types", [])
        return entitlement_types
    
    def get_new_training_patterns(self) -> List[Dict[str, Any]]:
        """Generate new training patterns for discovered items."""
        new_patterns = []
        new_discoveries = self.last_discovery.get("new_discoveries", {})
        
        # Generate patterns for new applications
        for new_app in new_discoveries.get("new_applications", []):
            app_name = new_app["name"]
            entitlement_types = new_app["entitlement_types"]
            
            for ent_type in entitlement_types:
                pattern = self._generate_training_pattern(app_name, ent_type)
                if pattern:
                    new_patterns.append(pattern)
        
        # Generate patterns for new entitlement types
        for new_ent in new_discoveries.get("new_entitlement_types", []):
            app_name = new_ent["application"]
            new_types = new_ent["new_types"]
            
            for ent_type in new_types:
                pattern = self._generate_training_pattern(app_name, ent_type)
                if pattern:
                    new_patterns.append(pattern)
        
        return new_patterns
    
    def _generate_training_pattern(self, app_name: str, entitlement_type: str) -> Dict[str, Any]:
        """Generate training pattern for new application/entitlement type."""
        
        # Generate natural language variations
        natural_language_variations = [
            f"Show me users who have {entitlement_type} in {app_name}",
            f"Find identities with {entitlement_type} access in {app_name}",
            f"Get users who have {entitlement_type} in {app_name} application",
            f"List identities with {entitlement_type} in {app_name}",
            f"Show users with {entitlement_type} membership in {app_name}"
        ]
        
        # Generate SQL template
        sql_template = f"""SELECT DISTINCT 
    i.firstname, 
    i.lastname, 
    i.displayname, 
    i.email,
    ie.value as {entitlement_type}_value,
    a.name as application_name,
    ie.name as entitlement_type
FROM spt_identity_entitlement ie
JOIN spt_identity i ON ie.identity_id = i.id
JOIN spt_application a ON ie.application = a.id
WHERE a.name = '{app_name}' 
  AND ie.name = '{entitlement_type}'
ORDER BY i.lastname, i.firstname;"""
        
        return {
            "natural_language": natural_language_variations[0],  # Use first variation
            "sql": sql_template,
            "explanation": f"Query to find users with {entitlement_type} in {app_name} application using spt_identity_entitlement table",
            "application": app_name,
            "entitlement_type": entitlement_type,
            "pattern_type": "new_discovery",
            "generated_at": datetime.now().isoformat()
        }


def main():
    """Command-line interface for schema discovery."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Discover new applications and entitlement types")
    parser.add_argument("--discover", action="store_true", help="Run schema discovery")
    parser.add_argument("--show-new", action="store_true", help="Show new discoveries")
    parser.add_argument("--generate-patterns", action="store_true", help="Generate training patterns for new discoveries")
    
    args = parser.parse_args()
    
    try:
        discovery = SchemaDiscovery()
        
        if args.discover:
            results = discovery.run_discovery()
            print("✅ Schema discovery completed!")
            print(f"Total applications: {results['summary']['total_applications']}")
            print(f"New applications: {results['summary']['new_applications']}")
            print(f"New entitlement types: {results['summary']['new_entitlement_types']}")
        
        if args.show_new:
            new_discoveries = discovery.last_discovery.get("new_discoveries", {})
            if new_discoveries.get("new_applications"):
                print("\n🆕 New Applications:")
                for app in new_discoveries["new_applications"]:
                    print(f"  - {app['name']}: {app['entitlement_types']}")
            
            if new_discoveries.get("new_entitlement_types"):
                print("\n🆕 New Entitlement Types:")
                for ent in new_discoveries["new_entitlement_types"]:
                    print(f"  - {ent['application']}: {ent['new_types']}")
        
        if args.generate_patterns:
            patterns = discovery.get_new_training_patterns()
            if patterns:
                print(f"\n🎯 Generated {len(patterns)} new training patterns:")
                for pattern in patterns:
                    print(f"  - {pattern['natural_language']}")
                    print(f"    App: {pattern['application']}, Type: {pattern['entitlement_type']}")
            else:
                print("\n✅ No new training patterns to generate")
        
        if not any([args.discover, args.show_new, args.generate_patterns]):
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
