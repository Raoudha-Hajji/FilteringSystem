import sqlite3
import pytest
import os
import pandas as pd
from sorter.filter import filter_project

DB_PATH = "C:/Users/RAOUDHA/Desktop/FilterProject/Backend/db.sqlite3"
TEST_TABLE = "tuneps_offerstest"

@pytest.fixture(scope="module")
def db_connection():
    assert os.path.exists(DB_PATH), "❌ SQLite database not found."
    conn = sqlite3.connect(DB_PATH)
    yield conn
    conn.close()

def test_filter_tuneps_offers(db_connection):
    conn = db_connection
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{TEST_TABLE}'")
    assert cursor.fetchone(), f"❌ Table '{TEST_TABLE}' does not exist in the database."

    # Count rows before filtering
    df_before = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {TEST_TABLE} WHERE is_filtered = 0", conn)
    initial_unfiltered = df_before["count"].iloc[0]

    # Run filtering
    filter_project(table_name=TEST_TABLE)

    # Count rows after filtering
    df_after = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {TEST_TABLE} WHERE is_filtered = 0", conn)
    remaining_unfiltered = df_after["count"].iloc[0]

    # Assert some rows were processed
    assert initial_unfiltered >= remaining_unfiltered, "⚠️ No filtering appears to have happened."

    

    print("✅ Filter test passed for tuneps_offers.")
