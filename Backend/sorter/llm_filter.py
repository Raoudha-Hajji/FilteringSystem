import requests
import re
from sorter.augment import translate_text

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

def is_arabic(text):
    return bool(re.search(r"[\u0600-\u06FF]", text))

def build_prompt(text):
    prompt = f"""
You are an expert in classifying project descriptions.

Your task: Decide if the following project is related to Information Technology (IT) and is focused on software, digital platforms, or IT services. 
- Accept only if the project is about software, digital solutions, IT services, or online platforms.
- Reject any project that is mainly about hardware, equipment, physical devices, or includes significant hardware purchases, even if software is also mentioned.
- Reject all non-IT projects (e.g., construction, vehicles, cleaning, physical infrastructure, etc.).

Reply with only "yes" if the project is IT-related and not focused on hardware. Reply with only "no" for hardware-focused or non-IT projects. Do not explain your answer.

Project title: {text}
Answer:
"""
    return prompt

def mistral_filter(text):
    print(f"LLM called with: {text}")
    prompt = build_prompt(text)
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        full_response = result.get("response", "").strip().lower()
        print(f"Ollama response: {full_response}")

        # Extract only the actual response part (after "answer:" or "réponse:")
        response_text = ""
        if "answer:" in full_response:
            response_text = full_response.split("answer:")[-1].strip()
        elif "réponse:" in full_response:
            response_text = full_response.split("réponse:")[-1].strip()
        elif "الجواب:" in full_response:
            response_text = full_response.split("الجواب:")[-1].strip()
        else:
            response_text = full_response.split()[-3:] if len(full_response.split()) >= 3 else full_response.split()
            response_text = " ".join(response_text)

        print(f"Extracted response: '{response_text}'")

        positive_words = ["oui", "نعم", "yes", "it"]
        negative_words = ["non", "لا", "no"]
        response_clean = response_text.strip().lower().replace('"', '').replace("'", "")

        print(f"Cleaned response: '{response_clean}'")
        print(f"Positive words found: {[word for word in positive_words if response_clean == word]}")
        print(f"Negative words found: {[word for word in negative_words if response_clean == word]}")

        if response_clean == "yes" or response_clean == "oui":
            print("✅ Returning True (yes/oui)")
            return True
        if response_clean == "no" or response_clean == "non":
            print("❌ Returning False (no/non)")
            return False
        if any(word in response_clean for word in positive_words):
            print("✅ Returning True (positive response)")
            return True
        if any(word in response_clean for word in negative_words):
            print("❌ Returning False (negative response)")
            return False

        print("⚠️ No clear response found, defaulting to False")
        return False

    except Exception as e:
        print(f"⚠️ LLM filtering error: {e}")
        return False
