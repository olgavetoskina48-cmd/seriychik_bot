import telebot
import sqlite3
import threading
import time
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = "8310099970:AAGpML1jCzhMpSL4U_GeFkUltJDs1hv_F6s"
bot = telebot.TeleBot(TOKEN)

ADMINS = []

# --- ПРОСТОЙ HTTP-СЕРВЕР ДЛЯ RENDER ---
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running!')

def run_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('pets.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            user_id INTEGER PRIMARY KEY,
            голод INTEGER DEFAULT 50,
            счастье INTEGER DEFAULT 50,
            гигиена INTEGER DEFAULT 50,
            энергия INTEGER DEFAULT 50,
            дисциплина INTEGER DEFAULT 50,
            дни INTEGER DEFAULT 0,
            одежда TEXT DEFAULT 'без одежды',
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            total_messages INTEGER DEFAULT 0,
            stage TEXT DEFAULT 'яйцо',
            pet_type TEXT DEFAULT 'кошка'
        )
    ''')
    conn.commit()
    return conn

db = init_db()

def get_pet(user_id):
    cursor = db.cursor()
    cursor.execute('SELECT * FROM pets WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        return {
            'голод': row[1],
            'счастье': row[2],
            'гигиена': row[3],
            'энергия': row[4],
            'дисциплина': row[5],
            'дни': row[6],
            'одежда': row[7],
            'xp': row[8],
            'level': row[9],
            'total_messages': row[10],
            'stage': row[11],
            'pet_type': row[12]
        }
    return None

def create_pet(user_id, pet_type):
    cursor = db.cursor()
    cursor.execute('INSERT INTO pets (user_id, pet_type) VALUES (?, ?)', (user_id, pet_type))
    db.commit()

def update_pet(user_id, field, value):
    cursor = db.cursor()
    cursor.execute(f'UPDATE pets SET {field} = ? WHERE user_id = ?', (value, user_id))
    db.commit()

def add_xp(user_id, amount):
    cursor = db.cursor()
    cursor.execute('SELECT xp, level FROM pets WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        return
    xp, level = row
    xp += amount
    xp_needed = level * 50
    while xp >= xp_needed:
        xp -= xp_needed
        level += 1
        xp_needed = level * 50
        bot.send_message(user_id, f'🎉 Поздравляю! Твой Серийчик достиг {level} уровня!')
    cursor.execute('UPDATE pets SET xp = ?, level = ? WHERE user_id = ?', (xp, level, user_id))
    db.commit()

def get_stage(total_messages):
    if total_messages < 50:
        return "ещё не вылупилось 🌱"
    elif total_messages <= 100:
        return "яйцо 🥚"
    elif total_messages <= 500:
        return "малыш 🐣"
    elif total_messages <= 1000:
        return "подросток 🧒"
    else:
        return "взрослый 🧑"

def check_stage_upgrade(user_id, pet):
    old_stage = pet['stage']
    new_stage = get_stage(pet['total_messages'])
    if new_stage != old_stage:
        update_pet(user_id, 'stage', new_stage)
        if new_stage != "ещё не вылупилось 🌱":
            bot.send_message(user_id, f"🌟 Твой Серийчик вырос! Теперь он {new_stage}!")

def get_state(pet):
    if pet['голод'] < 20:
        return "голодный 🍂"
    if pet['гигиена'] < 20:
        return "грязный 💧"
    if pet['энергия'] < 20:
        return "уставший 😴"
    if pet['счастье'] < 20:
        return "грустный 🌧️"
    if pet['голод'] > 80 and pet['счастье'] > 80 and pet['гигиена'] > 80 and pet['энергия'] > 80:
        return "счастливый 🌟"
    return "спокойный 🙂"

pet_emojis = {
    "кошка": "🐱",
    "лиса": "🦊",
    "собака": "🐶",
    "енот": "🦝",
    "хомяк": "🐹"
}

# --- КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🐾 Привет! Это Серийчик.\n/newpet — завести питомца\n/feed, /play, /wash, /sleep, /train — ухаживать\n/status — состояние\n/dress — переодеть")

@bot.message_handler(commands=['newpet'])
def new_pet(message):
    user_id = message.from_user.id
    if get_pet(user_id):
        bot.send_message(message.chat.id, "У тебя уже есть питомец!")
        return
    bot.send_message(message.chat.id, "🥚 Напиши тип питомца: кошка, лиса, собака, енот, хомяк")
    bot.register_next_step_handler(message, set_pet_type)

def set_pet_type(message):
    user_id = message.from_user.id
    pet_type = message.text.lower()
    if pet_type not in pet_emojis:
        bot.send_message(message.chat.id, "❌ Неверный тип. Напиши: кошка, лиса, собака, енот, хомяк")
        bot.register_next_step_handler(message, set_pet_type)
        return
    create_pet(user_id, pet_type)
    bot.send_message(message.chat.id, f"✅ Ты выбрал {pet_emojis[pet_type]} {pet_type.capitalize()}! Пиши сообщения, чтобы он рос.")

@bot.message_handler(commands=['feed'])
def feed(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала /newpet")
        return
    update_pet(user_id, 'голод', min(100, pet['голод'] + 20))
    bot.send_message(message.chat.id, "🍖 Покормлен! Голод +20")

@bot.message_handler(commands=['play'])
def play(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала /newpet")
        return
    update_pet(user_id, 'счастье', min(100, pet['счастье'] + 15))
    update_pet(user_id, 'энергия', max(0, pet['энергия'] - 10))
    bot.send_message(message.chat.id, "🎾 Поиграл! Счастье +15, Энергия -10")

@bot.message_handler(commands=['wash'])
def wash(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала /newpet")
        return
    update_pet(user_id, 'гигиена', min(100, pet['гигиена'] + 25))
    bot.send_message(message.chat.id, "🧼 Помыт! Гигиена +25")

@bot.message_handler(commands=['sleep'])
def sleep(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала /newpet")
        return
    update_pet(user_id, 'энергия', min(100, pet['энергия'] + 30))
    bot.send_message(message.chat.id, "😴 Поспал! Энергия +30")

@bot.message_handler(commands=['train'])
def train(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала /newpet")
        return
    update_pet(user_id, 'дисциплина', min(100, pet['дисциплина'] + 15))
    bot.send_message(message.chat.id, "🏋️ Тренировка! Дисциплина +15")

@bot.message_handler(commands=['status'])
def status(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Нет питомца. /newpet")
        return
    state = get_state(pet)
    xp_needed = pet['level'] * 50
    emoji = pet_emojis.get(pet['pet_type'], '🐾')
    text = f"📊 {emoji} Серийчик ({state})\n{pet['stage']}\n\n🍖 Голод: {pet['голод']}\n😊 Счастье: {pet['счастье']}\n🧼 Гигиена: {pet['гигиена']}\n⚡ Энергия: {pet['энергия']}\n📏 Дисциплина: {pet['дисциплина']}\n📅 Дней: {pet['дни']}\n👕 Одежда: {pet['одежда']}\n⭐ Уровень: {pet['level']}\n📈 XP: {pet['xp']}/{xp_needed}\n💬 Сообщений: {pet['total_messages']}"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['dress'])
def dress(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала /newpet")
        return
    options = ["без одежды", "шапка 🧢", "шарф 🧣", "очки 🕶️", "плащ 🧥"]
    current = pet['одежда']
    idx = options.index(current) if current in options else 0
    new_idx = (idx + 1) % len(options)
    update_pet(user_id, 'одежда', options[new_idx])
    bot.send_message(message.chat.id, f"Теперь на питомце: {options[new_idx]}")

# --- XP И СООБЩЕНИЯ ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    if message.text and message.text.startswith('/'):
        return
    pet = get_pet(user_id)
    if not pet:
        return
    new_total = pet['total_messages'] + 1
    update_pet(user_id, 'total_messages', new_total)
    check_stage_upgrade(user_id, pet)
    xp_gain = 3 if user_id in ADMINS else 5
    add_xp(user_id, xp_gain)

# --- ДНИ ---
def update_days():
    while True:
        time.sleep(86400)
        cursor = db.cursor()
        cursor.execute('''
            UPDATE pets SET
                дни = дни + 1,
                голод = MAX(0, голод - 5),
                счастье = MAX(0, счастье - 3),
                гигиена = MAX(0, гигиена - 5),
                энергия = MAX(0, энергия - 4),
                дисциплина = MAX(0, дисциплина - 2)
        ''')
        db.commit()

thread = threading.Thread(target=update_days)
thread.daemon = True
thread.start()

# --- ЗАПУСК СЕРВЕРА И БОТА ---
threading.Thread(target=run_server).start()
print("✅ Бот с портом запущен!")
bot.polling()
