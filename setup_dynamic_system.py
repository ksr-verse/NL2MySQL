#!/usr/bin/env python3
"""Setup Dynamic System - Complete setup for dynamic schema discovery and training.

NL2MySQL v1.0 - IdentityIQ Natural Language to SQL Generator
Developed by: Kuldeep Singh Rautela
Contact: rautela.ks.job@gmail.com for commercial licensing
"""

import os
import json
import subprocess
import sys
from datetime import datetime
from loguru import logger


def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    dependencies = [
        "schedule",
        "mysql-connector-python"
    ]
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ Installed {dep}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            return False
    
    return True


def setup_directories():
    """Setup required directories."""
    print("📁 Setting up directories...")
    
    directories = [
        "chromadb",
        "logs",
        "discovery_data"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")


def run_initial_discovery():
    """Run initial schema discovery."""
    print("🔍 Running initial schema discovery...")
    
    try:
        from schema_discovery import SchemaDiscovery
        
        discovery = SchemaDiscovery()
        results = discovery.run_discovery()
        
        print(f"✅ Initial discovery completed:")
        print(f"  - Total applications: {results['summary']['total_applications']}")
        print(f"  - New applications: {results['summary']['new_applications']}")
        print(f"  - New entitlement types: {results['summary']['new_entitlement_types']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Initial discovery failed: {e}")
        return False


def generate_initial_training():
    """Generate initial training patterns."""
    print("🎯 Generating initial training patterns...")
    
    try:
        from dynamic_training_generator import DynamicTrainingGenerator
        
        generator = DynamicTrainingGenerator()
        patterns = generator.process_new_discoveries()
        
        print(f"✅ Generated {len(patterns)} initial training patterns")
        
        return True
        
    except Exception as e:
        print(f"❌ Training generation failed: {e}")
        return False


def setup_vector_database():
    """Setup vector database with training data."""
    print("🗄️ Setting up vector database...")
    
    try:
        from training_embedder import training_embedder
        
        # Embed training data
        success = training_embedder.embed_training_data(reset=True)
        
        if success:
            info = training_embedder.get_collection_info()
            print(f"✅ Vector database setup completed:")
            print(f"  - Collection: {info['collection_name']}")
            print(f"  - Total examples: {info['total_examples']}")
            print(f"  - Status: {info['status']}")
            return True
        else:
            print("❌ Vector database setup failed")
            return False
            
    except Exception as e:
        print(f"❌ Vector database setup failed: {e}")
        return False


def create_cron_job():
    """Create cron job for daily updates."""
    print("⏰ Setting up daily update schedule...")
    
    try:
        # Create a simple batch file for Windows
        batch_content = f"""@echo off
cd /d "{os.getcwd()}"
python auto_update_scheduler.py --manual-update
"""
        
        with open("daily_update.bat", "w") as f:
            f.write(batch_content)
        
        print("✅ Created daily_update.bat")
        print("💡 To schedule daily updates:")
        print("   1. Open Task Scheduler")
        print("   2. Create Basic Task")
        print("   3. Set trigger to Daily at 2:00 AM")
        print("   4. Set action to run daily_update.bat")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create cron job: {e}")
        return False


def create_configuration():
    """Create configuration file."""
    print("⚙️ Creating configuration...")
    
    config = {
        "dynamic_system": {
            "enabled": True,
            "discovery_schedule": "daily",
            "discovery_time": "02:00",
            "cleanup_schedule": "weekly",
            "cleanup_time": "03:00",
            "max_patterns_per_app": 5,
            "max_patterns_per_entitlement": 3
        },
        "vector_database": {
            "collection_name": "training_examples",
            "embedding_model": "all-MiniLM-L6-v2",
            "top_k_examples": 3
        },
        "schema_discovery": {
            "discovery_file": "schema_discovery.json",
            "generated_patterns_file": "generated_training_patterns.json",
            "scheduler_log_file": "scheduler_log.json"
        }
    }
    
    try:
        with open("dynamic_system_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration created: dynamic_system_config.json")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create configuration: {e}")
        return False


def test_system():
    """Test the dynamic system."""
    print("🧪 Testing dynamic system...")
    
    try:
        # Test schema discovery
        from schema_discovery import SchemaDiscovery
        discovery = SchemaDiscovery()
        results = discovery.run_discovery()
        
        # Test training generation
        from dynamic_training_generator import DynamicTrainingGenerator
        generator = DynamicTrainingGenerator()
        patterns = generator.process_new_discoveries()
        
        # Test vector database
        from training_embedder import training_embedder
        info = training_embedder.get_collection_info()
        
        print("✅ System test completed successfully:")
        print(f"  - Schema discovery: {results['summary']['total_applications']} applications")
        print(f"  - Training patterns: {len(patterns)} generated")
        print(f"  - Vector database: {info['total_examples']} examples")
        
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Setting up Dynamic Schema Discovery and Training System")
    print("=" * 60)
    
    setup_steps = [
        ("Installing dependencies", install_dependencies),
        ("Setting up directories", setup_directories),
        ("Creating configuration", create_configuration),
        ("Running initial discovery", run_initial_discovery),
        ("Generating initial training", generate_initial_training),
        ("Setting up vector database", setup_vector_database),
        ("Creating daily update schedule", create_cron_job),
        ("Testing system", test_system)
    ]
    
    success_count = 0
    
    for step_name, step_function in setup_steps:
        print(f"\n📋 {step_name}...")
        if step_function():
            success_count += 1
        else:
            print(f"❌ {step_name} failed")
    
    print("\n" + "=" * 60)
    print(f"🎉 Setup completed: {success_count}/{len(setup_steps)} steps successful")
    
    if success_count == len(setup_steps):
        print("\n✅ Dynamic system is ready!")
        print("\n📚 Usage:")
        print("  - Daily updates: python auto_update_scheduler.py --start")
        print("  - Manual update: python auto_update_scheduler.py --manual-update")
        print("  - Check status: python auto_update_scheduler.py --status")
        print("  - Discover new: python schema_discovery.py --discover")
        print("  - Generate patterns: python dynamic_training_generator.py --discover")
    else:
        print("\n⚠️ Some steps failed. Please check the errors above.")
        print("You can run individual steps manually to fix issues.")


if __name__ == "__main__":
    main()
