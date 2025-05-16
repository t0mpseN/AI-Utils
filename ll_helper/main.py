import requests
import json
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TARGET_LANGUAGE = "japanese"
MODEL_NAME = "gemma3:12b"
MAX_WORDS = 10000
INPUT_FILE = "words.txt"
OUTPUT_FILE = f"{TARGET_LANGUAGE}_deck.json"

PROMPT_TEMPLATE = """
You are an AI assistant helping create flashcards for language learning.

For the English word "{word}", provide the following fields in JSON:

- "target": translation into {target_lang}
- "source_example": simple English sentence using the word (try to write a short sentence)
- "target_example": translation of the sentence
- "furigana": the Japanese reading of the word only (if applicable)
- "romanization": Hepburn romanization of the word only
- "ipa": IPA pronunciation of the word only

Only output a clean JSON object like this:
{{
  "target": "...",
  "source_example": "...",
  "target_example": "...",
  "furigana": "...",
  "romanization": "...",
  "ipa": "..."
}}
"""

def ask_ai(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }
        )
        return response.json()["response"].strip()
    except Exception as e:
        print("Erro com o modelo:", e)
        return ""

def safe_parse_json(text):
    try:
        # Corrige casos de texto extra antes/depois do JSON
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])
    except:
        print("⚠️ Erro ao interpretar resposta JSON:")
        print(text)
        return None

def generate_card(word):
    prompt = PROMPT_TEMPLATE.format(word=word, target_lang=TARGET_LANGUAGE.capitalize())
    raw_output = ask_ai(prompt)
    parsed = safe_parse_json(raw_output)

    if not parsed or not parsed.get("target"):
        print(f"❌ Falha para '{word}'")
        return None

    return {
        "source": word,
        "target": parsed["target"],
        "source_example": parsed["source_example"],
        "target_example": parsed["target_example"],
        "extras": {
            "furigana": parsed["furigana"],
            "romanization": parsed["romanization"],
            "ipa": parsed["ipa"]
        },
        "srs_data": {
            "balance": 0,
            "interval": 0,
            "ease": 2.5,
            "lastreviewed": 0,
            "due": 0
        }
    }

def main():
    if sys.stdout.encoding != 'UTF-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f.readlines()[:MAX_WORDS]]

    deck = {
        "deck_properties": {
            "public": True,
            "quiz": True,
            "typing": True,
            "speech_to_text": True,
            "text_to_speech": True,
            "source_language": "english",
            "target_language": TARGET_LANGUAGE
        },
        "cards": []
    }

    for i, word in enumerate(words):
        print(f"[{i+1}/{MAX_WORDS}] Gerando carta para: {word}")
        card = generate_card(word)
        if card:
            deck["cards"].append(card)
        time.sleep(1.5)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Deck salvo em: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
