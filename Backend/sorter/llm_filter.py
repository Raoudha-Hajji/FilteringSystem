from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import re 
from sorter.augment import translate_text

# Load model and tokenizer
model_name = "bigscience/bloomz-1b7"
local_dir = "./models/bloomz-1b7"  # relative path inside your project

# This will download and save the model and tokenizer to local_dir
tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=local_dir)
model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir=local_dir)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Detect if Arabic (simple heuristic based on presence of Arabic letters)
def is_arabic(text):
    return bool(re.search(r"[\u0600-\u06FF]", text))

# Build the prompt depending on language
def build_prompt(text):
    # Use English prompt for all languages (BLOOMZ is multilingual)
    prompt = f"""
You are an expert in IT project classification. Your task is to determine whether the following project title is related to **Information Technology (IT)** or not.

IT = "yes" ONLY if the project contains:
- website, web, site web, site internet
- application, software, system, logiciel
- development, programming, développement
- maintenance informatique, IT maintenance
- cybersecurity, cybersécurité
- database, base de données, API
- redesign, refonte, conception informatique
- platform, plateforme (digital/software)
- digitalization, digitalisation
- online services, services en ligne

CRITICAL: NON-IT = "no" if the project contains ANY of these:
- truck, camion, vehicle, véhicule, transport
- construction, bâtiment, infrastructure
- equipment, matériel, achat, acquisition
- cleaning, nettoyage, security, gardiennage
- physical platform, plateforme physique
- scanner, printer, hardware purchase
- environmental study, étude environnementale
- physical services, services physiques
- scanners, imprimantes, équipements physiques
- acquisition de matériel (even if it includes software)

IMPORTANT RULES:
1. Hardware purchases (scanners, printers, equipment) are ALWAYS "no", even if software is included
2. Environmental studies are ALWAYS "no"
3. Physical equipment acquisition is ALWAYS "no"
4. Only pure software development, digital platforms, and IT services should be "yes"

IMPORTANT: Reject any project that includes **hardware or physical items**, even if it also mentions **software**. Hardware + software = "no".

Examples:
- "website development" → yes
- "développement site web" → yes
- "plateforme digitale" → yes
- "digitalisation services" → yes
- "truck rental" → no
- "location camion" → no
- "acquisition matériel" → no (even with software)
- "scanners avec logiciel" → no (hardware purchase)
- "étude environnementale" → no
- "acquisition matériels informatiques" → no (hardware purchase)

Project: {text}
Answer:"""

    return prompt

# Main function to be called from filter_project
def bloomz_filter(text):
    print(f"LLM called with: {text}")  # Debug: show input
    
    # Use the text directly without translation (BLOOMZ is multilingual)
    classification_text = text
    
    prompt = build_prompt(classification_text)
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(device)
        outputs = model.generate(**inputs, max_new_tokens=3)
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=True).strip().lower()
        
        # Extract only the actual response part (after "answer:" or "réponse:")
        response = ""
        if "answer:" in full_response:
            response = full_response.split("answer:")[-1].strip()
        elif "réponse:" in full_response:
            response = full_response.split("réponse:")[-1].strip()
        elif "الجواب:" in full_response:
            response = full_response.split("الجواب:")[-1].strip()
        else:
            # Fallback: take the last few words
            response = full_response.split()[-3:] if len(full_response.split()) >= 3 else full_response.split()
            response = " ".join(response)
        
        print(f"Extracted response: '{response}'")  # Debug: show extracted response

        # Check for positive and negative responses
        positive_words = ["oui", "نعم", "yes", "it"]
        negative_words = ["non", "لا", "no"]
        response_clean = response.strip().lower()
        
        # Clean up quotes and extra characters
        response_clean = response_clean.replace('"', '').replace("'", "").strip()
        
        print(f"Cleaned response: '{response_clean}'")  # Debug: show cleaned response
        print(f"Positive words found: {[word for word in positive_words if response_clean == word]}")
        print(f"Negative words found: {[word for word in negative_words if response_clean == word]}")
        
        # Check for exact matches first
        if response_clean == "yes" or response_clean == "oui":
            print("✅ Returning True (yes/oui)")
            return True
        
        if response_clean == "no" or response_clean == "non":
            print("❌ Returning False (no/non)")
            return False
            
        # If no exact match, check for partial matches
        if any(word in response_clean for word in positive_words):
            print("✅ Returning True (positive response)")
            return True
        
        if any(word in response_clean for word in negative_words):
            print("❌ Returning False (negative response)")
            return False
            
        # If neither positive nor negative words found, default to False
        print("⚠️ No clear response found, defaulting to False")
        return False
        
    except Exception as e:
        print(f"⚠️ LLM filtering error: {e}")
        return False
