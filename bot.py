import telebot
import sqlite3
import threading
import time

TOKEN = "8961168833:AAHX1WQPNPFyaeHjmBY3HY2imTT5ifOGKeE"  # ВСТАВЬ СВОЙ ТОКЕН
bot = telebot.TeleBot(TOKEN)

# Список админов (Telegram ID)
ADMINS = []  # Добавь сюда ID админов, например [123456789, 987654321]

# --- БАЗА ДАННЫХ (SQLite) ---
def init_db():
    conn = sqlite3.connect('pets.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            user_id INTEGER PRIMARY KEY,
            голод INTEGER DEFAULT 50,
            счастье INTEGER DEFAULT 50,
            дни INTEGER DEFAULT 0,
            одежда TEXT DEFAULT 'без одежды',
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1
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
            'дни': row[3],
            'одежда': row[4],
            'xp': row[5],
            'level': row[6]
        }
    return None

def create_pet(user_id):
    cursor = db.cursor()
    cursor.execute('INSERT INTO pets (user_id) VALUES (?)', (user_id,))
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

# --- КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я бот с питомцами 🐾\nКоманды: /newpet, /feed, /play, /status, /dress")

@bot.message_handler(commands=['newpet'])
def new_pet(message):
    user_id = message.from_user.id
    if get_pet(user_id):
        bot.send_message(message.chat.id, "У тебя уже есть питомец!")
        return
    create_pet(user_id)
    bot.send_message(message.chat.id, "Ты завёл питомца! 🎉\n/feed - покормить\n/play - поиграть\n/status - состояние\n/dress - переодеть")

@bot.message_handler(commands=['feed'])
def feed(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала заведи питомца командой /newpet")
        return
    new_val = min(100, pet['голод'] + 20)
    update_pet(user_id, 'голод', new_val)
    bot.send_message(message.chat.id, f"🍖 Покормлен! Голод +20")

@bot.message_handler(commands=['play'])
def play(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала заведи питомца командой /newpet")
        return
    new_val = min(100, pet['счастье'] + 15)
    update_pet(user_id, 'счастье', new_val)
    bot.send_message(message.chat.id, f"🎾 Поиграл! Счастье +15")

@bot.message_handler(commands=['status'])
def status(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Нет питомца. Заведи через /newpet")
        return
    xp_needed = pet['level'] * 50
    text = f"📊 Серийчик:\n🍖 Голод: {pet['голод']}\n😊 Счастье: {pet['счастье']}\n📅 Дней: {pet['дни']}\n👕 Одежда: {pet['одежда']}\n⭐ Уровень: {pet['level']}\n📈 XP: {pet['xp']}/{xp_needed}"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['dress'])
def dress(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала заведи питомца командой /newpet")
        return
    options = ["без одежды", "шапка 🧢", "шарф 🧣", "очки 🕶️"]
    current = pet['одежда']
    idx = options.index(current) if current in options else 0
    new_idx = (idx + 1) % len(options)
    update_pet(user_id, 'одежда', options[new_idx])
    bot.send_message(message.chat.id, f"Теперь на питомце: {options[new_idx]}")

# --- ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ (XP за общение) ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    # Игнорируем команды
    if message.text and message.text.startswith('/'):
        return
    pet = get_pet(user_id)
    if not pet:
        return
    # Начисляем XP
    if user_id in ADMINS:
        add_xp(user_id, 3)
    else:
        add_xp(user_id, 5)

# --- ФОНОВЫЙ СЧЁТЧИК ДНЕЙ ---
def update_days():
    while True:
        time.sleep(86400)
        cursor = db.cursor()
        cursor.execute('UPDATE pets SET дни = дни + 1')
        db.commit()

thread = threading.Thread(target=update_days)
thread.daemon = True
thread.start()

print("✅ Бот запущен с SQLite и уровнями!")
bot.polling()
