import os
import time
import json
import hmac
import hashlib
from threading import Thread
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

# ==========================================
# 🛑 APNI DETAILS YAHAN CHECK KAR LO 🛑
# ==========================================
BOT_TOKEN = "9028905265:AAGjwYOrfuAJnicGHPE4BtG2IMPDX9HVInk" 
CHANNEL_USERNAME = "@GodMode_SMS" # YAHAN APNA CHANNEL USERNAME DAAL LENA
SASTASMS_API_KEY = "Stp_c02085951a459afbedc5ba2203aea8d553472b25bf0b909e" 
API_BASE_URL = "https://sastasms.pro/api/handler_api.php" 

# 👇 NAYA: SASTASMS WEBHOOK SECRET YAHAN DAAL (Dashboard -> Settings -> Webhook me milega) 👇
SASTASMS_WEBHOOK_SECRET = "whsec_3046dbe0e008c05cc05fe108d22b5213c4ab4c022474a33f" 

OWNER_IDS = [8226471885, 8692723368] 
# ==========================================

bot = telebot.TeleBot(BOT_TOKEN)
users_db = {} 
active_orders = {} # NAYA: Activation ID aur User ID ko map karne ke liye

# ================= 1. FLASK SERVER (24/7 Keep-Alive & WEBHOOK) =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running 24/7 Successfully!", 200

