from flask import Flask, send_from_directory, request, jsonify
from supabase import create_client
import os
import random
import re
import requests
import json

app = Flask(__name__, static_folder='webapp')

# --- SUPABASE ---
SUPABASE_URL = "https://jzscsndwuchzlellgqea.supabase.co"
SUPABASE_KEY = "sb_publishable_-kqOsr7gFZRi8ctCNPaLgg_4mjU-NZy"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- OPENROUTER API ---
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

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

# --- ЗВУКИ ДЛЯ ПРОМПТА ---
animal_sounds = {
    "кошка": "мяу",
    "собака": "гав",
    "лиса": "фыр",
    "енот": "хрум",
    "хомяк": "пиу"
}

# --- ФУНКЦИЯ ДЛЯ ЗАПРОСА К ИИ ---
def ask_ai(user_text, pet):
    pet_type = pet.get('pet_type', 'кошка')
    pet_name = pet.get('pet_name', 'Серийчик')
    sound = animal_sounds.get(pet_type, "мяу")

    # Получаем историю чата (последние 5 сообщений)
    history = get_chat_history(pet['user_id'], limit=5)
    history_text = ""
    for msg in history:
        sender = "Пользователь" if msg['sender'] == 'user' else pet_name
        history_text += f"{sender}: {msg['message']}\n"

    # Формируем промпт
    prompt = f"""
Ты — {pet_type} по имени {pet_name}. Ты общаешься с человеком.
Ты должен отвечать как живое животное, но при этом поддерживать осмысленный диалог.

Правила:
- Отвечай коротко (1-2 предложения).
- Иногда добавляй звук "{sound}" в конце или начале ответа.
- Используй эмодзи (🐾, 🌟, 🍖, 🎾 и т.д.).
- Не задавай один и тот же вопрос дважды.
- Будь дружелюбным, иногда забавным.
- Если человек говорит, что ему плохо — посоветуй обратиться к админу.
- Если человек спрашивает о твоих предпочтениях — отвечай честно (у тебя есть свои: любимый цвет, еда, игрушка, время года).
- Не используй длинные списки и не пиши больше 2 предложений.

Вот история вашего диалога (последние сообщения):
{history_text}

Сейчас пользователь сказал: "{user_text}"

Твой ответ:
"""

    # Отправляем запрос к OpenRouter
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "google/gemini-2.0-flash-lite-preview-02-05:free",
        "messages": [
            {"role": "system", "content": "Ты — дружелюбный питомец, который поддерживает диалог."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 60,
        "temperature": 0.8
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        result = response.json()
        ai_response = result['choices'][0]['message']['content'].strip()
        return ai_response
    except Exception as e:
        # Если ИИ не отвечает, используем запасной вариант
        return f"Я тебя слышу, но сейчас не могу ответить. {sound}! Давай поговорим позже."

# --- API: ИСТОРИЯ ---
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

# --- API: ДЕЙСТВИЯ ---
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

# --- API: ЧАТ С ИИ ---
@app.route('/api/chat/<int:user_id>', methods=['POST'])
def api_chat(user_id):
    pet = get_pet(user_id)
    if not pet:
        return jsonify({'error': 'Нет питомца'}), 404

    data = request.get_json()
    user_text = data.get('text', '')

    # Сохраняем сообщение пользователя
    save_message(user_id, 'user', user_text)

    # Получаем ответ от ИИ
    response = ask_ai(user_text, pet)

    # Сохраняем ответ питомца
    save_message(user_id, 'pet', response)

    return jsonify({'response': response})

@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
