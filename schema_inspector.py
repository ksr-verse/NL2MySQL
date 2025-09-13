"""Schema inspector for extracting database schema information."""

import json
import argparse
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, inspect, MetaData, Table, text
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
from config import settings


class SchemaInspector:
    """Extract and analyze database schema."""
    
    def __init__(self, connection_string: Optional[str] = None):
        """Initialize schema inspector with database connection."""
        self.connection_string = connection_string or settings.db.connection_string
        self.engine = None
        self.inspector = None
        
    def connect(self) -> bool:
        """Establish database connection."""
        try:
            logger.info(f"Attempting connection to: {self.connection_string}")
            
            # Create engine with fast timeout settings
            self.engine = create_engine(
                self.connection_string,
                pool_size=1,
                max_overflow=0,
                pool_timeout=5,
                pool_recycle=300,
                connect_args={
                    "connect_timeout": 5
                }
            )
            
            # Test connection immediately with timeout
            logger.info("Testing database connection...")
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
            self.inspector = inspect(self.engine)
            logger.info("✅ Database connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            logger.error(f"Connection string: {self.connection_string}")
            return False
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")
    
    def get_table_info(self, table_name: str, schema: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed information about a specific table."""
        if not self.inspector:
            raise RuntimeError("Database connection not established")
        
        try:
            # Get columns
            columns = self.inspector.get_columns(table_name, schema=schema)
            
            # Get primary keys
            pk_constraint = self.inspector.get_pk_constraint(table_name, schema=schema)
            primary_keys = pk_constraint.get('constrained_columns', [])
            
            # Get foreign keys
            foreign_keys = self.inspector.get_foreign_keys(table_name, schema=schema)
            
            # Get indexes
            indexes = self.inspector.get_indexes(table_name, schema=schema)
            
            # Get unique constraints (not supported by all dialects)
            try:
                unique_constraints = self.inspector.get_unique_constraints(table_name, schema=schema)
            except NotImplementedError:
                unique_constraints = []
            
            # Get check constraints (not supported by all dialects)
            try:
                check_constraints = self.inspector.get_check_constraints(table_name, schema=schema)
            except NotImplementedError:
                check_constraints = []
            
            return {
                "name": table_name,
                "schema": schema,
                "columns": columns,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys,
                "indexes": indexes,
                "unique_constraints": unique_constraints,
                "check_constraints": check_constraints
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            return {}
    
    def get_all_tables(self, schema: Optional[str] = None) -> List[str]:
        """Get list of all tables in the database."""
        if not self.inspector:
            raise RuntimeError("Database connection not established")
        
        try:
            return self.inspector.get_table_names(schema=schema)
        except SQLAlchemyError as e:
            logger.error(f"Error getting table list: {e}")
            return []
    
    def get_all_schemas(self) -> List[str]:
        """Get list of all schemas in the database."""
        if not self.inspector:
            raise RuntimeError("Database connection not established")
        
        try:
            return self.inspector.get_schema_names()
        except SQLAlchemyError as e:
            logger.error(f"Error getting schema list: {e}")
            return []
    
    def extract_full_schema(self) -> Dict[str, Any]:
        """Extract complete database schema information."""
        if not self.connect():
            return {}
        
        schema_info = {
            "database_type": "mssql",
            "schemas": {},
            "relationships": [],
            "metadata": {
                "extraction_timestamp": None,
                "total_tables": 0,
                "total_columns": 0
            }
        }
        
        try:
            # Get all schemas
            schemas = self.get_all_schemas()
            logger.info(f"Found {len(schemas)} schemas")
            
            total_tables = 0
            total_columns = 0
            
            for schema_name in schemas:
                # Skip system schemas
                if schema_name.lower() in ['information_schema', 'sys', 'guest', 'INFORMATION_SCHEMA']:
                    continue
                
                schema_info["schemas"][schema_name] = {
                    "tables": {},
                    "views": []
                }
                
                # Get tables in this schema
                tables = self.get_all_tables(schema=schema_name)
                logger.info(f"Found {len(tables)} tables in schema '{schema_name}'")
                
                for table_name in tables:
                    table_info = self.get_table_info(table_name, schema=schema_name)
                    if table_info:
                        schema_info["schemas"][schema_name]["tables"][table_name] = table_info
                        total_tables += 1
                        total_columns += len(table_info.get("columns", []))
                        
                        # Collect relationships
                        for fk in table_info.get("foreign_keys", []):
                            relationship = {
                                "from_table": f"{schema_name}.{table_name}" if schema_name else table_name,
                                "from_columns": fk.get("constrained_columns", []),
                                "to_table": f"{fk.get('referred_schema', schema_name)}.{fk.get('referred_table')}" if fk.get('referred_schema') else fk.get('referred_table'),
                                "to_columns": fk.get("referred_columns", [])
                            }
                            schema_info["relationships"].append(relationship)
            
            # Update metadata
            from datetime import datetime
            schema_info["metadata"]["extraction_timestamp"] = datetime.now().isoformat()
            schema_info["metadata"]["total_tables"] = total_tables
            schema_info["metadata"]["total_columns"] = total_columns
            
            logger.info(f"Schema extraction completed: {total_tables} tables, {total_columns} columns")
            return schema_info
            
        except Exception as e:
            logger.error(f"Error during schema extraction: {e}")
            logger.exception("Full traceback:")
            return {}
        finally:
            if self.engine:
                self.engine.dispose()
    
    def save_schema(self, schema_info: Dict[str, Any], filename: str = None) -> bool:
        """Save schema information to JSON file."""
        filename = filename or settings.app.schema_file
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(schema_info, f, indent=2, default=str)
            logger.info(f"Schema saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving schema to {filename}: {e}")
            return False
    
    def load_schema(self, filename: str = None) -> Dict[str, Any]:
        """Load schema information from JSON file."""
        filename = filename or settings.app.schema_file
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                schema_info = json.load(f)
            logger.info(f"Schema loaded from {filename}")
            return schema_info
        except Exception as e:
            logger.error(f"Error loading schema from {filename}: {e}")
            return {}


def main():
    """Command-line interface for schema extraction."""
    parser = argparse.ArgumentParser(description="Extract database schema")
    parser.add_argument("--connection", "-c", help="Database connection string")
    parser.add_argument("--output", "-o", help="Output filename", default="schema.json")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.remove()
        logger.add("schema_extraction.log", level="DEBUG")
        logger.add(lambda msg: print(msg, end=""), level="INFO")
    
    inspector = SchemaInspector(connection_string=args.connection)
    schema_info = inspector.extract_full_schema()
    
    if schema_info:
        inspector.save_schema(schema_info, args.output)
        print(f"Schema extracted and saved to {args.output}")
    else:
        print("Schema extraction failed")
        exit(1)


if __name__ == "__main__":
    main()
