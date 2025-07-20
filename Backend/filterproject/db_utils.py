"""
Database utility functions for centralized MySQL connections
"""
import mysql.connector
from django.conf import settings
from sqlalchemy import create_engine


def get_database_name():
    """Get the database name from settings"""
    return settings.MYSQL_CONFIG['database']


def get_mysql_connection():
    return mysql.connector.connect(**settings.MYSQL_CONFIG)


def get_sqlalchemy_engine():
    return create_engine(settings.SQLALCHEMY_DATABASE_URL)


def table_exists(cursor, table_name):
    """Check if a table exists in the configured database"""
    db_name = get_database_name()
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = %s
    """, (db_name, table_name))
    return cursor.fetchone() is not None 