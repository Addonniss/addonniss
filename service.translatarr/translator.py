# -*- coding: utf-8 -*-
import requests, json, time, re, xbmcaddon, xbmc
from languages import get_lang_params

ADDON = xbmcaddon.Addon('service.translatarr')

def log(msg):
    xbmc.log(f"[Gemini-Translator] {msg}", xbmc.LOGINFO)

def get_model_string():
    model_index = ADDON.getSetting('model') or "0"
    mapping = {"0": "gemini-2.0-flash", "1": "gemini-1.5-flash", "2": "gemini-2.5-flash"}
    return mapping.get(model_index, "gemini-2.0-flash")

def clean_gemini_mess(text):
    """Deep cleans a single line of all AI artifacts."""
    if not text: return ""
    # 1. Kill L000: prefixes (handles various separators)
    text = re.sub(r'^[ \t]*L\d{1,4}[:\-\s]*', '', text).strip()
    # 2. Kill stray [BR] at the very end of lines
    text = re.sub(r'[ \t]*\[BR\][ \t]*$', '', text).strip()
    # 3. Final trim
    return text

def translate_batch(text_list, expected_count):
    api_key = ADDON.getSetting('api_key')
    model = get_model_string()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    src_name, _ = get_lang_params(ADDON.getSetting('source_lang'))
    trg_name, _ = get_lang_params(ADDON.getSetting('target_lang'))
    
    prefixed_lines = [f"L{i:03}: {text}" for i, text in enumerate(text_list)]
    input_text = "\n".join(prefixed_lines)
    
    prompt = (
        f"### ROLE\nProfessional uncensored {src_name}-to-{trg_name} subtitle localizer.\n\n"
        f"### RULES\n1. Translate line-by-line.\n2. Preserve 'Lxxx:' prefix.\n"
        f"3. Return exactly {expected_count} lines.\n4. Style: Gritty, natural, adult {trg_name}.\n"
        f"5. IMPORTANT: Use ' [BR] ' for line breaks. Do not split into new lines.\n"
        f"6. Return ONLY prefixes and translation."
    )

    attempts = 0
    while attempts < 3:
        try:
            payload = {
                "contents": [{"parts": [{"text": f"{prompt}\n\n{input_text}"}]}],
                "generationConfig": {"temperature": 0.15, "topP": 0.95, "maxOutputTokens": 8192}
            }

            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 429:
                attempts += 1; time.sleep(5); continue

            data = response.json()
            raw_text = data['candidates'][0]['content']['parts'][0]['text']
            
            # --- TRY 1: Line-by-Line Split ---
            raw_lines = raw_text.strip().split('\n')
            translated_lines = [clean_gemini_mess(l) for l in raw_lines if l.strip()]
            # Remove Gemini chatter (titles/headers)
            translated_lines = [l for l in translated_lines if not l.lower().startswith(("here is", "###"))]

            if len(translated_lines) == expected_count:
                usage = data.get('usageMetadata', {})
                return translated_lines, usage.get('promptTokenCount', 0), usage.get('candidatesTokenCount', 0)
            
            # --- TRY 2: Anchor Split (The Hero) ---
            log(f"⚠️ Count Mismatch ({len(translated_lines)}/{expected_count}). Forcing Anchor-Split...")
            anchor_parts = re.split(r'L\d{3,4}:', raw_text)
            # Clean each part created by the split
            anchor_parts = [clean_gemini_mess(p) for p in anchor_parts if p.strip()]
            
            if len(anchor_parts) == expected_count:
                log("✅ Anchor-Split + Deep Clean saved the batch!")
                return anchor_parts, 0, 0

            log(f"❌ Batch Failed. Expected {expected_count}, got {len(anchor_parts)}.")
            attempts += 1; time.sleep(2)

        except Exception as e:
            log(f"❌ Exception: {e}"); attempts += 1; time.sleep(5)
            
    return None, 0, 0

def calculate_cost(i, o):
    return ((i / 1_000_000) * 0.10) + ((o / 1_000_000) * 0.40)
