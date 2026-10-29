import telebot
import requests
from flask import Flask
from threading import Thread

# Yahan apna bot token daalo
BOT_TOKEN = "9028905265:AAE0XYHL2KvqgpSff3QYWK-_HKwGSC8WFUY"
# Yahan apni aur apne dost ki Telegram User ID daalo
ADMIN_IDS = [8692723368, 8226471885] 

# Aapki API Key 
API_KEY = "abd57e445024aacd7bfde06d64b16341"
BASE_URL = "https://premiumotp.pro/api/v1/stark"

bot = telebot.TeleBot(BOT_TOKEN)

# --- FLASK KEEP-ALIVE SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running smoothly!"

def run_server():
    # Aap port change kar sakte ho agar host pe zaroorat ho
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_server)
    t.start()
# -------------------------------

def is_admin(user_id):
    return user_id in ADMIN_IDS

@bot.message_handler(commands=['start'])
def start_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Sorry, aap is bot ko use nahi kar sakte. Access denied.")
        return
    
    welcome_text = (
        "Welcome Admin! 🚀\n\n"
        "Available Commands:\n"
        "/balance - Check wallet balance\n"
        "/buy <service> - Buy a number (e.g. /buy wa)\n"
        "/status <id> - Check OTP status\n"
        "/cancel <id> - Cancel number/refund\n\n"
        "Service codes: wa (WhatsApp), tg (Telegram), ig (Instagram), fb (Facebook)"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['balance'])
def check_balance(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        response = requests.get(f"{BASE_URL}?api_key={API_KEY}&action=getBalance")
        text = response.text
        if "ACCESS_BALANCE" in text:
            balance = text.split(":")[1]
            bot.reply_to(message, f"💰 Current Balance: ₹{balance}")
        else:
            bot.reply_to(message, f"Error: {text}")
    except Exception as e:
        bot.reply_to(message, "API error occurred.")

@bot.message_handler(commands=['buy'])
def buy_number(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Bhai, format galat hai. Aise likho: /buy wa")
        return
    
    service_code = parts[1].lower()
    
    try:
        response = requests.get(f"{BASE_URL}?api_key={API_KEY}&action=getNumber&service={service_code}")
        text = response.text
        
        if "ACCESS_NUMBER" in text:
            _, order_id, phone_number = text.split(":")
            bot.reply_to(message, f"✅ Number Bought Successfully!\n\n📱 Number: `+{phone_number}`\n🆔 Order ID: `{order_id}`\n\nAb OTP check karne ke liye type karein: /status {order_id}", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"Failed to get number. Response: {text}")
    except Exception as e:
        bot.reply_to(message, "API error occurred.")

@bot.message_handler(commands=['status'])
def check_status(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Order ID daalna zaroori hai. Format: /status <order_id>")
        return
    
    order_id = parts[1]
    
    try:
        response = requests.get(f"{BASE_URL}?api_key={API_KEY}&action=getStatus&id={order_id}")
        text = response.text
        
        if "STATUS_WAIT_CODE" in text:
            bot.reply_to(message, "⏳ OTP ka wait ho raha hai...")
        elif "STATUS_OK" in text:
            otp = text.split(":")[1]
            bot.reply_to(message, f"🎉 OTP Received: `{otp}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"Status: {text}")
    except Exception as e:
        bot.reply_to(message, "API error occurred.")

@bot.message_handler(commands=['cancel'])
def cancel_order(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Order ID daalna zaroori hai. Format: /cancel <order_id>")
        return
    
    order_id = parts[1]
    
    try:
        response = requests.get(f"{BASE_URL}?api_key={API_KEY}&action=setStatus&id={order_id}&status=8")
        text = response.text
        
        if "ACCESS_CANCEL" in text:
            bot.reply_to(message, "❌ Order cancel ho gaya aur refund mil gaya.")
        else:
            bot.reply_to(message, f"Failed to cancel. Response: {text}")
    except Exception as e:
        bot.reply_to(message, "API error occurred.")

# Pehle Flask server start karo
keep_alive()

# Fir bot ki polling start karo
bot.infinity_polling()
