import mantoq

tekst = "مَرْحَبًا خَالِدْ"

print("=== TEKST WEJŚCIOWY ===")
print(tekst)
print()

# Przed translacją na IPA (oryginalne fonemy Mantoq)
print("--- PRZED: Oryginalny format Buckwalter (Mantoq) ---")
original_phonemes = mantoq.arabic_to_phonemes(tekst)
print(original_phonemes)
print()

# Po translacji na IPA
print("--- PO: Przekonwertowane na IPA ---")
ipa_spaced = mantoq.arabic_to_ipa(tekst, space_separated=True)
print(ipa_spaced)
print()

# Po translacji na listę
print("--- PO: Lista elementów ---")
ipa_list = mantoq.arabic_to_ipa(tekst, as_list=True)
print(ipa_list)

