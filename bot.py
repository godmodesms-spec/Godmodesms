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
    # Render apne aap PORT assign karega
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    server = Thread(target=run_flask)
    server.daemon = True
    server.start()
# =====================================================================


# ==========================================
# 🛑 YAHAN APNI DETAILS DALO 🛑
# ==========================================
BOT_TOKEN = "YAHAN_BOTFATHER_WALA_TOKEN_DALO" # BotFather se mila token yahan daalein
CHANNEL_USERNAME = "@YourChannelUsername" # Apne channel ka username daalein
SASTASMS_API_KEY = "Stp_c02085951a459afbedc5ba2203aea8d553472b25bf0b909e" # Tumhari SastaSMS API

# 👑 YAHAN APNI AUR APNE DOST KI TELEGRAM USER ID DALO (Numbers mein)
OWNER_IDS = [1234567890, 9876543210] # Example id hata kar apni asli ID daalna
# ==========================================

bot = telebot.TeleBot(BOT_TOKEN)

# Abhi ke liye temporary wallet data
users_db = {} 

# --- CHANNEL JOIN CHECK KARNE WALA SYSTEM ---
def check_membership(user_id):
    # Agar user khud OWNER hai, toh usko channel join check bypass karne do (optional)
    if user_id in OWNER_IDS:
        return True
        
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        if status in ['member', 'administrator', 'creator']:
            return True
        return False
    except:
        return False

# --- ADMIN COMMAND (Sirf Owners ke liye) ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if user_id in OWNER_IDS:
        bot.reply_to(message, "👑 *Welcome Boss!* Aap dono owners mein se ek hain. Yahan aap aage chal kar admin buttons laga sakte hain.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Aap owner nahi hain!")

# --- START COMMAND & MAIN MENU ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # Check karega ki bande ne channel join kiya hai ya nahi
    if not check_membership(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Join Our Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("✅ I have Joined", callback_data="check_join"))
        bot.send_message(message.chat.id, "👋 Welcome! Please join our official channel to use this bot.", reply_markup=markup)
        return

    # Agar naya user hai toh uska wallet 0.0 balance ke sath bana dega
    if user_id not in users_db:
        users_db[user_id] = {"balance": 0.0}

    # Main Menu ke Buttons
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

# --- BUTTON DABAANE PAR KYA HOGA (CALLBACK HANDLER) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id

    # 1. Channel Join Check Button
    if call.data == "check_join":
        if check_membership(user_id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_welcome(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined the channel yet!", show_alert=True)

    # 2. Wallet Button
    elif call.data == "wallet":
        balance = users_db.get(user_id, {}).get("balance", 0.0)
        text = f"💳 *Your Wallet*\n\n💰 Balance: ₹{balance}\n\nTo add funds, please contact Support."
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # 3. Support Button (Tumhara aur dost ka link)
    elif call.data == "support":
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("👨‍💻 Main Owner", url="https://t.me/YourUsernameHere")) # Yahan apna username daalna
        markup.add(InlineKeyboardButton("👨‍💻 Co-Owner", url="https://t.me/FriendUsernameHere")) # Yahan dost ka username daalna
        markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_home"))
        bot.edit_message_text("📞 *Support Team*\n\nNeed help? Contact us below:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # 4. Products & Services (SastaSMS API)
    elif call.data == "services":
        bot.answer_callback_query(call.id, "Loading services... 🔄")
        
        # Abhi dummy text dikhayega
        text = "🛒 *Available Services*\n\n📱 WhatsApp OTP - ₹10\n✈️ Telegram OTP - ₹12\n📸 Instagram OTP - ₹8\n\n_(Connecting to Server...)_"
            
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    # 5. Back Button
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
    keep_alive()  # Pehle Flask chalega
    
    print("Starting Main Bot...")
    start_bot()   # Phir bot chalega crash-proof mode mein
