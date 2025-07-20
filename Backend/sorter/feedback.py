import mysql.connector
from sqlalchemy import create_engine
import pandas as pd
from sorter.augment import augment_with_translations  
import random
from filterproject.db_utils import table_exists

def collect_feedback(filtered_table="filtered_opp", rejected_table="rejected_opp", 
                     target_table="training_data", feedback_limit=10):

    print(f"Starting feedback collection process...")

    # Connect to MySQL
    from filterproject.db_utils import get_mysql_connection, get_sqlalchemy_engine
    conn = get_mysql_connection()
    cursor = conn.cursor()

    if not table_exists(cursor, filtered_table) or not table_exists(cursor, rejected_table):
        print(f"One or both source tables ('{filtered_table}', '{rejected_table}') do not exist. Skipping feedback collection.")
        conn.close()
        return

    # Set up engine for pandas
    engine = get_sqlalchemy_engine()

    # Query from filtered (positive examples)
    filtered_query = f"""
    SELECT consultation_id, client, intitule_projet, lien 
    FROM {filtered_table}
    WHERE consultation_id NOT IN (
        SELECT consultation_id FROM {target_table}
    )
    ORDER BY RAND()
    LIMIT {feedback_limit}
    """
    filtered_df = pd.read_sql(filtered_query, engine)
    if not filtered_df.empty:
        filtered_df["Selection"] = 1
        print(f"Collected {len(filtered_df)} positive examples")
    else:
        print(f"No records found in {filtered_table}")

    # Query from rejected (negative examples)
    rejected_query = f"""
    SELECT consultation_id, client, intitule_projet, lien 
    FROM {rejected_table}
    WHERE consultation_id NOT IN (
        SELECT consultation_id FROM {target_table}
    )
    ORDER BY RAND()
    LIMIT {feedback_limit}
    """
    rejected_df = pd.read_sql(rejected_query, engine)
    if not rejected_df.empty:
        rejected_df["Selection"] = 0
        print(f"Collected {len(rejected_df)} negative examples")
    else:
        print(f"No records found in {rejected_table}")

    # Combine both
    feedback_df = pd.concat([filtered_df, rejected_df], ignore_index=True)
    if feedback_df.empty:
        print("No feedback data collected. Exiting.")
        conn.close()
        return

    required_columns = ["consultation_id", "client", "intitule_projet", "lien", "Selection"]
    for col in required_columns:
        if col not in feedback_df.columns:
            print(f"Warning: Required column '{col}' is missing from the feedback data")

    feedback_df = feedback_df[required_columns]

    # Save as temporary table (in MySQL) — required for SQL-based translation logic
    temp_table_name = "temp_feedback_collection"
    feedback_df.to_sql(temp_table_name, engine, if_exists="replace", index=False)

    # Augmentation step still assumes SQLite; you'll need to rewrite it for MySQL later
    try:
        print("Augmenting feedback data with translations (SQLite version)...")
        augment_with_translations("db.sqlite3", temp_table_name, "intitule_projet")
        print("Augmentation complete.")
    except Exception as e:
        print(f" Error during augmentation (probably due to SQLite dependency): {e}")

    # Insert feedback into training_data (from MySQL temp table)
    try:
        cursor.execute(f"""
        INSERT INTO {target_table} (consultation_id, client, intitule_projet, lien, Selection)
        SELECT consultation_id, client, intitule_projet, lien, Selection
        FROM {temp_table_name}
        """)
        conn.commit()
        print(f" Successfully inserted feedback data into {target_table}")
    except Exception as e:
        print(f" Error adding feedback to training data: {e}")

    # Clean up
    cursor.execute(f"DROP TABLE IF EXISTS {temp_table_name}")
    conn.commit()

    cursor.close()
    conn.close()
