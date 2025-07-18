import sqlite3

def drop_duplicates():
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    # Delete duplicates keeping the row with the smallest rowid per consultation_id
    cursor.execute("""
    DELETE FROM merged_filtered
    WHERE rowid NOT IN (
        SELECT MIN(rowid)
        FROM merged_filtered
        GROUP BY consultation_id
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Duplicates dropped based on consultation_id.")

drop_duplicates()
