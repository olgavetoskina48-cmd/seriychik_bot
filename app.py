from flask import Flask, send_from_directory, request, jsonify
from supabase import create_client
import os
import random

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

# --- ЗВУКИ И ФРАЗЫ ДЛЯ ЧАТА ---
animal_sounds = {
    "кошка": ["мяу", "мур", "мяф", "фыр"],
    "собака": ["гав", "тяф", "вуф", "ррр"],
    "лиса": ["фыр", "кхе", "ууу", "шшш"],
    "енот": ["хрум", "шурх", "фырк", "пиу"],
    "хомяк": ["пиу", "цок", "чив", "фрр"]
}

pet_phrases = [
    "Привет! Как у тебя дела?",
    "Я тебя очень люблю!",
    "Сегодня такой классный день!",
    "Ты мой самый лучший друг!",
    "Мне так хорошо с тобой!",
    "А что мы будем делать сегодня?",
    "Я скучал по тебе!",
    "Ты такой добрый! Спасибо тебе!",
    "У меня отличное настроение!",
    "Я хочу с тобой играть!",
    "Ты сегодня очень красиво выглядишь!",
    "Я тебя обожаю!",
    "Как прошёл твой день?",
    "Ты мне очень дорог!",
    "Давай гулять!",
    "У тебя такие тёплые руки",
    "Ты мой герой!"
]

@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')

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
    new_val = min(100, pet['голод'] + 20)
    update_pet(user_id, 'голод', new_val)
    return jsonify({'голод': new_val})

@app.route('/api/play/<int:user_id>', methods=['POST'])
def api_play(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    new_s = min(100, pet['счастье'] + 15)
    new_e = max(0, pet['энергия'] - 10)
    update_pet(user_id, 'счастье', new_s)
    update_pet(user_id, 'энергия', new_e)
    return jsonify({'счастье': new_s, 'энергия': new_e})

@app.route('/api/wash/<int:user_id>', methods=['POST'])
def api_wash(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    new_val = min(100, pet['гигиена'] + 25)
    update_pet(user_id, 'гигиена', new_val)
    return jsonify({'гигиена': new_val})

@app.route('/api/sleep/<int:user_id>', methods=['POST'])
def api_sleep(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    new_val = min(100, pet['энергия'] + 30)
    update_pet(user_id, 'энергия', new_val)
    return jsonify({'энергия': new_val})

@app.route('/api/train/<int:user_id>', methods=['POST'])
def api_train(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    new_val = min(100, pet['дисциплина'] + 15)
    update_pet(user_id, 'дисциплина', new_val)
    return jsonify({'дисциплина': new_val})

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
    return jsonify({'одежда': options[new_idx]})

# --- НОВЫЙ API: ЧАТ С ПИТОМЦЕМ ---
@app.route('/api/chat/<int:user_id>', methods=['POST'])
def api_chat(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404

    pet_type = pet.get('pet_type', 'кошка')
    sounds = animal_sounds.get(pet_type, ["мяу"])

    phrase = random.choice(pet_phrases)

    # Вставляем звук с вероятностью 50%
    if random.random() < 0.5:
        sound = random.choice(sounds)
        if random.random() < 0.5:
            phrase = f"{sound}! " + phrase
        else:
            phrase = phrase + f" {sound}!"

    # Реакция на состояние
    if pet['голод'] < 20:
        phrase += " (я голодный... покорми меня)"
    elif pet['энергия'] < 20:
        phrase += " (я устал, хочу спать)"
    elif pet['счастье'] > 80:
        phrase += " (я так счастлив!!)"

    return jsonify({'response': phrase})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