# 👇 NAYA: WEBHOOK ROUTE OTP RECEIVE KARNE KE LIYE 👇
@app.route('/webhook', methods=['POST'])
def webhook_handler():
    try:
        # X-Signature verification SastaSMS docs ke hisaab se
        signature = request.headers.get('X-Signature')
        raw_body = request.data
        
        # HMAC-SHA256 signature calculate karo secret ke sath
        expected_signature = hmac.new(SASTASMS_WEBHOOK_SECRET.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return "Invalid Signature", 401
        
        # Data parse karo
        data = request.json
        act_id = str(data.get("activationId"))
        otp_code = data.get("code")
        full_text = data.get("text")
        service = data.get("service")
        
        # Check karo ye order kis user ka hai
        user_id = active_orders.get(act_id)
        if user_id:
            msg = (
                f"🔔 *OTP RECEIVED!*\n\n"
                f"📱 *Service:* {service.upper()}\n"
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


# --- EMOJI / ICONS MAP ---
SERVICE_ICONS = {
    'wa': '💬', 'whatsapp': '💬',
    'tg': '✈️', 'telegram': '✈️',
    'ig': '📸', 'instagram': '📸',
    'fb': '📘', 'facebook': '📘',
    'go': '🌐', 'google': '🌐',
    'tw': '🐦', 'twitter': '🐦', 'x': '🐦',
    'nf': '🍿', 'netflix': '🍿',
    'am': '🛒', 'amazon': '🛒',
    'dc': '🎮', 'discord': '🎮',
    'yt': '▶️', 'youtube': '▶️'
}

# --- COUNTRY FLAGS MAP ---
COUNTRY_FLAGS = {
    'in': '🇮🇳', 'india': '🇮🇳',
    'us': '🇺🇸', 'usa': '🇺🇸',
    'uk': '🇬🇧', 'gb': '🇬🇧',
    'ru': '🇷🇺', 'russia': '🇷🇺',
    'id': '🇮🇩', 'indonesia': '🇮🇩',
    'br': '🇧🇷', 'brazil': '🇧🇷',
    'cn': '🇨🇳', 'china': '🇨🇳',
    'pk': '🇵🇰', 'pakistan': '🇵🇰',
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
    except:
        return False

# --- SASTASMS API CALLS ---
def fetch_services():
    try:
        url = f"{API_BASE_URL}?api_key={SASTASMS_API_KEY}&action=getServicesList&format=json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching services: {e}")
        return None

def fetch_service_price(service_code, country_code="in"):
    services_data = fetch_services()
    if services_data:
        # Check specific service + country or just service
        search_key = f"{service_code}_{country_code}"
        if search_key in services_data:
            return services_data[search_key]
        elif service_code in services_data:
            return services_data[service_code]
    return None

# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if not check_membership(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Join Our Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("✅ I have Joined", callback_data="check_join"))
        bot.send_message(message.chat.id, "👋 Welcome! Please join our official channel to use this bot.", reply_markup=markup)
        return

    if user_id not in users_db:
        # NAYA: Testing ke liye balance 50 de diya hai taaki tu check kar sake. Baad me isko 0.0 kar dena.
        users_db[user_id] = {"balance": 50.0}

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
        "`/buy <service> <country>`\n"
        "Example: `/buy wa in`"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

# 👇 NAYA: BUY NUMBER COMMAND 👇
@bot.message_handler(commands=['buy'])
def buy_number(message):
    user_id = message.from_user.id
    if not check_membership(user_id):
        bot.reply_to(message, "❌ Please join our channel first. Send /start")
        return

    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ *Correct Usage:*\n`/buy <service_code> [country_code]`\nExample: `/buy wa in`", parse_mode="Markdown")
        return

    service = args[1].lower()
    country = args[2].lower() if len(args) > 2 else "in"
    
    bot.send_message(message.chat.id, "⏳ Checking availability and price...")

    # Fetch Base Price
    base_price_data = fetch_service_price(service, country)
    if not base_price_data:
        bot.reply_to(message, "❌ Service not found or currently unavailable.")
        return

    try:
        base_price = float(base_price_data.get('price', base_price_data) if isinstance(base_price_data, dict) else base_price_data)
        final_price = round(base_price * 1.70, 2) # 70% Profit Markup
    except:
        bot.reply_to(message, "❌ Pricing error. Try again later.")
        return

    # Check User Balance
    user_balance = users_db.get(user_id, {}).get("balance", 0.0)
    if user_balance < final_price:
        bot.reply_to(message, f"❌ *Insufficient Balance!*\n\n💰 Price: ₹{final_price}\n💳 Your Wallet: ₹{user_balance}\n\nPlease add funds.", parse_mode="Markdown")
        return

    # Call API to get number
    bot.send_message(message.chat.id, "🔄 Purchasing number from server...")
    try:
        url = f"{API_BASE_URL}?api_key={SASTASMS_API_KEY}&action=getNumber&service={service}&country={country}&format=json"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # Handle successful number retrieval (assuming SastaSMS JSON format returns 'phone' and 'activationId')
            # Ya phir plain text aayega 'ACCESS_NUMBER:id:number'
            if isinstance(data, dict):
                act_id = str(data.get("activationId", data.get("activation_id")))
                phone = data.get("phone", data.get("number"))
            else:
                # Agar fallback plain text hui (ACCESS_NUMBER:123:919876)
                parts = response.text.split(":")
                if parts[0] == "ACCESS_NUMBER":
                    act_id = parts[1]
                    phone = parts[2]
                else:
                    bot.reply_to(message, f"❌ Failed to get number. API Response: {response.text}")
                    return

            if act_id and phone:
                # Deduct Balance
                users_db[user_id]["balance"] -= final_price
                
                # Save Order for Webhook
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
                bot.reply_to(message, f"❌ Could not retrieve number details. Server returned: {data}")
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

                base_price = details.get('price', details) if isinstance(details, dict) else details
                try:
                    profit_price = float(base_price) * 1.70
                    final_price = round(profit_price, 2) 
                except ValueError:
                    final_price = base_price 
                
                text += f"{icon} {flag} *{str(service).upper()}* - ₹{final_price}\n"
                count += 1
                
                if len(text) > 3800:
                    break
                    
            text += "\n_(Prices & Availability are fetched directly from server)_"
        else:
            text = "❌ *Error*\n\nServer is busy or API response failed. Please try again later."
            
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
