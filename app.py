from flask import Flask, send_from_directory, request, jsonify
from supabase import create_client
import os
import random
import re

app = Flask(__name__, static_folder='webapp')

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

def get_chat_history(user_id, limit=50):
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

def get_smart_response(text, pet):
    sound = random.choice(animal_sounds.get(pet.get('pet_type', 'кошка'), ["мяу"]))
    text_lower = text.lower()

    if re.search(r'любимый цвет|какой цвет любишь|твой цвет', text_lower):
        if pet.get('fav_color'):
            return f"Мой любимый цвет — {pet['fav_color']}! {sound} А твой?"
        else:
            return f"Я ещё не выбрал любимый цвет, {sound}... Какой у тебя любимый? Напиши!"

    if re.search(r'любимое время суток|какое время любишь|утро|день|вечер|ночь', text_lower):
        if pet.get('fav_time'):
            return f"Я больше всего люблю {pet['fav_time']}! {sound} В это время так хорошо!"
        else:
            return f"Я ещё не знаю, какое время суток люблю, {sound}... А ты что любишь?"

    if re.search(r'любимое время года|какое время года любишь|весна|лето|осень|зима', text_lower):
        if pet.get('fav_season'):
            return f"Обожаю {pet['fav_season']}! {sound} Это самое лучшее время года!"
        else:
            return f"Я ещё не решил, какое время года люблю, {sound}... А твоё любимое?"

    if re.search(r'любимая еда|любимое блюдо|что любишь есть|твоя любимая еда', text_lower):
        if pet.get('fav_food'):
            return f"Моя любимая еда — {pet['fav_food']}! {sound} А у тебя?"
        else:
            return f"Я ещё не знаю, что люблю есть, {sound}... А что ты любишь?"

    if re.search(r'любимая игрушка|во что любишь играть|твоя игрушка', text_lower):
        if pet.get('fav_toy'):
            return f"Моя любимая игрушка — {pet['fav_toy']}! {sound} Давай поиграем!"
        else:
            return f"Я ещё не выбрал любимую игрушку, {sound}... А какая у тебя?"

    if re.search(r'привет|здравствуй|хай|hello|салют|ку', text_lower):
        return random.choice([
            f"Привет-привет! {sound}! Как жизнь?",
            f"О, привет! {sound} Я так рад тебя видеть!",
            f"Здравствуй! {sound} Давно не виделись!",
            f"Хай! {sound} Как у тебя дела?"
        ])

    if re.search(r'как дел|как сам|как жизнь|как ты|как настроение', text_lower):
        return random.choice([
            f"У меня всё супер! {sound} А у тебя?",
            f"Отлично! {sound} Сегодня чудесный день!",
            f"Я в порядке, {sound}! Немного устал, но держусь.",
            f"Всё замечательно! {sound} Особенно теперь, когда ты рядом!"
        ])

    if re.search(r'что делаешь|чем занят|чем занимаешься|что делаешь сейчас', text_lower):
        activities = [
            f"Смотрю в окошко, {sound}... там птичка на дереве!",
            f"Играю с хвостом, {sound}! Он всё время от меня убегает!",
            f"Лежу на солнышке, {sound}... так тепло и хорошо.",
            f"Думаю о чём-то важном, {sound}... о мире во всём мире.",
            f"Жду тебя! {sound} А то скучно одному.",
            f"Смотрю на облака, {sound}... одно похоже на рыбку!"
        ]
        return random.choice(activities)

    if re.search(r'есть|кушать|еда|голод|кормить|любишь ли ты кушать', text_lower):
        return random.choice([
            f"О! Еда! {sound} {sound} Я очень голоден!",
            f"Обожаю кушать! {sound} Особенно вкусняшки!",
            f"Конечно, люблю! {sound} А кто не любит?",
            f"Я бы сейчас что-нибудь съел, {sound}... покорми меня!"
        ])

    if re.search(r'играть|игра|поиграй|поиграем', text_lower):
        return random.choice([
            f"Давай! {sound}! Я люблю играть!",
            f"Ура! Игра! {sound} Я уже бегу!",
            f"Конечно! {sound} Что будем делать?"
        ])

    if re.search(r'люблю|скучал|соскучился|ты мой любимый', text_lower):
        return random.choice([
            f"Я тоже тебя очень люблю! {sound}! Ты мой самый лучший друг!",
            f"Конечно, скучал! {sound} Ты долго не появлялся!",
            f"Я тебя обожаю! {sound} Ты у меня самый лучший!"
        ])

    return random.choice([
        f"Я не совсем понял, {sound}... Но я тебя слушаю!",
        f"Прости, {sound}... Я не знаю, что сказать.",
        f"Хм, {sound}... Давай поговорим о чём-то другом?"
    ])

@app.route('/api/history/<int:user_id>')
def api_history(user_id):
    return jsonify(get_chat_history(user_id))

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
        return jsonify({'error': 'Я уже сыт!'}), 400
    new_val = min(100, pet['голод'] + 20)
    update_pet(user_id, 'голод', new_val)
    return jsonify({'голод': new_val, 'message': 'Покормлен! +20'})

@app.route('/api/play/<int:user_id>', methods=['POST'])
def api_play(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    if pet['энергия'] < 10:
        return jsonify({'error': 'Я устал!'}), 400
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
        return jsonify({'error': 'Я уже чистый!'}), 400
    new_val = min(100, pet['гигиена'] + 25)
    update_pet(user_id, 'гигиена', new_val)
    return jsonify({'гигиена': new_val, 'message': 'Помыт! +25'})

@app.route('/api/sleep/<int:user_id>', methods=['POST'])
def api_sleep(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    if pet['энергия'] >= 100:
        return jsonify({'error': 'Я не хочу спать!'}), 400
    new_val = min(100, pet['энергия'] + 30)
    update_pet(user_id, 'энергия', new_val)
    return jsonify({'энергия': new_val, 'message': 'Поспал! +30'})

@app.route('/api/train/<int:user_id>', methods=['POST'])
def api_train(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404
    if pet['дисциплина'] >= 100:
        return jsonify({'error': 'Я уже дисциплинированный!'}), 400
    if pet['энергия'] < 10:
        return jsonify({'error': 'Я устал для тренировки!'}), 400
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
    response = get_smart_response(user_text, pet)
    if pet['голод'] < 20:
        response += " (я голоден...)"
    elif pet['энергия'] < 20:
        response += " (я устал...)"
    elif pet['счастье'] > 80:
        response += " (я счастлив!!)"
    save_message(user_id, 'pet', response)
    return jsonify({'response': response})

@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
