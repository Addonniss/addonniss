# -*- coding: utf-8 -*-
import requests
import re
import xbmc
import xbmcaddon

ADDON = xbmcaddon.Addon('service.translatarr')


# ----------------------------------------------------------
# Logging
# ----------------------------------------------------------

def log(msg):
    xbmc.log(f"[Translatarr] {msg}", xbmc.LOGINFO)

# ----------------------------------------------------------
# Style Builder
# ----------------------------------------------------------

def build_style_instruction(trg_name):
    style_mode = ADDON.getSetting('translation_style') or "0"

    # 0 = Family-Friendly (default)
    # 1 = Natural
    # 2 = Gritty / Adult

    if style_mode == "2":
        return (
            "STYLE REQUIREMENT:\n"
            f"- Tone: gritty, raw, adult {trg_name}.\n"
            "- Preserve profanity and strong language.\n"
            "- Do NOT soften insults.\n"
            "- Maintain emotional intensity.\n"
        )

    elif style_mode == "1":
        return (
            "STYLE REQUIREMENT:\n"
            f"- Tone: natural conversational {trg_name}.\n"
            "- Sound realistic and fluid.\n"
            "- Avoid overly literal translation.\n"
        )

    # Default = Family-Friendly
    return (
        "STYLE REQUIREMENT:\n"
        f"- Tone: clean, neutral, broadcast-safe {trg_name}.\n"
        "- Avoid profanity.\n"
        "- Replace strong insults with mild alternatives.\n"
        "- Keep dialogue suitable for general audiences.\n"
    )

# ----------------------------------------------------------
# Base
# ----------------------------------------------------------

class BaseTranslator:
    def translate_batch(self, text_list, expected_count):
        raise NotImplementedError

    def calculate_cost(self, input_tokens, output_tokens):
        raise NotImplementedError

    def get_model_string(self):
        raise NotImplementedError


# ==========================================================
# GEMINI
# ==========================================================

class GeminiTranslator(BaseTranslator):

    PRICING = {
        "gemini-2.0-flash": (0.0000005, 0.0000015),
        "gemini-1.5-flash": (0.0000005, 0.0000015),
        "gemini-2.5-flash": (0.0000007, 0.0000020),
    }

    def __init__(self):
        self.api_key = ADDON.getSetting('api_key')
        self.model_idx = ADDON.getSetting('model') or "0"
        self.temperature = self._get_temperature()

        model_map = {
            "0": "gemini-2.0-flash",
            "1": "gemini-1.5-flash",
            "2": "gemini-2.5-flash"
        }

        self.model = model_map.get(self.model_idx, "gemini-2.0-flash")

    def _get_temperature(self):
        try:
            temp = float(ADDON.getSetting('temp') or 0.15)
            return max(0.0, min(temp, 1.0))
        except:
            return 0.15

    # --------------------------
    # Translation
    # --------------------------

    def translate_batch(self, text_list, expected_count):

        if not self.api_key:
            return None, 0, 0

        from languages import get_lang_params
        src_name, _ = get_lang_params(ADDON.getSetting('source_lang'))
        trg_name, _ = get_lang_params(ADDON.getSetting('target_lang'))

        if src_name.lower() != "auto-detect":
            lang_instruction = f"Translate from {src_name} to {trg_name}."
        else:
            lang_instruction = f"Detect the source language and translate to {trg_name}."

        prefixed = [f"L{i:03}: {t}" for i, t in enumerate(text_list)]
        input_text = "\n".join(prefixed)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [{
                "parts": [{
                    "text": (
                        "You are a professional subtitle localizer.\n"
                        f"{lang_instruction}\n"
                        "Rules:\n"
                        "1. Translate strictly line-by-line.\n"
                        "2. Preserve 'Lxxx:' anchors exactly.\n"
                        f"3. Return exactly {expected_count} lines.\n"
                        "4. Return ONLY prefixed translated lines.\n\n"
                        f"{input_text}"
                    )
                }]
            }],
            "generationConfig": {
                "temperature": self.temperature
            }
        }

        try:
            r = requests.post(url, json=payload, timeout=30)
            if r.status_code != 200:
                return None, 0, 0

            data = r.json()
            raw = data['candidates'][0]['content']['parts'][0]['text'].strip()

            translated = self._scrub(raw, expected_count)
            if not translated:
                return None, 0, 0

            usage = data.get("usageMetadata", {})
            in_t = usage.get("promptTokenCount", 0)
            out_t = usage.get("candidatesTokenCount", 0)

            return translated, in_t, out_t

        except:
            return None, 0, 0

    def _scrub(self, raw_text, expected):
        lines = raw_text.split("\n")
        cleaned = []
        for line in lines:
            if re.match(r'^L\d{3}:\s*', line.strip()):
                clean = re.sub(r'^L\d{3}:\s*', '', line.strip())
                cleaned.append(clean)
        return cleaned if len(cleaned) == expected else None

    # --------------------------
    # Cost
    # --------------------------

    def calculate_cost(self, input_tokens, output_tokens):
        in_price, out_price = self.PRICING.get(self.model, (0, 0))
        return (input_tokens * in_price) + (output_tokens * out_price)

    def get_model_string(self):
        return f"Gemini ({self.model})"


