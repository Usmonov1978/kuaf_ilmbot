import os
import threading
import telebot
from telebot import types

# 🔹 Token va Admin ID environment'dan olinadi
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

if TOKEN is None:
    raise RuntimeError("BOT_TOKEN environment o'zgaruvchisi topilmadi!")
if ADMIN_ID is None:
    raise RuntimeError("ADMIN_ID environment o'zgaruvchisi topilmadi!")

ADMIN_ID = int(ADMIN_ID)

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Foydalanuvchi holati va savollar
user_state = {}
questions = {}
next_q_id = 1


# /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_question = types.KeyboardButton("❓ SAVOL YUBORISH")
    markup.add(btn_question)

    bot.send_message(
        message.chat.id,
        "Assalomu alaykum! 😊\n"
        "Bu bot orqali admin'ga savol yuborishingiz mumkin.\n"
        "Savol yuborish uchun tugmani bosing:",
        reply_markup=markup
    )


# "❓ SAVOL YUBORISH" tugmasi
@bot.message_handler(func=lambda m: m.text == "❓ SAVOL YUBORISH")
def ask_question_button(message):
    user_id = message.from_user.id
    user_state[user_id] = "waiting_question"
    bot.send_message(message.chat.id, "Savolingizni matn ko‘rinishida yozib yuboring 👇")


# Foydalanuvchi savol yozganda
@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "waiting_question")
def save_question(message):
    global next_q_id

    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    text = message.text.strip()

    if not text:
        bot.send_message(message.chat.id, "Bo‘sh xabar yuborilmadi, iltimos savol yozing.")
        return

    q_id = next_q_id
    next_q_id += 1

    questions[q_id] = {
        "user_id": user_id,
        "username": username,
        "text": text
    }

    user_state.pop(user_id, None)

    bot.send_message(
        message.chat.id,
        f"✅ Savolingiz qabul qilindi!\n"
        f"Savol ID: <b>{q_id}</b>\n"
        "Admin tez orada javob yuboradi."
    )

    admin_text = (
        f"🆕 <b>Yangi savol keldi</b>\n\n"
        f"ID: <b>{q_id}</b>\n"
        f"Foydalanuvchi: <b>{username}</b> (ID: <code>{user_id}</code>)\n\n"
        f"Matn:\n{text}\n\n"
        f"Javob berish uchun misol:\n"
        f"/javob {q_id} Javob matni..."
    )
    bot.send_message(ADMIN_ID, admin_text)


# /savollar – faqat admin
@bot.message_handler(commands=['savollar'])
def list_questions(message):
    if message.from_user.id != ADMIN_ID:
        return

    if not questions:
        bot.reply_to(message, "Hozircha ochiq savollar yo‘q. 😊")
        return

    lines = ["📋 <b>Ochiq savollar ro'yxati:</b>"]
    for q_id, data in questions.items():
        lines.append(
            f"\nID: <b>{q_id}</b>\n"
            f"Foydalanuvchi: {data['username']}\n"
            f"Savol: {data['text']}"
        )
    bot.reply_to(message, "\n".join(lines))


# /javob – admin javob qaytaradi
@bot.message_handler(commands=['javob'])
def answer_question(message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(
            message,
            "Format noto‘g‘ri.\n"
            "To‘g‘ri ko‘rinish: <code>/javob 1 Bu savolga javob...</code>"
        )
        return

    try:
        q_id = int(parts[1])
    except ValueError:
        bot.reply_to(message, "Savol ID butun son bo‘lishi kerak. Masalan: /javob 1 Javob matni")
        return

    if q_id not in questions:
        bot.reply_to(message, f"ID {q_id} bo‘yicha savol topilmadi.")
        return

    answer_text = parts[2].strip()
    if not answer_text:
        bot.reply_to(message, "Javob matni bo‘sh bo‘lishi mumkin emas.")
        return

    data = questions[q_id]
    user_id = data["user_id"]

    user_msg = (
        "📩 <b>Sizning savolingizga admin javobi:</b>\n\n"
        f"❓ <b>Savol:</b> {data['text']}\n\n"
        f"✅ <b>Javob:</b> {answer_text}"
    )
    bot.send_message(user_id, user_msg)

    bot.reply_to(message, f"✅ Javob foydalanuvchiga yuborildi.\nSavol ID: {q_id}")

    del questions[q_id]


# Boshqa matnlar
@bot.message_handler(func=lambda m: True)
def fallback(message):
    if message.text != "❓ SAVOL YUBORISH":
        bot.send_message(
            message.chat.id,
            "Noma'lum buyruq.\nSavol yuborish uchun '❓ SAVOL YUBORISH' tugmasidan foydalaning yoki /start bosing."
        )


# 🔹 Botni alohida thread’da, HTTP serverni asosiy thread’da ishlatamiz
def run_bot():
    print("KUAF_Ilmbot polling boshlandi...")
    bot.infinity_polling(skip_pending=True)


def run_http_server():
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        def log_message(self, format, *args):
            # logni tiqib yubormaslik uchun
            return

    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"HTTP health server {port} portda ishga tushdi...")
    server.serve_forever()


if __name__ == "__main__":
    # Botni fon thread’da ishga tushiramiz
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()

    # Asosiy thread’da HTTP server turadi (Render portni ko‘rishi uchun)
    run_http_server()
