"""Prompt templates for LLM-based SQL generation."""

from typing import Dict, Any, List, Optional
from datetime import datetime


class PromptTemplates:
    """Collection of prompt templates for different SQL generation scenarios."""
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get the system prompt that defines the AI's role and behavior."""
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

KEY RELATIONSHIPS:
- Identity to Accounts: spt_identity.id → spt_link.identity_id (one person, many accounts)
- Accounts to Apps: spt_application.id → spt_link.application (one app, many accounts)
- Manager Hierarchy: spt_identity.manager → spt_identity.id (self-reference)

CRITICAL: ENTITLEMENT/PERMISSION STORAGE:
IdentityIQ stores entitlements/permissions in spt_link.attributes and spt_link.entitlements as structured data
ALWAYS search BOTH l.attributes AND l.entitlements using LIKE operator!

PROVEN QUERY PATTERNS:

1. Show identities who have accounts on Workday:
   SELECT DISTINCT i.firstname, i.lastname, i.display_name, i.email FROM spt_identity i JOIN spt_link l ON i.id = l.identity_id JOIN spt_application app ON l.application = app.id WHERE app.name = 'Workday' ORDER BY i.lastname

2. Find identities with accounts on multiple specific applications:
   SELECT i.firstname, i.lastname, i.display_name, i.email FROM spt_identity i WHERE i.id IN (SELECT l.identity_id FROM spt_link l JOIN spt_application app ON l.application = app.id WHERE app.name IN ('Workday', 'Active Directory', 'SAP') GROUP BY l.identity_id HAVING COUNT(DISTINCT app.name) = 3) ORDER BY i.lastname

3. Show identities who have PayrollAnalysis group in Finance application:
   SELECT DISTINCT i.firstname, i.lastname, i.display_name, i.email FROM spt_identity i JOIN spt_link l ON i.id = l.identity_id JOIN spt_application app ON l.application = app.id WHERE app.name = 'Finance' AND (l.attributes LIKE '%PayrollAnalysis%' OR l.entitlements LIKE '%PayrollAnalysis%') ORDER BY i.lastname

