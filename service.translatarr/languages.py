# -*- coding: utf-8 -*-

# -----------------------------
# Languages dictionary (alphabetical)
# -----------------------------
LANGUAGES = {
    "0": ("Arabic", "ar"),
    "1": ("Catalan", "ca"),
    "2": ("Chinese", "zh"),
    "3": ("Croatian", "hr"),
    "4": ("Czech", "cs"),
    "5": ("Danish", "da"),
    "6": ("Dutch", "nl"),
    "7": ("English", "en"),
    "8": ("Finnish", "fi"),
    "9": ("French", "fr"),
    "10": ("German", "de"),
    "11": ("Greek", "el"),
    "12": ("Hebrew", "he"),
    "13": ("Hindi", "hi"),
    "14": ("Hungarian", "hu"),
    "15": ("Italian", "it"),
    "16": ("Japanese", "ja"),
    "17": ("Korean", "ko"),
    "18": ("Norwegian", "no"),
    "19": ("Polish", "pl"),
    "20": ("Portuguese", "pt"),
    "21": ("Romanian", "ro"),
    "22": ("Russian", "ru"),
    "23": ("Slovenian", "sl"),
    "24": ("Spanish", "es"),
    "25": ("Swedish", "sv"),
    "26": ("Thai", "th"),
    "27": ("Turkish", "tr"),
    "28": ("Vietnamese", "vi")
}

# -----------------------------
# ISO variants mapping
# -----------------------------
ISO_VARIANTS = {
    "ar": ["ar", "ara"],
    "ca": ["ca", "cat"],
    "zh": ["zh", "chi", "zho"],
    "hr": ["hr", "hrv"],
    "cs": ["cs", "cze", "ces"],
    "da": ["da", "dan"],
    "nl": ["nl", "dut", "nld"],
    "en": ["en", "eng"],
    "fi": ["fi", "fin"],
    "fr": ["fr", "fra", "fre"],
    "de": ["de", "ger", "deu"],
    "el": ["el", "gre", "ell"],
    "he": ["he", "heb"],
    "hi": ["hi", "hin"],
    "hu": ["hu", "hun"],
    "it": ["it", "ita"],
    "ja": ["ja", "jpn"],
    "ko": ["ko", "kor"],
    "no": ["no", "nor"],
    "pl": ["pl", "pol"],
    "pt": ["pt", "por"],
    "ro": ["ro", "ron", "rum"],
    "ru": ["ru", "rus"],
    "sl": ["sl", "slv"],
    "es": ["es", "spa"],
    "sv": ["sv", "swe"],
    "th": ["th", "tha"],
    "tr": ["tr", "tur"],
    "vi": ["vi", "vie"]
}

# -----------------------------
# Functions
# -----------------------------
def get_lang_params(index):
    """
    Return (Full Name, ISO Code)
    Defaults to Romanian if index not found
    """
    return LANGUAGES.get(index, ("Romanian", "ro"))

def get_iso_variants(index):
    """Return list of possible ISO variants for a language index"""
    _, iso = get_lang_params(index)
    return ISO_VARIANTS.get(iso, [iso])
