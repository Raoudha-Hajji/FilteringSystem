from sentence_transformers import SentenceTransformer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import numpy as np
import pandas as pd
import re
import sqlite3
import os
import pickle
from sorter.augment import translate_text
from sorter.feedback import collect_feedback
from django.conf import settings

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
    text = re.sub(r"[^\u0600-\u06FFa-zA-Z0-9\s.,:/\-()]", "", text)
    text = text.lower()
    return text

def train_with_sbert(table_name, text_column="intitule_projet", label_column="Selection"):
    collect_feedback()

    global classifier
        # Connect to SQLite and load data
    db_path="db.sqlite3"
    conn = sqlite3.connect(db_path)
    query = f'SELECT "{text_column}", {label_column} FROM {table_name} WHERE {text_column} IS NOT NULL'
    data = pd.read_sql_query(query, conn)
    conn.close()

    if text_column not in data.columns or label_column not in data.columns:
        raise ValueError(f"Required columns not found in: {data.columns.tolist()}")

    # Preprocess
    texts = data[text_column].fillna("").tolist()
    labels = data[label_column].fillna(0)
    labels = [1 if label > 0 else 0 for label in labels]

    # Embeddings
    X = extract_sbert_embeddings(texts)
    y = np.array(labels)

    # Train/test split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model
    classifier = LogisticRegression(max_iter=1000)
    classifier.fit(X_train, y_train)

    model_path = os.path.join(os.path.dirname(__file__), "..", "trained_classifier.pkl")
    model_path = os.path.abspath(model_path)
    print("Saving model to:", model_path)
    with open(model_path, "wb") as f:
        pickle.dump(classifier, f)
    print("it got saved and it worked")

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

def filter_csv(table_name, text_column="intitule_projet", threshold=0.6):
    load_classifier()

    if classifier is None:
        raise ValueError("Model not trained. Please train the model first.")
    
    # Prompt for logic guidance
    prompt = """
    Classify the following project as related to computer science, software development, or technology.
    Do not exclude projects that may not explicitly use terms like 'coding,' 'programming,' or 'software development,'
    but still involve tasks related to technology, digital systems, machine learning, AI, or IT infrastructure.
    Keep in mind that projects related to coding or technical development might not always use the exact keyword.
    Ensure that any project with a technical focus is not mistakenly labeled as unrelated.
    """

    # Define keywords for fallback
    keywords = ['web', 'logiciel', 'plateforme', 'application', "système d\'information", "site web", "logiciel", "digital"]
    arabic_keywords = [translate_text(k, source_lang="fr", target_lang="ar") for k in keywords]
    normalized_keywords = [normalize_text(k) for k in keywords + arabic_keywords]

    db_path="db.sqlite3"
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()

    # Ensure 'is_filtered' column exists
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    if 'is_filtered' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN is_filtered INTEGER DEFAULT 0")
        conn.commit()

    # Fetch rows where is_filtered = 0
    df = pd.read_sql_query(f"SELECT rowid, * FROM {table_name} WHERE is_filtered = 0", conn)

    # Debugging: Check how many rows are in the DataFrame
    print(f"Rows to process: {len(df)}")
    if len(df) == 0:
        print("No unfiltered rows to process.")
        return df  # No rows to filter

    # Normalize texts
    df[text_column] = df[text_column].fillna("")
    normalized_texts = [normalize_text(t) for t in df[text_column].tolist()]
    embeddings = extract_sbert_embeddings(normalized_texts)

    selected_rows = []
    rejected_rows = []
    selected_predictions = []
    selected_confidences = []
    rejected_predictions = []
    rejected_confidences = []

    for idx, text in enumerate(normalized_texts):
        try:
            embedding = embeddings[idx].reshape(1, -1)
            prediction = classifier.predict(embedding)[0]
            confidence = classifier.predict_proba(embedding)[0][1]

            print(f"Processing row {idx + 1}/{len(normalized_texts)}: prediction = {prediction}, confidence = {confidence}")

            row = df.iloc[idx]

            if confidence >= threshold or any(k in text for k in normalized_keywords):
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

    # Columns to retain
    keep_columns = ["consultation_id", "client", "intitule_projet", "lien"]

        # Save selected (relevant)
    if selected_rows:
        selected_df = pd.DataFrame(selected_rows)[keep_columns]
        selected_df["prediction"] = selected_predictions
        selected_df["confidence"] = selected_confidences
        selected_df["source"] = table_name
        
        # Flag the rows in the source table as filtered (only once they are processed)
        for row in selected_rows:
            unique_value = row["consultation_id"]
            cursor.execute(
                f"UPDATE {table_name} SET is_filtered = 1 WHERE consultation_id = ?",
                (unique_value,)
            )
        conn.commit()

        selected_df.to_sql("merged_filtered", conn, if_exists="append", index=False)
        print(f"✅ Saved {len(selected_df)}  selected rows.")

    # Save rejected (not relevant)
    if rejected_rows:
        rejected_df = pd.DataFrame(rejected_rows)[keep_columns]
        rejected_df["prediction"] = rejected_predictions
        rejected_df["confidence"] = rejected_confidences
        rejected_df["source"] = table_name

        for row in rejected_rows:
            unique_value = row["consultation_id"]
            cursor.execute(
                f"UPDATE {table_name} SET is_filtered = 1 WHERE consultation_id = ?",
                (unique_value,)
            )
        conn.commit()

        rejected_df.to_sql("merged_rejected", conn, if_exists="append", index=False)

        print(f"❌ Saved {len(rejected_df)} rejected rows.")

    cursor.close()
    conn.close()
        
# Optional: Example training trigger
#train_with_sbert('augmented_Opportunités.csv', text_column="Intitulé du projet", label_column="Selection")
