import os
import random
import threading
from telebot import TeleBot
from supabase import create_client
from flask import Flask

# --- FLASK ДЛЯ ПОРТА ---
flask_app = Flask(__name__)

@flask_app.route('/ping')
def ping():
    return "I'm alive!", 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port)

# --- SUPABASE ---
SUPABASE_URL = "https://jzscsndwuchzlellgqea.supabase.co"
SUPABASE_KEY = "sb_publishable_-kqOsr7gFZRi8ctCNPaLgg_4mjU-NZy"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TOKEN = "8961168833:AAEtlADb8Tyng1LmMbD7d_0Q7AeNkqny_W8"
bot = TeleBot(TOKEN)

# --- БАЗА ---
def get_pet(user_id):
    response = supabase.table('pets').select('*').eq('user_id', user_id).execute()
    if response.data:
        return response.data[0]
    return None

def update_pet(user_id, field, value):
    supabase.table('pets').update({field: value}).eq('user_id', user_id).execute()

def save_message(user_id, sender, message):
    supabase.table('chat_history').insert({
        'user_id': user_id,
        'sender': sender,
        'message': message
    }).execute()

# --- КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🐾 Привет! Это Серийчик.\n\n"
        "/newpet — завести питомца\n"
        "/status — состояние питомца\n"
        "/feed — покормить\n"
        "/play — поиграть\n"
        "/wash — помыть\n"
        "/sleep — поспать\n"
        "/train — тренировать\n"
        "/dress — переодеть\n"
        "/app — открыть мини-приложение\n"
        "/help — этот список"
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "📋 Команды:\n"
        "/newpet — завести питомца\n"
        "/status — состояние питомца\n"
        "/feed — покормить\n"
        "/play — поиграть\n"
        "/wash — помыть\n"
        "/sleep — поспать\n"
        "/train — тренировать\n"
        "/dress — переодеть\n"
        "/app — открыть мини-приложение\n"
        "/help — этот список"
    )

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
    pet_emojis = {"кошка": "🐱", "лиса": "🦊", "собака": "🐶", "енот": "🦝", "хомяк": "🐹"}
    if pet_type not in pet_emojis:
        bot.send_message(message.chat.id, "❌ Неверный тип. Напиши: кошка, лиса, собака, енот, хомяк")
        bot.register_next_step_handler(message, set_pet_type)
        return
    colors = ["красный", "синий", "зелёный", "жёлтый", "фиолетовый", "розовый", "оранжевый", "голубой"]
    times = ["утро", "день", "вечер", "ночь"]
    seasons = ["весна", "лето", "осень", "зима"]
    foods = ["рыбка", "сосиски", "мороженое", "печенье", "мясо"]
    toys = ["мячик", "косточка", "мышка", "верёвка", "подушка"]
    supabase.table('pets').insert({
        'user_id': user_id,
        'pet_type': pet_type,
        'pet_name': 'Серийчик',
        'stage': 'в пути 🌱',
        'age': 1,
        'total_messages': 0,
        'голод': 50,
        'счастье': 50,
        'гигиена': 50,
        'энергия': 50,
        'дисциплина': 50,
        'дни': 0,
        'одежда': 'без одежды',
        'fav_color': random.choice(colors),
        'fav_time': random.choice(times),
        'fav_season': random.choice(seasons),
        'fav_food': random.choice(foods),
        'fav_toy': random.choice(toys)
    }).execute()
    bot.send_message(message.chat.id, f"✅ Ты выбрал {pet_emojis[pet_type]} {pet_type.capitalize()}! Чтобы он вылупился, нужно 100 сообщений.")

@bot.message_handler(commands=['status'])
def status(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Нет питомца. /newpet")
        return
    text = (
        f"📊 {pet['pet_type']} {pet['pet_name']}\n"
        f"Стадия: {pet['stage']}\n"
        f"Возраст: {pet['age']}\n"
        f"Голод: {pet['голод']}\n"
        f"Счастье: {pet['счастье']}\n"
        f"Гигиена: {pet['гигиена']}\n"
        f"Энергия: {pet['энергия']}\n"
        f"Дисциплина: {pet['дисциплина']}\n"
        f"Сообщений: {pet['total_messages']}"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['feed'])
def feed(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала /newpet")
        return
    new_val = min(100, pet['голод'] + 20)
    update_pet(user_id, 'голод', new_val)
    bot.send_message(message.chat.id, "🍖 Покормлен! Голод +20")

@bot.message_handler(commands=['play'])
def play(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала /newpet")
        return
    new_s = min(100, pet['счастье'] + 15)
    new_e = max(0, pet['энергия'] - 10)
    update_pet(user_id, 'счастье', new_s)
    update_pet(user_id, 'энергия', new_e)
    bot.send_message(message.chat.id, "🎾 Поиграл! Счастье +15, Энергия -10")

@bot.message_handler(commands=['wash'])
def wash(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала /newpet")
        return
    new_val = min(100, pet['гигиена'] + 25)
    update_pet(user_id, 'гигиена', new_val)
    bot.send_message(message.chat.id, "🧼 Помыт! Гигиена +25")

@bot.message_handler(commands=['sleep'])
def sleep(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала /newpet")
        return
    new_val = min(100, pet['энергия'] + 30)
    update_pet(user_id, 'энергия', new_val)
    bot.send_message(message.chat.id, "😴 Поспал! Энергия +30")

@bot.message_handler(commands=['train'])
def train(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала /newpet")
        return
    new_val = min(100, pet['дисциплина'] + 15)
    update_pet(user_id, 'дисциплина', new_val)
    bot.send_message(message.chat.id, "🏋️ Тренировка! Дисциплина +15")

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

@bot.message_handler(commands=['app'])
def app_command(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        text="🐾 Открыть Серийчика",
        web_app=telebot.types.WebAppInfo(url="https://seriychik-webapp.onrender.com")
    ))
    bot.send_message(message.chat.id, "Нажми на кнопку, чтобы открыть питомца:", reply_markup=markup)

# --- ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ (без диалогов) ---
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
    save_message(user_id, 'user', message.text)
    bot.send_message(message.chat.id, "🐾 Я тебя слышу!")

# --- ЗАПУСК ---
if __name__ == '__main__':
    bot.delete_webhook()
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("✅ Бот запущен (все команды есть, диалогов нет)!")
    bot.polling()