4. Complex: identities with accounts on multiple apps AND specific entitlements in DIFFERENT apps:
   SELECT DISTINCT i.firstname, i.lastname, i.display_name, i.email, mgr.display_name as manager_name 
   FROM spt_identity i 
   LEFT JOIN spt_identity mgr ON i.manager = mgr.id 
   WHERE i.id IN (
       SELECT l.identity_id FROM spt_link l JOIN spt_application app ON l.application = app.id 
       WHERE app.name IN ('Workday', 'Trakk', 'Finance', 'Apache DS') 
       GROUP BY l.identity_id HAVING COUNT(DISTINCT app.name) = 4
   ) 
   AND i.id IN (
       SELECT l.identity_id FROM spt_link l JOIN spt_application app ON l.application = app.id 
       WHERE app.name = 'Trakk' AND (l.attributes LIKE '%TimeSheetEnterAuthority%' OR l.entitlements LIKE '%TimeSheetEnterAuthority%')
   ) 
   AND i.id IN (
       SELECT l.identity_id FROM spt_link l JOIN spt_application app ON l.application = app.id 
       WHERE app.name = 'Finance' AND (l.attributes LIKE '%PayrollAnalysis%' OR l.entitlements LIKE '%PayrollAnalysis%')
   ) 
   ORDER BY i.lastname

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

    @staticmethod
    def get_main_prompt_template() -> str:
        """Get the main prompt template for SQL generation."""
        return """Based on the following IdentityIQ database schema and natural language query, generate an optimized MySQL query for SailPoint IdentityIQ.

DATABASE SCHEMA:
{schema_context}

NATURAL LANGUAGE QUERY:
{user_query}

ADDITIONAL CONTEXT:
- Current date/time: {current_datetime}
- Database type: Microsoft SQL Server
- Generate optimized query with proper joins, indexes, and performance considerations

SQL QUERY:"""

    @staticmethod
    def get_schema_analysis_prompt() -> str:
        """Get prompt for analyzing which tables/columns are most relevant."""
        return """Analyze the following natural language query and identify the most relevant database tables and columns needed to answer it.

QUERY: {user_query}

AVAILABLE SCHEMA:
{schema_context}

Please identify:
1. Primary tables needed
2. Key columns for filtering, grouping, or selection
3. Relationships between tables
4. Any date/time considerations
5. Aggregation requirements

Format your response as a structured analysis."""

    @staticmethod
    def get_query_optimization_prompt() -> str:
        """Get prompt for optimizing an existing SQL query."""
        return """Optimize the following MSSQL query for better performance while maintaining the same result set.

ORIGINAL QUERY:
{original_query}

SCHEMA CONTEXT:
{schema_context}

Consider:
1. Index usage and query execution plan
2. Join optimization
3. WHERE clause positioning
4. Subquery vs JOIN performance
5. Appropriate use of window functions
6. Elimination of unnecessary operations

OPTIMIZED QUERY:"""

    @staticmethod
    def get_query_explanation_prompt() -> str:
        """Get prompt for explaining what a SQL query does."""
        return """Explain what the following MSSQL query does in plain English.

SQL QUERY:
{sql_query}

SCHEMA CONTEXT:
{schema_context}

Provide a clear, non-technical explanation of:
1. What data the query retrieves
2. How it filters or processes the data
3. What the final result represents
4. Any important business logic implemented

EXPLANATION:"""

    @staticmethod
    def get_query_validation_prompt() -> str:
        """Get prompt for validating SQL query syntax and logic."""
        return """Validate the following MSSQL query for syntax errors, logical issues, and potential improvements.

SQL QUERY:
{sql_query}

SCHEMA CONTEXT:
{schema_context}

Check for:
1. Syntax errors
2. Invalid table/column references
3. Logic errors or potential issues
4. Performance concerns
5. Security considerations (SQL injection risks)

VALIDATION RESULT:"""

    @staticmethod
    def format_schema_context(self, retrieved_schema: Dict[str, Any]) -> str:
        """Format retrieved schema information for use in prompts."""
        context_parts = []
        
        tables = retrieved_schema.get("tables", {})
        if tables:
            for table_name, table_info in tables.items():
                context_parts.append(f"Table: {table_name}")
                
                # Add table structure
                columns = table_info.get("columns", [])
                if columns:
                    context_parts.append("Columns:")
                    for col in columns:
                        col_info = f"  - {col['name']} ({col['data_type']})"
                        context_parts.append(col_info)
                
                context_parts.append("")  # Empty line between tables
        
        # Add relationships
        relationships = retrieved_schema.get("relationships", [])
        if relationships:
            context_parts.append("Relationships:")
            for rel in relationships:
                from_table = rel.get("from_table", "")
                to_table = rel.get("to_table", "")
                from_cols = ", ".join(rel.get("from_columns", []))
                to_cols = ", ".join(rel.get("to_columns", []))
                rel_info = f"  {from_table}({from_cols}) -> {to_table}({to_cols})"
                context_parts.append(rel_info)
        
        return "\n".join(context_parts)

    @staticmethod
    def build_sql_generation_prompt(
        user_query: str,
        schema_context: str,
        include_examples: bool = False,
        additional_context: Optional[str] = None
    ) -> str:
        """Build the complete prompt for SQL generation."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Base prompt
        prompt = PromptTemplates.get_main_prompt_template().format(
            schema_context=schema_context,
            user_query=user_query,
            current_datetime=current_time
        )
        
        # Add examples if requested
        if include_examples:
            examples = PromptTemplates.get_few_shot_examples()
            prompt = f"{examples}\n\n{prompt}"
        
        # Add additional context if provided
        if additional_context:
            prompt = f"{prompt}\n\nADDITIONAL CONTEXT:\n{additional_context}\n\nSQL QUERY:"
        
        return prompt

    @staticmethod
    def get_few_shot_examples() -> str:
        """Get few-shot examples for better SQL generation."""
        return """Here are some examples of natural language queries converted to MSSQL:

EXAMPLE 1:
Query: "Show me all customers who placed orders in the last 30 days"
Schema: Customers (CustomerID, Name, Email), Orders (OrderID, CustomerID, OrderDate)
SQL: SELECT DISTINCT c.CustomerID, c.Name, c.Email 
     FROM Customers c 
     INNER JOIN Orders o ON c.CustomerID = o.CustomerID 
     WHERE o.OrderDate >= DATEADD(day, -30, GETDATE());

