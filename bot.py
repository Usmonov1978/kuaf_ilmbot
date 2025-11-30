import os
import telebot
from telebot import types

# 🔹 Token va Admin ID-ni environment o'zgaruvchilaridan olamiz
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

if TOKEN is None:
    raise RuntimeError("❗ BOT_TOKEN environment o'zgaruvchisi topilmadi! Render yoki tizimda BOT_TOKEN qo‘shilganligini tekshiring.")

if ADMIN_ID is None:
    raise RuntimeError("❗ ADMIN_ID environment o'zgaruvchisi topilmadi! Render yoki tizimda ADMIN_ID qo‘shilganligini tekshiring.")

ADMIN_ID = int(ADMIN_ID)

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# foydalanuvchi holatini saqlash
user_state = {}
questions = {}
next_q_id = 1


# /start buyrug'i
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_question = types.KeyboardButton("❓ SAVOL YUBORISH")
    markup.add(btn_question)

    bot.send_message(
        message.chat.id,
        "Ассалому алайкум! 😊\n"
        "@KUAF_Ilmbot орқали саволингизни админга бера оласиз.\n"
        "Тугмани босинг:",
        reply_markup=markup
    )


# SAVOL tugmasi
@bot.message_handler(func=lambda m: m.text == "❓ SAVOL YUBORISH")
def ask_question_button(message):
    user_id = message.from_user.id
    user_state[user_id] = "waiting_question"

    bot.send_message(
        message.chat.id,
        "Savolingizni yozib yuboring 👇"
    )


# foydalanuvchi savol yozganda
@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "waiting_question")
def save_question(message):
    global next_q_id

    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    text = message.text

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
        f"✅ Savolingiz qabul qilindi.\nSavol ID: <b>{q_id}</b>"
    )

    admin_text = (
        f"🆕 <b>Yangi savol:</b>\n"
        f"ID: <b>{q_id}</b>\n"
        f"Foydalanuvchi: <b>{username}</b>\n"
        f"UserID: <code>{user_id}</code>\n\n"
        f"Matn:\n{text}\n\n"
        f"Javob berish:\n"
        f"/javob {q_id} Javob matni"
    )
    bot.send_message(ADMIN_ID, admin_text)


# admin savollar ro'yxatini ko'radi
@bot.message_handler(commands=['savollar'])
def list_questions(message):
    if message.from_user.id != ADMIN_ID:
        return

    if not questions:
        bot.send_message(message.chat.id, "Savollar yo‘q 😊")
        return

    msg = "📋 <b>Ochiq savollar:</b>\n"
    for q_id, data in questions.items():
        msg += f"\nID: <b>{q_id}</b>\n{data['username']}:\n{data['text']}\n"

    bot.send_message(message.chat.id, msg)


# admin javob qaytaradi
@bot.message_handler(commands=['javob'])
def answer_question(message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.send_message(
            message.chat.id,
            "❗ Format noto‘g‘ri.\nMisol:\n/javob 1 Bu savolga javob"
        )
        return

    try:
        q_id = int(parts[1])
    except:
        bot.send_message(message.chat.id, "❗ ID son bo‘lishi kerak.")
        return

    if q_id not in questions:
        bot.send_message(message.chat.id, f"❗ ID {q_id} bo‘yicha savol topilmadi.")
        return

    answer_text = parts[2]
    user_id = questions[q_id]['user_id']
    question_text = questions[q_id]['text']

    bot.send_message(
        user_id,
        f"📩 Savolingizga javob:\n\n❓ {question_text}\n\n💡 <b>{answer_text}</b>"
    )

    bot.send_message(
        message.chat.id,
        f"✅ Javob yuborildi (ID: {q_id})"
    )

    del questions[q_id]


# noma’lum matnlar
@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(
        message.chat.id,
        "Savol berish uchun '❓ SAVOL YUBORISH' tugmasidan foydalaning yoki /start yuboring."
    )


print("KUAF_Ilmbot ishga tushdi...")
bot.infinity_polling()
