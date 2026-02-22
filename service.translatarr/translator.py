# -*- coding: utf-8 -*- test dev
import requests, json, time, re, xbmcaddon, xbmc
from languages import get_lang_params

ADDON = xbmcaddon.Addon('service.translatarr')

def log(msg):
    xbmc.log(f"[Gemini-Translator] {msg}", xbmc.LOGINFO)

def get_model_string():
    model_index = ADDON.getSetting('model') or "0"
    mapping = {"0": "gemini-2.0-flash", "1": "gemini-1.5-flash", "2": "gemini-2.5-flash"}
    return mapping.get(model_index, "gemini-2.0-flash")

def translate_batch(text_list, expected_count):
    api_key = ADDON.getSetting('api_key')
    model = get_model_string()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    src_name, _ = get_lang_params(ADDON.getSetting('source_lang'))
    trg_name, _ = get_lang_params(ADDON.getSetting('target_lang'))
    
    # 1:1 Match of your standalone prefixing
    prefixed_lines = [f"L{i:03}: {text}" for i, text in enumerate(text_list)]
    input_text = "\n".join(prefixed_lines)
    
    # 1:1 Match of your standalone prompt
    prompt = (
        f"### ROLE\nProfessional uncensored {src_name}-to-{trg_name} subtitle localizer.\n\n"
        f"### RULES\n1. Translate line-by-line.\n2. Preserve 'Lxxx:' prefix.\n"
        f"3. Return exactly {expected_count} lines.\n4. Style: Gritty, natural, adult {trg_name}.\n"
        f"5. Return ONLY prefixes and translation."
    )

    attempts = 0
    while attempts < 3:
        try:
            payload = {
                "contents": [{"parts": [{"text": f"{prompt}\n\n{input_text}"}]}],
                "generationConfig": {"temperature": 0.15, "topP": 0.95}
            }

            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 429:
                time.sleep(5); attempts += 1; continue

            data = response.json()
            if 'candidates' not in data:
                attempts += 1; time.sleep(2); continue

            raw_text = data['candidates'][0]['content']['parts'][0]['text']
            
            # --- THE EXACT CLONE OF YOUR STANDALONE LOGIC ---
            raw_output = raw_text.strip().split('\n')
            
            # This is the magic line from your gemini_engine.py
            # It ONLY takes lines starting with Lxxx: and strips the prefix
            translated_lines = [
                re.sub(r'^L\d{3}:\s*', '', l.strip()) 
                for l in raw_output 
                if re.match(r'^L\d{3}:', l.strip())
            ]

            if len(translated_lines) == expected_count:
                usage = data.get('usageMetadata', {})
                return translated_lines, usage.get('promptTokenCount', 0), usage.get('candidatesTokenCount', 0)
            
            log(f"Count mismatch: {len(translated_lines)}/{expected_count}. Retrying...")
            attempts += 1; time.sleep(2)

        except Exception as e:
            log(f"Error: {e}"); attempts += 1; time.sleep(5)
            
    return None, 0, 0

def calculate_cost(i, o):
    # Matches your standalone billing logic
    return ((i / 1_000_000) * 0.075) + ((o / 1_000_000) * 0.30)