EXAMPLE 2:
Query: "What are the top 10 products by total sales amount?"
Schema: Products (ProductID, Name, Price), OrderItems (OrderID, ProductID, Quantity)
SQL: SELECT TOP 10 p.ProductID, p.Name, SUM(oi.Quantity * p.Price) AS TotalSales
     FROM Products p
     INNER JOIN OrderItems oi ON p.ProductID = oi.ProductID
     GROUP BY p.ProductID, p.Name
     ORDER BY TotalSales DESC;

EXAMPLE 3:
Query: "Find customers who have never placed an order"
Schema: Customers (CustomerID, Name), Orders (OrderID, CustomerID)
SQL: SELECT c.CustomerID, c.Name
     FROM Customers c
     LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
     WHERE o.CustomerID IS NULL;
"""

    @staticmethod
    def get_error_handling_prompt(error_message: str, original_query: str) -> str:
        """Get prompt for handling SQL errors and generating corrections."""
        return f"""The following MSSQL query resulted in an error. Please analyze and provide a corrected version.

ORIGINAL QUERY:
{original_query}

ERROR MESSAGE:
{error_message}

Please provide a corrected query that addresses the error while maintaining the original intent.

CORRECTED QUERY:"""

    @staticmethod
    def get_query_complexity_analysis_prompt() -> str:
        """Get prompt for analyzing query complexity."""
        return """Analyze the complexity of the following natural language query and determine the best approach for SQL generation.

QUERY: {user_query}
SCHEMA: {schema_context}

Assess:
1. Query complexity level (Simple/Medium/Complex)
2. Required tables and joins
3. Aggregation requirements
4. Filtering complexity
5. Sorting/grouping needs
6. Potential performance considerations

ANALYSIS:"""

    @staticmethod
    def get_business_context_prompt() -> str:
        """Get prompt that incorporates business context into SQL generation."""
        return """Generate an MSSQL query that addresses the following business question, considering typical business rules and data patterns.

BUSINESS QUESTION: {user_query}

DATABASE SCHEMA:
{schema_context}

BUSINESS CONTEXT CONSIDERATIONS:
- Consider typical business hours, fiscal periods, and reporting requirements
- Apply standard business logic for calculations (revenue, profit, growth, etc.)
- Handle common data quality issues (nulls, duplicates, etc.)
- Use appropriate date ranges and time periods
- Consider hierarchical relationships in organizational data

SQL QUERY:"""

    @staticmethod
    def get_data_quality_check_prompt() -> str:
        """Get prompt for generating queries that include data quality checks."""
        return """Generate an MSSQL query that not only answers the question but also includes appropriate data quality checks and validations.

QUERY: {user_query}
SCHEMA: {schema_context}

Include considerations for:
1. Handling NULL values appropriately
2. Checking for data consistency
3. Avoiding division by zero errors
4. Proper date range validations
5. Duplicate handling where relevant

QUALITY-ASSURED SQL QUERY:"""


class PromptBuilder:
    """Builder class for constructing complex prompts with multiple components."""
    
    def __init__(self):
        self.components = []
        self.templates = PromptTemplates()
    
    def add_system_context(self) -> 'PromptBuilder':
        """Add system context to the prompt."""
        self.components.append(("system", self.templates.get_system_prompt()))
        return self
    
    def add_schema_context(self, schema_context: str) -> 'PromptBuilder':
        """Add schema context to the prompt."""
        self.components.append(("schema", f"DATABASE SCHEMA:\n{schema_context}"))
        return self
    
    def add_user_query(self, user_query: str) -> 'PromptBuilder':
        """Add user query to the prompt."""
        self.components.append(("query", f"USER QUERY: {user_query}"))
        return self
    
    def add_examples(self) -> 'PromptBuilder':
        """Add few-shot examples to the prompt."""
        self.components.append(("examples", self.templates.get_few_shot_examples()))
        return self
    
    def add_additional_context(self, context: str) -> 'PromptBuilder':
        """Add additional context to the prompt."""
        self.components.append(("additional", f"ADDITIONAL CONTEXT:\n{context}"))
        return self
    
    def build(self) -> str:
        """Build the final prompt from all components."""
        prompt_parts = []
        
        for component_type, content in self.components:
            prompt_parts.append(content)
        
        # Add the final instruction
        prompt_parts.append("Generate an optimized MSSQL query:")
        
        return "\n\n".join(prompt_parts)
