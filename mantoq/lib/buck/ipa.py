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
    "+": " "
}

def phonemes_to_ipa(phonemes: str, space_separated: bool = False, as_list: bool = False):
    tokens = phonemes.split()
    ipa_tokens = []
    for t in tokens:
        mapped = ipa_map.get(t, t)
        if mapped:
            ipa_tokens.append(mapped)
    
    if as_list:
        return list("".join(ipa_tokens))

    separator = " " if space_separated else ""
    return separator.join(ipa_tokens)

def arabic_to_ipa(arabic: str, space_separated: bool = False, as_list: bool = False):
    buckw = arabic_to_buckwalter(arabic)
    phonemes = process_utterance(buckw)
    return phonemes_to_ipa(phonemes, space_separated=space_separated, as_list=as_list)
