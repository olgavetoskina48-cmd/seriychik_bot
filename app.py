from flask import Flask, send_from_directory, request, jsonify
from supabase import create_client
import os
import random
import re
import json
from difflib import SequenceMatcher

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

animal_sounds = {
    "кошка": ["мяу", "мур", "мяф", "фыр"],
    "собака": ["гав", "тяф", "вуф", "ррр"],
    "лиса": ["фыр", "кхе", "ууу", "шшш"],
    "енот": ["хрум", "шурх", "фырк", "пиу"],
    "хомяк": ["пиу", "цок", "чив", "фрр"]
}

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

# --- API ---
@app.route('/api/history/<int:user_id>')
def api_history(user_id):
    history = get_chat_history(user_id, limit=50)
    return jsonify(history)

@app.route('/api/clear_history/<int:user_id>', methods=['POST'])
def api_clear_history(user_id):
    supabase.table('chat_history').delete().eq('user_id', user_id).execute()
    return jsonify({'message': 'История очищена!'})

@app.route('/api/pet/<int:user_id>')
def api_pet(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    return jsonify(pet)

@app.route('/api/feed/<int:user_id>', methods=['POST'])
def api_feed(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    if pet['голод'] >= 100:
        return jsonify({'error': 'Я уже сыт! 🍖'}), 400
    new_val = min(100, pet['голод'] + 20)
    update_pet(user_id, 'голод', new_val)
    return jsonify({'голод': new_val, 'message': 'Покормлен! +20'})

@app.route('/api/play/<int:user_id>', methods=['POST'])
def api_play(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    if pet['энергия'] < 10:
        return jsonify({'error': 'Я устал! 😴'}), 400
    new_s = min(100, pet['счастье'] + 15)
    new_e = max(0, pet['энергия'] - 10)
    update_pet(user_id, 'счастье', new_s)
    update_pet(user_id, 'энергия', new_e)
    return jsonify({'счастье': new_s, 'энергия': new_e, 'message': 'Поиграл! +15 счастья'})

@app.route('/api/wash/<int:user_id>', methods=['POST'])
def api_wash(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    if pet['гигиена'] >= 100:
        return jsonify({'error': 'Я уже чистый! 🧼'}), 400
    new_val = min(100, pet['гигиена'] + 25)
    update_pet(user_id, 'гигиена', new_val)
    return jsonify({'гигиена': new_val, 'message': 'Помыт! +25'})

@app.route('/api/sleep/<int:user_id>', methods=['POST'])
def api_sleep(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    if pet['энергия'] >= 100:
        return jsonify({'error': 'Я не хочу спать! ⚡'}), 400
    new_val = min(100, pet['энергия'] + 30)
    update_pet(user_id, 'энергия', new_val)
    return jsonify({'энергия': new_val, 'message': 'Поспал! +30'})

@app.route('/api/train/<int:user_id>', methods=['POST'])
def api_train(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    if pet['дисциплина'] >= 100:
        return jsonify({'error': 'Я уже дисциплинированный! 📏'}), 400
    if pet['энергия'] < 10:
        return jsonify({'error': 'Я устал для тренировки! 😴'}), 400
    new_val = min(100, pet['дисциплина'] + 15)
    update_pet(user_id, 'дисциплина', new_val)
    return jsonify({'дисциплина': new_val, 'message': 'Тренировка! +15'})

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
    return jsonify({'одежда': options[new_idx], 'message': f'Теперь: {options[new_idx]}'})

@app.route('/api/chat/<int:user_id>', methods=['POST'])
def api_chat(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404

    data = request.get_json()
    user_text = data.get('text', '')

    save_message(user_id, 'user', user_text)
    response = get_smart_response(user_id, user_text, pet)
    save_message(user_id, 'pet', response)

    return jsonify({'response': response})

@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
