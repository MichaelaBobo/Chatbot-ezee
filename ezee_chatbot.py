from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
from datetime import datetime
import openpyxl
import os

app = Flask(__name__)
CORS(app)

OPENROUTER_API_KEY = "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"
MODEL = "openai/gpt-3.5-turbo"

PROMPTS = {
    "en": (
        "You are the official AI assistant of Ezee Studio, a creative marketing agency. "
        "Ezee provides businesses with high-quality, consistent content – including social media posts, graphics, branding assets, and marketing copy. "
        "Your role is to clearly explain Ezee's services, process, and value to potential clients in a helpful, friendly, and professional tone. "
        "Ezee is the ideal solution for companies that want great marketing content without the hassle. "
        "Always answer every question the user asks, even if they include multiple questions in a single message."
    ),
    "sk": (
        "Si oficiálny AI asistent agentúry Ezee Studio – kreatívnej marketingovej agentúry. "
        "Ezee poskytuje firmám kvalitný a konzistentný obsah – vrátane príspevkov na sociálne siete, grafiky, vizuálnej identity a marketingových textov. "
        "Tvojou úlohou je jasne a priateľsky vysvetliť služby Ezee, proces spolupráce a hodnotu, ktorú klienti získajú. "
        "Ezee je ideálnym riešením pre firmy, ktoré chcú skvelý marketingový obsah bez námahy. "
        "Vždy odpovedz na všetky otázky používateľa, aj ak sú v jednej správe."
    )
}

LOG_FILE = "chat_log.xlsx"

if not os.path.exists(LOG_FILE):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Chat Log"
    ws.append(["Timestamp", "User Question", "Bot Response"])
    wb.save(LOG_FILE)

def detect_language(text):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Detect the language of this input. Just return 'en' or 'sk'."},
            {"role": "user", "content": text}
        ]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        lang = response.json()["choices"][0]["message"]["content"].strip().lower()
        return "sk" if "sk" in lang else "en"
    return "en"  # fallback

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")

    lang = detect_language(user_input)
    system_prompt = PROMPTS.get(lang, PROMPTS["en"])

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        reply = response.json()["choices"][0]["message"]["content"]

        wb = openpyxl.load_workbook(LOG_FILE)
        ws = wb["Chat Log"]
        ws.append([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_input, reply])
        wb.save(LOG_FILE)

        return jsonify({"response": reply})
    else:
        return jsonify({"response": f"Error: {response.status_code}, {response.text}"}), response.status_code

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
