import os
import time
import hmac
import hashlib
from threading import Thread
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

# ==========================================
# 🛑 TOKENS AUR DETAILS 🛑
# ==========================================
BOT_TOKEN = "9028905265:AAE0XYHL2KvqgpSff3QYWK-_HKwGSC8WFUY" 
CHANNEL_USERNAME = "@GodMode_SMS" 
SASTASMS_API_KEY = "Stp_c02085951a459afbedc5ba2203aea8d553472b25bf0b909e" 
API_BASE_URL = "https://sastasms.pro/stubs/handler_api.php"
OWNER_IDS = [8226471885, 8692723368] 

# 👇 WEBHOOK SECRET YAHAN DAALNA MAT BHOOLNA 👇
SASTASMS_WEBHOOK_SECRET = "whsec_0d13a1039554d8fc9a0982ed3e12ed33de497fd59dccab4e" 
# ==========================================

bot = telebot.TeleBot(BOT_TOKEN)
users_db = {} 
active_orders = {} 

# ================= 1. FLASK SERVER & WEBHOOK =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running 24/7 Successfully!", 200

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    try:
        signature = request.headers.get('X-Signature')
        raw_body = request.data
        
        expected_signature = hmac.new(SASTASMS_WEBHOOK_SECRET.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return "Invalid Signature", 401
        
        data = request.json
        act_id = str(data.get("activationId"))
        otp_code = data.get("code")
        full_text = data.get("text")
        service = data.get("service")
        
        user_id = active_orders.get(act_id)
        if user_id:
            msg = (
                f"🔔 *OTP RECEIVED!*\n\n"
                f"📱 *Service:* {str(service).upper()}\n"
                f"💬 *OTP Code:* `{otp_code}`\n"
                f"📩 *Full SMS:* {full_text}"
            )
            bot.send_message(user_id, msg, parse_mode="Markdown")
            
        return "OK", 200
    except Exception as e:
        print(f"Webhook Error: {e}")
        return "Internal Error", 500

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    server = Thread(target=run_flask)
    server.daemon = True
    server.start()
# =====================================================================


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

def check_membership(user_id):
    if user_id in OWNER_IDS:
        return True
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Join check error: {e}")
        return False

# --- SMART PARSER API CALL ---
def fetch_services():
    try:
        url = f"{API_BASE_URL}?api_key={SASTASMS_API_KEY}&action=getPrices&country=in&format=json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            flat_services = {}
            
            # Smartly detect JSON structure (nested vs flat)
            target_data = data
            if "in" in data and isinstance(data["in"], dict):
                target_data = data["in"]
            elif "IN" in data and isinstance(data["IN"], dict):
                target_data = data["IN"]
                
            for service_name, details in target_data.items():
                if isinstance(details, dict):
                    price = details.get('cost', details.get('price', 0))
                    flat_services[service_name] = price
                else:
                    flat_services[service_name] = details
                    
            return flat_services
        return None
    except Exception as e:
        print(f"Error fetching services: {e}")
        return None

def fetch_service_price(service_code):
    services_data = fetch_services()
    if services_data and service_code in services_data:
        return services_data[service_code]
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
        users_db[user_id] = {"balance": 50.0} # Testing ke liye ₹50, baad me 0 kar dena

    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("🛒 Products & Services", callback_data="services")
    btn2 = InlineKeyboardButton("💳 My Wallet", callback_data="wallet")
    btn3 = InlineKeyboardButton("📞 Support", callback_data="support")
    markup.add(btn1, btn2)
    markup.add(btn3)

    welcome_text = (
        f"Hello *{message.from_user.first_name}*! 👋\n\n"
        "Welcome to the best and trusted OTP SMS Panel. 🚀\n"
        "Please select an option from below:\n\n"
        "💡 _To buy a number, use command:_\n"
        "`/buy <service>`\n"
        "Example: `/buy wa`"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

# --- BUY COMMAND ---
@bot.message_handler(commands=['buy'])
def buy_number(message):
    user_id = message.from_user.id
    if not check_membership(user_id):
        bot.reply_to(message, "❌ Please join our channel first. Send /start")
        return

    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ *Correct Usage:*\n`/buy <service_code>`\nExample: `/buy wa`", parse_mode="Markdown")
        return

    service = args[1].lower()
    bot.send_message(message.chat.id, "⏳ Checking availability and price...")

    base_price = fetch_service_price(service)
    if base_price is None:
        bot.reply_to(message, "❌ Service not found or currently unavailable.")
        return

    try:
        final_price = round(float(base_price) * 1.70, 2)
    except:
        bot.reply_to(message, "❌ Pricing error.")
        return

    user_balance = users_db.get(user_id, {}).get("balance", 0.0)
    if user_balance < final_price:
        bot.reply_to(message, f"❌ *Insufficient Balance!*\n\n💰 Price: ₹{final_price}\n💳 Your Wallet: ₹{user_balance}", parse_mode="Markdown")
        return

    bot.send_message(message.chat.id, "🔄 Purchasing number from server...")
    try:
        url = f"{API_BASE_URL}?api_key={SASTASMS_API_KEY}&action=getNumber&service={service}&country=in&format=json"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                act_id = str(data.get("activationId", data.get("activation_id")))
                phone = data.get("phone", data.get("number"))
            except:
                parts = response.text.split(":")
                if parts[0] == "ACCESS_NUMBER":
                    act_id = parts[1]
                    phone = parts[2]
                else:
                    bot.reply_to(message, f"❌ Failed to get number. Response: {response.text}")
                    return

            if act_id and phone:
                users_db[user_id]["balance"] -= final_price
                active_orders[act_id] = user_id
                
                success_msg = (
                    f"✅ *Number Purchased Successfully!*\n\n"
                    f"📱 *Service:* {service.upper()}\n"
                    f"📞 *Number:* `{phone}`\n"
                    f"💰 *Amount Deducted:* ₹{final_price}\n\n"
                    f"⏳ Waiting for OTP... (Will be sent here automatically)"
                )
                bot.reply_to(message, success_msg, parse_mode="Markdown")
            else:
                bot.reply_to(message, "❌ Could not retrieve number details.")
        else:
            bot.reply_to(message, "❌ API error. Server might be down.")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error processing purchase: {e}")

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
        
        if services_data:
            text = "🛒 *All Available Services (Live)*\n\n_Type /buy <service_code> to purchase_\n\n"
            count = 0
            
            for service, price in services_data.items():
                if count >= 100: 
                    break
                
                s_lower = str(service).lower()
                
                icon = "📱"
                for key, val in SERVICE_ICONS.items():
                    if key in s_lower:
                        icon = val
                        break
                        
                flag = "🇮🇳" 
                
                try:
                    profit_price = float(price) * 1.70
                    final_price = round(profit_price, 2)
                except:
                    final_price = price
                
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
