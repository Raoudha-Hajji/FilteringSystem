from sorter.llm_filter import bloomz_filter

# Test examples
example1 = "REFONTE, CONCEPTION ET MAINTENANCE ÉVOLUTIVE DU SITE WEB DE L'ANME"
example2 = "Location camion semi-remorque avec plateforme plateau pour dégagement RAB. Suivant les spécifications techniques en pièce jointe."
example1_ar = "إعادة تصميم وتطوير وصيانة تطورية لموقع الويب الخاص بالوكالة الوطنية للطاقة المتجددة"
example2_ar = "تأجير شاحنة نصف مقطورة مع منصة مسطحة لإزالة الحطام. حسب المواصفات التقنية المرفقة."

print("=" * 80)
print("TESTING EXAMPLE 1 (French):")
print(f"Text: {example1}")
print("-" * 40)
result1 = bloomz_filter(example1)
print(f"Result: {result1}")
print("=" * 80)

print("\nTESTING EXAMPLE 1 (Arabic):")
print(f"Text: {example1_ar}")
print("-" * 40)
result1_ar = bloomz_filter(example1_ar)
print(f"Result: {result1_ar}")
print("=" * 80)

print("\nTESTING EXAMPLE 2 (French):")
print(f"Text: {example2}")
print("-" * 40)
result2 = bloomz_filter(example2)
print(f"Result: {result2}")
print("=" * 80)

print("\nTESTING EXAMPLE 2 (Arabic):")
print(f"Text: {example2_ar}")
print("-" * 40)
result2_ar = bloomz_filter(example2_ar)
print(f"Result: {result2_ar}")
print("=" * 80)

print(f"\nSUMMARY:")
print(f"Example 1 (Website, French): {'✅ ACCEPTED' if result1 else '❌ REJECTED'}")
print(f"Example 1 (Website, Arabic): {'✅ ACCEPTED' if result1_ar else '❌ REJECTED'}")
print(f"Example 2 (Truck rental, French): {'✅ ACCEPTED' if result2 else '❌ REJECTED'}")
print(f"Example 2 (Truck rental, Arabic): {'✅ ACCEPTED' if result2_ar else '❌ REJECTED'}") 