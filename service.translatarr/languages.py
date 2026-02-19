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
    "10": ("Auto-Detect", "auto")
}

def get_lang_params(index):
    # Returns (Full Name, ISO Code)
    return LANGUAGES.get(index, ("Romanian", "ro"))
