from sentence_transformers import SentenceTransformer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import numpy as np
import pandas as pd
import re
import mysql.connector
import os
import pickle
from sorter.augment import translate_text
from sorter.feedback import collect_feedback
from django.conf import settings
from sorter.llm_filter import mistral_filter
import unicodedata
from sqlalchemy import create_engine
from filterproject.db_utils import table_exists, get_mysql_connection, get_database_name, get_sqlalchemy_engine

# Load multilingual Sentence-BERT model
sbert_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')

# Global classifier
classifier = None

def extract_sbert_embeddings(texts, batch_size=10):
    return sbert_model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True,
        batch_size=batch_size
    )

def normalize_text(text):
    # Unicode normalization (NFC is usually best for NLP)
    text = unicodedata.normalize('NFC', text)
    
    # Replace smart quotes with standard ones
    text = text.replace("'", "'").replace("'", "'").replace("`", "'")
    text = text.replace(""", '"').replace(""", '"')
    
    # Remove control characters and excessive whitespace
    text = re.sub(r'\\s+', ' ', text)
    text = text.strip()
    
    # Replace special characters with spaces instead of deleting them
    special_chars = r'[^\w\s\u00C0-\u00FF\u0600-\u06FF.,:/\-()\'""]'
    text = re.sub(special_chars, ' ', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def train_with_sbert(table_name, text_column="intitule_projet", label_column="Selection"):
    collect_feedback()

    global classifier

    # MySQL connection
    conn = get_mysql_connection()

    query = f"SELECT {text_column}, {label_column} FROM {table_name} WHERE {text_column} IS NOT NULL"

    # Use SQLAlchemy for Pandas compatibility
    engine = get_sqlalchemy_engine()
    data = pd.read_sql(query, engine)

    conn.close()

    # Check required columns
    if text_column not in data.columns or label_column not in data.columns:
        raise ValueError(f"Required columns not found in: {data.columns.tolist()}")

    # Preprocessing
    texts = data[text_column].fillna("").tolist()
    labels = data[label_column].fillna(0)
    labels = [1 if label > 0 else 0 for label in labels]

    # Embeddings
    X = extract_sbert_embeddings(texts)
    y = np.array(labels)

    # Split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model
    classifier = LogisticRegression(max_iter=1000)
    classifier.fit(X_train, y_train)

    model_path = os.path.join(os.path.dirname(__file__), "..", "trained_classifier.pkl")
    model_path = os.path.abspath(model_path)
    print("Saving model to:", model_path)

    with open(model_path, "wb") as f:
        pickle.dump(classifier, f)
    print("Model saved successfully.")

    # Evaluation
    train_acc = classifier.score(X_train, y_train)
    val_acc = classifier.score(X_val, y_val)
    print(f"Train Accuracy: {train_acc:.4f}, Validation Accuracy: {val_acc:.4f}")

    y_pred = classifier.predict(X_val)
    print(classification_report(y_val, y_pred))

    return val_acc

def load_classifier():
    global classifier
    model_path = os.path.join(os.path.dirname(__file__), "..", "trained_classifier.pkl")
    model_path = os.path.abspath(model_path)
    if os.path.exists(model_path):
        with open(model_path, "rb") as f:
            classifier = pickle.load(f)
    else:
        print(f"[WARNING] Model file not found at: {model_path}")

def predict(text):
    load_classifier()
    embedding = extract_sbert_embeddings([text])
    prediction = classifier.predict(embedding)[0]
    confidence = classifier.predict_proba(embedding)[0][1]
    return prediction, confidence

def load_keywords_translated():
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT keyword_fr FROM keywords")
    rows = cursor.fetchall()
    conn.close()

    keywords_fr = [row[0] for row in rows]

    # Translate each keyword from French to Arabic
    keywords_ar = [translate_text(k, source_lang="fr", target_lang="ar") for k in keywords_fr]

    # Normalize all keywords (French + Arabic)
    normalized_keywords = []
    for kw_fr, kw_ar in zip(keywords_fr, keywords_ar):
        normalized_keywords.append(normalize_text(kw_fr))
        normalized_keywords.append(normalize_text(kw_ar))

    return normalized_keywords

def filter_project(table_name, text_column="intitule_projet", threshold=0.6):
    load_classifier()

    if classifier is None:
        raise ValueError("Model not trained. Please train the model first.")

    normalized_keywords = load_keywords_translated()

    # Connect to MySQL
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)

    # SQLAlchemy engine for to_sql
    engine = get_sqlalchemy_engine()

    # Ensure 'is_filtered' column exists
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'filter_db'
    """, (table_name,))
    columns = [col["COLUMN_NAME"] for col in cursor.fetchall()]

    if 'is_filtered' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN is_filtered TINYINT DEFAULT 0")
        conn.commit()

    # Fetch unfiltered rows
    df = pd.read_sql(f"SELECT * FROM {table_name} WHERE is_filtered = 0", conn)

    print(f"Rows to process: {len(df)}")
    if len(df) == 0:
        print("No unfiltered rows to process.")
        return df

    df[text_column] = df[text_column].fillna("")
    normalized_texts = [normalize_text(t) for t in df[text_column].tolist()]
    embeddings = extract_sbert_embeddings(normalized_texts)

    selected_rows, rejected_rows = [], []
    selected_predictions, selected_confidences = [], []
    rejected_predictions, rejected_confidences = [], []

    BORDERLINE_LOW = 0.4
    BORDERLINE_HIGH = 0.59

    for idx, text in enumerate(normalized_texts):
        try:
            embedding = embeddings[idx].reshape(1, -1)
            prediction = classifier.predict(embedding)[0]
            confidence = classifier.predict_proba(embedding)[0][1]

            print(f"Processing row {idx + 1}/{len(normalized_texts)}: prediction = {prediction}, confidence = {confidence}")
            row = df.iloc[idx]

            keyword_match = any(k in text for k in normalized_keywords)
            is_borderline = BORDERLINE_LOW <= confidence < BORDERLINE_HIGH
            use_llm = confidence >= threshold or keyword_match or is_borderline

            if use_llm and mistral_filter(text):
                selected_rows.append(row)
                selected_predictions.append(int(prediction))
                selected_confidences.append(float(confidence))
            else:
                rejected_rows.append(row)
                rejected_predictions.append(int(prediction))
                rejected_confidences.append(float(confidence))

        except Exception as e:
            print(f"⚠️ Error processing row {idx + 1}: {e}")
            continue

    keep_columns = ["consultation_id", "client", "intitule_projet", "lien"]

    # === Save selected rows ===
    if selected_rows:
        selected_df = pd.DataFrame(selected_rows)[keep_columns]
        selected_df["prediction"] = selected_predictions
        selected_df["confidence"] = selected_confidences
        selected_df["source"] = table_name

        existing_ids = set()
        if table_exists(cursor, "filtered_opp") and len(selected_df) > 0:
            placeholders = ",".join(["%s"] * len(selected_df["consultation_id"]))
            query = f"SELECT consultation_id FROM filtered_opp WHERE consultation_id IN ({placeholders})"
            cursor.execute(query, tuple(selected_df["consultation_id"]))
            existing_ids = set(row["consultation_id"] for row in cursor.fetchall())

        selected_df = selected_df[~selected_df["consultation_id"].isin(existing_ids)]

        for row in selected_df["consultation_id"]:
            cursor.execute(
                f"UPDATE {table_name} SET is_filtered = 1 WHERE consultation_id = %s",
                (row,)
            )
        conn.commit()

        selected_df.to_sql("filtered_opp", engine, if_exists="append", index=False)
        print(f"✅ Saved {len(selected_df)} selected rows.")

    # === Save rejected rows ===
    if rejected_rows:
        rejected_df = pd.DataFrame(rejected_rows)[keep_columns]
        rejected_df["prediction"] = rejected_predictions
        rejected_df["confidence"] = rejected_confidences
        rejected_df["source"] = table_name

        existing_ids = set()
        if table_exists(cursor, "rejected_opp") and len(rejected_df) > 0:
            placeholders = ",".join(["%s"] * len(rejected_df["consultation_id"]))
            query = f"SELECT consultation_id FROM rejected_opp WHERE consultation_id IN ({placeholders})"
            cursor.execute(query, tuple(rejected_df["consultation_id"]))
            existing_ids = set(row["consultation_id"] for row in cursor.fetchall())

        rejected_df = rejected_df[~rejected_df["consultation_id"].isin(existing_ids)]

        for row in rejected_df["consultation_id"]:
            cursor.execute(
                f"UPDATE {table_name} SET is_filtered = 1 WHERE consultation_id = %s",
                (row,)
            )
        conn.commit()

        rejected_df.to_sql("rejected_opp", engine, if_exists="append", index=False)
        print(f"❌ Saved {len(rejected_df)} rejected rows.")

    cursor.close()
    conn.close()

        
'''Keywords CRUD and refiltering'''
        
def add_keyword(keyword_fr):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO keywords (keyword_fr) VALUES (%s)", (keyword_fr,))
    conn.commit()
    conn.close()

def update_keyword(keyword_id, new_keyword_fr):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE keywords SET keyword_fr = %s, last_updated = CURRENT_TIMESTAMP WHERE id = %s",
        (new_keyword_fr, keyword_id)
    )
    conn.commit()
    conn.close()

def delete_keyword(keyword_id):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM keywords WHERE id = %s", (keyword_id,))
    conn.commit()
    conn.close()

def get_source_tables():
    conn = get_mysql_connection()
    cursor = conn.cursor()
    db_name = get_database_name()
    # Get all table names
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (db_name,))
    all_tables = [row[0] for row in cursor.fetchall()]
    source_tables = []
    for table in all_tables:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = %s
        """, (table, db_name))
        columns = [col[0] for col in cursor.fetchall()]
        if ("consultation_id" in columns) and ("Selection" not in columns) and ("source" not in columns):
            source_tables.append(table)
    cursor.close()
    conn.close()
    return source_tables

