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

def save_message(user_id, sender, message):
    supabase.table('chat_history').insert({
        'user_id': user_id,
        'sender': sender,
        'message': message
    }).execute()

def get_chat_history(user_id, limit=5):
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

# --- ОТВЕТЧИК С КОНТЕКСТОМ ---
def get_smart_response(user_id, text, pet):
    sound = random.choice(animal_sounds.get(pet.get('pet_type', 'кошка'), ["мяу"]))
    text_lower = text.lower()

    # Загружаем историю (последние 5 сообщений)
    history = get_chat_history(user_id, limit=5)
    history_text = ""
    for msg in history:
        sender = "Пользователь" if msg['sender'] == 'user' else "Питомец"
        history_text += f"{sender}: {msg['message']}\n"

    # --- 1. ПРИВЕТСТВИЯ ---
    if re.search(r'привет|здравствуй|хай|hello|салют|ку', text_lower):
        return random.choice([
            f"Привет-привет! {sound} Как жизнь?",
            f"О, привет! {sound} Я так рад тебя видеть!",
            f"Здравствуй! {sound} Давно не виделись!",
            f"Хай, {sound}! Как ты сегодня?"
        ])

    # --- 2. КАК ДЕЛА ---
    if re.search(r'как дел|как сам|как жизнь|как ты|как настроение', text_lower):
        return random.choice([
            f"У меня всё супер! {sound} А у тебя?",
            f"Отлично! {sound} Сегодня чудесный день!",
            f"Я в порядке, {sound}! Немного устал(а), но держусь.",
            f"Всё замечательно! {sound} Особенно теперь, когда ты рядом!"
        ])

    # --- 3. ЧТО ДЕЛАЕШЬ ---
    if re.search(r'что делаешь|чем занят|чем занимаешься|что делаешь сейчас', text_lower):
        return random.choice([
            f"Смотрю в окошко, {sound}... там птичка!",
            f"Играю с хвостом, {sound}! Он всё время от меня убегает.",
            f"Лежу на солнышке, {sound}... так тепло!",
            f"Думаю о тебе, {sound}!",
            f"Жду тебя, {sound}! А то скучно одному(ой)."
        ])

    # --- 4. ЧЕМ УВЛЕКАЕШЬСЯ / ХОББИ ---
    if re.search(r'увлекаешься|хобби|чем любишь заниматься|твоё хобби', text_lower):
        return random.choice([
            f"Я люблю играть, спать и есть, {sound}! А ты?",
            f"Моё хобби — наблюдать за птицами, {sound}! Они такие смешные.",
            f"Я люблю лежать на солнышке и мечтать, {sound}! А у тебя есть хобби?"
        ])

    # --- 5. НЕГАТИВ ---
    if re.search(r'плохо|грустно|больно|обидно|ужасно|тяжело|слёзы|плачу|депрессия|одинок|одиноко|нет сил|вымотан', text_lower):
        return f"Мне жаль это слышать, {sound}... Ты не один(на). Напиши своему админу в боте, он поможет."

    # --- 6. ВСЁ ХОРОШО ---
    if re.search(r'всё хорошо|всё отлично|супер|классно|замечательно|нормально|отлично', text_lower):
        return random.choice([
            f"Я рад, что у тебя всё хорошо! {sound}",
            f"Ура! {sound} Отличные новости!",
            f"Здорово! {sound} Пусть так будет всегда!"
        ])

    # --- 7. ЛЮБИМЫЙ ЦВЕТ ПИТОМЦА ---
    if re.search(r'твой любимый цвет|какой цвет любишь|твой цвет', text_lower):
        if pet.get('fav_color') and pet['fav_color'] != 'None':
            return f"Мой любимый цвет — {pet['fav_color']}! {sound} А у тебя?"
        else:
            return f"Я люблю все цвета, {sound}! А ты?"

    # --- 8. ЛЮБИМАЯ ЕДА ---
    if re.search(r'твоя любимая еда|что любишь есть|еда', text_lower):
        if pet.get('fav_food') and pet['fav_food'] != 'None':
            return f"Обожаю {pet['fav_food']}! {sound} А у тебя?"
        else:
            return f"Я люблю всё вкусное, {sound}! А ты?"

    # --- 9. ЛЮБИМАЯ ИГРУШКА ---
    if re.search(r'твоя любимая игрушка|во что любишь играть', text_lower):
        if pet.get('fav_toy') and pet['fav_toy'] != 'None':
            return f"Моя любимая игрушка — {pet['fav_toy']}! {sound} Давай поиграем!"
        else:
            return f"Я люблю играть в мячик, {sound}! А ты?"

    # --- 10. ЛЮБИМОЕ ВРЕМЯ СУТОК ---
    if re.search(r'любимое время суток|какое время любишь|утро|день|вечер|ночь', text_lower):
        if pet.get('fav_time') and pet['fav_time'] != 'None':
            return f"Я больше всего люблю {pet['fav_time']}! {sound} А ты?"
        else:
            return f"Я люблю все времена суток, {sound}! А ты?"

    # --- 11. ЛЮБИМОЕ ВРЕМЯ ГОДА ---
    if re.search(r'любимое время года|какое время года любишь|весна|лето|осень|зима', text_lower):
        if pet.get('fav_season') and pet['fav_season'] != 'None':
            return f"Обожаю {pet['fav_season']}! {sound} А ты?"
        else:
            return f"Я люблю все сезоны, {sound}! А ты?"

    # --- 12. ФИЛЬМЫ ---
    if re.search(r'фильм|кино|сериал|фильмы|кинотеатр', text_lower):
        return random.choice([
            f"Обожаю фильмы, {sound}! Люблю комедии. А ты какой жанр любишь?",
            f"Сериалы — это круто, {sound}! Что смотришь сейчас?",
            f"Кино — это магия, {sound}! А ты любишь классику?"
        ])

    # --- 13. МУЗЫКА ---
    if re.search(r'музыка|песня|песни|музыкальный|исполнитель', text_lower):
        return random.choice([
            f"Музыка — это душа, {sound}! Что ты слушаешь?",
            f"Я люблю спокойную музыку, {sound}! А ты какую предпочитаешь?",
            f"Музыка помогает расслабиться, {sound}! А у тебя есть любимый исполнитель?"
        ])

    # --- 14. ЕДА ---
    if re.search(r'есть|кушать|еда|голод|кормить', text_lower):
        return random.choice([
            f"О! Еда! {sound} {sound} Я очень голоден(на)!",
            f"Обожаю кушать! {sound} Особенно вкусняшки!",
            f"Конечно, люблю есть! {sound} А кто не любит?",
            f"Покорми меня, {sound}! Я умираю с голоду!"
        ])

    # --- 15. ИГРАТЬ ---
    if re.search(r'играть|игра|поиграй|поиграем|давай играть', text_lower):
        return random.choice([
            f"Давай! {sound}! Я люблю играть!",
            f"Ура! Игра! {sound} Я уже бегу!",
            f"Конечно! {sound} Что будем делать?",
            f"Играть — это моё любимое занятие, {sound}!"
        ])

    # --- 16. ЛЮБОВЬ / СКУЧАЛ ---
    if re.search(r'люблю|скучал|соскучился|ты мой любимый', text_lower):
        return random.choice([
            f"Я тоже тебя очень люблю! {sound}!",
            f"Конечно, скучал(а)! {sound} Ты долго не появлялся(лась)!",
            f"Я тебя обожаю! {sound} Ты у меня самый лучший!"
        ])

    # --- 17. ПОГОДА ---
    if re.search(r'погода|солнце|дождь|снег|ветер|облачно|тепло|холодно', text_lower):
        return random.choice([
            f"Сегодня отличная погода, {sound}! А ты как думаешь?",
            f"Дождик за окном, {sound}... так уютно!",
            f"Солнце светит! {sound} Иди гулять!",
            f"Снег идёт, {sound}! Холодно, но красиво."
        ])

    # --- 18. ЕСЛИ НИЧЕГО НЕ ПОНЯЛ ---
    # Проверяем, был ли у пользователя уже вопрос о том же
    if history_text and len(history) > 0:
        last_user_msg = history[-1]['message'] if history[-1]['sender'] == 'user' else None
        if last_user_msg and len(last_user_msg) > 3:
            return f"Хм, {sound}... ты говорил(а) о '{last_user_msg[:30]}...' Я слушаю тебя. Расскажи ещё!"

    return random.choice([
        f"Я тебя слышу, {sound}... расскажи ещё!",
        f"Интересно, {sound}! А что ещё?",
        f"Хм, {sound}... давай поговорим о чём-то другом?",
        f"Я тут, {sound}! Я всегда рад(а) поболтать."
    ])

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
