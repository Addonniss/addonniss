# -*- coding: utf-8 -*-

# -----------------------------
# Languages dictionary (alphabetical)
# -----------------------------
# Key can be numeric string (old) or language name (new select)
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

# Mapping for select-based language names (new)
LANG_NAME_TO_ISO = {name: iso for _, (name, iso) in LANGUAGES.items()}

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

PROVIDER_LANGUAGE_CODES = {
    "DeepL": {
        "Arabic": "AR",
        "Chinese": "ZH",
        "Czech": "CS",
        "Danish": "DA",
        "Dutch": "NL",
        "English": "EN",
        "Finnish": "FI",
        "French": "FR",
        "German": "DE",
        "Greek": "EL",
        "Hungarian": "HU",
        "Italian": "IT",
        "Japanese": "JA",
        "Korean": "KO",
        "Norwegian": "NB",
        "Polish": "PL",
        "Portuguese": "PT",
        "Romanian": "RO",
        "Russian": "RU",
        "Slovenian": "SL",
        "Spanish": "ES",
        "Swedish": "SV",
        "Turkish": "TR",
    }
}

# -----------------------------
# Functions
# -----------------------------
def get_lang_params(value):
    """
    Return (Full Name, ISO Code)
    Accepts either:
      - old numeric string key ("7")
      - new select string ("English")
    Defaults to Romanian if value not found.
    """
    # Try numeric key first
    if str(value) in LANGUAGES:
        return LANGUAGES[str(value)]
    
    # Try select string name
    if isinstance(value, str) and value in LANG_NAME_TO_ISO:
        return (value, LANG_NAME_TO_ISO[value])
    
    # Fallback
    return ("Romanian", "ro")

def get_iso_variants(value):
    """
    Return list of ISO variants for a language.
    Accepts either numeric string or select string.
    """
    _, iso = get_lang_params(value)
    return ISO_VARIANTS.get(iso, [iso])


def get_provider_language_code(provider, value, allow_auto_detect=False):
    """
    Return the provider-specific language code for a saved setting value.

    Accepts either the old numeric setting value or the newer language name.
    Returns:
      - provider code string when supported
      - None when the provider does not support that language
    """
    name, _ = get_lang_params(value)

    if allow_auto_detect and isinstance(name, str) and name.lower() == "auto-detect":
        return None

    provider_map = PROVIDER_LANGUAGE_CODES.get(provider, {})
    return provider_map.get(name)


def get_active_language_setting(addon, provider, kind):
    """
    Return the currently active language setting value for the selected provider.

    `kind` must be either 'source' or 'target'.
    """
    provider_keys = {
        "DeepL": f"deepl_{kind}_lang",
        "OpenAI": f"{kind}_lang_openai",
    }

    provider_key = provider_keys.get(provider)
    if provider_key:
        provider_value = addon.getSetting(provider_key)
        if provider_value:
            return provider_value

    return addon.getSetting(f"{kind}_lang")
