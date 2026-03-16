from mantoq.lib.buck.phonetise_buckwalter import arabic_to_buckwalter, process_utterance
from mantoq.lib.buck.ipa import arabic_to_ipa

test_words = [
    "مَدْرَسَةٌ",       # madrasatun
    "كِتَابٌ",        # kitaabun
    "مُسْتَشْفَى",      # mustashfa
    "جَامِعَة",        # jaami'ah
    "طَالِب",        # Taalib
    "مُهَنْدِس",       # muhandis
    "كَبِير",        # kabiir
    "صَغِيرَة",       # Saghiirah
    "إِسْتِقْبَال",     # istiqbaal
    "مُشْكِلَة",       # mushkilah
    "سَيَّارَة",        # sayyaarah
    "طَائِرَة",        # Taa'irah
    "جُمْهُورِيَّة",      # jumhuuriyyah
    "إِقْتِصَاد",       # iqtiSaad
    "مُسْتَقْبَل",      # mustaqbal
    "حَيَاة",         # Hayaah
    "مَكْتَبَة",        # maktabah
    "تِلِيفُون",       # tiliifuun
    "كُومْبْيُوتَر",     # kuumbyuutar
    "سَلَام",         # salaam
    "شُكْرًا"         # shukran
]

def main():
    print("=" * 60)
    for i, word in enumerate(test_words, 1):
        buckw_raw = arabic_to_buckwalter(word)
        mantoq_phonemes = process_utterance(buckw_raw)
        ipa_stressed = arabic_to_ipa(word, space_separated=True)
        
        print(f"[{i}] Original Arabic: {word}")
        print(f"    Buckwalter Phons: {mantoq_phonemes}")
        print(f"    IPA with stress : {ipa_stressed}")
        print("-" * 60)

if __name__ == "__main__":
    main()
