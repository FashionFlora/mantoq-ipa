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
    "j": "ʤ",
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
            syllables[stress_idx].insert(0, "ˈ")
            
        for s in syllables:
            stressed_tokens.extend(s)
            
    return stressed_tokens


def _apply_post_lexical_rules(tokens):
    def is_cons(t):
        return t not in _VOWELS and t not in _PUNCT and t not in ['+', 'sil']

    def shorten_vowel(v):
        if v.startswith('aa'): return 'a'
        if v.startswith('AA'): return 'A'
        if v.lower().startswith('ii'): return v[0] + '0'
        if v.lower().startswith('uu'): return v[0] + '0'
        return v

    # 1. Sandhi across word boundaries
    i = 0
    while i < len(tokens):
        if tokens[i] == '+' and i >= 1 and i + 2 < len(tokens):
            if is_cons(tokens[i+1]) and is_cons(tokens[i+2]):
                last_idx = i - 1
                if tokens[last_idx] in _VOWELS:
                    tokens[last_idx] = shorten_vowel(tokens[last_idx])
                    # Remove the space for a smoother connected speech IPA if preceded by short word like fi
                    # Actually, the user prefers space mostly but shortens. We'll drop '+' so it merges and gets proper stress.
                    tokens.pop(i)
                    continue
                elif is_cons(tokens[last_idx]):
                    word1 = []
                    j = i - 1
                    while j >= 0 and tokens[j] != '+':
                        word1.insert(0, tokens[j])
                        j -= 1
                    w_str = ''.join(word1).lower()
                    if w_str.endswith('min') or w_str.endswith('mi0n'):
                        tokens.insert(i, 'a')
                    elif w_str.endswith('m'):
                        tokens.insert(i, 'u0')
                    elif w_str.endswith('w'):
                        tokens.insert(i, 'i0')
                    else:
                        tokens.insert(i, 'i0')
                    i += 1
        i += 1

    # 2. Fix I'rab before possessive pronouns
    # Split by '+', fix each word, then rejoin
    words = []
    current = []
    for t in tokens:
        if t == '+':
            words.append(current)
            current = []
        else:
            current.append(t)
    if current:
        words.append(current)
        
    for w in words:
        if len(w) < 3: continue
        w_str = ''.join(w).lower()
        if any(w_str.startswith(p) for p in ['mi0nh', 'mi0nk', 'eanh', 'eank', 'qadh', 'qadk', 'halh', 'halk', 'lamh', 'lamk', 'lanh', 'lank', 'inh', 'ink', 'wajh', 'fawh']):
            continue
            
        if is_cons(w[-3]) and w[-2] in ['h', 'k'] and not is_cons(w[-1]):
            v = 'u0'
            if w[-1] in ['aa', 'AA']: v = 'a'
            elif w[-1].lower().startswith('i'): v = 'i0'
            w.insert(-2, v)
        elif len(w) >= 4 and is_cons(w[-4]) and w[-3] in ['h', 'k'] and not is_cons(w[-2]) and w[-1] == 'm':
            v = 'i0' if w[-2].lower().startswith('i') else 'u0'
            w.insert(-3, v)
        elif len(w) >= 6 and is_cons(w[-6]) and w[-5] in ['h', 'k'] and not is_cons(w[-4]) and w[-3] == 'n' and w[-2] == 'n' and not is_cons(w[-1]):
            v = 'i0' if w[-4].lower().startswith('i') else 'u0'
            w.insert(-5, v)
        elif len(w) >= 5 and is_cons(w[-5]) and w[-4] in ['h', 'k'] and not is_cons(w[-3]) and w[-2] == 'm' and not is_cons(w[-1]):
            v = 'i0' if w[-3].lower().startswith('i') else 'u0'
            w.insert(-4, v)

    new_tokens = []
    for idx, w in enumerate(words):
        new_tokens.extend(w)
        if idx < len(words) - 1:
            new_tokens.append('+')

    return new_tokens

def phonemes_to_ipa(phonemes: str, space_separated: bool = False, as_list: bool = False):

    raw_tokens = phonemes.split()
    
    tokens = []
    for t in raw_tokens:
        if len(t) >= 2 and t[0] == t[1] and t[0] not in _VOWELS and t[0].lower() in ipa_map:
            tokens.extend([t[0], t[1:]])
        else:
            tokens.append(t)
        
    tokens = _apply_post_lexical_rules(tokens)
    tokens = _apply_stress(tokens)
    ipa_tokens = []
    
    i = 0
    while i < len(tokens):
        t = tokens[i]
        
        # Check for duplicate consecutive consonants to merge back into geminates
        if i + 1 < len(tokens) and tokens[i+1] == t and t not in _VOWELS and t in ipa_map:
            ipa_tokens.append(ipa_map[t] + "ː")
            i += 2
        elif t in ipa_map:
            ipa_tokens.append(ipa_map[t])
            i += 1
        elif len(t) >= 2 and t[0] == t[1] and t[0] in ipa_map:
            ipa_tokens.append(ipa_map[t[0]] + "ː")
            i += 1
        elif len(t) >= 2 and t[0] == t[1] and t[0].lower() in ipa_map:
            ipa_tokens.append(ipa_map[t[0].lower()] + "ː")
            i += 1
        else:
            ipa_tokens.append(t)
            i += 1
    
    if as_list:
        return list("".join(ipa_tokens))

    separator = " " if space_separated else ""
    return separator.join(ipa_tokens)

def arabic_to_ipa(arabic: str, space_separated: bool = False, as_list: bool = False):
    buckw = arabic_to_buckwalter(arabic)
    phonemes = process_utterance(buckw)
    return phonemes_to_ipa(phonemes, space_separated=space_separated, as_list=as_list)
