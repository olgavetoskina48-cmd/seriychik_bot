import telebot
import threading
import time
import os
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
from supabase import create_client

TOKEN = "8961168833:AAEtlADb8Tyng1LmMbD7d_0Q7AeNkqny_W8"
bot = telebot.TeleBot(TOKEN)

ADMINS = []
user_choice = {}

# --- SUPABASE ---
SUPABASE_URL = "https://jzscsndwuchzlellgqea.supabase.co"
SUPABASE_KEY = "sb_publishable_-kqOsr7gFZRi8ctCNPaLgg_4mjU-NZy"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- СПИСОК ДЛЯ СЛУЧАЙНЫХ ПРЕДПОЧТЕНИЙ ---
colors = ["красный", "синий", "зелёный", "жёлтый", "фиолетовый", "розовый", "оранжевый", "голубой"]
times = ["утро", "день", "вечер", "ночь"]
seasons = ["весна", "лето", "осень", "зима"]
foods = ["рыбка", "сосиски", "мороженое", "печенье", "мясо"]
toys = ["мячик", "косточка", "мышка", "верёвка", "подушка"]

# --- ПОРТ ДЛЯ RENDER ---
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running!')

def run_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()

# --- БАЗА ДАННЫХ (Supabase) ---
def get_pet(user_id):
    response = supabase.table('pets').select('*').eq('user_id', user_id).execute()
    if response.data:
        return response.data[0]
    return None

def create_pet(user_id, pet_type):
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

def update_pet(user_id, field, value):
    supabase.table('pets').update({field: value}).eq('user_id', user_id).execute()

def get_stage(total_messages):
    if total_messages < 100:
        return "в пути 🌱"
    elif total_messages <= 250:
        return "яйцо 🥚"
    elif total_messages <= 500:
        return "малыш 🐣"
    elif total_messages <= 1000:
        return "подросток 🧒"
    else:
        return "взрослый 🧑"

def get_age(total_messages):
    return total_messages // 100 + 1

def check_stage_upgrade(user_id, pet):
    old_stage = pet['stage']
    new_stage = get_stage(pet['total_messages'])
    new_age = get_age(pet['total_messages'])
    if new_stage != old_stage:
        update_pet(user_id, 'stage', new_stage)
        if new_stage != "в пути 🌱":
            bot.send_message(user_id, f"🌟 Твой Серийчик вырос до {new_stage}!")
    if new_age != pet['age']:
        update_pet(user_id, 'age', new_age)
        bot.send_message(user_id, f"🎂 Твой Серийчик стал старше! Ему {new_age} возраст!")

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
    bot.send_message(message.chat.id, "🐾 Привет! Это Серийчик.\n/newpet — завести питомца\n/name — дать имя питомцу\n/feed, /play, /wash, /sleep, /train — ухаживать\n/status — состояние\n/dress — переодеть\n/app — открыть питомца в мини-приложении")

@bot.message_handler(commands=['newpet'])
def new_pet(message):
    user_id = message.from_user.id
    if get_pet(user_id):
        bot.send_message(message.chat.id, "У тебя уже есть питомец!")
        return
    user_choice[user_id] = True
    bot.send_message(message.chat.id, "🥚 Напиши тип питомца: кошка, лиса, собака, енот, хомяк")
    bot.register_next_step_handler(message, set_pet_type)

def set_pet_type(message):
    user_id = message.from_user.id
    if user_id not in user_choice:
        return
    if message.text.startswith('/'):
        user_choice.pop(user_id, None)
        return
    pet_type = message.text.lower()
    if pet_type not in pet_emojis:
        bot.send_message(message.chat.id, "❌ Неверный тип. Напиши: кошка, лиса, собака, енот, хомяк")
        bot.register_next_step_handler(message, set_pet_type)
        return
    create_pet(user_id, pet_type)
    user_choice.pop(user_id, None)
    bot.send_message(message.chat.id, f"✅ Ты выбрал {pet_emojis[pet_type]} {pet_type.capitalize()}! Чтобы он вылупился, нужно 100 сообщений.")

@bot.message_handler(commands=['name'])
def set_name(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Сначала заведи питомца через /newpet")
        return
    bot.send_message(message.chat.id, "✏️ Напиши новое имя для своего питомца:")
    bot.register_next_step_handler(message, save_name)

def save_name(message):
    user_id = message.from_user.id
    name = message.text.strip()
    if len(name) > 20:
        bot.send_message(message.chat.id, "❌ Имя слишком длинное. Напиши короче (до 20 символов).")
        bot.register_next_step_handler(message, save_name)
        return
    update_pet(user_id, 'pet_name', name)
    bot.send_message(message.chat.id, f"✅ Отлично! Теперь твоего питомца зовут {name}!")

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

@bot.message_handler(commands=['status'])
def status(message):
    user_id = message.from_user.id
    pet = get_pet(user_id)
    if not pet:
        bot.send_message(message.chat.id, "Нет питомца. /newpet")
        return
    state = get_state(pet)
    emoji = pet_emojis.get(pet['pet_type'], '🐾')
    text = f"📊 {emoji} Серийчик ({state})\n{pet['stage']}\nВозраст: {pet['age']}\n\n🍖 Голод: {pet['голод']}\n😊 Счастье: {pet['счастье']}\n🧼 Гигиена: {pet['гигиена']}\n⚡ Энергия: {pet['энергия']}\n📏 Дисциплина: {pet['дисциплина']}\n📅 Дней: {pet['дни']}\n👕 Одежда: {pet['одежда']}\n💬 Сообщений: {pet['total_messages']}"
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

@bot.message_handler(commands=['app'])
def app_command(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        text="🐾 Открыть Серийчика",
        web_app=telebot.types.WebAppInfo(url="https://seriychik-webapp.onrender.com")
    ))
    bot.send_message(message.chat.id, "Нажми на кнопку, чтобы открыть питомца в отдельном окне:", reply_markup=markup)

# --- СООБЩЕНИЯ ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    if message.text and message.text.startswith('/'):
        return
    if user_id in user_choice:
        return
    pet = get_pet(user_id)
    if not pet:
        return
    new_total = pet['total_messages'] + 1
    update_pet(user_id, 'total_messages', new_total)
    check_stage_upgrade(user_id, pet)

# --- ДНИ ---
def update_days():
    while True:
        time.sleep(86400)
        pets = supabase.table('pets').select('user_id', 'голод', 'счастье', 'гигиена', 'энергия', 'дисциплина', 'дни').execute()
        for p in pets.data:
            new_data = {
                'дни': p['дни'] + 1,
                'голод': max(0, p['голод'] - 5),
                'счастье': max(0, p['счастье'] - 3),
                'гигиена': max(0, p['гигиена'] - 5),
                'энергия': max(0, p['энергия'] - 4),
                'дисциплина': max(0, p['дисциплина'] - 2)
            }
            supabase.table('pets').update(new_data).eq('user_id', p['user_id']).execute()

thread = threading.Thread(target=update_days)
thread.daemon = True
thread.start()

# --- ЗАПУСК ---
threading.Thread(target=run_server).start()
print("✅ Бот с памятью и умным чатом запущен!")
bot.polling()
