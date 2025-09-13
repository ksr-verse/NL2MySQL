"""Schema embedder for creating vector embeddings of database schema.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from loguru import logger
from config import settings as app_settings


class SchemaEmbedder:
    """Create and manage vector embeddings of database schema."""
    
    def __init__(self):
        """Initialize schema embedder with ChromaDB and sentence transformer."""
        self.embedding_model = SentenceTransformer(app_settings.vector_db.embedding_model)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=app_settings.vector_db.persist_directory,
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(
                name=app_settings.vector_db.collection_name
            )
            logger.info(f"Using existing collection: {app_settings.vector_db.collection_name}")
        except Exception:
            self.collection = self.chroma_client.create_collection(
                name=app_settings.vector_db.collection_name,
                metadata={"description": "Database schema embeddings for NL2SQL"}
            )
            logger.info(f"Created new collection: {app_settings.vector_db.collection_name}")
    
    def reset_collection(self) -> None:
        """Reset the collection by deleting and recreating it."""
        try:
            self.chroma_client.delete_collection(name=app_settings.vector_db.collection_name)
            logger.info("Deleted existing collection")
        except Exception:
            pass
        
        self.collection = self.chroma_client.create_collection(
            name=app_settings.vector_db.collection_name,
            metadata={"description": "Database schema embeddings for NL2SQL"}
        )
        logger.info("Created new collection")
    
    def _format_table_description(self, table_info: Dict[str, Any], schema_name: str) -> str:
        """Format table information into a descriptive text."""
        table_name = table_info.get("name", "")
        full_table_name = f"{schema_name}.{table_name}" if schema_name else table_name
        
        description = f"Table: {full_table_name}\n"
        
        # Add columns information
        columns = table_info.get("columns", [])
        if columns:
            description += "Columns:\n"
            for col in columns:
                col_name = col.get("name", "")
                col_type = col.get("type", "")
                nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
                default = col.get("default", "")
                
                col_desc = f"  - {col_name} ({col_type}) {nullable}"
                if default:
                    col_desc += f" DEFAULT {default}"
                description += col_desc + "\n"
        
        # Add primary keys
        primary_keys = table_info.get("primary_keys", [])
        if primary_keys:
            description += f"Primary Keys: {', '.join(primary_keys)}\n"
        
        # Add foreign keys
        foreign_keys = table_info.get("foreign_keys", [])
        if foreign_keys:
            description += "Foreign Keys:\n"
            for fk in foreign_keys:
                from_cols = ", ".join(fk.get("constrained_columns", []))
                to_table = fk.get("referred_table", "")
                to_schema = fk.get("referred_schema", "")
                to_cols = ", ".join(fk.get("referred_columns", []))
                
                if to_schema and to_schema != schema_name:
                    to_table = f"{to_schema}.{to_table}"
                
                description += f"  - {from_cols} -> {to_table}({to_cols})\n"
        
        # Add indexes
        indexes = table_info.get("indexes", [])
        if indexes:
            description += "Indexes:\n"
            for idx in indexes:
                idx_name = idx.get("name", "")
                idx_cols = ", ".join(idx.get("column_names", []))
                unique = "UNIQUE " if idx.get("unique", False) else ""
                description += f"  - {unique}INDEX {idx_name} ON ({idx_cols})\n"
        
        return description
    
    def _format_column_description(self, col_info: Dict[str, Any], table_name: str, schema_name: str) -> str:
        """Format column information into a descriptive text."""
        col_name = col_info.get("name", "")
        col_type = col_info.get("type", "")
        nullable = "nullable" if col_info.get("nullable", True) else "not nullable"
        default = col_info.get("default", "")
        
        full_table_name = f"{schema_name}.{table_name}" if schema_name else table_name
        
        description = f"Column: {col_name} in table {full_table_name}\n"
        description += f"Type: {col_type}\n"
        description += f"Nullable: {nullable}\n"
        
        if default:
            description += f"Default: {default}\n"
        
        return description
    
    def _create_schema_chunks(self, schema_info: Dict[str, Any]) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Create text chunks from schema information for embedding."""
        chunks = []
        
        schemas = schema_info.get("schemas", {})
        
        for schema_name, schema_data in schemas.items():
            tables = schema_data.get("tables", {})
            
            for table_name, table_info in tables.items():
                # Create table-level chunk
                table_description = self._format_table_description(table_info, schema_name)
                table_id = f"table_{schema_name}_{table_name}"
                table_metadata = {
                    "type": "table",
                    "schema": schema_name,
                    "table": table_name,
                    "full_name": f"{schema_name}.{table_name}" if schema_name else table_name
                }
                chunks.append((table_id, table_description, table_metadata))
                
        # Create column-level chunks
        columns = table_info.get("columns", [])
        for col_idx, col_info in enumerate(columns):
            col_name = col_info.get("name", "")
            col_description = self._format_column_description(col_info, table_name, schema_name)
            col_id = f"column_{schema_name}_{table_name}_{col_name}_{col_idx}"
            col_metadata = {
                "type": "column",
                "schema": schema_name,
                "table": table_name,
                "column": col_name,
                "full_table_name": f"{schema_name}.{table_name}" if schema_name else table_name,
                "data_type": str(col_info.get("type", ""))
            }
            chunks.append((col_id, col_description, col_metadata))
        
        # Create relationship chunks
        relationships = schema_info.get("relationships", [])
        for i, rel in enumerate(relationships):
            rel_description = f"Foreign Key Relationship:\n"
            rel_description += f"From: {rel.get('from_table')} ({', '.join(rel.get('from_columns', []))})\n"
            rel_description += f"To: {rel.get('to_table')} ({', '.join(rel.get('to_columns', []))})\n"
            
            rel_id = f"relationship_{i}"
            rel_metadata = {
                "type": "relationship",
                "from_table": rel.get("from_table"),
                "to_table": rel.get("to_table"),
                "from_columns": ",".join(rel.get("from_columns", [])),
                "to_columns": ",".join(rel.get("to_columns", []))
            }
            chunks.append((rel_id, rel_description, rel_metadata))
        
        return chunks
    
    def embed_schema(self, schema_info: Dict[str, Any], reset: bool = True) -> bool:
        """Embed schema information into ChromaDB."""
        try:
            if reset:
                self.reset_collection()
            
            # Create text chunks from schema
            chunks = self._create_schema_chunks(schema_info)
            logger.info(f"Created {len(chunks)} schema chunks")
            
            if not chunks:
                logger.warning("No schema chunks to embed")
                return False
            
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            
            for chunk_id, description, metadata in chunks:
                ids.append(chunk_id)
                documents.append(description)
                metadatas.append(metadata)
            
            # Add to collection in batches
            batch_size = 100
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_docs = documents[i:i + batch_size]
                batch_meta = metadatas[i:i + batch_size]
                
                self.collection.add(
                    ids=batch_ids,
                    documents=batch_docs,
                    metadatas=batch_meta
                )
                logger.info(f"Added batch {i//batch_size + 1}/{(len(ids)-1)//batch_size + 1}")
            
            logger.info(f"Successfully embedded {len(chunks)} schema chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error embedding schema: {e}")
            return False
    
    def load_and_embed_schema(self, schema_file: str = None, reset: bool = True) -> bool:
        """Load schema from file and embed it."""
        schema_file = schema_file or app_settings.app.schema_file
        
        if not os.path.exists(schema_file):
            # Try manual schema file
            manual_file = app_settings.app.manual_schema_file
            if os.path.exists(manual_file):
                schema_file = manual_file
                logger.info(f"Using manual schema file: {manual_file}")
            else:
                logger.error(f"Schema file not found: {schema_file}")
                return False
        
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_info = json.load(f)
            
            logger.info(f"Loaded schema from {schema_file}")
            return self.embed_schema(schema_info, reset=reset)
            
        except Exception as e:
            logger.error(f"Error loading schema file {schema_file}: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedded schema collection."""
        try:
            count = self.collection.count()
            
            # Get sample of metadata to understand collection contents
            if count > 0:
                sample = self.collection.get(limit=min(10, count))
                metadata_sample = sample.get("metadatas", [])
                
                # Count by type
                type_counts = {}
                for meta in metadata_sample:
                    chunk_type = meta.get("type", "unknown")
                    type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
                
                return {
                    "total_chunks": count,
                    "sample_type_distribution": type_counts,
                    "collection_name": app_settings.vector_db.collection_name
                }
            else:
                return {
                    "total_chunks": 0,
                    "collection_name": app_settings.vector_db.collection_name
                }
                
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}


def main():
    """Command-line interface for schema embedding."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Embed database schema into ChromaDB")
    parser.add_argument("--schema", "-s", help="Schema JSON file", default="schema.json")
    parser.add_argument("--reset", "-r", action="store_true", help="Reset collection before embedding")
    parser.add_argument("--stats", action="store_true", help="Show collection statistics")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.remove()
        logger.add("schema_embedding.log", level="DEBUG")
        logger.add(lambda msg: print(msg, end=""), level="INFO")
    
    embedder = SchemaEmbedder()
    
    if args.stats:
        stats = embedder.get_collection_stats()
        print("Collection Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        return
    
    success = embedder.load_and_embed_schema(args.schema, reset=args.reset)
    
    if success:
        stats = embedder.get_collection_stats()
        print(f"Schema embedding completed successfully!")
        print(f"Total chunks: {stats.get('total_chunks', 0)}")
    else:
        print("Schema embedding failed")
        exit(1)


if __name__ == "__main__":
    main()
