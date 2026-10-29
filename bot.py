import os
import time
import html
from threading import Thread
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

# ================= 1. FLASK SERVER (24/7 Keep-Alive) =================
app = Flask(__name__)

@app.route('/')
def home():
    return "GodMode SMS Bot is Running 24/7 Successfully!", 200

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    server = Thread(target=run_flask)
    server.daemon = True
    server.start()

# ================= 2. BOT & API CONFIGURATION =================
BOT_TOKEN = "9272520655:AAEieDq9xznV7U2pscfnAs6HA-m3C-xUlJ0"
CHANNEL_USERNAME = "@GodMode_SMS"
PREMIUMOTP_API_KEY = "ff653726dc0895dc4fb639bea1e937e4"

BASE_URL = "https://premiumotp.pro/api/v1"
STARK_URL = "https://premiumotp.pro/api/v1/stark"

OWNER_IDS = [8226471885, 8692723368]
PROFIT_MULTIPLIER = 1.70  # 70% Profit

bot = telebot.TeleBot(BOT_TOKEN)

users_db = {}
active_orders = {}
services_cache = {"server1": [], "server2": []}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

SERVICE_ICONS = {
    'wa': '💬', 'whatsapp': '💬',
    'tg': '✈️', 'telegram': '✈️',
    'ig': '📸', 'instagram': '📸',
    'fb': '📘', 'facebook': '📘',
    'go': '🌐', 'google': '🌐', 'gmail': '🌐',
    'tw': '🐦', 'twitter': '🐦', 'x': '🐦',
    'nf': '🍿', 'netflix': '🍿',
    'am': '🛒', 'amazon': '🛒',
    'dc': '🎮', 'discord': '🎮',
    'yt': '▶️', 'youtube': '▶️',
    'fk': '🛍️', 'flipkart': '🛍️',
    'sw': '🍔', 'swiggy': '🍔',
    'zm': '🍕', 'zomato': '🍕',
    'sn': '👻', 'snapchat': '👻',
    'tt': '🎵', 'tiktok': '🎵'
}

COUNTRY_FLAGS = {
    'in': '🇮🇳', 'india': '🇮🇳',
    'us': '🇺🇸', 'usa': '🇺🇸',
    'uk': '🇬🇧', 'gb': '🇬🇧',
    'ru': '🇷🇺', 'russia': '🇷🇺',
    'id': '🇮🇩', 'indonesia': '🇮🇩',
    'br': '🇧🇷', 'brazil': '🇧🇷',
    'pk': '🇵🇰', 'pakistan': '🇵🇰',
    'bd': '🇧🇩', 'bangladesh': '🇧🇩'
}

def ensure_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {"balance": 0.0}

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

def get_api_balance():
    try:
        url = f"{STARK_URL}?api_key={PREMIUMOTP_API_KEY}&action=getBalance"
        res = requests.get(url, headers=HEADERS, timeout=12)
        text = res.text.strip()
        if "ACCESS_BALANCE:" in text:
            return text.split(":")[1]
        return text
    except Exception as e:
        return f"Error: {e}"

def fetch_services(server_name="server1"):
    try:
        url = f"{BASE_URL}/get-services?api_key={PREMIUMOTP_API_KEY}&server={server_name}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data.get("status") == "success":
                srv_list = data.get("services", [])
                services_cache[server_name] = srv_list
                return srv_list, None
            elif isinstance(data, list):
                services_cache[server_name] = data
                return data, None
            else:
                return None, data.get("message", f"No services found on {server_name}")
        else:
            return None, f"HTTP Error {response.status_code}"
    except Exception as e:
        print(f"Error fetching services: {e}")
        return None, str(e)

def get_icon_and_flag(s_name, s_code):
    icon = "📱"
    for key, val in SERVICE_ICONS.items():
        if key == s_code or key in s_name.lower():
            icon = val
            break

    flag = "🇮🇳"
    for key, val in COUNTRY_FLAGS.items():
        if key in s_name.lower():
            flag = val
            break
    return icon, flag

