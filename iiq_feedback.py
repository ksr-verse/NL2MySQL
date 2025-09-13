#!/usr/bin/env python3
"""IIQ Feedback and Learning System for Continuous Improvement."""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from loguru import logger

class IIQFeedbackManager:
    """Manages feedback, corrections, and continuous learning."""
    
    def __init__(self, feedback_file: str = "iiq_feedback.json", learning_file: str = "iiq_learning.json"):
        """Initialize feedback and learning manager."""
        self.feedback_file = feedback_file
        self.learning_file = learning_file
        self.feedback_history = self._load_feedback()
        self.learning_data = self._load_learning()
        
        logger.info(f"Loaded {len(self.feedback_history)} feedback entries and {len(self.learning_data)} learning examples")
    
    def _load_feedback(self) -> List[Dict[str, Any]]:
        """Load feedback history from file."""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load feedback: {e}")
        return []
    
    def _load_learning(self) -> List[Dict[str, Any]]:
        """Load learning data from file."""
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load learning data: {e}")
        return []
    
    def record_feedback(self, 
                       original_query: str, 
                       generated_sql: str, 
                       corrected_sql: str, 
                       feedback_type: str = "correction",
                       feedback_notes: str = "",
                       dba_user: str = "unknown") -> str:
        """Record feedback from DBA corrections."""
        
        feedback_id = f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        feedback_entry = {
            "id": feedback_id,
            "timestamp": datetime.now().isoformat(),
            "original_query": original_query,
            "generated_sql": generated_sql,
            "corrected_sql": corrected_sql,
            "feedback_type": feedback_type,  # "correction", "improvement", "bug_fix"
            "feedback_notes": feedback_notes,
            "dba_user": dba_user,
            "status": "pending_learning"
        }
        
        self.feedback_history.append(feedback_entry)
        self._save_feedback()
        
        logger.info(f"Recorded feedback {feedback_id}: {feedback_type}")
        return feedback_id
    
    def add_learning_example(self, 
                           natural_language: str, 
                           sql_query: str, 
                           description: str = "",
                           source: str = "feedback") -> str:
        """Add a new learning example."""
        
        learning_id = f"learn_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        learning_entry = {
            "id": learning_id,
            "timestamp": datetime.now().isoformat(),
            "natural_language": natural_language,
            "sql_query": sql_query,
            "description": description,
            "source": source,  # "feedback", "manual", "import"
            "usage_count": 0,
            "success_rate": 0.0
        }
        
        self.learning_data.append(learning_entry)
        self._save_learning()
        
        logger.info(f"Added learning example {learning_id}: {source}")
        return learning_id
    
    def process_feedback(self, feedback_id: str) -> bool:
        """Process feedback and convert to learning data."""
        try:
            feedback = next((f for f in self.feedback_history if f["id"] == feedback_id), None)
            if not feedback:
                logger.error(f"Feedback {feedback_id} not found")
                return False
            
            # Convert feedback to learning example
            learning_id = self.add_learning_example(
                natural_language=feedback["original_query"],
                sql_query=feedback["corrected_sql"],
                description=f"Corrected from: {feedback['generated_sql'][:100]}...",
                source="feedback"
            )
            
            # Update feedback status
            feedback["status"] = "processed"
            feedback["learning_id"] = learning_id
            self._save_feedback()
            
            logger.info(f"Processed feedback {feedback_id} → learning {learning_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process feedback {feedback_id}: {e}")
            return False
    
    def get_learning_examples(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent learning examples."""
        return sorted(self.learning_data, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def get_feedback_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent feedback history."""
        return sorted(self.feedback_history, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def get_relevant_learning(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get learning examples relevant to the query."""
        query_lower = query.lower()
        relevant_examples = []
        
        for example in self.learning_data:
            # Simple keyword matching
            if any(keyword in query_lower for keyword in example["natural_language"].lower().split()):
                relevant_examples.append(example)
                if len(relevant_examples) >= limit:
                    break
        
        return relevant_examples
    
    def record_query_execution(self, 
                             natural_query: str, 
                             sql_query: str, 
                             execution_time: float,
                             row_count: int,
                             success: bool,
                             error_message: str = "") -> str:
        """Record query execution for audit and learning."""
        
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        execution_entry = {
            "id": execution_id,
            "timestamp": datetime.now().isoformat(),
            "natural_query": natural_query,
            "sql_query": sql_query,
            "execution_time": execution_time,
            "row_count": row_count,
            "success": success,
            "error_message": error_message
        }
        
        # Add to learning data if successful
        if success and row_count > 0:
            self.add_learning_example(
                natural_language=natural_query,
                sql_query=sql_query,
                description=f"Successful execution: {row_count} rows in {execution_time:.2f}s",
                source="execution"
            )
        
        logger.info(f"Recorded execution {execution_id}: {success}, {row_count} rows, {execution_time:.2f}s")
        return execution_id
    
    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit log of all activities."""
        audit_entries = []
        
        # Add feedback entries
        for feedback in self.feedback_history:
            audit_entries.append({
                "timestamp": feedback["timestamp"],
                "type": "feedback",
                "id": feedback["id"],
                "description": f"Feedback: {feedback['feedback_type']}",
                "user": feedback.get("dba_user", "unknown")
            })
        
        # Add learning entries
        for learning in self.learning_data:
            audit_entries.append({
                "timestamp": learning["timestamp"],
                "type": "learning",
                "id": learning["id"],
                "description": f"Learning: {learning['source']}",
                "user": "system"
            })
        
        # Sort by timestamp
        audit_entries.sort(key=lambda x: x["timestamp"], reverse=True)
        return audit_entries[:limit]
    
    def _save_feedback(self) -> None:
        """Save feedback to file."""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.feedback_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
    
    def _save_learning(self) -> None:
        """Save learning data to file."""
        try:
            with open(self.learning_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save learning data: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about feedback and learning."""
        total_feedback = len(self.feedback_history)
        processed_feedback = len([f for f in self.feedback_history if f["status"] == "processed"])
        total_learning = len(self.learning_data)
        
        feedback_types = {}
        for feedback in self.feedback_history:
            ftype = feedback["feedback_type"]
            feedback_types[ftype] = feedback_types.get(ftype, 0) + 1
        
        learning_sources = {}
        for learning in self.learning_data:
            source = learning["source"]
            learning_sources[source] = learning_sources.get(source, 0) + 1
        
        return {
            "total_feedback": total_feedback,
            "processed_feedback": processed_feedback,
            "pending_feedback": total_feedback - processed_feedback,
            "total_learning": total_learning,
            "feedback_types": feedback_types,
            "learning_sources": learning_sources
        }
