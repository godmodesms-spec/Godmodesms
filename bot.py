import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from flask import Flask
from threading import Thread

# Yahan apna bot token daalo
BOT_TOKEN = "9028905265:AAE0XYHL2KvqgpSff3QYWK-_HKwGSC8WFUY"

# Aap dono ki IDs (Future admin commands ke liye)
OWNER_IDS = [] 

# Aapki API Key
API_KEY = "abd57e445024aacd7bfde06d64b16341"
BASE_URL = "https://premiumotp.pro/api/v1/stark"

bot = telebot.TeleBot(BOT_TOKEN)

# --- FLASK KEEP-ALIVE SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running smoothly for everyone!"

def run_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_server)
    t.start()
# -------------------------------

# Main Menu Command (Ab sabke liye khula hai)
@bot.message_handler(commands=['start', 'menu'])
def start_command(message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    
    # Services ke buttons[span_1](start_span)[span_1](end_span)
    markup.add(
        InlineKeyboardButton("🟢 WhatsApp", callback_data="buy_wa"),
        InlineKeyboardButton("🔵 Telegram", callback_data="buy_tg"),
        InlineKeyboardButton("🟣 Instagram", callback_data="buy_ig"),
        InlineKeyboardButton("🔵 Facebook", callback_data="buy_fb")
    )
    markup.add(InlineKeyboardButton("💰 Check Wallet Balance", callback_data="balance"))
    
    bot.reply_to(message, f"👋 Welcome {message.from_user.first_name}!\n\nKonsi service ka number chahiye? Niche button dabayein 👇", reply_markup=markup)

# Button Clicks Handle Karne Ke Liye (Sabke liye open)
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    data = call.data

    # Check Balance Button[span_2](start_span)[span_2](end_span)
    if data == "balance":
        try:
            response = requests.get(f"{BASE_URL}?api_key={API_KEY}&action=getBalance")
            text = response.text
            if "ACCESS_BALANCE" in text:
                balance = text.split(":")[1]
                bot.answer_callback_query(call.id, f"💰 Balance: ₹{balance}", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "Error fetching balance.", show_alert=True)
        except Exception as e:
            bot.answer_callback_query(call.id, "API Error!", show_alert=True)

    # Buy Number Button[span_3](start_span)[span_3](end_span)
    elif data.startswith("buy_"):
        service_code = data.split("_")[1]
        bot.answer_callback_query(call.id, "Number khareed raha hu, wait karo...")
        
        try:
            response = requests.get(f"{BASE_URL}?api_key={API_KEY}&action=getNumber&service={service_code}")
            text = response.text
            
            if "ACCESS_NUMBER" in text:
                _, order_id, phone_number = text.split(":")
                
                # Order aane ke baad Status aur Cancel ke naye buttons banayenge
                order_markup = InlineKeyboardMarkup()
                order_markup.row_width = 2
                order_markup.add(
                    InlineKeyboardButton("🔄 Check OTP", callback_data=f"status_{order_id}"),
                    InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_{order_id}")
                )
                
                msg = f"✅ **Number Ready!**\n\n📱 Number: `+{phone_number}`\n🆔 Order ID: `{order_id}`\n\nApp me number daalo aur OTP aane par niche 'Check OTP' dabao."
                bot.send_message(call.message.chat.id, msg, parse_mode="Markdown", reply_markup=order_markup)
            else:
                bot.send_message(call.message.chat.id, f"⚠️ Failed! Response: {text}")
        except Exception as e:
            bot.send_message(call.message.chat.id, "API Error occurred.")

    # Check Status Button[span_4](start_span)[span_4](end_span)
    elif data.startswith("status_"):
        order_id = data.split("_")[1]
        try:
            response = requests.get(f"{BASE_URL}?api_key={API_KEY}&action=getStatus&id={order_id}")
            text = response.text
            
            if "STATUS_WAIT_CODE" in text:
                bot.answer_callback_query(call.id, "⏳ Abhi OTP nahi aaya hai, thoda wait karo...", show_alert=True)
            elif "STATUS_OK" in text:
                otp = text.split(":")[1]
                bot.send_message(call.message.chat.id, f"🎉 **OTP RECEIVED!**\n\n🆔 Order ID: `{order_id}`\n🔑 OTP: `{otp}`", parse_mode="Markdown")
                bot.answer_callback_query(call.id, "OTP Mil Gaya!")
            else:
                bot.answer_callback_query(call.id, f"Status: {text}", show_alert=True)
        except Exception as e:
            bot.answer_callback_query(call.id, "API Error!", show_alert=True)

    # Cancel Button[span_5](start_span)[span_5](end_span)
    elif data.startswith("cancel_"):
        order_id = data.split("_")[1]
        try:
            response = requests.get(f"{BASE_URL}?api_key={API_KEY}&action=setStatus&id={order_id}&status=8")
            text = response.text
            
            if "ACCESS_CANCEL" in text:
                bot.send_message(call.message.chat.id, f"❌ Order `{order_id}` cancel kar diya gaya hai aur paise refund ho gaye hain.", parse_mode="Markdown")
                bot.answer_callback_query(call.id, "Order Cancelled!")
            else:
                bot.answer_callback_query(call.id, "Cancel nahi ho paaya ya already complete hai.", show_alert=True)
        except Exception as e:
            bot.answer_callback_query(call.id, "API Error!", show_alert=True)

# Pehle Flask server start karo
keep_alive()

# Fir bot ki polling start karo
bot.infinity_polling()
                                  
