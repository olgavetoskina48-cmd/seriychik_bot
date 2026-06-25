from flask import Flask, send_from_directory, request, jsonify
from supabase import create_client
import os
import random
import re

app = Flask(__name__, static_folder='webapp')

# --- SUPABASE ---
SUPABASE_URL = "https://jzscsndwuchzlellgqea.supabase.co"
SUPABASE_KEY = "sb_publishable_-kqOsr7gFZRi8ctCNPaLgg_4mjU-NZy"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_pet(user_id):
    response = supabase.table('pets').select('*').eq('user_id', user_id).execute()
    if response.data:
        return response.data[0]
    return None

def update_pet(user_id, field, value):
    supabase.table('pets').update({field: value}).eq('user_id', user_id).execute()

# --- ЗВУКИ ЖИВОТНЫХ ---
animal_sounds = {
    "кошка": ["мяу", "мур", "мяф", "фыр"],
    "собака": ["гав", "тяф", "вуф", "ррр"],
    "лиса": ["фыр", "кхе", "ууу", "шшш"],
    "енот": ["хрум", "шурх", "фырк", "пиу"],
    "хомяк": ["пиу", "цок", "чив", "фрр"]
}

# --- УМНЫЙ ОТВЕТЧИК (по ключевым словам) ---
def get_smart_response(text, pet_type):
    sounds = animal_sounds.get(pet_type, ["мяу"])
    sound = random.choice(sounds)
    text_lower = text.lower()

    # Приветствия
    if re.search(r'привет|здравствуй|хай|hello|салют', text_lower):
        return f"Привет! {sound}! Как твои дела?"

    # Как дела
    if re.search(r'как дел|как сам|как жизнь|как ты', text_lower):
        return f"У меня всё отлично! {sound} А у тебя?"

    # Что делаешь / чем занят
    if re.search(r'что делаешь|чем занят|чем занимаешься', text_lower):
        activities = [
            f"Смотрю в окошко, {sound}... там птичка!",
            f"Играю с хвостом, {sound}!",
            f"Лежу на солнышке, {sound}...",
            f"Думаю о чём-то важном, {sound}..."
        ]
        return random.choice(activities)

    # Имя
    if re.search(r'как зовут|как тебя звать|твое имя', text_lower):
        return f"Меня зовут Серийчик! {sound} А как зовут тебя?"

    # Любовь / скучал
    if re.search(r'люблю|скучал|соскучился', text_lower):
        return f"Я тоже тебя очень люблю! {sound}! Ты мой самый лучший друг!"

    # Еда
    if re.search(r'есть|кушать|еда|голод|кормить', text_lower):
        return f"О! Еда! {sound} {sound}! Я очень голоден!"

    # Сон
    if re.search(r'спать|сон|устал', text_lower):
        return f"Да, я немного устал, {sound}... Пойду посплю."

    # Игра
    if re.search(r'играть|игра|поиграй', text_lower):
        return f"Давай! {sound}! Я люблю играть!"

    # Погода
    if re.search(r'погода|солнце|дождь|снег', text_lower):
        return f"Сегодня хорошая погода, {sound}! А ты что думаешь?"

    # Спасибо
    if re.search(r'спасибо|благодар', text_lower):
        return f"Пожалуйста! {sound} Я рад помочь!"

    # Если ничего не понял
    return f"Я не совсем понял, {sound}... Но я тебя слушаю!"

# --- API: ПОЛУЧИТЬ ПИТОМЦА ---
@app.route('/api/pet/<int:user_id>')
def api_pet(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    return jsonify(pet)

# --- API: ПОКОРМИТЬ (с проверкой) ---
@app.route('/api/feed/<int:user_id>', methods=['POST'])
def api_feed(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    if pet['голод'] >= 100:
        return jsonify({'error': 'Я уже сыт! Не корми меня больше 🍖'}), 400
    new_val = min(100, pet['голод'] + 20)
    update_pet(user_id, 'голод', new_val)
    return jsonify({'голод': new_val, 'message': 'Покормлен! Голод +20'})

# --- API: ПОИГРАТЬ (с проверкой) ---
@app.route('/api/play/<int:user_id>', methods=['POST'])
def api_play(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    if pet['энергия'] < 10:
        return jsonify({'error': 'Я слишком устал! Дай мне поспать 😴'}), 400
    if pet['счастье'] >= 100:
        return jsonify({'error': 'Я уже счастлив! 🌟'}), 400
    new_s = min(100, pet['счастье'] + 15)
    new_e = max(0, pet['энергия'] - 10)
    update_pet(user_id, 'счастье', new_s)
    update_pet(user_id, 'энергия', new_e)
    return jsonify({'счастье': new_s, 'энергия': new_e, 'message': 'Поиграл! Счастье +15, Энергия -10'})

# --- API: ПОМЫТЬ (с проверкой) ---
@app.route('/api/wash/<int:user_id>', methods=['POST'])
def api_wash(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    if pet['гигиена'] >= 100:
        return jsonify({'error': 'Я уже чистый! 🧼'}), 400
    new_val = min(100, pet['гигиена'] + 25)
    update_pet(user_id, 'гигиена', new_val)
    return jsonify({'гигиена': new_val, 'message': 'Помыт! Гигиена +25'})

# --- API: ПОСПАТЬ (с проверкой) ---
@app.route('/api/sleep/<int:user_id>', methods=['POST'])
def api_sleep(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    if pet['энергия'] >= 100:
        return jsonify({'error': 'Я не хочу спать! У меня полная энергия ⚡'}), 400
    new_val = min(100, pet['энергия'] + 30)
    update_pet(user_id, 'энергия', new_val)
    return jsonify({'энергия': new_val, 'message': 'Поспал! Энергия +30'})

# --- API: ТРЕНИРОВАТЬ (с проверкой) ---
@app.route('/api/train/<int:user_id>', methods=['POST'])
def api_train(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    if pet['дисциплина'] >= 100:
        return jsonify({'error': 'Я уже очень дисциплинированный! 📏'}), 400
    if pet['энергия'] < 10:
        return jsonify({'error': 'Я слишком устал для тренировки! 😴'}), 400
    new_val = min(100, pet['дисциплина'] + 15)
    update_pet(user_id, 'дисциплина', new_val)
    return jsonify({'дисциплина': new_val, 'message': 'Тренировка! Дисциплина +15'})

# --- API: ПЕРЕОДЕТЬ ---
@app.route('/api/dress/<int:user_id>', methods=['POST'])
def api_dress(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    options = ["без одежды", "шапка 🧢", "шарф 🧣", "очки 🕶️", "плащ 🧥"]
    current = pet['одежда']
    idx = options.index(current) if current in options else 0
    new_idx = (idx + 1) % len(options)
    update_pet(user_id, 'одежда', options[new_idx])
    return jsonify({'одежда': options[new_idx], 'message': f'Теперь на питомце: {options[new_idx]}'})

# --- API: ЧАТ С ПИТОМЦЕМ (умный) ---
@app.route('/api/chat/<int:user_id>', methods=['POST'])
def api_chat(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404

    data = request.get_json()
    user_text = data.get('text', '')

    pet_type = pet.get('pet_type', 'кошка')
    response = get_smart_response(user_text, pet_type)

    # Добавляем реакцию на состояние
    if pet['голод'] < 20:
        response += " (кстати, я голоден... покорми меня)"
    elif pet['энергия'] < 20:
        response += " (я устал, хочу спать)"
    elif pet['счастье'] > 80:
        response += " (я так счастлив!!)"

    return jsonify({'response': response})

# --- ОТДАЁМ СТРАНИЦУ ---
@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
