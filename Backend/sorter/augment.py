import mysql.connector
import re
from transformers import MarianMTModel, MarianTokenizer
import pandas as pd

# Arabic detection
def is_arabic(text):
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+')
    arabic_chars = sum(len(match) for match in arabic_pattern.findall(text))
    total_chars = len(text.strip())
    return total_chars > 0 and arabic_chars / total_chars > 0.3

# Load translation models
fr_ar_model_name = "Helsinki-NLP/opus-mt-fr-ar"
fr_ar_tokenizer = MarianTokenizer.from_pretrained(fr_ar_model_name)
fr_ar_model = MarianMTModel.from_pretrained(fr_ar_model_name)

ar_fr_model_name = "Helsinki-NLP/opus-mt-ar-fr"
ar_fr_tokenizer = MarianTokenizer.from_pretrained(ar_fr_model_name)
ar_fr_model = MarianMTModel.from_pretrained(ar_fr_model_name)

def translate_text(text, source_lang, target_lang):
    if not text or text.strip() == "":
        return ""
    try:
        tokenizer = fr_ar_tokenizer if source_lang == "fr" else ar_fr_tokenizer
        model = fr_ar_model if source_lang == "fr" else ar_fr_model
        inputs = tokenizer(text, return_tensors="pt", padding=True)
        output = model.generate(**inputs)
        return tokenizer.decode(output[0], skip_special_tokens=True)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def augment_with_translations(table_name, text_column="intitule_projet"):
    # Connect to MySQL
    from filterproject.db_utils import get_mysql_connection
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all rows
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    if not rows:
        print("No data to translate.")
        conn.close()
        return

    columns = list(rows[0].keys())
    text_idx = columns.index(text_column)
    col_names = ", ".join(f"`{col}`" for col in columns)
    placeholders = ", ".join(["%s"] * len(columns))

    inserted_count = 0
    for row in rows:
        original_text = str(row[text_column])
        lang = "ar" if is_arabic(original_text) else "fr"
        translated_text = translate_text(original_text, lang, "fr" if lang == "ar" else "ar")

        # Copy the row and replace text with translation
        translated_row = [row[col] if col != text_column else translated_text for col in columns]

        try:
            cursor.execute(
                f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})",
                tuple(translated_row)
            )
            inserted_count += 1
        except Exception as e:
            print(f"⚠️ Failed to insert translated row: {e}")

    conn.commit()
    conn.close()
    print(f"✅ Augmentation complete — {inserted_count} translated rows inserted.")
