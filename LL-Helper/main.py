import requests
import json
import time
import os

TARGET_LANGUAGE = "japanese"
MODEL_NAME = "gemma3:12b"
MAX_WORDS = 10000
INPUT_FILE = "words.txt"
OUTPUT_FILE = f"{TARGET_LANGUAGE}_deck.json"

REQUIRED_FIELDS = [
    "source", "source_example", "target_example",
    "furigana", "furigana_example", "romanization"
]

PROMPT_TEMPLATE = """[INST]
You are a precise Japanese language assistant. Create flashcard data EXACTLY as specified.

For the Japanese word/phrase: 「{word}」

Provide these details in CLEAN JSON ONLY (no commentary):

1. "source": English translation (short, literal)
2. "target_example": Natural Japanese sentence using {word} (polite/neutral)
3. "source_example": Direct English translation of above sentence
4. "word_furigana": Reading of {word} in hiragana only
5. "sentence_furigana": Full sentence reading in hiragana
6. "romanization": Romaji of {word}

RULES:
- Convert verbs to dictionary form (〜ます → 〜る)
- Convert adjectives to dictionary form (きれいです → きれいだ)
- For kanji without common reading, use [漢字|ふりがな] format
- Never add explanations or notes

Output ONLY this format:
```json
{{
  "source": "...",
  "source_example": "...",
  "target_example": "...",
  "word_furigana": "...",
  "sentence_furigana": "...",
  "romanization": "..."
}}
```[/INST]
"""


VERIFY_PROMPT_TEMPLATE = PROMPT_TEMPLATE + """

Here is the existing data for this word. If all values are correct and match the structure and intention of the instructions, return the exact same JSON. If any values seems incorrect to you, regenerate them.:

{existing_json}
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
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])
    except:
        print("⚠️ Erro ao interpretar resposta JSON:")
        print(text)
        return None

def load_existing_deck():
    if not os.path.exists(OUTPUT_FILE):
        return {"deck_properties": {}, "cards": []}
    
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def word_card_lookup(word, deck):
    for card in deck["cards"]:
        if card.get("target") == word:
            return card
    return None

def to_prompt_card_json(card):
    # Converts a card back to the same JSON format used in prompt (for verification)
    return json.dumps({
        "source": card["source"],
        "source_example": card["source_example"],
        "target_example": card["target_example"],
        "word_furigana": card.get("extras", {}).get("word_furigana", ""),
        "sentence_furigana": card.get("extras", {}).get("sentence_furigana", ""),
        "romanization": card.get("extras", {}).get("romanization", "")
    }, ensure_ascii=False, indent=2)

def verify_or_generate_card(word, existing_card=None):
    if existing_card:
        prompt = VERIFY_PROMPT_TEMPLATE.format(
            word=word,
            target_lang=TARGET_LANGUAGE.capitalize(),
            existing_json=to_prompt_card_json(existing_card)
        )
    else:
        prompt = PROMPT_TEMPLATE.format(
            word=word,
            target_lang=TARGET_LANGUAGE.capitalize()
        )
    
    raw_output = ask_ai(prompt)
    parsed = safe_parse_json(raw_output)

    if not parsed or not parsed.get("source"):
        print(f"❌ Falha para '{word}'")
        return None

    return {
        "source": parsed["source"],
        "target": word,
        "source_example": parsed["source_example"],
        "target_example": parsed["target_example"],
        "extras": {
            "word_furigana": parsed.get("word_furigana", ""),
            "sentence_furigana": parsed.get("sentence_furigana", ""),
            "romanization": parsed.get("romanization", ""),
            "ipa": parsed.get("ipa", "")
        },
        "srs_data": existing_card.get("srs_data", {
            "balance": 0,
            "interval": 0,
            "ease": 2.5,
            "lastreviewed": 0,
            "due": 0
        }) if existing_card else {
            "balance": 0,
            "interval": 0,
            "ease": 2.5,
            "lastreviewed": 0,
            "due": 0
        }
    }

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f.readlines()[:MAX_WORDS]]

    deck = load_existing_deck()

    if not deck.get("deck_properties"):
        deck["deck_properties"] = {
            "public": True,
            "quiz": True,
            "typing": True,
            "speech_to_text": True,
            "text_to_speech": True,
            "source_language": "english",
            "target_language": TARGET_LANGUAGE
        }

    # Initialize cards if not present
    if "cards" not in deck:
        deck["cards"] = []

    for i, word in enumerate(words):
        existing_card = word_card_lookup(word, deck)
        print(f"[{i+1}/{MAX_WORDS}] 🔍 Verificando ou criando: {word}")

        card = verify_or_generate_card(word, existing_card)
        if card:
            # Remove old version if it exists
            deck["cards"] = [c for c in deck["cards"] if c.get("target") != word]
            deck["cards"].append(card)
        
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(deck, f, ensure_ascii=False, indent=2)

        time.sleep(1.5)

    print(f"\n✅ Deck salvo em: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
