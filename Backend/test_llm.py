from sorter.llm_filter import bloomz_filter, normalize_text

# Test the problematic case
text = "REFONTE, CONCEPTION ET MAINTENANCE ÉVOLUTIVE DU SITE WEB DE L'ANME"

print("Original text:", text)
print("Normalized text:", normalize_text(text))
print()

# Test the LLM filter
result = bloomz_filter(text)
print("LLM result:", result) 