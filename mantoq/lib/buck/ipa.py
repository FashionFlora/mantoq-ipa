from .phonetise_buckwalter import arabic_to_buckwalter, process_utterance

ipa_map = {
    # Consonants
    "b": "b",
    "*": "ð",
    "T": "tˤ",
    "m": "m",
    "t": "t",
    "r": "r",
    "Z": "ðˤ",
    "n": "n",
    "^": "θ",
    "z": "z",
    "E": "ʕ",
    "h": "h",
    "j": "dʒ",
    "s": "s",
    "g": "ɣ",
    "H": "ħ",
    "q": "q",
    "f": "f",
    "x": "x",
    "S": "sˤ",
    "$": "ʃ",
    "d": "d",
    "D": "dˤ",
    "k": "k",
    "<": "ʔ",
    ">": "ʔ",
    "'": "ʔ",
    "}": "ʔ",
    "&": "ʔ",
    "l": "l",
    "w": "w",
    "y": "j",
    "p": "t",
    "v": "v", # loanword
    
    # Vowels
    "aa": "aː",
    "AA": "ɑː",
    "uu0": "uː",
    "uu1": "uː",
    "UU0": "uː",
    "UU1": "uː",
    "ii0": "iː",
    "ii1": "iː",
    "II0": "iː",
    "II1": "iː",
    "a": "a",
    "A": "ɑ",
    "u0": "u",
    "u1": "u",
    "U0": "u",
    "U1": "u",
    "i0": "i",
    "i1": "i",
    "I0": "i",
    "I1": "i",
    
    "sil": " ",
    "+": " ",
    "ˈ": "ˈ"
}

_VOWELS = {"aa", "AA", "uu0", "uu1", "UU0", "UU1", "ii0", "ii1", "II0", "II1", "a", "A", "u0", "u1", "U0", "U1", "i0", "i1", "I0", "I1"}
_PUNCT = {".", ",", "?", "!", ":", ";", "؛", "،", "؟", "-", '"', "'"}

def _get_syllweight(syll):
    v_weight = 0
    coda_len = 0
    vowel_found = False
    for t in syll:
        if t in _VOWELS:
            vowel_found = True
            if len(t) >= 2 and t[:2].lower() in ['aa', 'uu', 'ii']:
                v_weight = 2
            else:
                v_weight = 1
        elif vowel_found and t not in _PUNCT:
            coda_len += 1
    
    if (v_weight == 2 and coda_len >= 1) or (v_weight == 1 and coda_len >= 2):
        return 'superheavy'
    elif (v_weight == 2 and coda_len == 0) or (v_weight == 1 and coda_len == 1):
        return 'heavy'
    else:
        return 'light'

def _apply_stress(tokens):
    words = []
    current_word = []
    for t in tokens:
        if t in ['sil', '+'] or t in _PUNCT:
            if current_word:
                words.append(current_word)
                current_word = []
            words.append([t])
        else:
            current_word.append(t)
            
    if current_word:
        words.append(current_word)
        
    stressed_tokens = []
    
    for word_tokens in words:
        if len(word_tokens) == 1 and (word_tokens[0] in ['sil', '+'] or word_tokens[0] in _PUNCT):
            stressed_tokens.extend(word_tokens)
            continue
            
        syllables = []
        current_syll = []
        
        for i, token in enumerate(word_tokens):
            is_cons = token not in _VOWELS
            next_is_vowel = (i + 1 < len(word_tokens)) and (word_tokens[i+1] in _VOWELS)
            
            if is_cons and next_is_vowel and current_syll:
                syllables.append(current_syll)
                current_syll = []
                
            current_syll.append(token)
            
        if current_syll:
            syllables.append(current_syll)
            
        stress_idx = 0
        if len(syllables) == 1:
            stress_idx = 0
        elif len(syllables) >= 2:
            last_weight = _get_syllweight(syllables[-1])
            if last_weight == 'superheavy':
                stress_idx = len(syllables) - 1
            else:
                penult_weight = _get_syllweight(syllables[-2])
                if penult_weight in ['heavy', 'superheavy'] or len(syllables) == 2:
                    stress_idx = len(syllables) - 2
                else:
                    if len(syllables) >= 4 and _get_syllweight(syllables[-3]) == 'light' and _get_syllweight(syllables[-4]) in ['heavy', 'superheavy']:
                        stress_idx = len(syllables) - 4
                    else:
                        stress_idx = len(syllables) - 3
                    
        if stress_idx < len(syllables):
            syllables[stress_idx].insert(0, 'ˈ')
            
        for s in syllables:
            stressed_tokens.extend(s)
            
    return stressed_tokens

def phonemes_to_ipa(phonemes: str, space_separated: bool = False, as_list: bool = False):
    tokens = phonemes.split()
        
    tokens = _apply_stress(tokens)
    ipa_tokens = []
    for t in tokens:
        if t in ipa_map:
            ipa_tokens.append(ipa_map[t])
        elif len(t) >= 2 and t[0] == t[1] and t[0] in ipa_map:
            ipa_tokens.append(ipa_map[t[0]] + "ː")
        elif len(t) >= 2 and t[0] == t[1] and t[0].lower() in ipa_map:
            ipa_tokens.append(ipa_map[t[0].lower()] + "ː")
        else:
            ipa_tokens.append(t)
    
    if as_list:
        return list("".join(ipa_tokens))

    separator = " " if space_separated else ""
    return separator.join(ipa_tokens)

def arabic_to_ipa(arabic: str, space_separated: bool = False, as_list: bool = False):
    buckw = arabic_to_buckwalter(arabic)
    phonemes = process_utterance(buckw)
    return phonemes_to_ipa(phonemes, space_separated=space_separated, as_list=as_list)
