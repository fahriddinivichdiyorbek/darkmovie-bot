import telebot
from telebot import types
import sqlite3
import os

# --- KONFIGURATSIYA ---
TOKEN = "8888356925:AAGLC6sMRGVB4WyVxx_vLqYLMBLk7H77c-c"
ADMIN_ID = 8125292730
CHANNEL = "@Darkmovieuz1"
GROUP = "@darkmoviechat"

bot = telebot.TeleBot(TOKEN)

# --- BAZA BILAN ISHLASH ---
if not os.path.exists("data"): os.makedirs("data")
conn = sqlite3.connect("data/bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS movies(code TEXT PRIMARY KEY, file_id TEXT, caption TEXT)")
conn.commit()

# --- HOLATLAR (STATES) ---
user_state = {}

# --- YORDAMCHI FUNKSIYALAR ---
def add_user(user_id):
    cur.execute("INSERT OR IGNORE INTO users VALUES(?)", (user_id,))
    conn.commit()

def check_sub(user_id):
    try:
        ch = bot.get_chat_member(CHANNEL, user_id).status
        gr = bot.get_chat_member(GROUP, user_id).status
        return ch in ["member", "administrator", "creator"] and gr in ["member", "administrator", "creator"]
    except: return False

# --- ASOSIY START ---
@bot.message_handler(commands=["start"])
def start(message):
    add_user(message.from_user.id)
    if not check_sub(message.from_user.id):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📢 Kanal", url=f"https://t.me/{CHANNEL.replace('@','')}"))
        kb.add(types.InlineKeyboardButton("💬 Guruh", url=f"https://t.me/{GROUP.replace('@','')}"))
        kb.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check"))
        bot.send_message(message.chat.id, "❗ Botdan foydalanish uchun obuna bo'ling!", reply_markup=kb)
        return
    bot.send_message(message.chat.id, "🎬 Kino kodini yuboring (Masalan: 1, 2, 3...):")

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check(call):
    if check_sub(call.from_user.id):
        bot.edit_message_text("✅ Tasdiqlandi! Kino kodini yuboring.", call.message.chat.id, call.message.message_id)
    else: bot.answer_callback_query(call.id, "❌ Obuna bo'lmagansiz!", show_alert=True)

# --- KINO QIDIRISH ---
@bot.message_handler(func=lambda m: m.text and m.text.isdigit())
def send_movie(message):
    if not check_sub(message.from_user.id): return
    cur.execute("SELECT file_id, caption FROM movies WHERE code=?", (message.text,))
    movie = cur.fetchone()
    if movie: 
        try: bot.send_video(message.chat.id, movie[0], caption=movie[1])
        except: bot.send_message(message.chat.id, "❌ Video yuborishda xatolik!")
    else: bot.send_message(message.chat.id, "❌ Bunday kodli kino topilmadi.")

# --- ADMIN PANEL ---
@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Kino qo'shish", "🗑 Kino o'chirish", "📊 Statistika", "📢 Reklama")
    bot.send_message(message.chat.id, "⚙️ Admin Paneliga xush kelibsiz!", reply_markup=kb)

# --- ADMIN: KINO QO'SHISH LOGIKASI ---
@bot.message_handler(func=lambda m: m.text == "➕ Kino qo'shish" and m.from_user.id == ADMIN_ID)
def add_movie_start(message):
    user_state[message.from_user.id] = {"step": "video"}
    bot.send_message(message.chat.id, "🎥 Kino faylini (video) yuboring:")

@bot.message_handler(content_types=["video"])
def get_video(message):
    if user_state.get(message.from_user.id, {}).get("step") == "video":
        user_state[message.from_user.id] = {"step": "code", "file_id": message.video.file_id}
        bot.send_message(message.chat.id, "🔢 Kino uchun kod yuboring (faqat raqam):")

@bot.message_handler(func=lambda m: m.from_user.id in user_state and user_state[m.from_user.id]["step"] == "code")
def get_code(message):
    if message.text.isdigit():
        user_state[message.from_user.id]["code"] = message.text
        user_state[message.from_user.id]["step"] = "caption"
        bot.send_message(message.chat.id, "📝 Kino nomini yozing:")
    else: bot.send_message(message.chat.id, "❌ Iltimos, raqam kiriting!")

@bot.message_handler(func=lambda m: m.from_user.id in user_state and user_state[m.from_user.id]["step"] == "caption")
def save_movie(message):
    data = user_state[message.from_user.id]
    cur.execute("INSERT OR REPLACE INTO movies VALUES(?,?,?)", (data["code"], data["file_id"], message.text))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ Kino saqlandi! Kod: {data['code']}")
    del user_state[message.from_user.id]

# --- ADMIN: STATISTIKA VA REKLAMA ---
@bot.message_handler(func=lambda m: m.text == "📊 Statistika" and m.from_user.id == ADMIN_ID)
def stats(message):
    cur.execute("SELECT COUNT(*) FROM users"); u = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM movies"); m = cur.fetchone()[0]
    bot.send_message(message.chat.id, f"👥 Foydalanuvchilar: {u}\n🎬 Jami kinolar: {m}")

@bot.message_handler(func=lambda m: m.text == "📢 Reklama" and m.from_user.id == ADMIN_ID)
def ask_reklama(message):
    msg = bot.send_message(message.chat.id, "📢 Reklama xabarini (rasm/matn) yuboring:")
    bot.register_next_step_handler(msg, send_reklama)

def send_reklama(message):
    cur.execute("SELECT id FROM users")
    users = cur.fetchall()
    for u in users:
        try: bot.copy_message(u[0], message.chat.id, message.message_id)
        except: continue
    bot.send_message(message.chat.id, "✅ Reklama barchaga yuborildi!")

# --- ADMIN: O'CHIRISH ---
@bot.message_handler(func=lambda m: m.text == "🗑 Kino o'chirish" and m.from_user.id == ADMIN_ID)
def ask_delete(message):
    msg = bot.send_message(message.chat.id, "❌ O'chirmoqchi bo'lgan kino kodini yuboring:")
    bot.register_next_step_handler(msg, lambda m: [cur.execute("DELETE FROM movies WHERE code=?", (m.text,)), conn.commit(), bot.send_message(m.chat.id, "🗑 O'chirildi!")])

bot.infinity_polling()
