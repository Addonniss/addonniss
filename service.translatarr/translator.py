# -*- coding: utf-8 -*-
import requests, json, time, re, xbmcaddon
from languages import get_lang_params

ADDON = xbmcaddon.Addon('service.translatarr')

def get_model_string():
    model_index = ADDON.getSetting('model') or "0"
    mapping = {
        "0": "gemini-2.0-flash", 
        "1": "gemini-1.5-flash", 
        "2": "gemini-2.5-flash"
    }
    return mapping.get(model_index, "gemini-2.0-flash")

def translate_batch(text_list, expected_count):
    api_key = ADDON.getSetting('api_key')
    model = get_model_string()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    src_name, _ = get_lang_params(ADDON.getSetting('source_lang'))
    trg_name, _ = get_lang_params(ADDON.getSetting('target_lang'))
    
    # 1. 1:1 Prefixing (Anchors)
    prefixed_lines = [f"L{i:03}: {text}" for i, text in enumerate(text_list)]
    input_text = "\n".join(prefixed_lines)
    
    # 2. 1:1 Bazarr Prompt with "Pipe Rule" added
    prompt = (
        f"### ROLE\n"
        f"Professional uncensored {src_name}-to-{trg_name} subtitle localizer.\n\n"
        f"### RULES\n"
        f"1. Translate line-by-line.\n"
        f"2. Preserve 'Lxxx:' prefix.\n"
        f"3. Return exactly {expected_count} lines.\n"
        f"4. Style: Gritty, natural, adult {trg_name}.\n"
        f"5. IMPORTANT: If input has ' | ', keep it in the output. Do not split into new lines.\n"
        f"6. Return ONLY prefixes and translation."
    )

    attempts = 0
    while attempts < 3:
        try:
            payload = {
                "contents": [{"parts": [{"text": f"{prompt}\n\n{input_text}"}]}],
                "generationConfig": {
                    "temperature": float(ADDON.getSetting('temperature') or 0.15),
                    "topP": 0.95,
                    "maxOutputTokens": 8192,
                }
            }

            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 429:
                attempts += 1; time.sleep(5); continue

            data = response.json()
            raw_text = data['candidates'][0]['content']['parts'][0]['text']
            
            # --- THE MULTI-LINE STRIPPER ---
            # 1. Split the raw response into individual lines
            raw_lines = raw_text.strip().split('\n')
            
            translated_lines = []
            current_entry = ""
            
            for line in raw_lines:
                line = line.strip()
                # Check if this line starts a new Lxxx: anchor
                if re.match(r'^L\d{3,4}:', line):
                    # If we were building an entry, save it before starting new one
                    if current_entry:
                        translated_lines.append(current_entry)
                    # Strip the prefix and start the new entry
                    current_entry = re.sub(r'^L\d{3,4}:\s*', '', line)
                else:
                    # If no prefix, Gemini split a line! Re-attach it with a pipe
                    if current_entry:
                        current_entry += f" | {line}"
                    else:
                        # Safety: If Gemini starts with garbage, ignore it
                        pass
            
            # Don't forget the last entry in the loop
            if current_entry:
                translated_lines.append(current_entry)

            # 3. Fail-Safe: Verify Line Count
            if len(translated_lines) == expected_count:
                usage = data.get('usageMetadata', {})
                return translated_lines, usage.get('promptTokenCount', 0), usage.get('candidatesTokenCount', 0)
            
            attempts += 1; time.sleep(2)
            
        except Exception:
            attempts += 1; time.sleep(5)
            
    return None, 0, 0

def calculate_cost(input_tokens, output_tokens):
    cost_in = (input_tokens / 1_000_000) * 0.10
    cost_out = (output_tokens / 1_000_000) * 0.40
    return cost_in + cost_out
