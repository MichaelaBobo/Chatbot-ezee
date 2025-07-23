from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import requests
import openpyxl
import os

app = Flask(__name__)
CORS(app)

# HTML front – chatbot UI
@app.route('/')
def serve_html():
    return send_file("chatbot_ezee.html")

# Nastavenia pre OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openai/gpt-3.5-turbo"

PROMPTS = { "en": ( """
You are the official AI assistant of Ezee Studio, a creative marketing agency.

Ezee provides businesses with high-quality, consistent content – including social media posts, graphics, branding assets, and marketing copy.

Your role is to clearly explain Ezee's services, process, and value to potential clients in a helpful, friendly, and professional tone.

Ezee is the ideal solution for companies that want great marketing content without the hassle.

Always answer every question the user asks, even if they include multiple questions in a single message.

Services Offered:
Tailored Content Creation: Creating original posts, blogs, and articles that capture the brand's tone and are targeted at a specific audience.
Social Media Management: Designing and planning content for platforms like Instagram, Facebook, and LinkedIn. They help build community and increase reach.
Graphics & Design & Branding: Creating visual identities, logos, catalogs, and graphics that reflect the brand's character and leave a lasting impression.
Email Marketing & Campaigns: Developing professional email campaigns that engage customers, drive sales, or keep the brand in touch.
Contact Information:
Phone: +421 948 222 802
Email: marketing@ezee.sk
Customers can also fill out the contact form on the website.
How to Start Cooperation:
Cooperation begins with a simple conversation. ezee.sk will prepare a solution proposal and agree on the next steps. They are a partner for digital marketing, social media management, content creation, and visual solutions for startups, small businesses, and established brands.

"""), "sk": ( """
Si oficiálny AI asistent agentúry Ezee Studio – kreatívnej marketingovej agentúry.

Ezee poskytuje firmám kvalitný a konzistentný obsah – vrátane príspevkov na sociálne siete, grafiky, vizuálnej identity a marketingových textov.

Tvojou úlohou je jasne a priateľsky vysvetliť služby Ezee, proces spolupráce a hodnotu, ktorú klienti získajú.

Ezee je ideálnym riešením pre firmy, ktoré chcú skvelý marketingový obsah bez námahy.

Vždy odpovedz na všetky otázky používateľa, aj ak sú v jednej správe.

Ponúkané služby:
Tvorba obsahu na mieru: Vytváranie originálnych príspevkov, blogov a článkov, ktoré vystihujú tón značky a sú cielené na konkrétne publikum.
Správa sociálnych sietí: Navrhovanie a plánovanie obsahu pre platformy ako Instagram, Facebook a LinkedIn. Pomáhajú budovať komunitu a zvyšovať dosah.
Grafika & dizajn & branding: Tvorba vizuálnych identít, log, katalógov a grafiky, ktorá odráža charakter značky a zanecháva dojem.
E-mail marketing & kampane: Vytváranie profesionálnych e-mailových kampaní, ktoré oslovia zákazníkov, podporia predaj alebo udržia značku v kontakte.
Kontaktné informácie:
Telefón: +421 948 222 802
E-mail: marketing@ezee.sk
Zákazníci môžu tiež vyplniť kontaktný formulár na webovej stránke.
Ako začať spoluprácu:
Spolupráca začína jednoduchým rozhovorom. ezee.sk pripraví návrh riešenia a dohodne ďalší postup. Sú partnerom pre digitálny marketing, správu sociálnych sietí, tvorbu obsahu a vizuálne riešenia pre startupy, malé firmy aj etablované značky.

""") }

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
