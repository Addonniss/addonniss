# -*- coding: utf-8 -*-
import requests
import re
import xbmc

# ----------------------------------------------------------
# Logging
# ----------------------------------------------------------

def log(msg):
    xbmc.log(f"[Translatarr] {msg}", xbmc.LOGINFO)


# ----------------------------------------------------------
# Style Builder
# ----------------------------------------------------------

def build_style_instruction(trg_name, style_mode):
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


# ==========================================================
# BASE TRANSLATOR
# ==========================================================

class BaseTranslator:
    def __init__(self, settings):
        self.settings = settings

    def translate_batch(self, text_list, expected_count):
        raise NotImplementedError

    def calculate_cost(self, input_tokens, output_tokens):
        return 0.0

    def get_model_string(self):
        return "Unknown"


# ==========================================================
# GEMINI TRANSLATOR
# ==========================================================

class GeminiTranslator(BaseTranslator):
    PRICING = {
        "gemini-2.0-flash": (0.0000005, 0.0000015),
        "gemini-1.5-flash": (0.0000005, 0.0000015),
        "gemini-2.5-flash": (0.0000007, 0.0000020),
    }

    MODEL_MAP = {
        "0": "gemini-2.0-flash",
        "1": "gemini-1.5-flash",
        "2": "gemini-2.5-flash"
    }

    def __init__(self, settings):
        super().__init__(settings)
        self.api_key = settings["api_key"]
        self.model = self.MODEL_MAP.get(settings["model"], "gemini-2.0-flash")
        self.temperature = settings["temperature"]

    def translate_batch(self, text_list, expected_count):
        if not self.api_key:
            return None, 0, 0

        src_name = self.settings["source_name"]
        trg_name = self.settings["target_name"]
        style_mode = self.settings["translation_style"]

        if src_name.lower() != "auto-detect":
            lang_instruction = f"Translate from {src_name} to {trg_name}."
        else:
            lang_instruction = f"Detect the source language and translate to {trg_name}."

        prefixed = [f"L{i:03}: {t}" for i, t in enumerate(text_list)]
        input_text = "\n".join(prefixed)
        style_block = build_style_instruction(trg_name, style_mode)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [{
                "parts": [{
                    "text": (
                        "You are a professional subtitle localizer.\n"
                        f"{lang_instruction}\n\n"
                        "STRICT RULES (MANDATORY):\n"
                        "1. Translate strictly line-by-line.\n"
                        "2. Preserve 'Lxxx:' anchors EXACTLY.\n"
                        f"3. Return EXACTLY {expected_count} lines.\n"
                        "4. Return ONLY prefixed translated lines.\n"
                        "5. Do NOT add commentary.\n\n"
                        f"{style_block}\n"
                        f"{input_text}"
                    )
                }]
            }],
            "generationConfig": {
                "temperature": self.temperature
            }
        }

        try:
            r = requests.post(url, json=payload, timeout=60)
            if r.status_code != 200:
                log(f"Gemini API error: {r.status_code}")
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
        except Exception as e:
            log(f"Gemini exception: {e}")
            return None, 0, 0

    def _scrub(self, raw_text, expected):
        lines = raw_text.split("\n")
        cleaned = []
        for line in lines:
            if re.match(r'^L\d{3}:\s*', line.strip()):
                cleaned.append(re.sub(r'^L\d{3}:\s*', '', line.strip()))
        return cleaned if len(cleaned) == expected else None

    def calculate_cost(self, input_tokens, output_tokens):
        in_price, out_price = self.PRICING.get(self.model, (0, 0))
        return (input_tokens * in_price) + (output_tokens * out_price)

    def get_model_string(self):
        return f"Gemini ({self.model})"


# ==========================================================
# OPENAI TRANSLATOR
# ==========================================================

class OpenAITranslator(BaseTranslator):
    PRICING = {
        "gpt-4o-mini": (0.00000015, 0.00000060),
        "gpt-4o": (0.000005, 0.000015),
        "gpt-5-mini": (0.00000025, 0.0000020),
    }

    MODEL_MAP = {
        "0": "gpt-4o-mini",
        "1": "gpt-4o",
        "2": "gpt-5-mini"
    }

    def __init__(self, settings):
        super().__init__(settings)
        self.api_key = settings["api_key"]
        self.model = self.MODEL_MAP.get(settings["model"], "gpt-4o-mini")
        self.temperature = settings["temperature"]

    def translate_batch(self, text_list, expected_count):
        if not self.api_key:
            return None, 0, 0

        src_name = self.settings["source_name"]
        trg_name = self.settings["target_name"]
        style_mode = self.settings["translation_style"]

        if src_name.lower() != "auto-detect":
            lang_instruction = f"Translate from {src_name} to {trg_name}."
        else:
            lang_instruction = f"Detect the source language and translate to {trg_name}."

        prefixed = [f"L{i:03}: {t}" for i, t in enumerate(text_list)]
        input_text = "\n".join(prefixed)
        style_block = build_style_instruction(trg_name, style_mode)

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
                        f"{lang_instruction}\n\n"
                        "STRICT RULES (MANDATORY):\n"
                        "1. Translate strictly line-by-line.\n"
                        "2. Preserve 'Lxxx:' anchors EXACTLY.\n"
                        f"3. Return EXACTLY {expected_count} lines.\n"
                        "4. Return ONLY prefixed translated lines.\n"
                        "5. Do NOT add commentary.\n\n"
                        f"{style_block}"
                    )
                },
                {"role": "user", "content": input_text}
            ],
            "temperature": self.temperature
        }

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code != 200:
                log(f"OpenAI API error: {r.status_code}")
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
        except Exception as e:
            log(f"OpenAI exception: {e}")
            return None, 0, 0

    def _scrub(self, raw_text, expected):
        lines = raw_text.split("\n")
        cleaned = []
        for line in lines:
            if re.match(r'^L\d{3}:\s*', line.strip()):
                cleaned.append(re.sub(r'^L\d{3}:\s*', '', line.strip()))
        return cleaned if len(cleaned) == expected else None

    def calculate_cost(self, input_tokens, output_tokens):
        in_price, out_price = self.PRICING.get(self.model, (0, 0))
        return (input_tokens * in_price) + (output_tokens * out_price)

    def get_model_string(self):
        return f"OpenAI ({self.model})"


# ==========================================================
# PUBLIC API (Used by service.py)
# ==========================================================

def get_translator(settings):
    provider = settings.get("provider", "0")
    return OpenAITranslator(settings) if provider == "1" else GeminiTranslator(settings)


def translate_batch(settings, text_list, expected_count):
    return get_translator(settings).translate_batch(text_list, expected_count)


def calculate_cost(settings, input_tokens, output_tokens):
    return get_translator(settings).calculate_cost(input_tokens, output_tokens)


def get_model_string(settings):
    return get_translator(settings).get_model_string()