def get_main_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("🛒 Services & Price List", callback_data="services_server1")
    btn2 = InlineKeyboardButton("📲 Buy OTP Number", callback_data="buymenu_server1_0")
    btn3 = InlineKeyboardButton("💳 My Wallet", callback_data="wallet")
    btn4 = InlineKeyboardButton("📞 Support", callback_data="support")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    
    if user_id in OWNER_IDS:
        markup.add(InlineKeyboardButton("👑 Owner Admin Panel", callback_data="admin_panel"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    ensure_user(user_id)
    
    if not check_membership(user_id):
        markup = InlineKeyboardMarkup()
        clean_channel = CHANNEL_USERNAME.replace("@", "")
        markup.add(InlineKeyboardButton("📢 Join Official Channel", url=f"https://t.me/{clean_channel}"))
        markup.add(InlineKeyboardButton("✅ I have Joined", callback_data="check_join"))
        bot.send_message(
            message.chat.id,
            "👋 <b>Welcome to GodMode SMS!</b>\n\nPlease join our official channel first to unlock the bot.",
            reply_markup=markup,
            parse_mode="HTML"
        )
        return

    first_name = html.escape(message.from_user.first_name or "User")
    welcome_text = (
        f"Hello <b>{first_name}</b>! 👋\n\n"
        "Welcome to <b>GodMode SMS</b> — The Best & Fastest OTP Panel. 🚀\n"
        f"💰 <b>Your Balance:</b> ₹{users_db[user_id]['balance']}\n\n"
        "Please select an option from below:"
    )
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=get_main_menu(user_id),
        parse_mode="HTML"
    )

@bot.message_handler(commands=['addbal'])
def add_balance_cmd(message):
    if message.from_user.id not in OWNER_IDS:
        return
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        amount = float(parts[2])
        ensure_user(target_id)
        users_db[target_id]["balance"] = round(users_db[target_id]["balance"] + amount, 2)
        bot.reply_to(
            message,
            f"✅ <b>Balance Added!</b>\n👤 User ID: <code>{target_id}</code>\n💰 Added: ₹{amount}\n💳 New Balance: ₹{users_db[target_id]['balance']}",
            parse_mode="HTML"
        )
        try:
            bot.send_message(
                target_id,
                f"🎉 <b>Wallet Credited!</b>\n\n₹{amount} has been added to your wallet by Admin.\n💰 <b>New Balance:</b> ₹{users_db[target_id]['balance']}",
                parse_mode="HTML"
            )
        except Exception:
            pass
    except Exception:
        bot.reply_to(message, "⚠️ <b>Format:</b> <code>/addbal USER_ID AMOUNT</code>\nExample: <code>/addbal 8226471885 100</code>", parse_mode="HTML")

@bot.message_handler(commands=['cutbal'])
def cut_balance_cmd(message):
    if message.from_user.id not in OWNER_IDS:
        return
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        amount = float(parts[2])
        ensure_user(target_id)
        users_db[target_id]["balance"] = max(0.0, round(users_db[target_id]["balance"] - amount, 2))
        bot.reply_to(
            message,
            f"✅ <b>Balance Deducted!</b>\n👤 User ID: <code>{target_id}</code>\n💳 New Balance: ₹{users_db[target_id]['balance']}",
            parse_mode="HTML"
        )
    except Exception:
        bot.reply_to(message, "⚠️ <b>Format:</b> <code>/cutbal USER_ID AMOUNT</code>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    ensure_user(user_id)

    if call.data == "check_join":
        if check_membership(user_id):
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            send_welcome(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined @GodMode_SMS yet!", show_alert=True)

    elif call.data == "wallet":
        balance = users_db[user_id]["balance"]
        text = (
            f"💳 <b>Your GodMode Wallet</b>\n\n"
            f"👤 <b>Your User ID:</b> <code>{user_id}</code>\n"
            f"💰 <b>Available Balance:</b> ₹{balance}\n\n"
            f"<i>To add funds, send your User ID to Support below.</i>"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📞 Contact Support to Deposit", callback_data="support"))
        markup.add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data == "support":
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("👨‍💻 Main Owner", url="tg://user?id=8226471885"))
        markup.add(InlineKeyboardButton("👨‍💻 Co-Owner", url="tg://user?id=8692723368"))
        markup.add(InlineKeyboardButton("📢 Official Channel", url="https://t.me/GodMode_SMS"))
        markup.add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_home"))
        bot.edit_message_text(
            f"📞 <b>Support & Deposit Team</b>\n\n👤 <b>Your ID:</b> <code>{user_id}</code>\nNeed help or want to add balance? Contact the owners below:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )

    elif call.data == "admin_panel":
        if user_id not in OWNER_IDS:
            bot.answer_callback_query(call.id, "❌ Access Denied!", show_alert=True)
            return
        bot.answer_callback_query(call.id, "Fetching Live API Balance... 🔄")
        api_bal = get_api_balance()
        text = (
            "👑 <b>Owner Admin Panel</b>\n\n"
            f"🔌 <b>Connected API:</b> PremiumOTP.pro\n"
            f"💰 <b>Master API Balance:</b> <code>₹{html.escape(str(api_bal))}</code>\n"
            f"📈 <b>Profit Margin Set:</b> <code>+70% Auto</code>\n"
            f"👥 <b>Total Active Users:</b> <code>{len(users_db)}</code>\n\n"
            "🛠 <b>Owner Commands:</b>\n"
            "• Add Balance: <code>/addbal USER_ID AMOUNT</code>\n"
            "• Cut Balance: <code>/cutbal USER_ID AMOUNT</code>"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔄 Refresh API Balance", callback_data="admin_panel"))
        markup.add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_home"))
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            pass

    elif call.data.startswith("services_"):
        server_name = call.data.replace("services_", "")
        bot.answer_callback_query(call.id, f"Fetching live {server_name.upper()} prices... 🔄")
        
        services_list, error_msg = fetch_services(server_name)
        
        if services_list is not None:
            server_title = "Server 1 (Fastest ⚡)" if server_name == "server1" else "Server 2 (Premium ⭐)"
            text = f"🛒 <b>Live Services — {server_title}</b>\n\n"
            
            if len(services_list) == 0:
                text += "<i>No services currently listed on this server. Try switching servers below.</i>\n"
            else:
                count = 0
                for item in services_list:
                    if count >= 100:
                        break
                    s_name = html.escape(str(item.get("service_name", "Service")))
                    s_code = html.escape(str(item.get("service_code", "")).lower())
                    base_price = item.get("price", 0)
                    
                    icon, flag = get_icon_and_flag(s_name, s_code)
                    
                    try:
                        final_price = round(float(base_price) * PROFIT_MULTIPLIER, 2)
                    except (ValueError, TypeError):
                        final_price = base_price
                    
                    text += f"{icon} {flag} <b>{s_name}</b> (<code>{s_code}</code>) — ₹{final_price}\n"
                    count += 1
                    
                    if len(text) > 3600:
                        break
                        
            text += "\n⚡ <i>All prices include instant delivery & auto-refund guarantee.</i>"
        else:
            text = (
                "❌ <b>Server Busy / API Error</b>\n\n"
                f"Reason: <code>{html.escape(str(error_msg))}</code>"
            )
            
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("⚡ Server 1 List", callback_data="services_server1"),
            InlineKeyboardButton("⭐ Server 2 List", callback_data="services_server2")
        )
        markup.add(InlineKeyboardButton("📲 Buy OTP Number Now", callback_data=f"buymenu_{server_name}_0"))
        markup.add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_home"))
        
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            pass

    elif call.data.startswith("buymenu_"):
        parts = call.data.split("_")
        server_name = parts[1]
        page = int(parts[2])
        
        bot.answer_callback_query(call.id, "Loading services... 🔄")
        services_list = services_cache.get(server_name)
        if not services_list:
            services_list, error_msg = fetch_services(server_name)
            
        markup = InlineKeyboardMarkup(row_width=2)
        if not services_list:
            text = "❌ <b>Could not load services right now.</b> Please try again."
            markup.add(InlineKeyboardButton("🔙 Back", callback_data="back_home"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            return

        per_page = 10
        start_idx = page * per_page
        end_idx = start_idx + per_page
        current_slice = services_list[start_idx:end_idx]

        buttons = []
        for item in current_slice:
            s_name = str(item.get("service_name", "Service"))
            s_code = str(item.get("service_code", "")).lower()
            base_price = item.get("price", 0)
            icon, flag = get_icon_and_flag(s_name, s_code)
            try:
                final_price = round(float(base_price) * PROFIT_MULTIPLIER, 2)
            except Exception:
                final_price = base_price
            
            btn_text = f"{icon}{flag} {s_name[:12]} ₹{final_price}"
            buttons.append(InlineKeyboardButton(btn_text, callback_data=f"buy_{server_name}_{s_code}_{final_price}"))
        
        markup.add(*buttons)

        nav_btns = []
        if page > 0:
            nav_btns.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"buymenu_{server_name}_{page-1}"))
        if end_idx < len(services_list):
            nav_btns.append(InlineKeyboardButton("Next ➡️", callback_data=f"buymenu_{server_name}_{page+1}"))
        if nav_btns:
            markup.row(*nav_btns)

        markup.row(
            InlineKeyboardButton("⚡ Server 1", callback_data="buymenu_server1_0"),
            InlineKeyboardButton("⭐ Server 2", callback_data="buymenu_server2_0")
        )
        markup.add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_home"))

        server_label = "Server 1 (Fastest)" if server_name == "server1" else "Server 2 (Premium)"
        text = (
            f"📲 <b>Select a Service to Buy OTP</b>\n"
            f"🖥 <b>Active Server:</b> {server_label}\n"
            f"💳 <b>Your Wallet:</b> ₹{users_db[user_id]['balance']}\n\n"
            f"<i>Tap on any service button below to instantly generate a number:</i>"
        )
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            pass

    elif call.data.startswith("buy_"):
        parts = call.data.split("_")
        server_name = parts[1]
        s_code = parts[2]
        price = float(parts[3])

        if users_db[user_id]["balance"] < price:
            bot.answer_callback_query(
                call.id,
                f"❌ Insufficient Balance! You need ₹{price}, but your wallet has ₹{users_db[user_id]['balance']}.",
                show_alert=True
            )
            return

        bot.answer_callback_query(call.id, "Buying number from server... 🔄")
        srv_num = "1" if server_name == "server1" else "2"
        url = f"{STARK_URL}?api_key={PREMIUMOTP_API_KEY}&action=getNumber&service={s_code}&server={srv_num}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            resp_text = res.text.strip()
        except Exception as e:
            resp_text = f"ERROR:{e}"

        if "ACCESS_NUMBER:" in resp_text:
            _, order_id, phone_num = resp_text.split(":", 2)
            users_db[user_id]["balance"] = round(users_db[user_id]["balance"] - price, 2)
            active_orders[order_id] = {
                "user_id": user_id,
                "price": price,
                "service": s_code.upper(),
                "phone": phone_num,
                "refunded": False
            }
            
            text = (
                f"✅ <b>Number Purchased Successfully!</b>\n\n"
                f"📱 <b>Number:</b> <code>{html.escape(phone_num)}</code>\n"
                f"🛒 <b>Service:</b> {html.escape(s_code.upper())}\n"
                f"🆔 <b>Order ID:</b> <code>{html.escape(order_id)}</code>\n"
                f"💰 <b>Deducted:</b> ₹{price} | <b>Left:</b> ₹{users_db[user_id]['balance']}\n\n"
                f"⏳ <b>Status:</b> Waiting for OTP SMS...\n"
                f"<i>Send the OTP to this number and click Check OTP below.</i>"
            )
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("🔄 Check OTP", callback_data=f"checkotp_{order_id}"),
                InlineKeyboardButton("❌ Cancel & Refund", callback_data=f"cancelotp_{order_id}")
            )
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        else:
            bot.answer_callback_query(
                call.id,
                f"❌ Stock Out / Server Response: {resp_text[:120]}",
                show_alert=True
            )

    elif call.data.startswith("checkotp_"):
        order_id = call.data.replace("checkotp_", "")
        order = active_orders.get(order_id)
        if not order:
            bot.answer_callback_query(call.id, "❌ Order not found or expired!", show_alert=True)
            return

        bot.answer_callback_query(call.id, "Checking SMS status... 🔄")
        url = f"{STARK_URL}?api_key={PREMIUMOTP_API_KEY}&action=getStatus&id={order_id}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=12)
            resp_text = res.text.strip()
        except Exception as e:
            resp_text = f"ERROR:{e}"

        if "STATUS_OK:" in resp_text:
            otp_code = resp_text.split(":", 1)[1]
            try:
                requests.get(f"{STARK_URL}?api_key={PREMIUMOTP_API_KEY}&action=setStatus&status=6&id={order_id}", headers=HEADERS, timeout=5)
            except Exception:
                pass
            text = (
                f"🎉 <b>OTP Received Successfully!</b>\n\n"
                f"📱 <b>Number:</b> <code>{html.escape(order['phone'])}</code>\n"
                f"🔑 <b>OTP Code:</b> <code>{html.escape(otp_code)}</code>\n"
                f"🆔 <b>Order ID:</b> <code>{html.escape(order_id)}</code>\n\n"
                f"✅ <i>Thank you for using GodMode SMS!</i>"
            )
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📲 Buy Another Number", callback_data="buymenu_server1_0"))
            markup.add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_home"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        elif "STATUS_WAIT_CODE" in resp_text:
            bot.answer_callback_query(call.id, "⏳ Still waiting for SMS... Try again in 5 seconds!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, f"ℹ️ Status: {resp_text[:100]}", show_alert=True)

    elif call.data.startswith("cancelotp_"):
        order_id = call.data.replace("cancelotp_", "")
        order = active_orders.get(order_id)
        if not order or order.get("refunded"):
            bot.answer_callback_query(call.id, "❌ Order already cancelled or completed!", show_alert=True)
            return

        url = f"{STARK_URL}?api_key={PREMIUMOTP_API_KEY}&action=setStatus&status=8&id={order_id}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=12)
            resp_text = res.text.strip()
        except Exception as e:
            resp_text = f"ERROR:{e}"

        if "ACCESS_CANCEL" in resp_text or "CANCEL" in resp_text.upper():
            order["refunded"] = True
            users_db[user_id]["balance"] = round(users_db[user_id]["balance"] + order["price"], 2)
            text = (
                f"❌ <b>Number Cancelled & Refunded!</b>\n\n"
                f"📱 <b>Number:</b> <code>{html.escape(order['phone'])}</code>\n"
                f"💰 <b>Refunded:</b> ₹{order['price']}\n"
                f"💳 <b>Current Wallet Balance:</b> ₹{users_db[user_id]['balance']}"
            )
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📲 Buy Another Number", callback_data="buymenu_server1_0"))
            markup.add(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_home"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, f"⚠️ Cannot cancel yet: {resp_text[:100]}", show_alert=True)

    elif call.data == "back_home":
        first_name = html.escape(call.from_user.first_name or "User")
        welcome_text = (
            f"Hello <b>{first_name}</b>! 👋\n\n"
            "Welcome to <b>GodMode SMS</b> — The Best & Fastest OTP Panel. 🚀\n"
            f"💰 <b>Your Balance:</b> ₹{users_db[user_id]['balance']}\n\n"
            "Please select an option from below:"
        )
        try:
            bot.edit_message_text(
                welcome_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_main_menu(user_id),
                parse_mode="HTML"
            )
        except Exception:
            pass

# ================= 3. CRASH PROOF BOT RUNNER =================
def start_bot():
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception as e:
        print(f"Webhook clear info: {e}")

    while True:
        try:
            print("GodMode SMS Bot polling started... 🚀")
            bot.infinity_polling(timeout=60, long_polling_timeout=30, skip_pending=True)
        except Exception as e:
            print(f"Bot error: {e}. Restarting in 5 seconds... 🔄")
            time.sleep(5)

if __name__ == "__main__":
    print("Starting Flask Web Server...")
    keep_alive()
    print("Starting Main Bot...")
    start_bot()
