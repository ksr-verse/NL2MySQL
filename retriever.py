"""Schema retriever for finding relevant database schema chunks based on natural language queries.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

from typing import List, Dict, Any, Optional, Set
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
# Training embedder no longer needed - using new Vector DB approach
from loguru import logger
from config import settings
# Basic synonyms mapping for query preprocessing
SYNONYMS = {
    "users": "spt_identity",
    "user": "spt_identity", 
    "employees": "spt_identity",
    "people": "spt_identity",
    "identities": "spt_identity",
    "accounts": "spt_link",
    "account": "spt_link",
    "user accounts": "spt_link",
    "identity accounts": "spt_link",
    "links": "spt_link",
    "applications": "spt_application",
    "application": "spt_application",
    "apps": "spt_application",
    "systems": "spt_application"
}


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
            # Connect to schema collection
            self.schema_collection = self.chroma_client.get_collection(
                name=settings.vector_db.collection_name
            )
            logger.info(f"Connected to schema collection: {settings.vector_db.collection_name}")
            
            # Connect to training examples collection
            self.training_collection = self.chroma_client.get_collection("training_examples")
            logger.info(f"Connected to training collection: training_examples")
            
        except Exception as e:
            logger.error(f"Failed to connect to collections: {e}")
            raise RuntimeError(f"Collections not found. Please run schema and training embedding first.")
    
    def _preprocess_query_with_synonyms(self, query: str) -> str:
        """Preprocess query by replacing synonyms with database terms."""
        enhanced_query = query.lower()
        
        # Apply synonym mappings
        for human_term, db_term in SYNONYMS.items():
            if human_term.lower() in enhanced_query:
                enhanced_query = enhanced_query.replace(human_term.lower(), db_term)
                logger.info(f"RETRIEVER: Replaced '{human_term}' with '{db_term}'")
        
        # If synonyms were applied, log the enhancement
        if enhanced_query != query.lower():
            logger.info(f"RETRIEVER: Original query: '{query}'")
            logger.info(f"RETRIEVER: Enhanced query: '{enhanced_query}'")
        else:
            logger.info(f"RETRIEVER: No synonyms found in query: '{query}'")
        
        return enhanced_query
    
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
        logger.info(f"RETRIEVER: Starting schema retrieval")
        logger.info(f"RETRIEVER: Original query: '{query}'")
        logger.info(f"RETRIEVER: Parameters - top_k: {top_k}, include_relationships: {include_relationships}, filter_types: {filter_types}")
        
        # Preprocess query with synonyms
        enhanced_query = self._preprocess_query_with_synonyms(query)
        
        top_k = top_k or settings.vector_db.top_k
        # Increase top_k to ensure we get table chunks (not just column chunks)
        top_k = max(top_k, 20)  # Ensure we get at least 20 results to find table chunks
        logger.info(f"RETRIEVER: Using top_k: {top_k}")
        
        try:
            # Build where clause for filtering
            where_clause = None
            if filter_types:
                where_clause = {"type": {"$in": filter_types}}
                logger.info(f"RETRIEVER: Using filter: {where_clause}")
            else:
                logger.info(f"RETRIEVER: No filters applied")
            
            logger.info(f"RETRIEVER: Querying schema collection")
            # Query the schema collection with enhanced query
            schema_results = self.schema_collection.query(
                query_texts=[enhanced_query],
                n_results=top_k,
                where=where_clause
            )
            
            logger.info(f"RETRIEVER: Querying training examples collection")
            # Query the training examples collection with enhanced query
            training_results = self.training_collection.query(
                query_texts=[enhanced_query],
                n_results=3,  # Get top 3 most relevant training examples
                where=None  # No filters for training examples
            )
            
            # Combine results
            results = schema_results
            
            logger.info(f"RETRIEVER: ChromaDB query completed")
            logger.info(f"RETRIEVER: Results structure: {list(results.keys()) if results else 'None'}")
            
            if not results or not results.get("documents") or not results["documents"][0]:
                logger.warning(f"RETRIEVER: No relevant schema found for query: {query}")
                return {"tables": {}, "relationships": [], "query": query, "retrieved_chunks": [], "schema_context": ""}
            
            # Process schema results
            schema_documents = results["documents"][0] if results.get("documents") and results["documents"][0] else []
            schema_metadatas = results["metadatas"][0] if results.get("metadatas") and results["metadatas"][0] else []
            schema_distances = results["distances"][0] if results.get("distances") and results["distances"][0] else []
            schema_ids = results["ids"][0] if results.get("ids") and results["ids"][0] else []
            
            # Process training results
            training_documents = training_results["documents"][0] if training_results.get("documents") and training_results["documents"][0] else []
            training_metadatas = training_results["metadatas"][0] if training_results.get("metadatas") and training_results["metadatas"][0] else []
            training_distances = training_results["distances"][0] if training_results.get("distances") and training_results["distances"][0] else []
            training_ids = training_results["ids"][0] if training_results.get("ids") and training_results["ids"][0] else []
            
            logger.info(f"RETRIEVER: Retrieved {len(schema_documents)} schema chunks, {len(training_documents)} training examples")
            logger.info(f"RETRIEVER: Schema document lengths: {[len(doc) for doc in schema_documents[:3]]}")
            logger.info(f"RETRIEVER: Schema metadata types: {[meta.get('type', 'unknown') for meta in schema_metadatas[:3]]}")
            logger.info(f"RETRIEVER: Schema distance scores: {schema_distances[:3]}")
            logger.info(f"RETRIEVER: Training distance scores: {training_distances[:3]}")
            
            # Organize results by type
            logger.info(f"RETRIEVER: Processing {len(schema_documents)} schema chunks and {len(training_documents)} training examples")
            tables = {}
            relationships = []
            retrieved_chunks = []
            training_examples = []
            
            # Process schema chunks
            for i, (doc, meta, distance, chunk_id) in enumerate(zip(schema_documents, schema_metadatas, schema_distances, schema_ids)):
                chunk_info = {
                    "id": chunk_id,
                    "content": doc,
                    "metadata": meta,
                    "similarity_score": 1 - distance,  # Convert distance to similarity
                    "rank": i + 1,
                    "source": "schema"
                }
                retrieved_chunks.append(chunk_info)
                
                chunk_type = meta.get("type", "unknown")
                logger.info(f"RETRIEVER: Processing schema chunk {i+1}/{len(schema_documents)} - Type: {chunk_type}, Score: {chunk_info['similarity_score']:.3f}")
                
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
            
            # Process training examples
            for i, (doc, meta, distance, chunk_id) in enumerate(zip(training_documents, training_metadatas, training_distances, training_ids)):
                training_info = {
                    "id": chunk_id,
                    "content": doc,
                    "metadata": meta,
                    "similarity_score": 1 - distance,
                    "rank": i + 1,
                    "source": "training"
                }
                training_examples.append(training_info)
                logger.info(f"RETRIEVER: Processing training example {i+1}/{len(training_documents)} - Score: {training_info['similarity_score']:.3f}")
            
            # Sort relationships by similarity score
            relationships.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Sort training examples by similarity score
            training_examples.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Generate schema context for LLM
            schema_context = self._build_schema_context(tables, relationships, retrieved_chunks)
            
            # Generate training context for LLM
            training_context = self._build_training_context(training_examples)
            
            # Hybrid approach: Add core tables if they're mentioned in the enhanced query
            core_tables_to_check = ["spt_identity", "spt_link", "spt_application"]
            enhanced_query_lower = enhanced_query.lower()
            
            for core_table in core_tables_to_check:
                if core_table in enhanced_query_lower:
                    full_table_name = f"identityiq.{core_table}"
                    if full_table_name not in tables:
                        logger.info(f"RETRIEVER: Adding core table {core_table} based on enhanced query match")
                        # Try to find the table chunk in ChromaDB
                        try:
                            # Simple query without complex where clause
                            table_results = self.schema_collection.query(
                                query_texts=[core_table],
                                n_results=5
                            )
                            
                            if table_results['documents'] and len(table_results['documents'][0]) > 0:
                                table_doc = table_results['documents'][0][0]
                                table_meta = table_results['metadatas'][0][0]
                                table_distance = table_results['distances'][0][0]
                                table_similarity = 1 - table_distance
                                
                                tables[full_table_name] = {
                                    "schema": "identityiq",
                                    "table": core_table,
                                    "full_name": full_table_name,
                                    "table_info": table_doc,
                                    "columns": [],
                                    "similarity_score": table_similarity
                                }
                                logger.info(f"RETRIEVER: Found and added {core_table} table (score: {table_similarity:.3f})")
                            else:
                                logger.warning(f"RETRIEVER: Core table {core_table} not found in ChromaDB")
                        except Exception as e:
                            logger.error(f"RETRIEVER: Error searching for core table {core_table}: {e}")
            
            logger.info(f"RETRIEVER: Final results summary:")
            logger.info(f"   - Tables found: {len(tables)}")
            if tables:
                table_names = list(tables.keys())
                logger.info(f"   - Table names: {table_names}")
                for table_name, table_info in tables.items():
                    logger.info(f"     * {table_name}: score={table_info.get('similarity_score', 'N/A'):.3f}")
            logger.info(f"   - Relationships found: {len(relationships)}")
            logger.info(f"   - Schema chunks processed: {len(retrieved_chunks)}")
            logger.info(f"   - Training examples found: {len(training_examples)}")
            logger.info(f"   - Schema context length: {len(schema_context)}")
            logger.info(f"   - Training context length: {len(training_context)}")
            logger.info(f"RETRIEVER: Schema and training retrieval completed successfully")
            
            return {
                "tables": tables,
                "relationships": relationships,
                "query": query,
                "enhanced_query": enhanced_query,
                "retrieved_chunks": retrieved_chunks,
                "training_examples": training_examples,
                "schema_context": schema_context,
                "training_context": training_context,
                "chunks": retrieved_chunks  # For backward compatibility
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
    
    def retrieve_relevant_examples(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant training examples for the query."""
        try:
            # Get training collection
            training_collection = self.chroma_client.get_collection("training_examples")
            
            # Search for relevant examples
            results = training_collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            examples = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                    distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else 0
                    
                    examples.append({
                        "natural_language": metadata.get('natural_language', ''),
                        "sql": metadata.get('sql', ''),
                        "explanation": metadata.get('explanation', ''),
                        "relevance_score": 1 - distance,  # Convert distance to similarity score
                        "example_id": metadata.get('example_id', f'example_{i}')
                    })
            
            logger.info(f"Retrieved {len(examples)} relevant training examples for query: {query[:50]}...")
            return examples
            
        except Exception as e:
            logger.error(f"Error retrieving training examples: {e}")
            return []
    
    def _build_schema_context(self, tables: Dict[str, Any], relationships: List[Dict[str, Any]], retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Build schema context from retrieved information."""
        if not tables and not relationships:
            return ""
        
        context_parts = ["## DATABASE SCHEMA INFORMATION:"]
        
        # Add table information
        for table_name, table_info in tables.items():
            context_parts.append(f"\n### Table: {table_name}")
            context_parts.append(f"Schema: {table_info.get('schema', '')}")
            context_parts.append(f"Description: {table_info.get('table_info', '')}")
            
            # Add columns
            columns = table_info.get('columns', [])
            if columns:
                context_parts.append("Columns:")
                for col in columns[:10]:  # Limit to first 10 columns
                    col_name = col.get('name', '')
                    col_type = col.get('data_type', '')
                    col_desc = col.get('description', '')
                    context_parts.append(f"  - {col_name} ({col_type}): {col_desc}")
        
        # Add relationships
        if relationships:
            context_parts.append("\n### Relationships:")
            for rel in relationships[:5]:  # Limit to first 5 relationships
                context_parts.append(f"  - {rel.get('description', '')}")
        
        return "\n".join(context_parts)
    
    def _build_training_context(self, training_examples: List[Dict[str, Any]]) -> str:
        """Build training context from retrieved examples."""
        if not training_examples:
            return ""
        
        context_parts = ["## RELEVANT TRAINING EXAMPLES:"]
        
        for i, example in enumerate(training_examples[:3], 1):  # Top 3 examples
            content = example.get("content", "")
            similarity = example.get("similarity_score", 0)
            
            context_parts.append(f"\n### Example {i} (Similarity: {similarity:.3f}):")
            context_parts.append(content)
        
        return "\n".join(context_parts)


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
