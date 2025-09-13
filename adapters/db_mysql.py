"""MySQL database adapter for executing SQL queries."""

import mysql.connector
from mysql.connector import Error
from typing import Dict, Any, List, Optional, Tuple, Union
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
from config import settings
import pandas as pd


class MySQLAdapter:
    """Adapter for executing queries against MySQL database."""
    
    def __init__(self, connection_string: str = None):
        """Initialize MySQL adapter."""
        self.connection_string = connection_string or settings.db.connection_string
        self.engine = None
        self._init_engine()
        
    def _init_engine(self):
        """Initialize SQLAlchemy engine."""
        try:
            self.engine = create_engine(
                self.connection_string,
                pool_size=settings.db.max_pool_size,
                pool_timeout=30,
                pool_recycle=3600,
                connect_args={
                    "connect_timeout": settings.db.timeout,
                    "autocommit": False
                }
            )
            logger.info("MySQL adapter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MySQL adapter: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                return result.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None,
        fetch_results: bool = True,
        max_rows: int = 1000
    ) -> Dict[str, Any]:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_results: Whether to fetch and return results
            max_rows: Maximum number of rows to return
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            with self.engine.connect() as conn:
                # Execute query
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                
                response = {
                    "success": True,
                    "query": query,
                    "row_count": result.rowcount if hasattr(result, 'rowcount') else 0,
                    "columns": [],
                    "data": [],
                    "error": None
                }
                
                # Fetch results if requested and query returns data
                if fetch_results and result.returns_rows:
                    # Get column names
                    response["columns"] = list(result.keys())
                    
                    # Fetch data with row limit
                    rows = result.fetchmany(max_rows)
                    response["data"] = [list(row) for row in rows]
                    response["row_count"] = len(response["data"])
                    
                    # Check if there are more rows
                    if len(rows) == max_rows:
                        try:
                            next_row = result.fetchone()
                            if next_row:
                                response["truncated"] = True
                                response["message"] = f"Results truncated to {max_rows} rows"
                        except:
                            pass
                
                logger.info(f"Query executed successfully, returned {response['row_count']} rows")
                return response
                
        except SQLAlchemyError as e:
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            logger.error(f"SQL execution error: {error_msg}")
            return {
                "success": False,
                "query": query,
                "error": error_msg,
                "error_type": "SQLAlchemyError",
                "columns": [],
                "data": [],
                "row_count": 0
            }
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__,
                "columns": [],
                "data": [],
                "row_count": 0
            }
    
    def execute_query_pandas(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 10000
    ) -> Dict[str, Any]:
        """
        Execute query and return results as pandas DataFrame.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            max_rows: Maximum number of rows to return
            
        Returns:
            Dictionary containing DataFrame and metadata
        """
        try:
            # Add row limit to query if not already present
            query_upper = query.upper().strip()
            if not any(keyword in query_upper for keyword in ['LIMIT ', 'TOP ']):
                # Add LIMIT clause for MySQL
                if query_upper.startswith('SELECT'):
                    query = f"{query} LIMIT {max_rows}"
            
            df = pd.read_sql_query(query, self.engine, params=params)
            
            return {
                "success": True,
                "query": query,
                "dataframe": df,
                "row_count": len(df),
                "columns": df.columns.tolist(),
                "data": df.values.tolist(),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error executing query with pandas: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "dataframe": None,
                "row_count": 0,
                "columns": [],
                "data": []
            }
    
    def validate_query_syntax(self, query: str) -> Dict[str, Any]:
        """
        Validate SQL query syntax without executing it.
        
        Args:
            query: SQL query to validate
            
        Returns:
            Dictionary containing validation results
        """
        try:
            # MySQL doesn't have a direct syntax-only validation like MSSQL's SET PARSEONLY
            # We'll use EXPLAIN to validate SELECT queries, or try to prepare the statement
            validation_query = query.strip()
            
            with self.engine.connect() as conn:
                # For SELECT queries, use EXPLAIN
                if validation_query.upper().startswith('SELECT'):
                    explain_query = f"EXPLAIN {validation_query}"
                    conn.execute(text(explain_query))
                else:
                    # For other queries, try to prepare the statement
                    # This is a basic validation - MySQL will check syntax
                    conn.execute(text(f"PREPARE stmt FROM '{validation_query.replace(chr(39), chr(39)+chr(39))}'"))
                    conn.execute(text("DEALLOCATE PREPARE stmt"))
            
            return {
                "valid": True,
                "error": None,
                "query": query
            }
            
        except SQLAlchemyError as e:
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            return {
                "valid": False,
                "error": error_msg,
                "query": query
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "query": query
            }
    
    def get_query_plan(self, query: str) -> Dict[str, Any]:
        """
        Get execution plan for a query without executing it.
        
        Args:
            query: SQL query to analyze
            
        Returns:
            Dictionary containing execution plan
        """
        try:
            # Use EXPLAIN for MySQL execution plans
            plan_query = f"EXPLAIN FORMAT=JSON {query}"
            
            with self.engine.connect() as conn:
                result = conn.execute(text(plan_query))
                plan_rows = result.fetchall()
                
                plan_data = []
                for row in plan_rows:
                    plan_data.append(str(row[0]))
            
            return {
                "success": True,
                "query": query,
                "execution_plan": "\n".join(plan_data),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error getting execution plan: {e}")
            return {
                "success": False,
                "query": query,
                "execution_plan": None,
                "error": str(e)
            }
    
    def get_table_info(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """Get detailed information about a table."""
        try:
            # Build table reference
            if schema:
                full_table_name = f"`{schema}`.`{table_name}`"
                where_clause = f"TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table_name}'"
            else:
                full_table_name = f"`{table_name}`"
                where_clause = f"TABLE_NAME = '{table_name}'"
            
            # Get column information
            columns_query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                ORDINAL_POSITION,
                COLUMN_KEY,
                EXTRA
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE {where_clause}
            ORDER BY ORDINAL_POSITION;
            """
            
            columns_result = self.execute_query(columns_query)
            
            # Get row count
            count_query = f"SELECT COUNT(*) as row_count FROM {full_table_name};"
            count_result = self.execute_query(count_query)
            row_count = count_result["data"][0][0] if count_result["success"] and count_result["data"] else 0
            
            return {
                "success": True,
                "table_name": table_name,
                "schema": schema,
                "columns": columns_result["data"] if columns_result["success"] else [],
                "column_names": columns_result["columns"] if columns_result["success"] else [],
                "row_count": row_count,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            return {
                "success": False,
                "table_name": table_name,
                "schema": schema,
                "error": str(e)
            }
    
    def execute_batch_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute multiple queries in sequence."""
        results = []
        
        for i, query in enumerate(queries):
            logger.info(f"Executing batch query {i+1}/{len(queries)}")
            result = self.execute_query(query)
            results.append(result)
            
            # Stop on first error if desired
            if not result["success"]:
                logger.error(f"Batch execution stopped at query {i+1} due to error")
                break
        
        return results
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        conn = self.engine.connect()
        trans = conn.begin()
        try:
            yield conn
            trans.commit()
        except Exception:
            trans.rollback()
            raise
        finally:
            conn.close()
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


class MySQLQueryBuilder:
    """Helper class for building MySQL-specific queries."""
    
    @staticmethod
    def add_row_limit(query: str, limit: int) -> str:
        """Add row limit to a query using LIMIT clause."""
        query = query.strip()
        query_upper = query.upper()
        
        # If already has LIMIT, don't modify
        if 'LIMIT ' in query_upper:
            return query
        
        # Add LIMIT at the end
        return f"{query} LIMIT {limit}"
    
    @staticmethod
    def add_timeout_hint(query: str, timeout_seconds: int) -> str:
        """Add query timeout hint."""
        # MySQL doesn't have direct query timeout hints like MSSQL
        # This would typically be handled at the connection level
        return query
    
    @staticmethod
    def wrap_with_error_handling(query: str) -> str:
        """Wrap query with basic error handling."""
        # MySQL doesn't have TRY/CATCH blocks like MSSQL
        # Error handling is typically done at the application level
        return query
    
    @staticmethod
    def escape_identifier(identifier: str) -> str:
        """Escape MySQL identifier with backticks."""
        return f"`{identifier}`"
    
    @staticmethod
    def build_connection_string(host: str, port: int, database: str, username: str, password: str = None) -> str:
        """Build MySQL connection string."""
        if password:
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        else:
            return f"mysql+pymysql://{username}@{host}:{port}/{database}"


def main():
    """Test the MySQL adapter."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test MySQL adapter")
    parser.add_argument("--connection", "-c", help="Connection string")
    parser.add_argument("--query", "-q", help="SQL query to execute")
    parser.add_argument("--test", "-t", action="store_true", help="Test connection only")
    parser.add_argument("--table", help="Get table information")
    parser.add_argument("--schema", help="Schema name for table info")
    parser.add_argument("--validate", help="Validate query syntax")
    parser.add_argument("--plan", help="Get execution plan for query")
    
    args = parser.parse_args()
    
    try:
        adapter = MySQLAdapter(connection_string=args.connection)
        
        if args.test:
            success = adapter.test_connection()
            print(f"Connection test: {'SUCCESS' if success else 'FAILED'}")
            return
        
        if args.table:
            info = adapter.get_table_info(args.table, args.schema)
            if info["success"]:
                print(f"Table: {info['table_name']}")
                print(f"Schema: {info['schema']}")
                print(f"Row count: {info['row_count']}")
                print("Columns:")
                for col_data in info["columns"]:
                    print(f"  - {col_data}")
            else:
                print(f"Error: {info['error']}")
            return
        
        if args.validate:
            result = adapter.validate_query_syntax(args.validate)
            print(f"Query validation: {'VALID' if result['valid'] else 'INVALID'}")
            if not result["valid"]:
                print(f"Error: {result['error']}")
            return
        
        if args.plan:
            result = adapter.get_query_plan(args.plan)
            if result["success"]:
                print("Execution Plan:")
                print(result["execution_plan"])
            else:
                print(f"Error: {result['error']}")
            return
        
        if args.query:
            result = adapter.execute_query(args.query)
            if result["success"]:
                print(f"Query executed successfully")
                print(f"Rows returned: {result['row_count']}")
                if result["columns"]:
                    print(f"Columns: {result['columns']}")
                if result["data"]:
                    print("Sample data:")
                    for i, row in enumerate(result["data"][:5]):
                        print(f"  Row {i+1}: {row}")
            else:
                print(f"Query failed: {result['error']}")
        else:
            print("No query specified. Use --query to execute a SQL query.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            adapter.close()
        except:
            pass


if __name__ == "__main__":
    main()
