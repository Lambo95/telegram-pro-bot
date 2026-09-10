import os
import requests
from flask import Flask, request

TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)
user_state = {}

def stima_quota_futura(quota_iniziale, variazione_pct):
    return quota_iniziale * (1 + variazione_pct)

def calcola_lay_stake(stake, quota_puntata, quota_bancata, recupero_pct):
    return (stake * quota_puntata / quota_bancata) * recupero_pct

def calcola_pnl(stake, quota_puntata, lay_stake, quota_bancata):
    return stake * quota_puntata - lay_stake * quota_bancata

def suggerimento_operazione(quota_puntata, quota_bancata):
    if quota_bancata > quota_puntata:
        return "📉 La quota è salita: meglio BANCHARE per limitare la perdita."
    else:
        return "📈 La quota è scesa: meglio PUNTARE per aumentare il profitto."

def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def start(chat_id):
    user_state[chat_id] = {"step": "stake"}
    send_message(
        chat_id,
        "🎯 *Calcolatore PRO Stop Loss*\n\nInserisci lo *stake puntato* (es: 25):"
    )

def process_message(chat_id, text):
    if chat_id not in user_state:
        start(chat_id)
        return

    state = user_state[chat_id]

    if state["step"] == "stake":
        try:
            state["stake"] = float(text)
            state["step"] = "quota_puntata"
            send_message(chat_id, "Inserisci la *quota puntata* (es: 1.72):")
        except:
            send_message(chat_id, "❌ Valore non valido. Inserisci uno stake numerico.")
        return

    if state["step"] == "quota_puntata":
        try:
            state["quota_puntata"] = float(text)
            state["step"] = "variazione"

            keyboard = {
                "inline_keyboard": [
                    [{"text": "+15%", "callback_data": "var_0.15"}],
                    [{"text": "+30%", "callback_data": "var_0.30"}],
                    [{"text": "+50%", "callback_data": "var_0.50"}],
                ]
            }

            send_message(
                chat_id,
                "📈 Seleziona la *variazione prevista* della quota:",
                reply_markup=keyboard
            )
        except:
            send_message(chat_id, "❌ Valore non valido. Inserisci una quota numerica.")
        return

    if state["step"] == "quota_bancata":
        try:
            state["quota_bancata"] = float(text)
            calcola_risultato(chat_id)
        except:
            send_message(chat_id, "❌ Valore non valido. Inserisci una quota numerica.")
        return

def process_callback(chat_id, data):
    state = user_state.get(chat_id, None)
    if not state:
        start(chat_id)
        return

    if data.startswith("var_"):
        variazione = float(data.replace("var_", ""))
        state["variazione"] = variazione

        quota_stimata = stima_quota_futura(state["quota_puntata"], variazione)
        state["quota_stimata"] = quota_stimata

        state["step"] = "recupero"

        keyboard = {
            "inline_keyboard": [
                [{"text": "Recupero 25%", "callback_data": "rec_0.25"}],
                [{"text": "Recupero 50%", "callback_data": "rec_0.50"}],
                [{"text": "Recupero 75%", "callback_data": "rec_0.75"}],
            ]
        }

        send_message(
            chat_id,
            f"Quota stimata futura: *{quota_stimata:.2f}*\n\n"
            "Seleziona la *percentuale di recupero* dello stake:",
            reply_markup=keyboard
        )
        return

    if data.startswith("rec_"):
        recupero = float(data.replace("rec_", ""))
        state["recupero"] = recupero

        state["step"] = "quota_bancata"

        send_message(
            chat_id,
            f"Recupero selezionato: *{int(recupero*100)}%*\n\n"
            "Inserisci la *quota bancata* (puoi usare quella stimata):"
        )
        return

def calcola_risultato(chat_id):
    state = user_state[chat_id]

    stake = state["stake"]
    quota_puntata = state["quota_puntata"]
    quota_bancata = state["quota_bancata"]
    recupero = state["recupero"]

    lay_stake = calcola_lay_stake(stake, quota_puntata, quota_bancata, recupero)
    pnl = calcola_pnl(stake, quota_puntata, lay_stake, quota_bancata)
    suggerimento = suggerimento_operazione(quota_puntata, quota_bancata)

    send_message(
        chat_id,
        f"📊 *Risultato Calcolo PRO*\n\n"
        f"Stake: *{stake}€*\n"
        f"Quota puntata: *{quota_puntata}*\n"
        f"Quota bancata: *{quota_bancata}*\n"
        f"Recupero: *{int(recupero*100)}%*\n\n"
        f"💰 Bancata necessaria: *{lay_stake:.2f}€*\n"
        f"📉 P&L dopo bancata: *{pnl:.2f}€*\n\n"
        f"🧭 {suggerimento}\n\n"
        f"Premi /start per un nuovo calcolo."
    )

    user_state.pop(chat_id, None)

@app.route("/", methods=["GET", "POST", "HEAD"])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        process_message(chat_id, text)

    if "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        data_value = data["callback_query"]["data"]
        process_callback(chat_id, data_value)

    return "OK"

if __name__ == "__main__":
    print("Bot Telegram PRO avviato.")
    app.run(host="0.0.0.0", port=5000)
