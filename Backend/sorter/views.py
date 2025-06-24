from django.shortcuts import render
import sqlite3
from django.http import JsonResponse

def get_filtered_table(request):
    db_path = "db.sqlite3"  # adjust path if needed
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT consultation_id, client, intitule_projet, lien, source
        FROM merged_filtered
        ORDER BY confidence DESC
    """)
    rows = cursor.fetchall()

    # Optional: column names if needed
    column_names = [desc[0] for desc in cursor.description]

    data = [dict(zip(column_names, row)) for row in rows]

    conn.close()
    return JsonResponse(data, safe=False)

def get_rejected_table(request):
    db_path = "db.sqlite3"  # adjust path if needed
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT consultation_id, client, intitule_projet, lien, source
        FROM merged_rejected
        ORDER BY confidence DESC
    """)
    rows = cursor.fetchall()

    # Optional: column names if needed
    column_names = [desc[0] for desc in cursor.description]

    data = [dict(zip(column_names, row)) for row in rows]

    conn.close()
    return JsonResponse(data, safe=False)

