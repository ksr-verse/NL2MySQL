"""Schema retriever for finding relevant database schema chunks based on natural language queries.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

from typing import List, Dict, Any, Optional, Set
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from loguru import logger
from config import settings


class SchemaRetriever:
    """Retrieve relevant schema information based on natural language queries."""
    
    def __init__(self):
        """Initialize schema retriever with ChromaDB connection."""
        self.embedding_model = SentenceTransformer(settings.vector_db.embedding_model)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=settings.vector_db.persist_directory,
            settings=Settings(allow_reset=False, anonymized_telemetry=False)
        )
        
        try:
            self.collection = self.chroma_client.get_collection(
                name=settings.vector_db.collection_name
            )
            logger.info(f"Connected to collection: {settings.vector_db.collection_name}")
        except Exception as e:
            logger.error(f"Failed to connect to collection: {e}")
            raise RuntimeError(f"Schema collection not found. Please run schema embedding first.")
    
    def retrieve_relevant_schema(
        self, 
        query: str, 
        top_k: int = None, 
        include_relationships: bool = True,
        filter_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve the most relevant schema chunks for a given query.
        
        Args:
            query: Natural language query
            top_k: Number of top results to return
            include_relationships: Whether to include relationship information
            filter_types: List of chunk types to filter by ('table', 'column', 'relationship')
        
        Returns:
            Dictionary containing retrieved schema information
        """
        top_k = top_k or settings.vector_db.top_k
        
        try:
            # Build where clause for filtering
            where_clause = None
            if filter_types:
                where_clause = {"type": {"$in": filter_types}}
            
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_clause
            )
            
            if not results or not results.get("documents") or not results["documents"][0]:
                logger.warning(f"No relevant schema found for query: {query}")
                return {"tables": {}, "relationships": [], "query": query, "retrieved_chunks": []}
            
            # Process results
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]
            ids = results["ids"][0]
            
            # Organize results by type
            tables = {}
            relationships = []
            retrieved_chunks = []
            
            for i, (doc, meta, distance, chunk_id) in enumerate(zip(documents, metadatas, distances, ids)):
                chunk_info = {
                    "id": chunk_id,
                    "content": doc,
                    "metadata": meta,
                    "similarity_score": 1 - distance,  # Convert distance to similarity
                    "rank": i + 1
                }
                retrieved_chunks.append(chunk_info)
                
                chunk_type = meta.get("type", "unknown")
                
                if chunk_type == "table":
                    schema_name = meta.get("schema", "")
                    table_name = meta.get("table", "")
                    full_name = meta.get("full_name", f"{schema_name}.{table_name}")
                    
                    if full_name not in tables:
                        tables[full_name] = {
                            "schema": schema_name,
                            "table": table_name,
                            "full_name": full_name,
                            "table_info": doc,
                            "columns": [],
                            "similarity_score": chunk_info["similarity_score"]
                        }
                
                elif chunk_type == "column":
                    schema_name = meta.get("schema", "")
                    table_name = meta.get("table", "")
                    column_name = meta.get("column", "")
                    full_table_name = meta.get("full_table_name", f"{schema_name}.{table_name}")
                    data_type = meta.get("data_type", "")
                    
                    # Ensure table exists in results
                    if full_table_name not in tables:
                        tables[full_table_name] = {
                            "schema": schema_name,
                            "table": table_name,
                            "full_name": full_table_name,
                            "table_info": "",
                            "columns": [],
                            "similarity_score": 0
                        }
                    
                    tables[full_table_name]["columns"].append({
                        "name": column_name,
                        "data_type": data_type,
                        "description": doc,
                        "similarity_score": chunk_info["similarity_score"]
                    })
                
                elif chunk_type == "relationship" and include_relationships:
                    relationships.append({
                        "from_table": meta.get("from_table", ""),
                        "to_table": meta.get("to_table", ""),
                        "from_columns": meta.get("from_columns", []),
                        "to_columns": meta.get("to_columns", []),
                        "description": doc,
                        "similarity_score": chunk_info["similarity_score"]
                    })
            
            # Sort columns by similarity score
            for table_info in tables.values():
                table_info["columns"].sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Sort relationships by similarity score
            relationships.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            logger.info(f"Retrieved {len(tables)} tables, {len(relationships)} relationships for query: '{query}'")
            
            return {
                "tables": tables,
                "relationships": relationships,
                "query": query,
                "retrieved_chunks": retrieved_chunks
            }
            
        except Exception as e:
            logger.error(f"Error retrieving schema for query '{query}': {e}")
            return {"tables": {}, "relationships": [], "query": query, "retrieved_chunks": []}
    
    def get_tables_by_names(self, table_names: List[str]) -> Dict[str, Any]:
        """Retrieve specific tables by their names."""
        try:
            # Build where clause to filter by table names
            where_clause = {
                "$or": [
                    {"full_name": {"$in": table_names}},
                    {"table": {"$in": table_names}}
                ]
            }
            
            results = self.collection.get(
                where=where_clause,
                include=["documents", "metadatas"]
            )
            
            if not results or not results.get("documents"):
                return {"tables": {}, "relationships": []}
            
            tables = {}
            
            for doc, meta in zip(results["documents"], results["metadatas"]):
                chunk_type = meta.get("type", "unknown")
                
                if chunk_type in ["table", "column"]:
                    schema_name = meta.get("schema", "")
                    table_name = meta.get("table", "")
                    full_name = meta.get("full_name", f"{schema_name}.{table_name}")
                    
                    if full_name not in tables:
                        tables[full_name] = {
                            "schema": schema_name,
                            "table": table_name,
                            "full_name": full_name,
                            "table_info": "",
                            "columns": []
                        }
                    
                    if chunk_type == "table":
                        tables[full_name]["table_info"] = doc
                    elif chunk_type == "column":
                        column_name = meta.get("column", "")
                        data_type = meta.get("data_type", "")
                        tables[full_name]["columns"].append({
                            "name": column_name,
                            "data_type": data_type,
                            "description": doc
                        })
            
            return {"tables": tables, "relationships": []}
            
        except Exception as e:
            logger.error(f"Error retrieving tables by names: {e}")
            return {"tables": {}, "relationships": []}
    
    def get_related_tables(self, table_name: str, max_depth: int = 1) -> Set[str]:
        """Find tables related to the given table through foreign key relationships."""
        try:
            related_tables = set()
            current_tables = {table_name}
            
            for depth in range(max_depth):
                new_tables = set()
                
                # Find relationships involving current tables
                for current_table in current_tables:
                    # Query for relationships
                    results = self.collection.query(
                        query_texts=[f"foreign key relationship {current_table}"],
                        n_results=20,
                        where={"type": "relationship"}
                    )
                    
                    if results and results.get("metadatas") and results["metadatas"][0]:
                        for meta in results["metadatas"][0]:
                            from_table = meta.get("from_table", "")
                            to_table = meta.get("to_table", "")
                            
                            if current_table in from_table or current_table in to_table:
                                new_tables.add(from_table)
                                new_tables.add(to_table)
                
                related_tables.update(new_tables)
                current_tables = new_tables - related_tables
                
                if not current_tables:
                    break
            
            # Remove the original table from related tables
            related_tables.discard(table_name)
            
            return related_tables
            
        except Exception as e:
            logger.error(f"Error finding related tables for {table_name}: {e}")
            return set()
    
    def search_columns_by_type(self, data_types: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Search for columns by their data types."""
        try:
            where_clause = {
                "$and": [
                    {"type": "column"},
                    {"data_type": {"$in": data_types}}
                ]
            }
            
            results = self.collection.get(
                where=where_clause,
                include=["documents", "metadatas"]
            )
            
            columns_by_type = {}
            
            if results and results.get("documents"):
                for doc, meta in zip(results["documents"], results["metadatas"]):
                    data_type = meta.get("data_type", "")
                    if data_type not in columns_by_type:
                        columns_by_type[data_type] = []
                    
                    columns_by_type[data_type].append({
                        "schema": meta.get("schema", ""),
                        "table": meta.get("table", ""),
                        "column": meta.get("column", ""),
                        "full_table_name": meta.get("full_table_name", ""),
                        "description": doc
                    })
            
            return columns_by_type
            
        except Exception as e:
            logger.error(f"Error searching columns by type: {e}")
            return {}
    
    def format_schema_context(self, retrieved_schema: Dict[str, Any]) -> str:
        """Format retrieved schema information into a readable context string."""
        context_parts = []
        
        # Add table information
        tables = retrieved_schema.get("tables", {})
        if tables:
            context_parts.append("=== RELEVANT TABLES ===")
            for table_name, table_info in tables.items():
                context_parts.append(f"\nTable: {table_name}")
                if table_info.get("table_info"):
                    # Extract key information from table description
                    table_desc = table_info["table_info"]
                    context_parts.append(table_desc)
                
                # Add column information
                columns = table_info.get("columns", [])
                if columns:
                    context_parts.append("Key Columns:")
                    for col in columns[:10]:  # Limit to top 10 most relevant columns
                        context_parts.append(f"  - {col['name']} ({col['data_type']})")
        
        # Add relationship information
        relationships = retrieved_schema.get("relationships", [])
        if relationships:
            context_parts.append("\n=== RELATIONSHIPS ===")
            for rel in relationships[:5]:  # Limit to top 5 relationships
                from_table = rel.get("from_table", "")
                to_table = rel.get("to_table", "")
                from_cols = ", ".join(rel.get("from_columns", []))
                to_cols = ", ".join(rel.get("to_columns", []))
                context_parts.append(f"{from_table}({from_cols}) -> {to_table}({to_cols})")
        
        return "\n".join(context_parts)
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the schema collection."""
        try:
            count = self.collection.count()
            
            # Get sample to understand collection structure
            sample = self.collection.get(limit=min(100, count))
            
            type_counts = {}
            if sample and sample.get("metadatas"):
                for meta in sample["metadatas"]:
                    chunk_type = meta.get("type", "unknown")
                    type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
            
            return {
                "total_chunks": count,
                "type_distribution": type_counts,
                "collection_name": settings.vector_db.collection_name,
                "embedding_model": settings.vector_db.embedding_model
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"error": str(e)}


def main():
    """Command-line interface for testing schema retrieval."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test schema retrieval")
    parser.add_argument("query", help="Natural language query")
    parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of results to return")
    parser.add_argument("--info", action="store_true", help="Show collection information")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.remove()
        logger.add(lambda msg: print(msg, end=""), level="INFO")
    
    try:
        retriever = SchemaRetriever()
        
        if args.info:
            info = retriever.get_collection_info()
            print("Collection Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
            print()
        
        # Retrieve schema for query
        results = retriever.retrieve_relevant_schema(args.query, top_k=args.top_k)
        
        print(f"Query: {args.query}")
        print(f"Found {len(results['tables'])} relevant tables and {len(results['relationships'])} relationships\n")
        
        # Format and display results
        context = retriever.format_schema_context(results)
        print("Schema Context:")
        print(context)
        
        if args.verbose:
            print("\nDetailed Results:")
            for chunk in results["retrieved_chunks"]:
                print(f"Rank {chunk['rank']}: {chunk['metadata']['type']} (similarity: {chunk['similarity_score']:.3f})")
                print(f"  {chunk['content'][:200]}...")
                print()
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
