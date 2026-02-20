# -*- coding: utf-8 -*-
import requests, re, xbmcaddon
from languages import get_lang_params

ADDON = xbmcaddon.Addon('service.translatarr')

def get_model_string():
    model_index = ADDON.getSetting('model') or "0"
    mapping = {"0": "gemini-2.0-flash", "1": "gemini-1.5-flash", "2": "gemini-2.5-flash"}
    return mapping.get(model_index, "gemini-2.0-flash")

def translate_batch(text_list, expected_count):
    api_key = ADDON.getSetting('api_key')
    model_name = get_model_string()
    try: temp_val = float(ADDON.getSetting('temp') or 0.15)
    except: temp_val = 0.15
    
    src_name, _ = get_lang_params(ADDON.getSetting('source_lang'))
    trg_name, _ = get_lang_params(ADDON.getSetting('target_lang'))
    source_instruction = src_name if src_name != "Auto-Detect" else "the detected original language"
    
    input_text = "\n".join([f"L{i:03}: {text}" for i, text in enumerate(text_list)])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    prompt = f"Translate from {source_instruction} to {trg_name}. Prefix 'Lxxx:'."
    
    try:
        payload = {
            "contents": [{"parts": [{"text": f"{prompt}\n\n{input_text}"}]}],
            "generationConfig": {"temperature": temp_val, "topP": 0.95}
        }
        r = requests.post(url, json=payload, timeout=30)
        res_json = r.json()
        
        if 'candidates' not in res_json: return None, 0, 0
        
        raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
        usage = res_json.get('usageMetadata', {})
        in_tokens = usage.get('promptTokenCount', 0)
        out_tokens = usage.get('candidatesTokenCount', 0)
        
        translated = [re.sub(r'^.*?:\s*', '', l.strip()) for l in raw_text.strip().split('\n')]
        return translated[:expected_count], in_tokens, out_tokens
    except:
        return None, 0, 0

def calculate_cost(in_tokens, out_tokens):
    # Gemini 1.5/2.0 Flash pricing: $0.075/1M in, $0.30/1M out
    return ((in_tokens / 1_000_000) * 0.075) + ((out_tokens / 1_000_000) * 0.30)
