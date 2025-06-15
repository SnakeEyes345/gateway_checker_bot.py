# gateway_checker_bot.py
# Compatible with python-telegram-bot==13.15 and Render (via Flask)

import logging
import requests
import socket
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Bot Token
TOKEN = '7982376961:AAFf-SRqyFyTEZFw7zi-5PdqRyyrdMgRK40'

# Channel ID
CHANNEL_ID = -1002443574063

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app to keep the service alive
app = Flask(__name__)

@app.route('/')
def index():
    return 'Telegram Gateway Checker Bot is Running!'

# Keywords
GATEWAYS = ['stripe', 'paypal', 'eway', 'nab', 'omise']
DONATE_KEYWORDS = ['donate', 'donation', 'contribute', 'give']
MEMBERSHIP_KEYWORDS = ['membership', 'member', 'join', 'subscribe', 'account']

def get_country_from_ip(ip):
    try:
        r = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
        return r.json().get("country", "Unknown")
    except:
        return "Unknown"

def scan_url(update, context, url):
    try:
        r = requests.get(url, timeout=10)
        html = r.text.lower()
        soup = BeautifulSoup(r.text, 'html.parser')

        gateways = [g.capitalize() for g in GATEWAYS if g in html]
        captcha = 'Yes' if 'captcha' in html else 'No'
        cloudflare = 'Yes' if 'cloudflare' in r.headers.get('Server', '').lower() else 'No'
        graphql = 'Yes' if '/graphql' in r.text else 'No'
        donate = any(k in html for k in DONATE_KEYWORDS)
        membership = any(k in html for k in MEMBERSHIP_KEYWORDS)

        hostname = urlparse(url).hostname
        ip = socket.gethostbyname(hostname)
        country = get_country_from_ip(ip)

        msg = f"""🔥 𝐒𝐧𝐚𝐤𝐞𝐄𝐲𝐞𝐬 🔥
━━━━━━━━━━━━━━━━━━━━━━━
🌐 URL: {url}
💳 Gateways: {', '.join(gateways) if gateways else 'None ❌'}
🤖 Captcha: {captcha}
🛡️ Cloudflare: {cloudflare}
🧠 GraphQL: {graphql}
📡 Status: {r.status_code}
🌍 Country: {country}
❤️ Donate Site: {'Yes ✅' if donate else 'No ❌'}
👥 Membership Site: {'Yes ✅' if membership else 'No ❌'}
━━━━━━━━━━━━━━━━━━━━━━━
🧑‍💻 Checked by: @{update.effective_user.username or 'Anonymous'}
🤖 Bot By: @{context.bot.username}
"""
        update.message.reply_text(msg)
        context.bot.send_message(chat_id=CHANNEL_ID, text=msg)
    except Exception as e:
        logger.error(e)
        update.message.reply_text("❌ Failed to fetch URL.")

def start(update, context):
    update.message.reply_text("🔍 Welcome! Use /scanurl <url> to check for gateways.\nUse /fake <country_code> to get a fake profile.")

def scanurl(update, context):
    if not context.args:
        update.message.reply_text("❌ Usage: /scanurl <url>")
        return
    url = context.args[0].strip()
    if not url.startswith("http"):
        update.message.reply_text("❌ Please enter a valid URL starting with http:// or https://")
        return
    scan_url(update, context, url)

def check_url(update, context):
    url = update.message.text.strip()
    if url.startswith("http"):
        scan_url(update, context, url)

def fake(update, context):
    if not context.args:
        update.message.reply_text("❌ Usage: /fake <country_code>\nExample: /fake US")
        return

    code = context.args[0].upper()
    try:
        r = requests.get(f"https://randomuser.me/api/?nat={code}", timeout=10)
        data = r.json()["results"][0]

        msg = f"""📍 Fake Profile Generator ({code})
━━━━━━━━━━━━━━━━━━━━━━━
👤 Name: {data['name']['title']} {data['name']['first']} {data['name']['last']}
🏠 Address: {data['location']['street']['number']} {data['location']['street']['name']}
🏙️ City: {data['location']['city']}
🗺️ State: {data['location']['state']}
🌍 Country: {data['location']['country']}
📮 Postcode: {data['location']['postcode']}
📧 Email: {data['email']}
📞 Phone: {data['phone']}
📱 Cell: {data['cell']}
━━━━━━━━━━━━━━━━━━━━━━━
🤖 Bot By: @{context.bot.username}
"""
        update.message.reply_text(msg)
        context.bot.send_message(chat_id=CHANNEL_ID, text=msg)
    except Exception as e:
        logger.error(e)
        update.message.reply_text("❌ Failed to fetch profile.")

def run_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("scanurl", scanurl))
    dp.add_handler(CommandHandler("fake", fake))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_url))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    # Start bot in background thread
    Thread(target=run_bot).start()
    # Start Flask app
    app.run(host='0.0.0.0', port=8080)