# ==========================================================
# OPENAI
# ==========================================================

class OpenAITranslator(BaseTranslator):

    PRICING = {
        "gpt-4o-mini": (0.00000015, 0.00000060),
        "gpt-4o": (0.000005, 0.000015),
        "gpt-5-mini": (0.00000025,0.0000020),
    }

    def __init__(self):
        self.api_key = ADDON.getSetting('openai_api_key')
        self.model_idx = ADDON.getSetting('openai_model') or "0"
        self.temperature = self._get_temperature()

        model_map = {
            "0": "gpt-4o-mini",
            "1": "gpt-4o",
            "2": "gpt-5-mini"
        }

        self.model = model_map.get(self.model_idx, "gpt-4o-mini")

    def _get_temperature(self):
        try:
            temp = float(ADDON.getSetting('temp') or 0.15)
            return max(0.0, min(temp, 1.0))
        except:
            return 0.15

    # --------------------------
    # Translation
    # --------------------------

    def translate_batch(self, text_list, expected_count):

        if not self.api_key:
            return None, 0, 0

        from languages import get_lang_params
        src_name, _ = get_lang_params(ADDON.getSetting('source_lang'))
        trg_name, _ = get_lang_params(ADDON.getSetting('target_lang'))

        if src_name.lower() != "auto-detect":
            lang_instruction = f"Translate from {src_name} to {trg_name}."
        else:
            lang_instruction = f"Detect the source language and translate to {trg_name}."

        prefixed = [f"L{i:03}: {t}" for i, t in enumerate(text_list)]
        input_text = "\n".join(prefixed)

        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a professional subtitle localizer.\n"
                        f"{lang_instruction}\n"
                        "Rules:\n"
                        "1. Translate strictly line-by-line.\n"
                        "2. Preserve 'Lxxx:' anchors exactly.\n"
                        f"3. Return exactly {expected_count} lines.\n"
                        "4. Return ONLY prefixed translated lines."
                    )
                },
                {"role": "user", "content": input_text}
            ],
            "temperature": self.temperature
        }

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code != 200:
                return None, 0, 0

            data = r.json()
            raw = data['choices'][0]['message']['content'].strip()

            translated = self._scrub(raw, expected_count)
            if not translated:
                return None, 0, 0

            usage = data.get("usage", {})
            in_t = usage.get("prompt_tokens", 0)
            out_t = usage.get("completion_tokens", 0)

            return translated, in_t, out_t

        except:
            return None, 0, 0

    def _scrub(self, raw_text, expected):
        lines = raw_text.split("\n")
        cleaned = []
        for line in lines:
            if re.match(r'^L\d{3}:\s*', line.strip()):
                clean = re.sub(r'^L\d{3}:\s*', '', line.strip())
                cleaned.append(clean)
        return cleaned if len(cleaned) == expected else None

    # --------------------------
    # Cost
    # --------------------------

    def calculate_cost(self, input_tokens, output_tokens):
        in_price, out_price = self.PRICING.get(self.model, (0, 0))
        return (input_tokens * in_price) + (output_tokens * out_price)

    def get_model_string(self):
        return f"OpenAI ({self.model})"


# ==========================================================
# PUBLIC API (Used by service.py)
# ==========================================================

def _get_translator():
    provider = ADDON.getSetting('provider')  # 0=Gemini 1=OpenAI
    return OpenAITranslator() if provider == "1" else GeminiTranslator()


def translate_batch(text_list, expected_count):
    return _get_translator().translate_batch(text_list, expected_count)


def calculate_cost(input_tokens, output_tokens):
    return _get_translator().calculate_cost(input_tokens, output_tokens)


def get_model_string():
    return _get_translator().get_model_string()
