"""
Database utility functions for centralized MySQL connections
"""
import mysql.connector
from django.conf import settings
from sqlalchemy import create_engine


def get_mysql_connection():

    return mysql.connector.connect(**settings.MYSQL_CONFIG)


def get_sqlalchemy_engine():

    return create_engine(settings.SQLALCHEMY_DATABASE_URL) 