import requests
import re
from sorter.augment import translate_text

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

def is_arabic(text):
    return bool(re.search(r"[\u0600-\u06FF]", text))

def build_prompt(text):
    prompt = f"""
You are an expert in classifying project descriptions for IT opportunities.

Your task: Determine if this project is related to Information Technology, software development, or digital services.

ACCEPT if the project involves ANY of these:
- Web development, websites, web applications, web platforms
- Software development, programming, coding, applications
- Digital platforms, digital services, digitalization
- IT services, information systems, digital tools
- E-learning, online platforms, digital collaboration
- Database systems, APIs, IT infrastructure
- Mobile applications, digital applications
- Digital transformation, digital modernization
- IT consulting, digital consulting
- Cloud services, digital platforms
- Digital workspaces, virtual environments
- IT integration, system integration
- Digital communication tools, collaboration platforms

REJECT ONLY if clearly about:
- Physical construction (buildings, roads, bridges)
- Hardware purchases (computers, printers, equipment)
- Non-digital services (cleaning, maintenance, security)
- Vehicles, machinery, physical devices
- Agricultural, farming, or physical infrastructure
- Traditional non-digital business services

IMPORTANT: If the project mentions both digital/IT aspects AND physical elements, ACCEPT it as long as the digital/IT component is significant.

Project description: {text}

Answer with only "yes" if IT-related, "no" if clearly non-IT:
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
            # Take the last few words if no clear separator found
            response_text = full_response.split()[-3:] if len(full_response.split()) >= 3 else full_response.split()
            response_text = " ".join(response_text)

        print(f"Extracted response: '{response_text}'")

        # Expanded positive and negative indicators
        positive_words = ["oui", "نعم", "yes", "it", "accept", "approve", "valid", "good", "ok", "okay", "correct", "right", "true", "1", "one"]
        negative_words = ["non", "لا", "no", "reject", "deny", "invalid", "bad", "wrong", "false", "0", "zero"]
        
        # Check for mixed responses or unclear cases
        response_clean = response_text.strip().lower().replace('"', '').replace("'", "").replace(".", "").replace(",", "")

        print(f"Cleaned response: '{response_clean}'")
        
        # Check for exact matches first
        if response_clean in ["yes", "oui", "نعم"]:
            print("✅ Returning True (exact yes/oui match)")
            return True
        if response_clean in ["no", "non", "لا"]:
            print("❌ Returning False (exact no/non match)")
            return False
            
        # Check for positive indicators
        if any(word in response_clean for word in positive_words):
            print("✅ Returning True (positive response detected)")
            return True
            
        # Check for negative indicators
        if any(word in response_clean for word in negative_words):
            print("❌ Returning False (negative response detected)")
            return False

        # Check for mixed or unclear responses
        if len(response_clean.split()) > 3:
            # If response is long/complex, check if it contains positive IT-related keywords
            it_keywords = ["web", "software", "digital", "platform", "application", "system", "it", "information", "technology", "online", "virtual", "electronic"]
            if any(keyword in response_clean for keyword in it_keywords):
                print("✅ Returning True (long response with IT keywords)")
                return True
            else:
                print("❌ Returning False (long response without IT keywords)")
                return False

        print("⚠️ No clear response found, defaulting to False")
        return False

    except Exception as e:
        print(f"⚠️ LLM filtering error: {e}")
        # On error, be more permissive - don't reject automatically
        print("⚠️ LLM error occurred, defaulting to False (reject)")
        return False
