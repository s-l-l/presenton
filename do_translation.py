import json
import time
from deep_translator import GoogleTranslator

with open('d:/codeWorkspase/presenton/translate_all.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Create a dictionary to hold translations
translations = {}
translator = GoogleTranslator(source='en', target='zh-CN')

print(f"Translating {len(data)} items...")

for i, text in enumerate(data):
    # Try translating
    for _ in range(3):
        try:
            # Skip if already in Chinese (some may be because we ran neo-general already)
            # Actually, let's just translate
            if any('\u4e00' <= char <= '\u9fff' for char in text):
                translations[text] = text
            else:
                translated = translator.translate(text)
                translations[text] = translated
            break
        except Exception as e:
            print(f"Error translating '{text}': {e}. Retrying...")
            time.sleep(1)
    else:
        translations[text] = text # fallback
    
    if (i+1) % 50 == 0:
        print(f"Done {i+1}/{len(data)}")

with open('d:/codeWorkspase/presenton/all_translations.json', 'w', encoding='utf-8') as f:
    json.dump(translations, f, indent=2, ensure_ascii=False)

print("Translation complete!")
