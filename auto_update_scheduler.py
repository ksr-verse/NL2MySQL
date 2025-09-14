#!/usr/bin/env python3
"""Auto Update Scheduler - Schedules daily schema discovery and training updates.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

import os
import json
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from loguru import logger
from dynamic_training_generator import DynamicTrainingGenerator


class AutoUpdateScheduler:
    """Schedules and manages automatic updates for schema discovery and training."""
    
    def __init__(self):
        """Initialize auto update scheduler."""
        self.generator = DynamicTrainingGenerator()
        self.scheduler_log_file = "scheduler_log.json"
        self.scheduler_log = self._load_scheduler_log()
        
        logger.info("Auto update scheduler initialized")
    
    def _load_scheduler_log(self) -> Dict[str, Any]:
        """Load scheduler execution log."""
        if os.path.exists(self.scheduler_log_file):
            try:
                with open(self.scheduler_log_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load scheduler log: {e}")
        
        return {
            "last_run": None,
            "execution_history": [],
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0
        }
    
    def _save_scheduler_log(self):
        """Save scheduler execution log."""
        try:
            with open(self.scheduler_log_file, 'w') as f:
                json.dump(self.scheduler_log, f, indent=2)
            logger.info(f"Scheduler log saved to {self.scheduler_log_file}")
        except Exception as e:
            logger.error(f"Error saving scheduler log: {e}")
    
    def _log_execution(self, result: Dict[str, Any]):
        """Log execution result."""
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "status": result.get("status", "unknown"),
            "new_patterns": result.get("new_patterns_generated", 0),
            "vector_db_updated": result.get("vector_db_updated", False),
            "error": result.get("error", None)
        }
        
        # Add to execution history (keep last 30 runs)
        self.scheduler_log["execution_history"].append(execution_record)
        if len(self.scheduler_log["execution_history"]) > 30:
            self.scheduler_log["execution_history"] = self.scheduler_log["execution_history"][-30:]
        
        # Update counters
        self.scheduler_log["total_runs"] += 1
        self.scheduler_log["last_run"] = execution_record["timestamp"]
        
        if result.get("status") == "success":
            self.scheduler_log["successful_runs"] += 1
        else:
            self.scheduler_log["failed_runs"] += 1
        
        self._save_scheduler_log()
    
    def run_daily_update(self):
        """Run daily update process."""
        logger.info("Starting scheduled daily update...")
        
        try:
            result = self.generator.run_daily_update()
            self._log_execution(result)
            
            if result.get("status") == "success":
                logger.info("✅ Scheduled daily update completed successfully")
            else:
                logger.warning(f"⚠️ Scheduled daily update completed with issues: {result}")
                
        except Exception as e:
            error_result = {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "error"
            }
            self._log_execution(error_result)
            logger.error(f"❌ Scheduled daily update failed: {e}")
    
    def run_weekly_cleanup(self):
        """Run weekly cleanup and maintenance."""
        logger.info("Starting weekly cleanup...")
        
        try:
            # Clean up old logs
            self._cleanup_old_logs()
            
            # Validate vector database
            self._validate_vector_database()
            
            logger.info("✅ Weekly cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Weekly cleanup failed: {e}")
    
    def _cleanup_old_logs(self):
        """Clean up old log files."""
        try:
            # Keep only last 7 days of logs
            cutoff_date = datetime.now() - timedelta(days=7)
            
            # Clean up execution history
            self.scheduler_log["execution_history"] = [
                record for record in self.scheduler_log["execution_history"]
                if datetime.fromisoformat(record["timestamp"]) > cutoff_date
            ]
            
            self._save_scheduler_log()
            logger.info("Old logs cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up logs: {e}")
    
    def _validate_vector_database(self):
        """Validate vector database integrity."""
        try:
            from training_embedder import training_embedder
            
            # Get collection info
            info = training_embedder.get_collection_info()
            
            if info.get("status") == "ready":
                logger.info(f"Vector database validation passed: {info['total_examples']} examples")
            else:
                logger.warning(f"Vector database validation failed: {info}")
                
        except Exception as e:
            logger.error(f"Error validating vector database: {e}")
    
    def start_scheduler(self):
        """Start the scheduler."""
        logger.info("Starting auto update scheduler...")
        
        # Schedule daily update at 2 AM
        schedule.every().day.at("02:00").do(self.run_daily_update)
        
        # Schedule weekly cleanup on Sunday at 3 AM
        schedule.every().sunday.at("03:00").do(self.run_weekly_cleanup)
        
        logger.info("Scheduler started - Daily updates at 2:00 AM, Weekly cleanup on Sunday at 3:00 AM")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
    
    def run_manual_update(self):
        """Run manual update (for testing)."""
        logger.info("Running manual update...")
        self.run_daily_update()
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status and statistics."""
        return {
            "scheduler_log": self.scheduler_log,
            "next_daily_run": schedule.next_run(),
            "next_weekly_run": schedule.next_run(),
            "is_running": True
        }


def main():
    """Command-line interface for auto update scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto update scheduler for schema discovery")
    parser.add_argument("--start", action="store_true", help="Start the scheduler")
    parser.add_argument("--manual-update", action="store_true", help="Run manual update")
    parser.add_argument("--status", action="store_true", help="Show scheduler status")
    parser.add_argument("--test", action="store_true", help="Test the update process")
    
    args = parser.parse_args()
    
    try:
        scheduler = AutoUpdateScheduler()
        
        if args.start:
            print("🚀 Starting auto update scheduler...")
            print("Daily updates: 2:00 AM")
            print("Weekly cleanup: Sunday 3:00 AM")
            print("Press Ctrl+C to stop")
            scheduler.start_scheduler()
        
        if args.manual_update:
            print("🔄 Running manual update...")
            scheduler.run_manual_update()
            print("✅ Manual update completed")
        
        if args.status:
            status = scheduler.get_scheduler_status()
            print("📊 Scheduler Status:")
            print(f"  Total runs: {status['scheduler_log']['total_runs']}")
            print(f"  Successful: {status['scheduler_log']['successful_runs']}")
            print(f"  Failed: {status['scheduler_log']['failed_runs']}")
            print(f"  Last run: {status['scheduler_log']['last_run']}")
        
        if args.test:
            print("🧪 Testing update process...")
            scheduler.run_manual_update()
            print("✅ Test completed")
        
        if not any([args.start, args.manual_update, args.status, args.test]):
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
