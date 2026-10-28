import os
import time
from threading import Thread
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

# ================= 1. FLASK SERVER (24/7 Keep-Alive) =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running 24/7 Successfully!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    server = Thread(target=run_flask)
    server.daemon = True
    server.start()
# =====================================================================


# ==========================================
# 🛑 NAYA TOKEN AUR BAAKI DETAILS YAHAN HAIN 🛑
# ==========================================
BOT_TOKEN = "9028905265:AAE0XYHL2KvqgpSff3QYWK-_HKwGSC8WFUY" 
CHANNEL_USERNAME = "@GodMode_SMS" 
SASTASMS_API_KEY = "Stp_c02085951a459afbedc5ba2203aea8d553472b25bf0b909e" 
API_BASE_URL = "https://sastasms.pro/stubs/handler_api.php"
OWNER_IDS = [8226471885, 8692723368] 
# ==========================================

bot = telebot.TeleBot(BOT_TOKEN)
users_db = {} 

# --- EMOJI & FLAGS MAP ---
SERVICE_ICONS = {
    'wa': '💬', 'whatsapp': '💬', 'tg': '✈️', 'telegram': '✈️',
    'ig': '📸', 'instagram': '📸', 'fb': '📘', 'facebook': '📘',
    'go': '🌐', 'google': '🌐', 'tw': '🐦', 'twitter': '🐦', 'x': '🐦',
    'nf': '🍿', 'netflix': '🍿', 'am': '🛒', 'amazon': '🛒',
    'dc': '🎮', 'discord': '🎮', 'yt': '▶️', 'youtube': '▶️'
}

COUNTRY_FLAGS = {
    'in': '🇮🇳', 'india': '🇮🇳', 'us': '🇺🇸', 'usa': '🇺🇸',
    'uk': '🇬🇧', 'gb': '🇬🇧', 'ru': '🇷🇺', 'russia': '🇷🇺',
    'id': '🇮🇩', 'indonesia': '🇮🇩', 'br': '🇧🇷', 'brazil': '🇧🇷',
    'cn': '🇨🇳', 'china': '🇨🇳', 'pk': '🇵🇰', 'pakistan': '🇵🇰',
    'bd': '🇧🇩', 'bangladesh': '🇧🇩'
}

# --- CHANNEL JOIN CHECK ---
def check_membership(user_id):
    if user_id in OWNER_IDS:
        return True
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        if status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"Join check error: {e}")
        return False

# --- SASTASMS API CALL (WITH ERROR CATCHING) ---
def fetch_services():
    try:
        url = f"{API_BASE_URL}?api_key={SASTASMS_API_KEY}&action=getServicesList&format=json"
        response = requests.get(url, timeout=15) 
        
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                print(f"API ne JSON nahi bheja! Raw Response: {response.text}")
                return None
        else:
            print(f"API Error! Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching services: {e}")
        return None

# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if not check_membership(user_id):
        markup = InlineKeyboardMarkup()
        clean_channel_name = CHANNEL_USERNAME.replace("@", "")
        markup.add(InlineKeyboardButton("📢 Join Our Channel", url=f"https://t.me/{clean_channel_name}"))
        markup.add(InlineKeyboardButton("✅ I have Joined", callback_data="check_join"))
        bot.send_message(message.chat.id, "👋 Welcome! Please join our official channel to use this bot.", reply_markup=markup)
        return

    if user_id not in users_db:
        users_db[user_id] = {"balance": 0.0}

    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("🛒 Products & Services", callback_data="services")
    btn2 = InlineKeyboardButton("💳 My Wallet", callback_data="wallet")
    btn3 = InlineKeyboardButton("📞 Support", callback_data="support")
    markup.add(btn1, btn2)
    markup.add(btn3)

    welcome_text = (
        f"Hello *{message.from_user.first_name}*! 👋\n\n"
        "Welcome to the best and trusted OTP SMS Panel. 🚀\n"
        "Please select an option from below:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

# --- CALLBACK HANDLER ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id

    if call.data == "check_join":
        if check_membership(user_id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_welcome(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined the channel yet!", show_alert=True)

    elif call.data == "wallet":
        balance = users_db.get(user_id, {}).get("balance", 0.0)
        text = f"💳 *Your Wallet*\n\n💰 Balance: ₹{balance}\n\nTo add funds, please contact Support."
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "support":
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("👨‍💻 Main Owner", url="tg://user?id=8226471885")) 
        markup.add(InlineKeyboardButton("👨‍💻 Co-Owner", url="tg://user?id=8692723368")) 
        markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_home"))
        bot.edit_message_text("📞 *Support Team*\n\nNeed help? Contact us below:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "services":
        bot.answer_callback_query(call.id, "Fetching live services... 🔄")
        
        services_data = fetch_services()
        
        if services_data and isinstance(services_data, dict):
            text = "🛒 *All Available Services (Live)*\n\n"
            count = 0
            
            for service, details in services_data.items():
                if count >= 100: 
                    break
                
                s_lower = str(service).lower()
                
                icon = "📱"
                for key, val in SERVICE_ICONS.items():
                    if key in s_lower:
                        icon = val
                        break
                        
                flag = "🌍" 
                for key, val in COUNTRY_FLAGS.items():
                    if f"_{key}" in s_lower or key == s_lower.split('_')[-1]:
                        flag = val
                        break

                # 70% PROFIT CALCULATOR
                base_price = details.get('price', details) if isinstance(details, dict) else details
                try:
                    profit_price = float(base_price) * 1.70
                    final_price = round(profit_price, 2)
                except (ValueError, TypeError):
                    final_price = base_price
                
                text += f"{icon} {flag} *{str(service).upper()}* - ₹{final_price}\n"
                count += 1
                
                if len(text) > 3800:
                    break
                    
            text += "\n_(Prices & Availability are fetched directly from server)_"
        else:
            text = "❌ *Error*\n\nServer is busy or API response format is incorrect. Please try again later."
            
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "back_home":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_welcome(call.message)

# ================= 3. CRASH PROOF BOT RUNNER =================
def start_bot():
    while True:
        try:
            print("Bot polling started... 🚀")
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"Bot error: {e}. Restarting in 5 seconds... 🔄")
            time.sleep(5)

if __name__ == "__main__":
    print("Starting Flask Web Server...")
    keep_alive() 
    print("Starting Main Bot...")
    start_bot()
