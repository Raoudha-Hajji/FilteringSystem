#!/usr/bin/env python3
"""
Test script to verify centralized database connection
"""
import os
import sys
import django

# Add the Backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'filterproject.settings')
django.setup()

from filterproject.db_utils import get_mysql_connection, get_sqlalchemy_engine
from django.conf import settings

def test_connections():
    print("Testing centralized database connections...")
    
    # Test MySQL connection
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"✅ MySQL connection successful: {result}")
        conn.close()
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
    
    # Test SQLAlchemy connection
    try:
        engine = get_sqlalchemy_engine()
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print(f"✅ SQLAlchemy connection successful: {result.fetchone()}")
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
    
    # Print current settings
    print(f"\n📋 Current database settings:")
    print(f"   Host: {settings.MYSQL_CONFIG['host']}")
    print(f"   User: {settings.MYSQL_CONFIG['user']}")
    print(f"   Database: {settings.MYSQL_CONFIG['database']}")
    print(f"   Port: {settings.MYSQL_CONFIG['port']}")

if __name__ == "__main__":
    test_connections() 