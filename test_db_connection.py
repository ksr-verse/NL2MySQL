#!/usr/bin/env python3
"""Test database connection."""

import mysql.connector

def test_connection():
    """Test database connection with different configurations."""
    
    configs = [
        {"host": "localhost", "port": 3306, "user": "root", "password": "", "database": "identityiq"},
        {"host": "localhost", "port": 3306, "user": "root", "password": "password", "database": "identityiq"},
        {"host": "localhost", "port": 3306, "user": "root", "password": "root", "database": "identityiq"},
        {"host": "localhost", "port": 3306, "user": "root", "password": "admin", "database": "identityiq"},
    ]
    
    for i, config in enumerate(configs, 1):
        try:
            print(f"Testing config {i}: {config['user']}@{config['host']}:{config['port']}/{config['database']}")
            conn = mysql.connector.connect(**config)
            print(f"✅ Success with config {i}")
            
            # Test a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM spt_application")
            count = cursor.fetchone()[0]
            print(f"   Found {count} applications")
            
            cursor.close()
            conn.close()
            return config
            
        except Exception as e:
            print(f"❌ Failed with config {i}: {e}")
    
    print("❌ All connection attempts failed")
    return None

if __name__ == "__main__":
    test_connection()
