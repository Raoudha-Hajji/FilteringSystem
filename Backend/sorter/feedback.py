import sqlite3
import pandas as pd
import random
from sorter.augment import augment_sqlite_with_translations

def table_exists(conn, table_name):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def collect_feedback(filtered_table="merged_filtered", rejected_table="merged_rejected", 
                     target_table="training_data", feedback_limit=10):

    print(f"Starting feedback collection process...")
    
    # Connect to the database
    db_path = "db.sqlite3"
    conn = sqlite3.connect(db_path, timeout=30)

    if not table_exists(conn, filtered_table) or not table_exists(conn, rejected_table):
        print(f"One or both source tables ('{filtered_table}', '{rejected_table}') do not exist. Skipping feedback collection.")
        conn.close()
        return
    
    # Create a temporary table to hold our feedback data
    temp_table_name = "temp_feedback_collection"
    
    # Drop the temp table if it exists
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {temp_table_name}")
    conn.commit()
    
    # Get data from filtered table (positive examples)
    filtered_query = f"""
    SELECT consultation_id, client, intitule_projet, lien 
    FROM {filtered_table}
    WHERE consultation_id NOT IN (
    SELECT consultation_id FROM {target_table})
    ORDER BY RANDOM()
    LIMIT {feedback_limit}
    """
    filtered_df = pd.read_sql_query(filtered_query, conn)
    if not filtered_df.empty:
        filtered_df["Selection"] = 1  # Mark as positive examples
        print(f"Collected {len(filtered_df)} positive examples")
    else:
        print(f"No records found in {filtered_table}")
    
    # Get data from rejected table (negative examples)
    rejected_query = f"""
    SELECT consultation_id, client, intitule_projet, lien 
    FROM {rejected_table}
    WHERE consultation_id NOT IN (
    SELECT consultation_id FROM {target_table})
    ORDER BY RANDOM()
    LIMIT {feedback_limit}
    """
    rejected_df = pd.read_sql_query(rejected_query, conn)
    if not rejected_df.empty:
        rejected_df["Selection"] = 0  # Mark as negative examples
        print(f"Collected {len(rejected_df)} negative examples")
    else:
        print(f"No records found in {rejected_table}")
    
    # Combine the datasets
    feedback_df = pd.concat([filtered_df, rejected_df], ignore_index=True)
    
    if feedback_df.empty:
        print("No feedback data collected. Exiting.")
        conn.close()
        return
    
    # Since all tables share the same column names, we can use the dataframe as is
    # Just make sure we're only working with the columns we need
    required_columns = ["consultation_id", "client", "intitule_projet", "lien", "Selection"]
    
    # Ensure we have all required columns
    for col in required_columns:
        if col not in feedback_df.columns:
            print(f"Warning: Required column '{col}' is missing from the feedback data")
    
    # Use only the columns we need
    feedback_df = feedback_df[required_columns]
    
    # Create temporary table with the feedback data
    feedback_df.to_sql(temp_table_name, conn, if_exists="replace", index=False)
    
    # Use the existing augment function to add translations
    try:
        print("Augmenting feedback data with translations...")
        augment_sqlite_with_translations(db_path, temp_table_name, "intitule_projet")
        print("Augmentation complete.")
    except Exception as e:
        print(f"Error during augmentation: {e}")
    
    # Move the data (original + augmented) from temp table to training data
    try:
        cursor.execute(f"""
        INSERT INTO {target_table} (consultation_id, client, intitule_projet, lien, Selection)
        SELECT consultation_id, client, intitule_projet, lien, Selection
        FROM {temp_table_name}
        """)
        
        # Get count of inserted rows
        cursor.execute(f"SELECT COUNT(*) FROM {temp_table_name}")
        row_count = cursor.fetchone()[0]
        
        conn.commit()
        print(f"Successfully added {row_count} feedback rows (original + augmented) to {target_table}")
    except Exception as e:
        print(f"Error adding feedback to training data: {e}")
    
    # Clean up - drop the temporary table
    cursor.execute(f"DROP TABLE IF EXISTS {temp_table_name}")
    conn.commit()
    
    conn.close()

