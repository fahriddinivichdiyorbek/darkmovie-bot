import telebot
from telebot import types
import json
import os

TOKEN = "8888356925:AAGLC6sMRGVB4WyVxx_vLqYLMBLk7H77c-c"
ADMIN_ID = 8125292730

CHANNEL = "@darkmovieuz1"
GROUP = "@darkmoviechat"

bot = telebot.TeleBot(TOKEN)

# Holatlar uchun lug'atlar
ADD_MOVIE = {}
DELETE_MOVIE = {}
BROADCAST = {}

# Fayllarni tekshirish
if not os.path.exists("movies.json"):
    with open("movies.json", "w", encoding="utf-8") as f: json.dump({}, f)
if not os.path.exists("users.json"):
    with open("users.json", "w", encoding="utf-8") as f: json.dump([], f)

def load_movies():
    with open("movies.json", "r", encoding="utf-8") as f: return json.load(f)

def save_movies(data):
    with open("movies.json", "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

def load_users():
    with open("users.json", "r", encoding="utf-8") as f: return json.load(f)

def save_users(data):
    with open("users.json", "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

def check_sub(user_id):
    try:
        ch = bot.get_chat_member(CHANNEL, user_id).status
        gr = bot.get_chat_member(GROUP, user_id).status
        return ch in ["member", "administrator", "creator"] and gr in ["member", "administrator", "creator"]
    except:
        return False

# --- ASOSIY MENYU ---
@bot.message_handler(commands=["start"])
def start(message):
    users = load_users()
    if message.from_user.id not in users:
        users.append(message.from_user.id)
        save_users(users)

    if check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "🎬 Assalomu alaykum! Kino kodini yuboring.")
    else:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📢 Kanal", url="https://t.me/darkmovieuz1"))
        kb.add(types.InlineKeyboardButton("💬 Guruh", url="https://t.me/darkmoviechat"))
        kb.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check"))
        bot.send_message(message.chat.id, "❗️Botdan foydalanish uchun obuna bo'ling.", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check(call):
    if check_sub(call.from_user.id):
        bot.edit_message_text("✅ Obuna tasdiqlandi! Kino kodini yuboring.", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmagansiz!", show_alert=True)

# --- ADMIN PANEL ---
@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎥 Kino qo'shish", "🗑 Kino o'chirish", "📊 Statistika", "📢 Broadcast")
    bot.send_message(message.chat.id, "⚙️ Admin panel", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📊 Statistika" and m.from_user.id == ADMIN_ID)
def stat(message):
    bot.send_message(message.chat.id, f"👥 Foydalanuvchilar: {len(load_users())}\n🎬 Kinolar: {len(load_movies())}")

# --- BROADCAST (MUKAMMAL) ---
@bot.message_handler(func=lambda m: m.text == "📢 Broadcast" and m.from_user.id == ADMIN_ID)
def broadcast_step1(message):
    BROADCAST[message.from_user.id] = True
    bot.send_message(message.chat.id, "📢 Hammaga yubormoqchi bo'lgan xabarni (rasm/video/text) yuboring.")

@bot.message_handler(func=lambda m: m.from_user.id in BROADCAST, content_types=['text', 'video', 'photo'])
def broadcast_send(message):
    users = load_users()
    count = 0
    for user in users:
        try:
            if message.content_type == 'text': bot.send_message(user, message.text)
            elif message.content_type == 'video': bot.send_video(user, message.video.file_id, caption=message.caption)
            elif message.content_type == 'photo': bot.send_photo(user, message.photo[-1].file_id, caption=message.caption)
            count += 1
        except: pass
    del BROADCAST[message.from_user.id]
    bot.send_message(message.chat.id, f"✅ Xabar {count} ta foydalanuvchiga yetkazildi.")

# --- KINO QO'SHISH VA O'CHIRISH ---
@bot.message_handler(func=lambda m: m.text == "🎥 Kino qo'shish" and m.from_user.id == ADMIN_ID)
def add_movie_start(message):
    ADD_MOVIE[message.from_user.id] = {"step": "video"}
    bot.send_message(message.chat.id, "🎥 Videoni yuboring.")

@bot.message_handler(content_types=["video"], func=lambda m: m.from_user.id in ADD_MOVIE)
def get_video(message):
    ADD_MOVIE[message.from_user.id] = {"step": "code", "file_id": message.video.file_id}
    bot.send_message(message.chat.id, "✅ Video qabul qilindi. Kodni kiriting.")

@bot.message_handler(func=lambda m: m.from_user.id in ADD_MOVIE and m.from_user.id == ADMIN_ID)
def save_movie(message):
    if ADD_MOVIE[message.from_user.id]["step"] == "code":
        code = message.text.strip()
        movies = load_movies()
        movies[code] = {"file_id": ADD_MOVIE[message.from_user.id]["file_id"]}
        save_movies(movies)
        del ADD_MOVIE[message.from_user.id]
        bot.send_message(message.chat.id, f"✅ Kino {code} kodi bilan saqlandi.")

@bot.message_handler(func=lambda m: m.text == "🗑 Kino o'chirish" and m.from_user.id == ADMIN_ID)
def del_movie_start(message):
    DELETE_MOVIE[message.from_user.id] = True
    bot.send_message(message.chat.id, "🗑 O'chirmoqchi bo'lgan kodni yuboring.")

@bot.message_handler(func=lambda m: m.from_user.id in DELETE_MOVIE and m.from_user.id == ADMIN_ID)
def delete_movie(message):
    movies = load_movies()
    if message.text in movies:
        del movies[message.text]
        save_movies(movies)
        bot.send_message(message.chat.id, "✅ O'chirildi.")
    else: bot.send_message(message.chat.id, "❌ Kod topilmadi.")
    del DELETE_MOVIE[message.from_user.id]

# --- KINO QIDIRISH ---
@bot.message_handler(func=lambda m: m.text.isdigit())
def send_movie(message):
    if not check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Avval obuna bo'ling.")
        return
    movies = load_movies()
    if message.text in movies:
        bot.send_video(message.chat.id, movies[message.text]["file_id"])
    else:
        bot.send_message(message.chat.id, "❌ Bunday kino topilmadi.")

print("Bot muvaffaqiyatli ishga tushdi...")
bot.infinity_polling(skip_pending=True)
