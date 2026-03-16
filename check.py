from mantoq.lib.buck.ipa import ipa_map
user_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
user_ipa = "ɑɐɒæɓʙβɔɕçɗɖðʤəɘɚɛɜɝɞɟʄɡɠɢʛɦɧħɥʜɨɪʝɭɬɫɮʟɱɯɰŋɳɲɴøɵɸθœɶʘɹɺɾɻʀʁɽʂʃʈʧʉʊʋⱱʌɣɤʍχʎʏʑʐʒʔʡʕʢǃᵻ"
user_punct = ";:,.!?¡¿—…\"«»\"“”"
user_punct_ipa = "̃ˈˌːˑʼ'̩'|‖ʴʰʱʲʷˠˤ˞↓↑→↗↘'̪ "

allowed = set(user_letters + user_ipa + user_punct + user_punct_ipa + ' ')

for k, v in ipa_map.items():
    for char in v:
        if char not in allowed:
            print(f'Unallowed character in {k} ({v}): {char} (U+{ord(char):04X})')
