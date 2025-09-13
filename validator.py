"""SQL validator and sanitizer for security and correctness."""

import re
import sqlparse
from sqlparse import sql, tokens
from typing import Dict, Any, List, Optional, Set, Tuple
from loguru import logger
from enum import Enum


class ValidationLevel(Enum):
    """Validation strictness levels."""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


class SQLValidator:
    """Validate and sanitize SQL queries for security and correctness."""
    
    # Dangerous SQL keywords and patterns
    DANGEROUS_KEYWORDS = {
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE',
        'EXEC', 'EXECUTE', 'SP_', 'XP_', 'OPENROWSET', 'OPENDATASOURCE',
        'BULK', 'BACKUP', 'RESTORE', 'SHUTDOWN', 'RECONFIGURE'
    }
    
    # System tables and schemas to avoid
    SYSTEM_OBJECTS = {
        'sys.', 'information_schema.', 'master.', 'msdb.', 'model.',
        'tempdb.', 'sysadmin', 'serveradmin', 'securityadmin'
    }
    
    # Allowed SQL statement types for read-only operations
    ALLOWED_STATEMENTS = {
        'SELECT', 'WITH'  # Common Table Expressions
    }
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """Initialize SQL validator."""
        self.validation_level = validation_level
        logger.info(f"SQL Validator initialized with {validation_level.value} validation level")
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Comprehensive SQL query validation.
        
        Args:
            query: SQL query to validate
            
        Returns:
            Dictionary containing validation results
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "security_issues": [],
            "suggestions": [],
            "sanitized_query": query,
            "risk_level": "low"
        }
        
        try:
            # Basic syntax validation
            syntax_result = self._validate_syntax(query)
            if not syntax_result["valid"]:
                result["valid"] = False
                result["errors"].extend(syntax_result["errors"])
                return result
            
            # Parse the query
            parsed = sqlparse.parse(query)
            if not parsed:
                result["valid"] = False
                result["errors"].append("Failed to parse SQL query")
                return result
            
            # Security validation
            security_result = self._validate_security(query, parsed[0])
            result["security_issues"].extend(security_result["issues"])
            result["warnings"].extend(security_result["warnings"])
            
            if security_result["risk_level"] == "high":
                result["risk_level"] = "high"
                if self.validation_level == ValidationLevel.STRICT:
                    result["valid"] = False
                    result["errors"].append("High-risk query blocked by strict validation")
            elif security_result["risk_level"] == "medium":
                result["risk_level"] = "medium"
            
            # Statement type validation
            statement_result = self._validate_statement_types(parsed[0])
            if not statement_result["allowed"]:
                result["valid"] = False
                result["errors"].append(f"Statement type not allowed: {statement_result['type']}")
            
            # Structure validation
            structure_result = self._validate_structure(parsed[0])
            result["warnings"].extend(structure_result["warnings"])
            result["suggestions"].extend(structure_result["suggestions"])
            
            # Performance validation
            performance_result = self._validate_performance(parsed[0])
            result["warnings"].extend(performance_result["warnings"])
            result["suggestions"].extend(performance_result["suggestions"])
            
            # Sanitization
            result["sanitized_query"] = self._sanitize_query(query, parsed[0])
            
        except Exception as e:
            logger.error(f"Error validating query: {e}")
            result["valid"] = False
            result["errors"].append(f"Validation error: {str(e)}")
        
        return result
    
    def _validate_syntax(self, query: str) -> Dict[str, Any]:
        """Validate basic SQL syntax."""
        try:
            parsed = sqlparse.parse(query)
            if not parsed:
                return {"valid": False, "errors": ["Empty or invalid SQL query"]}
            
            # Check for basic syntax errors
            errors = []
            
            # Check for unmatched parentheses
            paren_count = query.count('(') - query.count(')')
            if paren_count != 0:
                errors.append(f"Unmatched parentheses (difference: {paren_count})")
            
            # Check for unmatched quotes
            single_quote_count = query.count("'") - query.count("\\'")
            if single_quote_count % 2 != 0:
                errors.append("Unmatched single quotes")
            
            # Check for basic SQL structure
            query_upper = query.upper().strip()
            if not any(query_upper.startswith(stmt) for stmt in ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE']):
                errors.append("Query does not start with a recognized SQL statement")
            
            return {"valid": len(errors) == 0, "errors": errors}
            
        except Exception as e:
            return {"valid": False, "errors": [f"Syntax validation error: {str(e)}"]}
    
    def _validate_security(self, query: str, parsed_query) -> Dict[str, Any]:
        """Validate query for security issues."""
        issues = []
        warnings = []
        risk_level = "low"
        
        query_upper = query.upper()
        
        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in query_upper:
                if keyword in ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']:
                    issues.append(f"Dangerous keyword detected: {keyword}")
                    risk_level = "high"
                elif keyword in ['INSERT', 'UPDATE']:
                    warnings.append(f"Potentially unsafe keyword: {keyword}")
                    risk_level = "medium"
                else:
                    issues.append(f"Potentially dangerous keyword: {keyword}")
                    risk_level = "medium"
        
        # Check for system object access
        for sys_obj in self.SYSTEM_OBJECTS:
            if sys_obj.lower() in query.lower():
                issues.append(f"Access to system object: {sys_obj}")
                risk_level = "high"
        
        # Check for SQL injection patterns
        injection_patterns = [
            r";\s*--",  # Comment injection
            r"union\s+select",  # Union-based injection
            r"'\s*or\s+'.*'='",  # Classic SQL injection
            r"'\s*or\s+1\s*=\s*1",  # Tautology injection
            r"exec\s*\(",  # Dynamic SQL execution
            r"char\s*\(",  # Character-based obfuscation
            r"cast\s*\(",  # Type casting attacks
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                issues.append(f"Potential SQL injection pattern detected: {pattern}")
                risk_level = "high"
        
        # Check for excessive wildcards
        if query.count('*') > 3:
            warnings.append("Excessive use of wildcards (*) may impact performance")
        
        # Check for missing WHERE clause in potentially destructive operations
        if any(keyword in query_upper for keyword in ['UPDATE', 'DELETE']) and 'WHERE' not in query_upper:
            issues.append("UPDATE/DELETE without WHERE clause is dangerous")
            risk_level = "high"
        
        return {
            "issues": issues,
            "warnings": warnings,
            "risk_level": risk_level
        }
    
    def _validate_statement_types(self, parsed_query) -> Dict[str, Any]:
        """Validate that only allowed statement types are used."""
        statement_type = None
        
        # Extract the first meaningful token
        for token in parsed_query.flatten():
            if token.ttype is tokens.Keyword and token.value.upper() in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'WITH']:
                statement_type = token.value.upper()
                break
        
        if not statement_type:
            return {"allowed": False, "type": "unknown"}
        
        # Check if statement type is allowed
        allowed = statement_type in self.ALLOWED_STATEMENTS
        
        return {
            "allowed": allowed,
            "type": statement_type
        }
    
    def _validate_structure(self, parsed_query) -> Dict[str, Any]:
        """Validate query structure and provide suggestions."""
        warnings = []
        suggestions = []
        
        query_str = str(parsed_query).upper()
        
        # Check for potential issues
        if 'SELECT *' in query_str:
            suggestions.append("Consider specifying column names instead of using SELECT *")
        
        if 'ORDER BY' not in query_str and 'GROUP BY' in query_str:
            suggestions.append("Consider adding ORDER BY for consistent results with GROUP BY")
        
        if query_str.count('JOIN') > 5:
            warnings.append("Query has many joins, consider breaking into smaller queries")
        
        if 'LIKE' in query_str and query_str.count('%') > 3:
            warnings.append("Multiple LIKE operations with wildcards may be slow")
        
        # Check for proper aliasing
        if ' JOIN ' in query_str and ' AS ' not in query_str:
            suggestions.append("Consider using table aliases for better readability")
        
        return {
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    def _validate_performance(self, parsed_query) -> Dict[str, Any]:
        """Validate query for performance issues."""
        warnings = []
        suggestions = []
        
        query_str = str(parsed_query).upper()
        
        # Check for performance anti-patterns
        if 'SELECT *' in query_str:
            warnings.append("SELECT * can impact performance, specify needed columns")
        
        if 'LIKE' in query_str and "'%'" in query_str.replace("'%", "").replace("%'", ""):
            warnings.append("Leading wildcard in LIKE clause prevents index usage")
        
        if 'ORDER BY' in query_str and 'LIMIT' not in query_str and 'TOP' not in query_str:
            suggestions.append("Consider adding TOP/LIMIT clause with ORDER BY for better performance")
        
        if query_str.count('OR') > 3:
            suggestions.append("Multiple OR conditions may benefit from UNION or IN clause")
        
        if 'NOT IN' in query_str:
            suggestions.append("NOT IN with NULL values can cause unexpected results, consider NOT EXISTS")
        
        # Check for functions in WHERE clause
        function_patterns = [
            'UPPER(', 'LOWER(', 'SUBSTRING(', 'CONVERT(', 'CAST('
        ]
        
        for pattern in function_patterns:
            if pattern in query_str and 'WHERE' in query_str:
                warnings.append(f"Function {pattern} in WHERE clause may prevent index usage")
        
        return {
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    def _sanitize_query(self, query: str, parsed_query) -> str:
        """Sanitize the query by removing or escaping dangerous elements."""
        sanitized = query
        
        # Remove comments (potential injection vector)
        sanitized = re.sub(r'--.*$', '', sanitized, flags=re.MULTILINE)
        sanitized = re.sub(r'/\*.*?\*/', '', sanitized, flags=re.DOTALL)
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Ensure query ends with semicolon
        if not sanitized.endswith(';'):
            sanitized += ';'
        
        return sanitized
    
    def check_column_references(self, query: str, available_columns: Set[str]) -> Dict[str, Any]:
        """Check if all referenced columns exist in the schema."""
        try:
            parsed = sqlparse.parse(query)[0]
            referenced_columns = set()
            
            # Extract column references (simplified approach)
            for token in parsed.flatten():
                if token.ttype is None and '.' in str(token):
                    # Likely a table.column reference
                    parts = str(token).split('.')
                    if len(parts) == 2:
                        referenced_columns.add(parts[1].strip('[]'))
            
            # Find missing columns
            missing_columns = referenced_columns - available_columns
            
            return {
                "valid": len(missing_columns) == 0,
                "referenced_columns": list(referenced_columns),
                "missing_columns": list(missing_columns),
                "available_columns": list(available_columns)
            }
            
        except Exception as e:
            logger.error(f"Error checking column references: {e}")
            return {
                "valid": False,
                "error": str(e),
                "referenced_columns": [],
                "missing_columns": [],
                "available_columns": list(available_columns)
            }
    
    def format_query(self, query: str) -> str:
        """Format SQL query for better readability."""
        try:
            formatted = sqlparse.format(
                query,
                reindent=True,
                keyword_case='upper',
                identifier_case='lower',
                strip_comments=False,
                use_space_around_operators=True
            )
            return formatted
        except Exception as e:
            logger.warning(f"Error formatting query: {e}")
            return query
    
    def get_query_complexity_score(self, query: str) -> Dict[str, Any]:
        """Calculate a complexity score for the query."""
        try:
            parsed = sqlparse.parse(query)[0]
            query_upper = query.upper()
            
            complexity_score = 0
            factors = {}
            
            # Count different complexity factors
            factors['joins'] = query_upper.count('JOIN')
            factors['subqueries'] = query_upper.count('SELECT') - 1  # Subtract main SELECT
            factors['unions'] = query_upper.count('UNION')
            factors['aggregations'] = sum(query_upper.count(func) for func in ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN('])
            factors['conditions'] = query_upper.count('WHERE') + query_upper.count('HAVING')
            factors['case_statements'] = query_upper.count('CASE')
            factors['window_functions'] = query_upper.count('OVER(')
            
            # Calculate weighted score
            weights = {
                'joins': 2,
                'subqueries': 3,
                'unions': 2,
                'aggregations': 1,
                'conditions': 1,
                'case_statements': 2,
                'window_functions': 3
            }
            
            for factor, count in factors.items():
                complexity_score += count * weights.get(factor, 1)
            
            # Determine complexity level
            if complexity_score <= 5:
                level = "simple"
            elif complexity_score <= 15:
                level = "moderate"
            elif complexity_score <= 30:
                level = "complex"
            else:
                level = "very_complex"
            
            return {
                "complexity_score": complexity_score,
                "complexity_level": level,
                "factors": factors
            }
            
        except Exception as e:
            logger.error(f"Error calculating complexity score: {e}")
            return {
                "complexity_score": 0,
                "complexity_level": "unknown",
                "factors": {},
                "error": str(e)
            }


def main():
    """Test the SQL validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test SQL validator")
    parser.add_argument("query", help="SQL query to validate")
    parser.add_argument("--level", choices=["basic", "standard", "strict"], 
                       default="standard", help="Validation level")
    parser.add_argument("--format", action="store_true", help="Format the query")
    parser.add_argument("--complexity", action="store_true", help="Show complexity score")
    
    args = parser.parse_args()
    
    validator = SQLValidator(ValidationLevel(args.level))
    
    # Validate query
    result = validator.validate_query(args.query)
    
    print(f"Query validation: {'PASSED' if result['valid'] else 'FAILED'}")
    print(f"Risk level: {result['risk_level']}")
    
    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  - {error}")
    
    if result["warnings"]:
        print("\nWarnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")
    
    if result["security_issues"]:
        print("\nSecurity Issues:")
        for issue in result["security_issues"]:
            print(f"  - {issue}")
    
    if result["suggestions"]:
        print("\nSuggestions:")
        for suggestion in result["suggestions"]:
            print(f"  - {suggestion}")
    
    if args.format:
        print(f"\nFormatted Query:\n{validator.format_query(args.query)}")
    
    if args.complexity:
        complexity = validator.get_query_complexity_score(args.query)
        print(f"\nComplexity Analysis:")
        print(f"  Score: {complexity['complexity_score']}")
        print(f"  Level: {complexity['complexity_level']}")
        print(f"  Factors: {complexity['factors']}")


if __name__ == "__main__":
    main()
