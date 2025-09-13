"""SQL optimizer for improving query performance and formatting."""

import re
import sqlparse
from sqlparse import sql, tokens
from typing import Dict, Any, List, Optional, Tuple, Set
from loguru import logger
from enum import Enum


class OptimizationLevel(Enum):
    """Optimization levels."""
    BASIC = "basic"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"


class SQLOptimizer:
    """Optimize SQL queries for better performance and readability."""
    
    def __init__(self, optimization_level: OptimizationLevel = OptimizationLevel.STANDARD):
        """Initialize SQL optimizer."""
        self.optimization_level = optimization_level
        logger.info(f"SQL Optimizer initialized with {optimization_level.value} optimization level")
    
    def optimize_query(self, query: str, schema_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize SQL query for better performance.
        
        Args:
            query: Original SQL query
            schema_info: Optional schema information for better optimization
            
        Returns:
            Dictionary containing optimization results
        """
        result = {
            "original_query": query,
            "optimized_query": query,
            "optimizations_applied": [],
            "performance_improvements": [],
            "warnings": [],
            "estimated_improvement": 0
        }
        
        try:
            # Parse the query
            parsed = sqlparse.parse(query)
            if not parsed:
                result["warnings"].append("Failed to parse query for optimization")
                return result
            
            optimized_query = query
            applied_optimizations = []
            
            # Apply different optimization techniques
            optimizations = [
                self._optimize_select_star,
                self._optimize_joins,
                self._optimize_where_clauses,
                self._optimize_subqueries,
                self._optimize_aggregations,
                self._optimize_ordering,
                self._optimize_case_statements,
                self._add_query_hints,
                self._optimize_in_clauses,
                self._optimize_exists_clauses
            ]
            
            for optimization_func in optimizations:
                try:
                    opt_result = optimization_func(optimized_query, schema_info)
                    if opt_result["modified"]:
                        optimized_query = opt_result["query"]
                        applied_optimizations.append(opt_result["optimization"])
                        result["performance_improvements"].extend(opt_result.get("improvements", []))
                except Exception as e:
                    logger.warning(f"Optimization step failed: {e}")
            
            # Format the final query
            result["optimized_query"] = self.format_query(optimized_query)
            result["optimizations_applied"] = applied_optimizations
            
            # Estimate improvement
            result["estimated_improvement"] = self._estimate_performance_improvement(
                query, result["optimized_query"], applied_optimizations
            )
            
        except Exception as e:
            logger.error(f"Error optimizing query: {e}")
            result["warnings"].append(f"Optimization error: {str(e)}")
        
        return result
    
    def _optimize_select_star(self, query: str, schema_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Optimize SELECT * statements."""
        if 'SELECT *' not in query.upper():
            return {"modified": False, "query": query}
        
        # If we have schema info, we could replace * with actual column names
        # For now, just add a warning and suggest improvement
        improvements = ["Consider specifying column names instead of SELECT * for better performance"]
        
        # In aggressive mode, try to replace SELECT * if we have schema info
        if (self.optimization_level == OptimizationLevel.AGGRESSIVE and 
            schema_info and 'tables' in schema_info):
            
            # This is a simplified implementation
            # In practice, you'd need to analyze the FROM clause to determine which table's columns to use
            return {
                "modified": False,  # Don't modify for now due to complexity
                "query": query,
                "optimization": "SELECT * analysis",
                "improvements": improvements
            }
        
        return {
            "modified": False,
            "query": query,
            "optimization": "SELECT * analysis",
            "improvements": improvements
        }
    
    def _optimize_joins(self, query: str, schema_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Optimize JOIN operations."""
        query_upper = query.upper()
        improvements = []
        modified = False
        optimized_query = query
        
        # Replace INNER JOIN with just JOIN for cleaner syntax
        if 'INNER JOIN' in query_upper:
            optimized_query = re.sub(r'\bINNER\s+JOIN\b', 'JOIN', optimized_query, flags=re.IGNORECASE)
            improvements.append("Simplified INNER JOIN to JOIN")
            modified = True
        
        # Suggest moving smaller tables to the left in joins
        if query_upper.count('JOIN') > 2:
            improvements.append("Consider ordering joins with smaller tables first")
        
        # Check for potential Cartesian products
        if 'JOIN' in query_upper and 'ON' not in query_upper and 'WHERE' not in query_upper:
            improvements.append("Warning: Potential Cartesian product detected - ensure proper join conditions")
        
        return {
            "modified": modified,
            "query": optimized_query,
            "optimization": "JOIN optimization",
            "improvements": improvements
        }
    
    def _optimize_where_clauses(self, query: str, schema_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Optimize WHERE clause conditions."""
        improvements = []
        modified = False
        optimized_query = query
        
        # Move most selective conditions first (if we can identify them)
        # This is a simplified heuristic
        if 'WHERE' in query.upper():
            improvements.append("Ensure most selective conditions are placed first in WHERE clause")
        
        # Optimize LIKE patterns
        like_pattern = r"LIKE\s+'%([^%]+)%'"
        if re.search(like_pattern, query, re.IGNORECASE):
            improvements.append("Consider using full-text search for LIKE patterns with leading wildcards")
        
        # Optimize IS NULL checks
        if 'IS NULL' in query.upper() and 'OR' in query.upper():
            improvements.append("Consider using ISNULL() or COALESCE() for better performance with NULL checks")
        
        return {
            "modified": modified,
            "query": optimized_query,
            "optimization": "WHERE clause optimization",
            "improvements": improvements
        }
    
    def _optimize_subqueries(self, query: str, schema_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Optimize subqueries by converting to JOINs where possible."""
        improvements = []
        modified = False
        optimized_query = query
        
        # Count subqueries
        subquery_count = query.upper().count('SELECT') - 1
        
        if subquery_count > 0:
            # Look for correlated subqueries that could be JOINs
            if 'EXISTS' in query.upper():
                improvements.append("EXISTS subqueries are generally well-optimized")
            elif 'IN (' in query.upper() and 'SELECT' in query.upper():
                improvements.append("Consider converting IN subqueries to JOINs for better performance")
            
            # Look for scalar subqueries in SELECT
            scalar_subquery_pattern = r'SELECT\s+[^,]*\(\s*SELECT\s+'
            if re.search(scalar_subquery_pattern, query, re.IGNORECASE):
                improvements.append("Consider converting scalar subqueries to LEFT JOINs")
        
        return {
            "modified": modified,
            "query": optimized_query,
            "optimization": "Subquery optimization",
            "improvements": improvements
        }
    
    def _optimize_aggregations(self, query: str, schema_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Optimize aggregate functions and GROUP BY clauses."""
        improvements = []
        modified = False
        optimized_query = query
        
        query_upper = query.upper()
        
        # Check for GROUP BY with ORDER BY
        if 'GROUP BY' in query_upper and 'ORDER BY' not in query_upper:
            improvements.append("Consider adding ORDER BY for consistent results with GROUP BY")
        
        # Check for COUNT(*) vs COUNT(column)
        if 'COUNT(*)' in query_upper:
            improvements.append("COUNT(*) is generally efficient, but COUNT(column) can be faster if column is indexed")
        
        # Check for DISTINCT in aggregates
        if 'COUNT(DISTINCT' in query_upper:
            improvements.append("COUNT(DISTINCT) can be expensive on large datasets")
        
        # Optimize HAVING clauses
        if 'HAVING' in query_upper:
            improvements.append("Ensure HAVING conditions can't be moved to WHERE clause for better performance")
        
        return {
            "modified": modified,
            "query": optimized_query,
            "optimization": "Aggregation optimization",
            "improvements": improvements
        }
    
    def _optimize_ordering(self, query: str, schema_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Optimize ORDER BY clauses."""
        improvements = []
        modified = False
        optimized_query = query
        
        query_upper = query.upper()
        
        if 'ORDER BY' in query_upper:
            # Check if TOP/LIMIT is used with ORDER BY
            if 'TOP ' not in query_upper and 'LIMIT ' not in query_upper:
                improvements.append("Consider adding TOP clause if you don't need all results")
            
            # Check for ordering by functions
            if any(func in query_upper for func in ['UPPER(', 'LOWER(', 'SUBSTRING(']):
                improvements.append("Avoid functions in ORDER BY clause - consider computed columns or indexes")
            
            # Check for multiple ORDER BY columns
            order_by_cols = query_upper.split('ORDER BY')[1].split('GROUP BY')[0] if 'GROUP BY' in query_upper else query_upper.split('ORDER BY')[1]
            if order_by_cols.count(',') > 2:
                improvements.append("Multiple ORDER BY columns may impact performance")
        
        return {
            "modified": modified,
            "query": optimized_query,
            "optimization": "ORDER BY optimization",
            "improvements": improvements
        }
    
    def _optimize_case_statements(self, query: str, schema_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Optimize CASE statements."""
        improvements = []
        modified = False
        optimized_query = query
        
        case_count = query.upper().count('CASE')
        if case_count > 0:
            improvements.append("Consider ordering CASE conditions by frequency of occurrence")
            
            if case_count > 3:
                improvements.append("Multiple CASE statements may benefit from lookup tables")
        
        return {
            "modified": modified,
            "query": optimized_query,
            "optimization": "CASE statement optimization",
            "improvements": improvements
        }
    
    def _add_query_hints(self, query: str, schema_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add query hints for MSSQL optimization."""
        improvements = []
        modified = False
        optimized_query = query
        
        if self.optimization_level == OptimizationLevel.AGGRESSIVE:
            # Only add hints in aggressive mode and if not already present
            if 'WITH (' not in query.upper() and 'OPTION (' not in query.upper():
                # Add basic query hints
                if 'JOIN' in query.upper():
                    improvements.append("Consider adding query hints like OPTION (HASH JOIN) for complex queries")
                
                if 'ORDER BY' in query.upper() and 'TOP' in query.upper():
                    improvements.append("Consider OPTION (FAST N) hint for queries with TOP and ORDER BY")
        
        return {
            "modified": modified,
            "query": optimized_query,
            "optimization": "Query hints",
            "improvements": improvements
        }
    
    def _optimize_in_clauses(self, query: str, schema_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Optimize IN clauses."""
        improvements = []
        modified = False
        optimized_query = query
        
        # Look for IN clauses with many values
        in_matches = re.findall(r'IN\s*\([^)]+\)', query, re.IGNORECASE)
        for match in in_matches:
            value_count = match.count(',') + 1
            if value_count > 10:
                improvements.append(f"IN clause with {value_count} values - consider using temporary table or table-valued parameter")
        
        # Look for NOT IN with potential NULL issues
        if 'NOT IN' in query.upper():
            improvements.append("NOT IN with NULL values can cause unexpected results - consider NOT EXISTS")
        
        return {
            "modified": modified,
            "query": optimized_query,
            "optimization": "IN clause optimization",
            "improvements": improvements
        }
    
    def _optimize_exists_clauses(self, query: str, schema_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Optimize EXISTS clauses."""
        improvements = []
        modified = False
        optimized_query = query
        
        if 'EXISTS' in query.upper():
            improvements.append("EXISTS clauses are generally well-optimized")
            
            # Check if EXISTS subquery uses SELECT *
            exists_pattern = r'EXISTS\s*\(\s*SELECT\s+\*'
            if re.search(exists_pattern, query, re.IGNORECASE):
                # Replace SELECT * with SELECT 1 in EXISTS
                optimized_query = re.sub(
                    r'(EXISTS\s*\(\s*)SELECT\s+\*',
                    r'\1SELECT 1',
                    optimized_query,
                    flags=re.IGNORECASE
                )
                improvements.append("Replaced SELECT * with SELECT 1 in EXISTS clause")
                modified = True
        
        return {
            "modified": modified,
            "query": optimized_query,
            "optimization": "EXISTS clause optimization",
            "improvements": improvements
        }
    
    def _estimate_performance_improvement(
        self, 
        original_query: str, 
        optimized_query: str, 
        optimizations: List[str]
    ) -> int:
        """Estimate performance improvement percentage."""
        # Simple heuristic-based estimation
        improvement_score = 0
        
        # Score based on optimizations applied
        optimization_scores = {
            "JOIN optimization": 5,
            "WHERE clause optimization": 10,
            "Subquery optimization": 15,
            "EXISTS clause optimization": 8,
            "IN clause optimization": 12,
            "Aggregation optimization": 7,
            "ORDER BY optimization": 5,
            "CASE statement optimization": 3,
            "Query hints": 10
        }
        
        for opt in optimizations:
            improvement_score += optimization_scores.get(opt, 2)
        
        # Cap at 50% estimated improvement
        return min(improvement_score, 50)
    
    def format_query(self, query: str) -> str:
        """Format SQL query for better readability."""
        try:
            formatted = sqlparse.format(
                query,
                reindent=True,
                keyword_case='upper',
                identifier_case='lower',
                strip_comments=False,
                use_space_around_operators=True,
                wrap_after=80,
                comma_first=False
            )
            return formatted
        except Exception as e:
            logger.warning(f"Error formatting query: {e}")
            return query
    
    def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """Analyze query for potential performance issues."""
        analysis = {
            "performance_score": 100,  # Start with perfect score
            "issues": [],
            "recommendations": [],
            "complexity_factors": {}
        }
        
        query_upper = query.upper()
        
        # Analyze different performance factors
        factors = {
            'select_star': 'SELECT *' in query_upper,
            'no_where': 'WHERE' not in query_upper and any(stmt in query_upper for stmt in ['UPDATE', 'DELETE']),
            'cartesian_join': 'JOIN' in query_upper and 'ON' not in query_upper,
            'leading_wildcard': re.search(r"LIKE\s+'%", query, re.IGNORECASE) is not None,
            'function_in_where': any(f in query_upper.split('WHERE')[1] if 'WHERE' in query_upper else '' 
                                   for f in ['UPPER(', 'LOWER(', 'SUBSTRING(']),
            'not_in_clause': 'NOT IN' in query_upper,
            'multiple_or': query_upper.count(' OR ') > 3,
            'subquery_count': query_upper.count('SELECT') - 1,
            'join_count': query_upper.count('JOIN')
        }
        
        analysis['complexity_factors'] = factors
        
        # Score deductions and recommendations
        if factors['select_star']:
            analysis['performance_score'] -= 10
            analysis['issues'].append("SELECT * reduces performance")
            analysis['recommendations'].append("Specify only needed columns")
        
        if factors['no_where']:
            analysis['performance_score'] -= 30
            analysis['issues'].append("UPDATE/DELETE without WHERE is dangerous and slow")
            analysis['recommendations'].append("Add appropriate WHERE clause")
        
        if factors['cartesian_join']:
            analysis['performance_score'] -= 40
            analysis['issues'].append("Potential Cartesian product")
            analysis['recommendations'].append("Add proper JOIN conditions")
        
        if factors['leading_wildcard']:
            analysis['performance_score'] -= 15
            analysis['issues'].append("Leading wildcard in LIKE prevents index usage")
            analysis['recommendations'].append("Avoid leading wildcards or use full-text search")
        
        if factors['function_in_where']:
            analysis['performance_score'] -= 12
            analysis['issues'].append("Functions in WHERE clause prevent index usage")
            analysis['recommendations'].append("Create computed columns or function-based indexes")
        
        if factors['not_in_clause']:
            analysis['performance_score'] -= 8
            analysis['issues'].append("NOT IN can cause issues with NULL values")
            analysis['recommendations'].append("Use NOT EXISTS instead")
        
        if factors['multiple_or']:
            analysis['performance_score'] -= 10
            analysis['issues'].append("Multiple OR conditions can be slow")
            analysis['recommendations'].append("Consider using UNION or IN clause")
        
        if factors['subquery_count'] > 2:
            analysis['performance_score'] -= factors['subquery_count'] * 5
            analysis['issues'].append(f"Multiple subqueries ({factors['subquery_count']}) may impact performance")
            analysis['recommendations'].append("Consider converting subqueries to JOINs")
        
        if factors['join_count'] > 5:
            analysis['performance_score'] -= (factors['join_count'] - 5) * 3
            analysis['issues'].append(f"Many JOINs ({factors['join_count']}) increase complexity")
            analysis['recommendations'].append("Consider breaking into smaller queries or using temp tables")
        
        # Ensure score doesn't go below 0
        analysis['performance_score'] = max(0, analysis['performance_score'])
        
        return analysis
    
    def suggest_indexes(self, query: str, schema_info: Optional[Dict[str, Any]] = None) -> List[str]:
        """Suggest indexes that might improve query performance."""
        suggestions = []
        
        try:
            # Extract table and column references
            parsed = sqlparse.parse(query)[0]
            
            # Look for WHERE clause columns
            where_columns = self._extract_where_columns(query)
            for col in where_columns:
                suggestions.append(f"Consider index on {col} for WHERE clause optimization")
            
            # Look for JOIN columns
            join_columns = self._extract_join_columns(query)
            for col in join_columns:
                suggestions.append(f"Consider index on {col} for JOIN optimization")
            
            # Look for ORDER BY columns
            order_columns = self._extract_order_by_columns(query)
            for col in order_columns:
                suggestions.append(f"Consider index on {col} for ORDER BY optimization")
            
        except Exception as e:
            logger.warning(f"Error suggesting indexes: {e}")
        
        return suggestions
    
    def _extract_where_columns(self, query: str) -> List[str]:
        """Extract column names from WHERE clause."""
        columns = []
        try:
            # Simple pattern matching for WHERE conditions
            where_pattern = r'WHERE\s+([^=<>!]+)[=<>!]'
            matches = re.findall(where_pattern, query, re.IGNORECASE)
            for match in matches:
                col = match.strip()
                if '.' in col:
                    col = col.split('.')[-1]
                columns.append(col)
        except Exception:
            pass
        return columns
    
    def _extract_join_columns(self, query: str) -> List[str]:
        """Extract column names from JOIN conditions."""
        columns = []
        try:
            # Pattern for JOIN ... ON conditions
            join_pattern = r'JOIN\s+\w+\s+\w*\s*ON\s+([^=]+)=([^=]+)'
            matches = re.findall(join_pattern, query, re.IGNORECASE)
            for left, right in matches:
                for col in [left.strip(), right.strip()]:
                    if '.' in col:
                        col = col.split('.')[-1]
                    columns.append(col)
        except Exception:
            pass
        return columns
    
    def _extract_order_by_columns(self, query: str) -> List[str]:
        """Extract column names from ORDER BY clause."""
        columns = []
        try:
            order_pattern = r'ORDER\s+BY\s+([^;]+)'
            match = re.search(order_pattern, query, re.IGNORECASE)
            if match:
                order_clause = match.group(1)
                for col in order_clause.split(','):
                    col = col.strip().split()[0]  # Remove ASC/DESC
                    if '.' in col:
                        col = col.split('.')[-1]
                    columns.append(col)
        except Exception:
            pass
        return columns


def main():
    """Test the SQL optimizer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test SQL optimizer")
    parser.add_argument("query", help="SQL query to optimize")
    parser.add_argument("--level", choices=["basic", "standard", "aggressive"], 
                       default="standard", help="Optimization level")
    parser.add_argument("--analyze", action="store_true", help="Analyze performance")
    parser.add_argument("--indexes", action="store_true", help="Suggest indexes")
    parser.add_argument("--format", action="store_true", help="Format query only")
    
    args = parser.parse_args()
    
    optimizer = SQLOptimizer(OptimizationLevel(args.level))
    
    if args.format:
        formatted = optimizer.format_query(args.query)
        print("Formatted Query:")
        print(formatted)
        return
    
    if args.analyze:
        analysis = optimizer.analyze_query_performance(args.query)
        print(f"Performance Analysis:")
        print(f"  Score: {analysis['performance_score']}/100")
        if analysis['issues']:
            print("  Issues:")
            for issue in analysis['issues']:
                print(f"    - {issue}")
        if analysis['recommendations']:
            print("  Recommendations:")
            for rec in analysis['recommendations']:
                print(f"    - {rec}")
        return
    
    if args.indexes:
        suggestions = optimizer.suggest_indexes(args.query)
        print("Index Suggestions:")
        for suggestion in suggestions:
            print(f"  - {suggestion}")
        return
    
    # Full optimization
    result = optimizer.optimize_query(args.query)
    
    print("Optimization Results:")
    print(f"  Estimated improvement: {result['estimated_improvement']}%")
    print(f"  Optimizations applied: {len(result['optimizations_applied'])}")
    
    if result['optimizations_applied']:
        print("  Applied optimizations:")
        for opt in result['optimizations_applied']:
            print(f"    - {opt}")
    
    if result['performance_improvements']:
        print("  Performance improvements:")
        for imp in result['performance_improvements']:
            print(f"    - {imp}")
    
    print(f"\nOptimized Query:\n{result['optimized_query']}")


if __name__ == "__main__":
    main()
