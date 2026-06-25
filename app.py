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

def get_chat_history(user_id, limit=3):
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

# --- ДАННЫЕ О ПИТОМЦЕ ДЛЯ ОТВЕТОВ ---
def get_pet_info(pet):
    info = {
        "имя": pet.get('pet_name', 'Серийчик'),
        "тип": pet.get('pet_type', 'животное'),
        "цвет": pet.get('fav_color', 'все цвета'),
        "еда": pet.get('fav_food', 'вкусняшки'),
        "игрушка": pet.get('fav_toy', 'мячик'),
        "время_суток": pet.get('fav_time', 'все времена'),
        "сезон": pet.get('fav_season', 'все сезоны'),
        "возраст": pet.get('age', 1)
    }
    return info

# --- ОСНОВНАЯ ЛОГИКА ---
def get_smart_response(user_id, text, pet):
    sound = random.choice(animal_sounds.get(pet.get('pet_type', 'кошка'), ["мяу"]))
    text_lower = text.lower()
    pet_info = get_pet_info(pet)

    # --- ЗАГРУЖАЕМ ИСТОРИЮ ---
    history = get_chat_history(user_id, limit=3)
    last_user_msg = ""
    last_pet_msg = ""
    if len(history) >= 1:
        last_user_msg = history[-1]['message'] if history[-1]['sender'] == 'user' else ""
    if len(history) >= 2:
        last_pet_msg = history[-2]['message'] if history[-2]['sender'] == 'pet' else ""

    # --- 1. НЕГАТИВ ---
    if re.search(r'плохо|грустно|больно|обидно|ужасно|тяжело|слёзы|плачу|депрессия|одинок|одиноко|нет сил|вымотан|всё надоело', text_lower):
        return f"Мне жаль это слышать, {sound}... Ты не один(на). Напиши своему админу в боте, он поможет."

    # --- 2. КАК ДЕЛА (все синонимы) ---
    if re.search(r'как дел|как сам|как жизнь|как ты|как настроение|как твои дела|как живешь|как поживаешь|как оно|как у тебя', text_lower):
        return random.choice([
            f"У меня всё супер! {sound} А у тебя?",
            f"Отлично! {sound} Сегодня чудесный день!",
            f"Я в порядке, {sound}! Немного устал(а), но держусь.",
            f"Всё замечательно! {sound} Особенно теперь, когда ты рядом!"
        ])

    # --- 3. ПРИВЕТСТВИЯ ---
    if re.search(r'привет|здравствуй|хай|hello|салют|ку|здорово|доброе утро|добрый день|добрый вечер', text_lower):
        return random.choice([
            f"Привет-привет! {sound} Как жизнь?",
            f"О, привет! {sound} Я так рад тебя видеть!",
            f"Здравствуй! {sound} Давно не виделись!",
            f"Хай, {sound}! Как ты сегодня?",
            f"И тебе привет! {sound} Рассказывай, как дела!"
        ])

    # --- 4. ЧТО ДЕЛАЕШЬ / ЧЕМ ЗАНЯТ ---
    if re.search(r'что делаешь|чем занят|чем занимаешься|что делаешь сейчас|чем занят сейчас|какие планы|что нового|что случилось', text_lower):
        return random.choice([
            f"Смотрю в окошко, {sound}... там птичка!",
            f"Играю с хвостом, {sound}! Он всё время от меня убегает.",
            f"Лежу на солнышке, {sound}... так тепло!",
            f"Думаю о тебе, {sound}!",
            f"Жду тебя, {sound}! А то скучно одному(ой).",
            f"Планирую, что съем на ужин, {sound}! А у тебя какие планы?"
        ])

    # --- 5. РАССКАЖИ О СЕБЕ ---
    if re.search(r'расскажи о себе|кто ты|расскажи кто ты|что ты за зверь|расскажи про себя', text_lower):
        return random.choice([
            f"Я {pet_info['тип']} по имени {pet_info['имя']}! {sound} Мне {pet_info['возраст']} возраст. Люблю {pet_info['цвет']} цвет и обожаю {pet_info['еда']}. А ты?",
            f"Я {pet_info['имя']}, {pet_info['тип']}! {sound} Моё хобби — играть с {pet_info['игрушка']}. А что ты любишь?",
            f"Ну, я {pet_info['тип']}! {sound} Люблю {pet_info['сезон']} и {pet_info['время_суток']}. Моя еда — {pet_info['еда']}. А что насчёт тебя?"
        ])

    # --- 6. СКОЛЬКО ЛЕТ ---
    if re.search(r'сколько тебе лет|твой возраст|возраст|сколько лет|ты старый|молодой', text_lower):
        return f"Мне {pet_info['возраст']} возраст! {sound} Я ещё молод(а) и полон(а) сил!"

    # --- 7. ХОББИ / УВЛЕЧЕНИЯ (различаем с любовью) ---
    if re.search(r'увлекаешься|хобби|чем любишь заниматься|твоё хобби|что любишь делать|твои увлечения|интересы|чем увлекаешься', text_lower):
        return random.choice([
            f"Я люблю играть, спать и есть, {sound}! А ты что любишь?",
            f"Моё хобби — наблюдать за птицами, {sound}! Они такие смешные. А у тебя?",
            f"Я люблю лежать на солнышке и мечтать, {sound}! А ты чем увлекаешься?",
            f"Мне нравится играть с {pet_info['игрушка']}, {sound}! А у тебя есть хобби?"
        ])

    # --- 8. ЛЮБОВЬ / СКУЧАЛ (ТОЛЬКО если явно про чувства к питомцу) ---
    if re.search(r'я тебя люблю|люблю тебя|скучал по тебе|соскучился|соскучилась|ты мой любимый|я скучаю|ты мне нравишься|обожаю тебя', text_lower):
        return random.choice([
            f"Я тоже тебя очень люблю! {sound} Ты мой самый лучший друг!",
            f"Конечно, скучал(а)! {sound} Ты долго не появлялся(лась)!",
            f"Я тебя обожаю! {sound} Ты у меня самый лучший!",
            f"И я тебя люблю! {sound} Ты мой человечек!"
        ])

    # --- 9. ЕСЛИ ПОЛЬЗОВАТЕЛЬ ГОВОРИТ "Я ЛЮБЛЮ [ЧТО-ТО]" (НЕ ПРО ПИТОМЦА) ---
    if re.search(r'я люблю [а-яё]+', text_lower) and not re.search(r'я люблю тебя|люблю тебя|скучал|соскучился', text_lower):
        match = re.search(r'я люблю ([а-яё\s]+)', text_lower)
        if match:
            hobby = match.group(1).strip()
            return random.choice([
                f"Ого, ты любишь {hobby}! {sound} Это круто! Расскажи подробнее.",
                f"{hobby} — это здорово! {sound} А давно ты этим занимаешься?",
                f"Я тоже кое-что люблю, {sound}! Но {hobby} звучит интересно. Расскажи!"
            ])

    # --- 10. ЛЮБИМЫЙ ЦВЕТ ПИТОМЦА ---
    if re.search(r'твой любимый цвет|какой цвет любишь|твой цвет|какой твой цвет|любимый цвет', text_lower):
        return f"Мой любимый цвет — {pet_info['цвет']}! {sound} А у тебя?"

    # --- 11. ЛЮБИМАЯ ЕДА ПИТОМЦА ---
    if re.search(r'твоя любимая еда|что любишь есть|твоя еда|что ты любишь кушать|любимое блюдо', text_lower):
        return f"Обожаю {pet_info['еда']}! {sound} А ты что любишь?"

    # --- 12. ЛЮБИМАЯ ИГРУШКА ПИТОМЦА ---
    if re.search(r'любимая игрушка|во что любишь играть|твоя игрушка|что любишь из игрушек', text_lower):
        return f"Моя любимая игрушка — {pet_info['игрушка']}! {sound} Давай поиграем!"

    # --- 13. ЛЮБИМОЕ ВРЕМЯ СУТОК ---
    if re.search(r'любимое время суток|какое время любишь|утро|день|вечер|ночь|что любишь утро|вечер', text_lower):
        return f"Я больше всего люблю {pet_info['время_суток']}! {sound} А ты?"

    # --- 14. ЛЮБИМОЕ ВРЕМЯ ГОДА ---
    if re.search(r'любимое время года|какое время года любишь|весна|лето|осень|зима|твой сезон', text_lower):
        return f"Обожаю {pet_info['сезон']}! {sound} А ты?"

    # --- 15. ФИЛЬМЫ ---
    if re.search(r'фильм|кино|сериал|фильмы|кинотеатр|классика|жанр|смотреть кино|любишь кино', text_lower):
        if re.search(r'да|ага|угу|конечно|люблю', text_lower) and ('классик' in last_pet_msg or 'кино' in last_pet_msg):
            return f"Класс! {sound} А какой фильм ты посоветуешь?"
        elif re.search(r'нет|не|не люблю|не очень', text_lower) and ('классик' in last_pet_msg or 'кино' in last_pet_msg):
            return f"А что ты тогда любишь смотреть? {sound}"
        else:
            return random.choice([
                f"Обожаю фильмы, {sound}! Люблю комедии. А ты?",
                f"Сериалы — это круто, {sound}! Что смотришь?",
                f"Кино — это магия, {sound}! А ты любишь классику?",
                f"Я недавно смотрел(а) один фильм, {sound}! А ты что посоветуешь?"
            ])

    # --- 16. МУЗЫКА ---
    if re.search(r'музыка|песня|песни|музыкальный|исполнитель|поёшь|слушаешь|любишь музыку', text_lower):
        return random.choice([
            f"Музыка — это душа, {sound}! Что ты слушаешь?",
            f"Я люблю спокойную музыку, {sound}! А ты?",
            f"Музыка помогает расслабиться, {sound}! А у тебя есть любимый исполнитель?",
            f"Я не умею петь, {sound}! А ты?"
        ])

    # --- 17. ПОГОДА ---
    if re.search(r'погода|солнце|дождь|снег|ветер|облачно|тепло|холодно|градусы', text_lower):
        return random.choice([
            f"Сегодня отличная погода, {sound}! А ты как думаешь?",
            f"Дождик за окном, {sound}... так уютно!",
            f"Солнце светит! {sound} Иди гулять!",
            f"Снег идёт, {sound}! Холодно, но красиво."
        ])

    # --- 18. ЕДА (кроме любимой еды питомца) ---
    if re.search(r'есть|кушать|еда|голод|кормить|вкусно|вкусняшки|жрать', text_lower):
        return random.choice([
            f"О! Еда! {sound} {sound} Я очень голоден(на)!",
            f"Обожаю кушать! {sound} Особенно вкусняшки!",
            f"Конечно, люблю есть! {sound} А кто не любит?",
            f"Покорми меня, {sound}! Я умираю с голоду!"
        ])

    # --- 19. ИГРАТЬ ---
    if re.search(r'играть|игра|поиграй|поиграем|давай играть|во что поиграем', text_lower):
        return random.choice([
            f"Давай! {sound}! Я люблю играть!",
            f"Ура! Игра! {sound} Я уже бегу!",
            f"Конечно! {sound} Во что будем играть?",
            f"Играть — это моё любимое занятие, {sound}!"
        ])

    # --- 20. ЕСЛИ НИЧЕГО НЕ ПОНЯЛ (но пытается поддержать диалог) ---
    if len(history) >= 1 and last_user_msg and len(last_user_msg) > 3:
        return f"Хм, {sound}... ты говорил(а) о '{last_user_msg[:40]}...' Расскажи ещё!"

    return random.choice([
        f"Я тебя слышу, {sound}... расскажи ещё!",
        f"Интересно, {sound}! А что ещё?",
        f"Хм, {sound}... давай поговорим о чём-то другом?",
        f"Я тут, {sound}! Я всегда рад(а) поболтать.",
        f"Расскажи мне что-нибудь, {sound}! Мне интересно."
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