def re_filter():
    tables = get_source_tables()
    normalized_keywords = load_keywords_translated()
    conn = get_mysql_connection()
    cursor = conn.cursor()
    for table in tables:
        like_clauses = [f"intitule_projet LIKE '%{{kw}}%'" for kw in normalized_keywords]
        where_clause = " OR ".join(like_clauses)

        sql_update = f"""
        UPDATE {table}
        SET is_filtered = 0
        WHERE is_filtered = 1 AND ({where_clause})
        """
        cursor.execute(sql_update)
        updated_count = cursor.rowcount
        print(f"Reset {updated_count} rows in table {table}")

        conn.commit()

        filter_project(table_name=table)

    cursor.close()
    conn.close()

def build_prompt(text):
    prompt = f"""
You are an expert in classifying project descriptions.

Your task: Decide if the following project is related to Information Technology (IT) and is focused on software, digital platforms, or IT services. 
- Accept only if the project is about software, digital solutions, IT services, or online platforms.
- Reject any project that is mainly about hardware, equipment, physical devices, or includes significant hardware purchases, even if software is also mentioned.
- Reject all non-IT projects (e.g., construction, roads, lighting, vehicles, cleaning, physical infrastructure, public works, etc.).

Examples:
- "website development" → yes
- "digital platform for e-learning" → yes
- "purchase of computers and printers" → no
- "building construction" → no
- "expanding public lighting network" → no
- "road works" → no

Reply with only "yes" if the project is IT-related and not focused on hardware. Reply with only "no" for hardware-focused or non-IT projects. Do not explain your answer.

Project title: {text}
Answer:
"""
    return prompt