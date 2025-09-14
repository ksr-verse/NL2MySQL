#!/usr/bin/env python3
"""Training data embedder - stores training examples in vector database.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

import os
import json
from typing import List, Dict, Any
from loguru import logger
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from iiq_training_data import iiq_training


class TrainingEmbedder:
    """Embeds training examples into vector database for semantic search."""
    
    def __init__(self, collection_name: str = "training_examples"):
        """Initialize training embedder."""
        self.collection_name = collection_name
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path="./chromadb",
            settings=Settings(anonymized_telemetry=False)
        )
        
        logger.info(f"Training embedder initialized with collection: {collection_name}")
    
    def embed_training_data(self, reset: bool = False):
        """Embed all training examples into vector database."""
        try:
            # Delete existing collection if reset requested
            if reset:
                try:
                    self.chroma_client.delete_collection(self.collection_name)
                    logger.info(f"Deleted existing collection: {self.collection_name}")
                except Exception as e:
                    logger.info(f"Collection {self.collection_name} doesn't exist or already deleted")
            
            # Create or get collection
            collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "IIQ training examples for semantic search"}
            )
            
            # Get training examples
            examples = iiq_training.examples
            logger.info(f"Embedding {len(examples)} training examples")
            
            # Prepare data for embedding
            documents = []
            metadatas = []
            ids = []
            
            for i, example in enumerate(examples):
                # Create searchable text from natural language and SQL
                searchable_text = f"""
Natural Language: {example['natural_language']}
SQL Query: {example['sql']}
Explanation: {example.get('explanation', '')}
"""
                
                documents.append(searchable_text)
                metadatas.append({
                    "natural_language": example['natural_language'],
                    "sql": example['sql'],
                    "explanation": example.get('explanation', ''),
                    "example_id": f"example_{i}",
                    "type": "training_example"
                })
                ids.append(f"example_{i}")
            
            # Add to collection
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully embedded {len(examples)} training examples")
            return True
            
        except Exception as e:
            logger.error(f"Error embedding training data: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the training collection."""
        try:
            collection = self.chroma_client.get_collection(self.collection_name)
            count = collection.count()
            
            return {
                "collection_name": self.collection_name,
                "total_examples": count,
                "embedding_model": "all-MiniLM-L6-v2",
                "status": "ready"
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                "collection_name": self.collection_name,
                "total_examples": 0,
                "status": "error",
                "error": str(e)
            }


# Global instance
training_embedder = TrainingEmbedder()


def main():
    """Command-line interface for embedding training data."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Embed training examples into vector database")
    parser.add_argument("--reset", action="store_true", help="Reset and recreate the training collection")
    parser.add_argument("--info", action="store_true", help="Show collection information")
    
    args = parser.parse_args()
    
    try:
        embedder = TrainingEmbedder()
        
        if args.info:
            info = embedder.get_collection_info()
            print("Training Collection Information:")
            print(f"  Collection: {info['collection_name']}")
            print(f"  Total Examples: {info['total_examples']}")
            print(f"  Status: {info['status']}")
            if 'error' in info:
                print(f"  Error: {info['error']}")
            return
        
        # Embed training data
        success = embedder.embed_training_data(reset=args.reset)
        
        if success:
            print("✅ Training examples embedded successfully!")
            
            # Show collection info
            info = embedder.get_collection_info()
            print(f"Collection: {info['collection_name']}")
            print(f"Total Examples: {info['total_examples']}")
        else:
            print("❌ Failed to embed training examples")
            exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
