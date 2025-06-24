import sqlite3
import re
from transformers import MarianMTModel, MarianTokenizer

# Arabic detection
def is_arabic(text):
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+')
    arabic_chars = sum(len(match) for match in arabic_pattern.findall(text))
    total_chars = len(text.strip())
    return total_chars > 0 and arabic_chars / total_chars > 0.3

# Load models (only once)
fr_ar_model_name = "Helsinki-NLP/opus-mt-fr-ar"
fr_ar_tokenizer = MarianTokenizer.from_pretrained(fr_ar_model_name)
fr_ar_model = MarianMTModel.from_pretrained(fr_ar_model_name)

ar_fr_model_name = "Helsinki-NLP/opus-mt-ar-fr"
ar_fr_tokenizer = MarianTokenizer.from_pretrained(ar_fr_model_name)
ar_fr_model = MarianMTModel.from_pretrained(ar_fr_model_name)

# Translate text
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

# Augment DB table by inserting translated rows
def augment_sqlite_with_translations(db_path, table_name, text_column):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    placeholders = ','.join(['?'] * len(columns))
    col_names = ', '.join([f'"{col}"' for col in columns])

    # Read all rows
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    # Identify index of text column
    text_idx = columns.index(text_column)

    for row in rows:
        row = list(row)
        original_text = str(row[text_idx])
        lang = "ar" if is_arabic(original_text) else "fr"
        translated_text = translate_text(original_text, lang, "fr" if lang == "ar" else "ar")
        translated_row = row.copy()
        translated_row[text_idx] = translated_text

        try:
            cursor.execute(
                f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})',
                tuple(translated_row)
            )
        except Exception as e:
            print(f"Failed to insert translated row: {e}")

    conn.commit()
    conn.close()  
    print("Augmentation complete — new translated rows inserted.")
