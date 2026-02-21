# -*- coding: utf-8 -*-

LANGUAGES = {
    "0": ("Romanian", "ro"),
    "1": ("French", "fr"),
    "2": ("Spanish", "es"),
    "3": ("German", "de"),
    "4": ("Italian", "it"),
    "5": ("Portuguese", "pt"),
    "6": ("Russian", "ru"),
    "7": ("Chinese", "zh"),
    "8": ("Japanese", "ja"),
    "9": ("English", "en"),
    "10": ("Auto-Detect", "auto"),
    "11": ("Arabic", "ar"),
    "12": ("Greek", "el"),
    "13": ("Turkish", "tr"),
    "14": ("Dutch", "nl"),
    "15": ("Polish", "pl"),
    "16": ("Hungarian", "hu"),
    "17": ("Czech", "cs"),
    "18": ("Swedish", "sv"),
    "19": ("Danish", "da"),
    "20": ("Finnish", "fi"),
    "21": ("Norwegian", "no"),
    "22": ("Hebrew", "he"),
    "23": ("Hindi", "hi"),
    "24": ("Korean", "ko"),
    "25": ("Thai", "th"),
    "26": ("Vietnamese", "vi")

}

def get_lang_params(index):
    # Returns (Full Name, ISO Code)
    # Defaulting to Romanian (0) if index is not found
    return LANGUAGES.get(index, ("Romanian", "ro"))
