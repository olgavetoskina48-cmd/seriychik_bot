import os
import random
import re
import json
import threading
import time
from telebot import TeleBot
from supabase import create_client
from flask import Flask, request
from difflib import SequenceMatcher

# --- SUPABASE ---
SUPABASE_URL = "https://jzscsndwuchzlellgqea.supabase.co"
SUPABASE_KEY = "sb_publishable_-kqOsr7gFZRi8ctCNPaLgg_4mjU-NZy"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TOKEN = "8961168833:AAEtlADb8Tyng1LmMbD7d_0Q7AeNkqny_W8"
bot = TeleBot(TOKEN)

# --- БАЗА ДАННЫХ ---
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

def get_chat_history(user_id, limit=6):
    response = supabase.table('chat_history')\
        .select('*')\
        .eq('user_id', user_id)\
        .order('created_at', desc=False)\
        .limit(limit)\
        .execute()
    return response.data if response.data else []

# --- ЗВУКИ ---
animal_sounds = {
    "кошка": ["мяу", "мур", "мяф", "фыр"],
    "собака": ["гав", "тяф", "вуф", "ррр"],
    "лиса": ["фыр", "кхе", "ууу", "шшш"],
    "енот": ["хрум", "шурх", "фырк", "пиу"],
    "хомяк": ["пиу", "цок", "чив", "фрр"]
}

# --- ДАННЫЕ О ПИТОМЦЕ ---
def get_pet_info(pet):
    return {
        "pet_name": pet.get('pet_name', 'Серийчик'),
        "pet_type": pet.get('pet_type', 'животное'),
        "age": pet.get('age', 1),
        "fav_color": pet.get('fav_color', 'все цвета'),
        "fav_food": pet.get('fav_food', 'вкусняшки'),
        "fav_toy": pet.get('fav_toy', 'мячик'),
        "fav_time": pet.get('fav_time', 'все времена'),
        "fav_season": pet.get('fav_season', 'все сезоны')
    }

# --- КЕШ ---
response_cache = {}

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_best_match(text, dialog_dataset):
    best_score = 0
    best_key = None
    for category_name, category_data in dialog_dataset.items():
        if "keywords" in category_data:
            for keyword in category_data["keywords"]:
                score = similarity(text, keyword)
                if score > best_score:
                    best_score = score
                    best_key = category_name
    if best_score > 0.65:
        return best_key
    return None

def load_dialogs():
    try:
        with open('dialogs.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

dialog_dataset = load_dialogs()

dialog_patterns = {
    r'(плохо|грустно|больно|обидно|ужасно|тяжело|слёзы|плачу|депрессия|одинок|одиноко|нет сил|вымотан|всё надоело)': [
        "Мне жаль это слышать, {sound}... Ты не один(на). Напиши своему админу в боте, он поможет.",
        "Я рядом, хозяин! {sound} Расскажи, что случилось. *прижимаюсь к тебе*",
        "Не грусти, хозяин! {sound} Я с тобой! *кладю голову тебе на колени*"
    ],
    r'(всё хорошо|всё отлично|супер|классно|замечательно|нормально|отлично|прекрасно)': [
        "Я рад, что у тебя всё хорошо! {sound}",
        "Ура! {sound} Отличные новости!",
        "Здорово! {sound} Пусть так будет всегда!"
    ]
}

def get_smart_response(user_id, text, pet):
    text_lower = text.lower().strip()
    sound = random.choice(animal_sounds.get(pet.get('pet_type', 'кошка'), ["мяу"]))
    pet_info = get_pet_info(pet)

    if text_lower in response_cache:
        return response_cache[text_lower]

    for pattern, responses in dialog_patterns.items():
        if re.search(pattern, text_lower):
            response = random.choice(responses)
            for key, value in pet_info.items():
                response = response.replace("{" + key + "}", str(value))
            response = response.replace("{sound}", sound)
            response_cache[text_lower] = response
            return response

    if dialog_dataset:
        best_category = find_best_match(text_lower, dialog_dataset)
        if best_category and best_category in dialog_dataset:
            responses = dialog_dataset[best_category].get("responses", [])
            if responses:
                response = random.choice(responses)
                for key, value in pet_info.items():
                    response = response.replace("{" + key + "}", str(value))
                response = response.replace("{sound}", sound)
                response_cache[text_lower] = response
                return response

    history = get_chat_history(user_id, limit=6)
    if history:
        last_msgs = [h['message'] for h in history if h['sender'] == 'user']
        if last_msgs:
            last = last_msgs[-1]
            response = random.choice([
                f"{sound} Я внимательно тебя слушаю. Ты говорил(а): «{last[:40]}». Расскажи ещё.",
                f"Мне интересно, хозяин. {sound} Продолжай, пожалуйста.",
                f"*внимательно смотрю на тебя* Расскажи подробнее."
            ])
            response_cache[text_lower] = response
            return response

    generic = [
        f"*виляю хвостом* Мне нравится разговаривать с тобой, хозяин.",
        f"{sound} Я не совсем понял, но мне интересно. Расскажи подробнее.",
        f"Продолжай, хозяин. Я тебя внимательно слушаю. {sound}",
        f"*прижимаюсь к тебе* Мне всегда интересно, что ты рассказываешь.",
        f"{sound} А что ты сам думаешь по этому поводу?",
        f"Это звучит интересно. Расскажи ещё немного, хозяин."
    ]
    response = random.choice(generic)
    response_cache[text_lower] = response
    return response

# --- КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🐾 Привет! Это Серийчик. Напиши /newpet — завести питомца, /help — список команд.")

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
    text = f"📊 {pet['pet_type']} {pet['pet_name']}\nСтадия: {pet['stage']}\nВозраст: {pet['age']}\nГолод: {pet['голод']}\nСчастье: {pet['счастье']}\nГигиена: {pet['гигиена']}\nЭнергия: {pet['энергия']}\nДисциплина: {pet['дисциплина']}\nСообщений: {pet['total_messages']}"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "📋 Команды:\n/newpet — завести питомца\n/status — состояние\n/feed — покормить\n/play — поиграть\n/wash — помыть\n/sleep — поспать\n/train — тренировать\n/dress — переодеть\n/app — мини-приложение\n/help — этот список")

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

# --- ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ ---
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
    response = get_smart_response(user_id, message.text, pet)
    save_message(user_id, 'pet', response)
    bot.send_message(message.chat.id, response)

# --- ЗАПУСК ---
if __name__ == '__main__':
    bot.delete_webhook()
    print("✅ Бот запущен!")
    bot.polling()
