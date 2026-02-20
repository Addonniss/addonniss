# -*- coding: utf-8 -*-
import requests, json, time, re, xbmcaddon, xbmc
from languages import get_lang_params

ADDON = xbmcaddon.Addon('service.translatarr')

def log(msg):
    xbmc.log(f"[Gemini-Translator] {msg}", xbmc.LOGINFO)

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
    
    # 1. Prefixing (Anchors) for the AI
    prefixed_lines = [f"L{i:03}: {text}" for i, text in enumerate(text_list)]
    input_text = "\n".join(prefixed_lines)
    
    # 2. Bazarr-Compliant Prompt
    prompt = (
        f"### ROLE\n"
        f"Professional uncensored {src_name}-to-{trg_name} subtitle localizer.\n\n"
        f"### RULES\n"
        f"1. Translate line-by-line.\n"
        f"2. Preserve 'Lxxx:' prefix.\n"
        f"3. Return exactly {expected_count} lines.\n"
        f"4. Style: Gritty, natural, adult {trg_name}.\n"
        f"5. IMPORTANT: If input has ' [BR] ', keep it in the output. Do not split into new lines.\n"
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
            
            # Handle 429 - Too Many Requests
            if response.status_code == 429:
                log(f"⚠️ API Rate Limit (429). Attempt {attempts+1}/3. Waiting 5s...")
                attempts += 1
                time.sleep(5)
                continue

            data = response.json()
            if 'candidates' not in data:
                log(f"❌ API Error: {json.dumps(data)}")
                attempts += 1; time.sleep(2); continue

            # ... (after getting raw_text from Gemini)
            raw_text = data['candidates'][0]['content']['parts'][0]['text']
            
            # 1. Split into raw lines first
            raw_lines = raw_text.strip().split('\n')
            
            translated_lines = []
            for line in raw_lines:
                line = line.strip()
                if not line: continue
                
                # 2. Aggressive Prefix Removal
                # This kills "L000:", "L000", "L000 - ", etc.
                clean_line = re.sub(r'^[ \t]*L\d{1,4}[:\-\s]*', '', line).strip()
                
                # 3. Only add if it's not a hallucinated line from Gemini
                # (Sometimes Gemini adds "Here is your translation:")
                if clean_line and not clean_line.lower().startswith(("here is", "translation:", "###")):
                    translated_lines.append(clean_line)

            # 4. THE PARITY FIX: If Gemini missed the last tag but gave us the right lines
            if len(translated_lines) == expected_count:
                log(f"✅ Success: Received {expected_count} clean lines.")
                usage = data.get('usageMetadata', {})
                return translated_lines, usage.get('promptTokenCount', 0), usage.get('candidatesTokenCount', 0)
            
            # 5. EMERGENCY FALLBACK: If count is wrong, try to split by the Lxxx markers 
            # instead of by newlines (in case Gemini merged lines)
            if len(translated_lines) != expected_count:
                log(f"⚠️ Count Mismatch ({len(translated_lines)}/{expected_count}). Trying Anchor-Split...")
                # Split by the pattern L000: but keep the text
                anchor_split = re.split(r'L\d{3,4}:', raw_text)
                # Remove the first element (usually empty or intro text)
                anchor_split = [l.strip() for l in anchor_split if l.strip()]
                
                if len(anchor_split) == expected_count:
                    log("✅ Anchor-Split saved the batch!")
                    return anchor_split, 0, 0 # Usage data lost in fallback but file saved

            log(f"❌ Batch Failed: Expected {expected_count}, got {len(translated_lines)}.")
            attempts += 1
            time.sleep(2)
            
    return None, 0, 0

def calculate_cost(input_tokens, output_tokens):
    # Updated to 2026 pricing for Gemini 2.0 Flash ($0.10/$0.40 per 1M)
    cost_in = (input_tokens / 1_000_000) * 0.10
    cost_out = (output_tokens / 1_000_000) * 0.40
    return cost_in + cost_out
