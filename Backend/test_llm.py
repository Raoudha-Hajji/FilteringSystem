from sorter.llm_filter import mistral_filter, normalize_text

# Test the problematic case
text = "REFONTE, CONCEPTION ET MAINTENANCE ÉVOLUTIVE DU SITE WEB DE L'ANME"

print("Original text:", text)
print("Normalized text:", normalize_text(text))
print()

# Test the LLM filter
result = mistral_filter(text)
print("LLM result:", result) 