# -*- coding: utf-8 -*-
import requests
import re
import xbmc
import xbmcaddon

ADDON = xbmcaddon.Addon('service.translatarr')


def log(msg):
    xbmc.log(f"[OpenAI-Engine] {msg}", xbmc.LOGINFO)


def translate_batch_openai(text_list, expected_count):
    api_key = ADDON.getSetting('openai_api_key')

    # ✅ API key validation
    if not api_key:
        log("OpenAI API key missing.")
        return None, 0, 0

    # Model mapping (must match settings.xml)
    model_idx = ADDON.getSetting('openai_model') or "0"
    model_map = {
        "0": "gpt-4o-mini",
        "1": "gpt-4o"
    }
    model = model_map.get(model_idx, "gpt-4o-mini")

    # ✅ Temperature from settings
    try:
        temperature = float(ADDON.getSetting('temp') or 0.15)
    except Exception:
        temperature = 0.15

    # Language handling
    from languages import get_lang_params
    src_name, _ = get_lang_params(ADDON.getSetting('source_lang'))
    trg_name, _ = get_lang_params(ADDON.getSetting('target_lang'))

    if src_name.lower() != "auto-detect":
        language_instruction = f"Translate from {src_name} to {trg_name}."
    else:
        language_instruction = f"Detect the source language and translate to {trg_name}."

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Anchor logic (L000, L001...)
    prefixed_lines = [f"L{i:03}: {text}" for i, text in enumerate(text_list)]
    input_text = "\n".join(prefixed_lines)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional subtitle localizer.\n"
                    f"{language_instruction}\n"
                    "Rules:\n"
                    "1. Translate strictly line-by-line.\n"
                    "2. Preserve 'Lxxx:' anchors exactly as provided.\n"
                    f"3. Return exactly {expected_count} lines.\n"
                    "4. Keep tone natural and suitable for film subtitles.\n"
                    "5. Do NOT add commentary.\n"
                    "6. Return ONLY prefixed translated lines."
                )
            },
            {
                "role": "user",
                "content": input_text
            }
        ],
        "temperature": temperature
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            log(f"API Error: {response.text}")
            return None, 0, 0

        data = response.json()
        raw_text = data['choices'][0]['message']['content'].strip()

        # ✅ Strict scrubber
        raw_output = raw_text.split('\n')
        translated = []

        for line in raw_output:
            stripped = line.strip()
            if re.match(r'^L\d{3}:\s*', stripped):
                clean_line = re.sub(r'^L\d{3}:\s*', '', stripped)
                translated.append(clean_line)

        if len(translated) == expected_count:
            usage = data.get('usage', {})
            return (
                translated,
                usage.get('prompt_tokens', 0),
                usage.get('completion_tokens', 0)
            )

        log(f"Line count mismatch. Expected {expected_count}, got {len(translated)}")

    except Exception as e:
        log(f"Critical Exception: {e}")

    return None, 0, 0
