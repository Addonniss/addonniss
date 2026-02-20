# -*- coding: utf-8 -*-
import requests, json, time, re, xbmcaddon
from languages import get_lang_params

ADDON = xbmcaddon.Addon('service.translatarr')

def get_model_string():
    # Restored: Your exact mapping logic
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
    
    # 2. 1:1 Bazarr Prompt
    prompt = (
        f"### ROLE\n"
        f"Professional uncensored {src_name}-to-{trg_name} subtitle localizer.\n\n"
        f"### RULES\n"
        f"1. Translate line-by-line.\n"
        f"2. Preserve 'Lxxx:' prefix.\n"
        f"3. Return exactly {expected_count} lines.\n"
        f"4. Style: Gritty, natural, adult {trg_name}.\n"
        f"5. Return ONLY prefixes and translation."
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
            
            # Handle 429 specifically (Rate Limit)
            if response.status_code == 429:
                attempts += 1
                time.sleep(5)
                continue

            data = response.json()
            
            # Extract content
            if 'candidates' not in data or not data['candidates'][0]['content']['parts'][0]['text']:
                attempts += 1
                time.sleep(2)
                continue
                
            raw_output = data['candidates'][0]['content']['parts'][0]['text'].strip().split('\n')
            
            # 3. 1:1 Regex Cleaning Logic
            translated_lines = [
                re.sub(r'^L\d{3}:\s*', '', l.strip()) 
                for l in raw_output 
                if re.match(r'^L\d{3}:', l.strip())
            ]
            
            # 4. Fail-Safe: Verify Line Count
            if len(translated_lines) == expected_count:
                usage = data.get('usageMetadata', {})
                # Note: 'thoughts' token count isn't standard in the REST API yet, 
                # so we stick to Prompt and Candidates
                return translated_lines, usage.get('promptTokenCount', 0), usage.get('candidatesTokenCount', 0)
            
            # Count mismatch retry
            attempts += 1
            time.sleep(2)
            
        except Exception:
            attempts += 1
            time.sleep(5)
            
    return None, 0, 0

def calculate_cost(input_tokens, output_tokens):
    # Costs for Gemini 2.0 Flash
    cost_in = (input_tokens / 1_000_000) * 0.10
    cost_out = (output_tokens / 1_000_000) * 0.40
    return cost_in + cost_out
