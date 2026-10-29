import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from flask import Flask
from threading import Thread

# Yahan apna bot token daalo
BOT_TOKEN = "9028905265:AAE0XYHL2KvqgpSff3QYWK-_HKwGSC8WFUY"

# Aapki API Key aur Base URL[span_2](start_span)[span_2](end_span)
API_KEY = "abd57e445024aacd7bfde06d64b16341"
BASE_URL = "https://premiumotp.pro/api/v1/stark"

bot = telebot.TeleBot(BOT_TOKEN)

# --- FLASK KEEP-ALIVE SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running smoothly with step-by-step UI!"

def run_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_server)
    t.start()
# -------------------------------

# 1. Main Menu - Start Command
@bot.message_handler(commands=['start', 'menu'])
def start_command(message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    
    # Step 1: Service ke buttons 
    markup.add(
        InlineKeyboardButton("🟢 WhatsApp", callback_data="service_wa"),
        InlineKeyboardButton("🔵 Telegram", callback_data="service_tg"),
        InlineKeyboardButton("🟣 Instagram", callback_data="service_ig"),
        InlineKeyboardButton("🔵 Facebook", callback_data="service_fb")
    )
    markup.add(InlineKeyboardButton("💰 Check Wallet Balance", callback_data="balance"))
    
    bot.reply_to(message, f"👋 Welcome {message.from_user.first_name}!\n\nStep 1: Konsi service ka number chahiye? Niche select karein 👇", reply_markup=markup)

# Button Clicks Handle Karne Ke Liye
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    data = call.data

    # Check Balance Button[span_3](start_span)[span_3](end_span)
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

    # Step 2: Service select hone ke baad Country/Server dikhana
    elif data.startswith("service_"):
        service_code = data.split("_")[1]
        
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        # Image ke according Server 1 aur Server 2 add kiye hain[span_4](start_span)[span_4](end_span)
        markup.add(
            InlineKeyboardButton("🌐 Server 1 (Fastest)", callback_data=f"buy_{service_code}_server1"),
            InlineKeyboardButton("🌟 Server 2 (Premium)", callback_data=f"buy_{service_code}_server2"),
            InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")
        )
        
        # Message edit karke server list dikhayega
        bot.edit_message_text(
            f"Step 2: Aapne `{service_code.upper()}` select kiya hai.\n\nAb niche se Country/Server select karein 👇", 
            call.message.chat.id, 
            call.message.message_id, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

    # Back to Menu Button
    elif data == "back_menu":
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(
            InlineKeyboardButton("🟢 WhatsApp", callback_data="service_wa"),
            InlineKeyboardButton("🔵 Telegram", callback_data="service_tg"),
            InlineKeyboardButton("🟣 Instagram", callback_data="service_ig"),
            InlineKeyboardButton("🔵 Facebook", callback_data="service_fb")
        )
        markup.add(InlineKeyboardButton("💰 Check Wallet Balance", callback_data="balance"))
        
        bot.edit_message_text(
            "Step 1: Konsi service ka number chahiye? Niche select karein 👇", 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=markup
        )

    # Step 3: Final Buy Request (Jahan error/No balance aayega)[span_5](start_span)[span_5](end_span)
    elif data.startswith("buy_"):
        # Format: buy_wa_server1
        parts = data.split("_")
        service_code = parts[1]
        server_code = parts[2]
        
        bot.answer_callback_query(call.id, "Number nikal raha hu, thoda wait karein...")
        
        try:
            # Yahan server parameter add kiya gaya hai[span_6](start_span)[span_6](end_span)
            response = requests.get(f"{BASE_URL}?api_key={API_KEY}&action=getNumber&service={service_code}&server={server_code}")
            text = response.text
            
            if "ACCESS_NUMBER" in text:
                _, order_id, phone_number = text.split(":")
                
                order_markup = InlineKeyboardMarkup()
                order_markup.row_width = 2
                order_markup.add(
                    InlineKeyboardButton("🔄 Check OTP", callback_data=f"status_{order_id}"),
                    InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_{order_id}")
                )
                
                msg = f"✅ **Number Ready!**\n\n📱 Number: `+{phone_number}`\n🆔 Order ID: `{order_id}`\n🌐 Server: `{server_code}`\n\nApp me number daalo aur OTP aane par niche 'Check OTP' dabao."
                bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=order_markup)
            
            # Agar balance nahi hai ya koi error aata hai
            else:
                bot.send_message(call.message.chat.id, f"⚠️ Number nahi mila!\n\nKaaran/Error: `{text}`\n(Agar NO_BALANCE aa raha hai to pehle site par paise add karein)", parse_mode="Markdown")
        
        except Exception as e:
            bot.send_message(call.message.chat.id, "API me koi dikkat aa gayi.")

    # Check Status Button[span_7](start_span)[span_7](end_span)
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

    # Cancel Button[span_8](start_span)[span_8](end_span)
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
        
