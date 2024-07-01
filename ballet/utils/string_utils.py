import unicodedata

def clean(input_string):
    no_spaces = input_string.replace(' ', '_')
    no_coma = no_spaces.replace(',', '_')
    no_parl = no_coma.replace('(', '_')
    no_parr = no_parl.replace(')', '_')
    normalized = unicodedata.normalize('NFD', no_parr)
    no_accents = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
    return no_accents

def startswith(s1, s2):
    return s1[0:len(s2)] == s2