
import sys
with open('mantoq/lib/buck/phonetise_buckwalter.py', encoding='utf-8') as f:
    text = f.read()
    s = re.search(r'vowelMap = .*?}', text, re.DOTALL)
    if s: print(s.group(0))
