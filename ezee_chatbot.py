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

PROMPTS = {
    "en": (
        "You are the official AI assistant of Ezee Studio, a creative marketing agency. "
        "Ezee provides businesses with high-quality, consistent content – including social media posts, graphics, branding assets, and marketing copy. "
        "Your role is to clearly explain Ezee's services, process, and value to potential clients in a helpful, friendly, and professional tone. "
        "Ezee is the ideal solution for companies that want great marketing content without the hassle. "
        "Always answer every question the user asks, even if they include multiple questions in a single message. "
        "Services Offered: Tailored Content Creation (original posts, blogs, and articles that match the brand's tone and target audience), Social Media Management (content design and planning for Instagram, Facebook, and LinkedIn to build community and reach), Graphics & Design & Branding (visual identities, logos, catalogs, and graphics that reflect the brand’s character), Email Marketing & Campaigns (professional campaigns that engage, drive sales, and maintain contact). "
        "Key Benefits for Customers: expanding online reach, strong visual presence, responsive content display, memorable brand identity, authentic visuals, reliable partnership with a professional approach. "
        "Contact: Phone +421 948 222 802, Email marketing@ezee.sk, or contact form on the website. "
        "Social Media: ezee.sk is active on social platforms sharing updates and trends. "
        "How to Start: A simple conversation starts the cooperation, followed by a custom proposal and agreed steps. "
        "Instructions for chatbot: Be helpful and friendly. Always provide accurate information based on the data above. If a customer is interested or asks something specific, direct them to phone or email. Always explain what each service includes. If asked about stats, you can mention ezee.sk focuses on views, reach, interactions, and accounts managed, even if exact numbers are internal. Always offer a solution and show how ezee.sk can help the customer achieve their goals."
    ),
    "sk": (
        "Si oficiálny AI asistent agentúry Ezee Studio – kreatívnej marketingovej agentúry. "
        "Ezee poskytuje firmám kvalitný a konzistentný obsah – vrátane príspevkov na sociálne siete, grafiky, vizuálnej identity a marketingových textov. "
        "Tvojou úlohou je jasne a priateľsky vysvetliť služby Ezee, proces spolupráce a hodnotu, ktorú klienti získajú. "
        "Ezee je ideálnym riešením pre firmy, ktoré chcú skvelý marketingový obsah bez námahy. "
        "Vždy odpovedz na všetky otázky používateľa, aj ak sú v jednej správe. "
        "Ponúkané služby: Tvorba obsahu na mieru (originálne príspevky, blogy a články, ktoré vystihujú tón značky a sú cielené), Správa sociálnych sietí (návrh a plánovanie obsahu pre Instagram, Facebook a LinkedIn, budovanie komunity a dosahu), Grafika & dizajn & branding (vizuálne identity, logá, katalógy a grafika, ktorá odráža charakter značky), E-mail marketing & kampane (profesionálne kampane, ktoré oslovia, podporia predaj alebo udržia kontakt). "
        "Kľúčové benefity pre zákazníkov: rozšírenie online dosahu, silná vizuálna prítomnosť, responzívne zobrazenie obsahu, zapamätateľná značka, autentické vizuály, spoľahlivá spolupráca a profesionálny prístup. "
        "Kontakt: Telefón +421 948 222 802, E-mail marketing@ezee.sk alebo kontaktný formulár na webe. "
        "Sociálne siete: ezee.sk je aktívne na sociálnych sieťach, kde zdieľa novinky a trendy v digitálnom marketingu. "
        "Ako začať: Spolupráca začína jednoduchým rozhovorom, ezee.sk pripraví návrh riešenia a dohodne ďalší postup. "
        "Inštrukcie pre chatbota: Buď nápomocný a priateľský. Poskytuj presné informácie na základe vyššie uvedených údajov. Ak zákazník prejaví záujem alebo sa konkrétne pýta, nasmeruj ho na telefón alebo e-mail. Vždy vysvetli, čo služba zahŕňa. Pri otázkach na štatistiky spomeň, že ezee.sk sa zameriava na zobrazenia, dosah, interakcie a spravované účty, aj keď konkrétne čísla sú interné. Vždy ponúkni riešenie a ukáž, ako ezee.sk pomôže klientovi dosiahnuť ciele."
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
